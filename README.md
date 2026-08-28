# Activation Link System

A production-ready activation link system: a Telegram bot generates secure,
one-time activation links for **your own service**, hosted on **your own
domain**. Not affiliated with, and does not interoperate with, Google's
`serviceactivation.google.com`.

---

## 1. Requirements

- Python 3.11+
- A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- A domain (or subdomain) you control, with HTTPS in production
- Linux/macOS/Windows for local development

---

## 2. Installation

```bash
git clone <your-repo-or-copy-these-files> activation-system
cd activation-system

python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Create Your Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts.
3. Copy the bot token BotFather gives you.
4. Get your own numeric Telegram user ID (e.g. via [@userinfobot](https://t.me/userinfobot)) — this becomes `ADMIN_TELEGRAM_ID`.

---

## 4. Configure `.env`

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=123456:ABC-your-real-bot-token
ADMIN_TELEGRAM_ID=123456789
DOMAIN=https://mydomain.com
TOKEN_EXPIRY_SECONDS=3600
DATABASE_PATH=database/activation.db
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=false
SERVICE_NAME=My Premium Service
```

`DOMAIN` must be a domain you control. During local testing this can be
`http://127.0.0.1:5000`.

---

## 5. Run Flask (the web app)

```bash
python app.py
```

This automatically creates `database/activation.db` and the `activations`
table on first run.

---

## 6. Run the Telegram Bot

In a second terminal (with the venv activated):

```bash
python bot.py
```

---

## 7. Test the Activation Link

1. Message your bot `/start` (or `/generate`).
2. Tap **🔐 Generate Activation Link**, then **🚀 ACTIVATE NOW**.
3. Confirm the activation page loads, shows "Ready to activate", and that
   clicking **🚀 Activate Now** redirects to the success page.
4. Reload the same link — it should now show "Already Used".
5. Wait past `TOKEN_EXPIRY_SECONDS` (or lower it temporarily for testing)
   and confirm an unused link shows "Expired".
6. As the admin, try `/stats`, `/check <token>`, and `/revoke <token>`.

---

## 8. Production Deployment (Ubuntu VPS)

### 8.1 Install system packages

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv nginx
```

### 8.2 Deploy the code

```bash
cd /opt
sudo git clone <your-repo> activation-system
cd activation-system
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with real production values
```

### 8.3 Run Flask with Gunicorn

```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

For a persistent service, create `/etc/systemd/system/activation-web.service`:

```ini
[Unit]
Description=Activation Link System (Flask/Gunicorn)
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/activation-system
EnvironmentFile=/opt/activation-system/.env
ExecStart=/opt/activation-system/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

And `/etc/systemd/system/activation-bot.service`:

```ini
[Unit]
Description=Activation Link System (Telegram Bot)
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/activation-system
EnvironmentFile=/opt/activation-system/.env
ExecStart=/opt/activation-system/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start both:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now activation-web activation-bot
```

### 8.4 Nginx reverse proxy

`/etc/nginx/sites-available/activation-system`:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/activation-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8.5 HTTPS with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d YOUR_DOMAIN.com
```

Certbot will configure HTTPS and auto-renewal.

---

## 9. Security Recommendations / Checklist

- [x] Tokens generated with `secrets.token_urlsafe(64)` (cryptographically secure)
- [x] Only SHA-256 hashes of tokens are stored — raw tokens are never persisted
- [x] Tokens expire after `TOKEN_EXPIRY_SECONDS` (default 1 hour)
- [x] Tokens are single-use (`activated` flag, enforced atomically in the UPDATE query)
- [x] Activation happens via POST only, never GET
- [x] Admin commands gated on `ADMIN_TELEGRAM_ID`
- [x] Parameterized SQL queries throughout (no string-built SQL)
- [x] Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- [x] `DEBUG=false` in production — no stack traces exposed
- [x] `.env` used for all secrets — nothing hardcoded in source
- [ ] Put the app behind HTTPS (via Nginx + Certbot, see above) — required in production
- [ ] Add rate limiting at the Nginx or application layer for `/activate/<token>` POST
- [ ] Rotate `BOT_TOKEN` if it is ever exposed
- [ ] Back up `database/activation.db` regularly
- [ ] Restrict file permissions on `.env` (`chmod 600 .env`)

---

## 10. About Google Integration

This system does **not** and cannot generate valid `serviceactivation.google.com`
links — that flow is entirely controlled by Google. `google_partner.py`
contains a clearly-marked, inert placeholder for wiring in a **legitimate**
Google Partner/Subscription API integration later, if your project is
actually enrolled in the relevant Google partner program. Until then, the
system runs fully self-contained on your own domain.
