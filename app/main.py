from app.core import bot_setup


if __name__ == "__main__":
    # --- Объект бота ---
    app = bot_setup.app

    # --- Commands ---
    bot_setup.add_basic_commands_to_bot(app)

    app.start_polling()
    app.idle()
