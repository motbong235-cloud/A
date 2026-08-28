"""
app.py
Flask web server for the activation link system.

Routes:
    GET/HEAD /              -> health check (for Render / uptime monitors)
    GET  /activate/<token>   -> shows activate / expired / invalid / used page
    POST /activate/<token>   -> performs the actual activation (one-time)
    GET  /success/<id>       -> confirmation screen
"""

import logging
import os

from flask import Flask, render_template, request, redirect, url_for, abort

import database
import token_service
from config import config
from token_service import TokenStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("activation-app")

app = Flask(__name__)
app.config["DEBUG"] = config.DEBUG


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


def _client_ip() -> str:
    # Respect a reverse proxy (Nginx) if X-Forwarded-For is set, else remote_addr.
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/", methods=["GET", "HEAD"])
def health_check():
    # Simple 200 OK so Render's health check (and any uptime monitor)
    # sees the service as healthy. Real activation links live at
    # /activate/<token>.
    return "Activation system is running.", 200


@app.route("/activate/<token>", methods=["GET"])
def activate_page(token):
    status, row = token_service.check_token(token)

    if status == TokenStatus.INVALID:
        return render_template("invalid.html"), 404
    if status == TokenStatus.EXPIRED:
        return render_template("expired.html"), 410
    if status == TokenStatus.REVOKED:
        return render_template("invalid.html", reason="revoked"), 403
    if status == TokenStatus.ALREADY_USED:
        return render_template("invalid.html", reason="used"), 409

    # VALID
    return render_template(
        "activate.html",
        token=token,
        service_name=config.SERVICE_NAME,
    )


@app.route("/activate/<token>", methods=["POST"])
def activate_submit(token):
    ip = _client_ip()
    user_agent = request.headers.get("User-Agent", "unknown")[:255]

    status, row = token_service.activate_token(token, ip, user_agent)

    if status == TokenStatus.INVALID:
        return render_template("invalid.html"), 404
    if status == TokenStatus.EXPIRED:
        return render_template("expired.html"), 410
    if status == TokenStatus.REVOKED:
        return render_template("invalid.html", reason="revoked"), 403
    if status == TokenStatus.ALREADY_USED:
        return render_template("invalid.html", reason="used"), 409

    logger.info("Activation success id=%s ip=%s", row["id"], ip)
    return redirect(url_for("success_page", activation_id=row["id"]))


@app.route("/success/<int:activation_id>", methods=["GET"])
def success_page(activation_id):
    with database.get_conn() as conn:
        cur = conn.execute(
            "SELECT * FROM activations WHERE id = ? AND activated = 1",
            (activation_id,),
        )
        row = cur.fetchone()

    if row is None:
        abort(404)

    return render_template(
        "success.html",
        activation_id=activation_id,
        service_name=config.SERVICE_NAME,
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("invalid.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Internal server error")
    return render_template("invalid.html", reason="error"), 500


if __name__ == "__main__":
    problems = config.validate()
    if problems:
        for p in problems:
            logger.warning("Config warning: %s", p)

    database.init_db()
    logger.info("Database ready at %s", config.DATABASE_PATH)
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG)

