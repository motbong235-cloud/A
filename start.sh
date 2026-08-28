#!/usr/bin/env bash
# start.sh
# Runs the Telegram bot (polling) in the background and the Flask app
# (via Gunicorn) in the foreground, inside a single Render service.
#
# Why: Render's persistent disks attach to ONE service. Since the bot
# and the web app must read/write the same SQLite database, they need
# to run together in this one service rather than as two separate
# Render services with two separate disks.

set -e

echo "Starting Telegram bot (polling)..."
python bot.py &
BOT_PID=$!

echo "Starting Flask web app (gunicorn)..."
gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} app:app &
WEB_PID=$!

# If either process dies, stop the container so Render restarts it cleanly.
wait -n "$BOT_PID" "$WEB_PID"
exit $?
