"""
bot.py
Telegram bot for generating and managing activation links.

Uses python-telegram-bot v20+ (async API).

User commands:
    /start      - welcome + "Generate Activation Link" button
    /help       - usage info
    /generate   - generate a new activation link directly

Admin commands (ADMIN_TELEGRAM_ID only):
    /stats          - counts of total/active/used/expired/revoked tokens
    /revoke TOKEN   - revoke a raw token
    /check TOKEN    - check the status of a raw token
"""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import database
import token_service
from config import config
from token_service import TokenStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("activation-bot")


def is_admin(user_id: int) -> bool:
    return config.ADMIN_TELEGRAM_ID != 0 and user_id == config.ADMIN_TELEGRAM_ID


# ---------------------------------------------------------------------------
# User commands
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔐 Generate Activation Link", callback_data="generate")]]
    )
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "🔐 *Activation System*\n\n"
        "Generate your secure activation link below.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Available commands*\n\n"
        "/start - show the main menu\n"
        "/generate - generate a new activation link\n"
        "/help - show this message",
        parse_mode="Markdown",
    )


async def _send_new_link(user_id: int, send_func):
    raw_token, activation_url = token_service.create_activation_link(user_id)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 ACTIVATE NOW", url=activation_url)]]
    )
    minutes = config.TOKEN_EXPIRY_SECONDS // 60
    await send_func(
        "🔐 *Your Activation Link*\n\n"
        f"This link is valid for {minutes} minutes and can only be used once.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await _send_new_link(user_id, update.message.reply_text)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "generate":
        user_id = query.from_user.id
        await _send_new_link(user_id, query.message.reply_text)


# ---------------------------------------------------------------------------
# Admin commands
# ---------------------------------------------------------------------------

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    s = database.get_stats()
    await update.message.reply_text(
        "📊 *Activation Stats*\n\n"
        f"Total Tokens: {s['total']}\n"
        f"Active Tokens: {s['active']}\n"
        f"Used Tokens: {s['used']}\n"
        f"Expired Tokens: {s['expired']}\n"
        f"Revoked Tokens: {s['revoked']}",
        parse_mode="Markdown",
    )


async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /revoke TOKEN")
        return

    raw_token = context.args[0]
    token_hash = token_service.hash_token(raw_token)
    success = database.revoke_token(token_hash)

    if success:
        await update.message.reply_text("✅ Token revoked.")
    else:
        await update.message.reply_text("❌ Token not found.")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /check TOKEN")
        return

    raw_token = context.args[0]
    status, row = token_service.check_token(raw_token)

    if row is None:
        await update.message.reply_text(f"Status: {status.value}")
        return

    await update.message.reply_text(
        f"Status: {status.value}\n"
        f"ID: {row['id']}\n"
        f"Telegram User: {row['telegram_user_id']}\n"
        f"Created: {row['created_at']}\n"
        f"Expires: {row['expires_at']}\n"
        f"Activated: {bool(row['activated'])}\n"
        f"Revoked: {bool(row['revoked'])}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    problems = config.validate()
    if problems:
        for p in problems:
            logger.warning("Config warning: %s", p)

    database.init_db()
    logger.info("Database ready at %s", config.DATABASE_PATH)

    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("generate", generate))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("revoke", revoke))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CallbackQueryHandler(on_button, pattern="^generate$"))

    logger.info("Bot starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
