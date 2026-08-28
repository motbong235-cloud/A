# Deploying to Render

This project ships with a `render.yaml` Blueprint plus a `start.sh` that
runs **both** the Flask web app and the Telegram bot inside **one**
Render service.

### Why one service instead of two

Render's persistent disks attach to a single service — they are not
shared between separate services. The bot writes token hashes and the
web app reads/updates them in the same SQLite file, so they need to
share a disk. Running them together in one service (bot in the
background, Gunicorn in the foreground) is the simplest way to get
that shared, persistent SQLite file without switching databases.

> If you'd rather run the bot and web app as fully separate Render
> services (e.g. to scale the web app independently), switch from
> SQLite to Render's managed **Postgres** and update `database.py`
> accordingly — Postgres can be shared across services, a local SQLite
> file cannot.

---

## Option A — Deploy with the Blueprint (recommended)

1. Push this project to a GitHub/GitLab repo.
2. In the Render dashboard: **New → Blueprint**, and point it at your repo.
   Render will read `render.yaml` and provision:
   - One **Web Service** (`activation-system`) running `bash start.sh`
   - A **1 GB persistent disk** mounted at `database/`
3. Render will prompt you for the env vars marked `sync: false`:
   - `BOT_TOKEN` — from @BotFather
   - `ADMIN_TELEGRAM_ID` — your numeric Telegram ID
   - `DOMAIN` — your Render URL, e.g. `https://activation-system.onrender.com`
     (or your custom domain once attached — see below)
4. Click **Apply**. First deploy takes a few minutes.

## Option B — Manual setup (no Blueprint)

1. **New → Web Service**, connect your repo.
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `bash start.sh`
4. **Environment → Add Disk:**
   - Name: `activation-data`
   - Mount path: `database`
   - Size: 1 GB
5. **Environment Variables:**
   ```
   BOT_TOKEN=<from BotFather>
   ADMIN_TELEGRAM_ID=<your Telegram user id>
   DOMAIN=https://<your-service>.onrender.com
   TOKEN_EXPIRY_SECONDS=3600
   DATABASE_PATH=database/activation.db
   FLASK_HOST=0.0.0.0
   DEBUG=false
   SERVICE_NAME=My Premium Service
   ```
6. Deploy.

---

## Custom domain

Render → your service → **Settings → Custom Domain** → add your domain
and follow the DNS instructions (CNAME to your `onrender.com` host).
Render issues a free TLS certificate automatically. Once attached,
update the `DOMAIN` env var to your custom domain and redeploy so
generated activation links use it.

---

## Verifying after deploy

1. Check the **Logs** tab — you should see both:
   `Starting Telegram bot (polling)...` and
   `Starting Flask web app (gunicorn)...`
2. Message your bot `/start` on Telegram → **Generate Activation Link**.
3. Open the link — it should load on your Render URL/custom domain.
4. As admin, run `/stats` in the bot to confirm the database is being
   written to correctly.

## Notes on the free/starter plan

- Render's free web services spin down after inactivity, which would
  drop the bot's polling connection. Use at least the **Starter** paid
  plan (as set in `render.yaml`) for a bot that must stay online and
  responsive 24/7.
- The persistent disk survives deploys and restarts, but **not**
  deleting the service — back up `database/activation.db` periodically
  if the data matters long-term (e.g. via a scheduled job that copies
  it somewhere, since Render disks aren't automatically backed up).
