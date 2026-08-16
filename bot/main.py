from telegram.error import InvalidToken
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers.admin import admin_commands, handle_admin_callback
from bot.handlers.commands import (
    handle_main_menu_callback,
    handle_user_message,
    start_command,
)
from bot.utils.logging import setup_logging

logger = setup_logging()


def main() -> None:
    init_db()
    if not BOT_TOKEN or BOT_TOKEN.startswith("your_bot_token_here"):
        logger.error("BOT_TOKEN is missing or still set to the placeholder value in .env")
        raise SystemExit("Set a valid BOT_TOKEN in .env before starting the bot.")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", admin_commands))
    application.add_handler(CommandHandler("users", admin_commands))
    application.add_handler(CommandHandler("pending", admin_commands))
    application.add_handler(CommandHandler("withdrawals", admin_commands))
    application.add_handler(CommandHandler("broadcast", admin_commands))
    application.add_handler(
        CallbackQueryHandler(
            handle_main_menu_callback,
            pattern=r"^(submit_uid|my_balance|withdraw_balance|my_stats|check_subscription)$",
        )
    )
    application.add_handler(CallbackQueryHandler(handle_admin_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    logger.info("Starting bot...")
    try:
        application.run_polling(allowed_updates=["message", "callback_query"])
    except InvalidToken as exc:
        logger.error("The provided Telegram bot token is invalid: %s", exc)
        raise SystemExit("Invalid Telegram bot token. Please update .env with a valid token.") from exc


if __name__ == "__main__":
    main()
