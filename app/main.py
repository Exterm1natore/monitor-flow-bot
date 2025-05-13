from app.core import bot_setup, logging_setup


# --- Enable logging
logging_setup.enable_logging("ERROR")


if __name__ == "__main__":
    # --- Объект бота ---
    app = bot_setup.app

    # --- General commands ---
    bot_setup.add_general_commands_to_bot(app)

    # --- User commands ------
    bot_setup.add_user_command_to_bot(app)

    app.start_polling()
    app.idle()
