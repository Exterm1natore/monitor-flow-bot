from app.core import bot_setup, logging_setup
from app import api

# --- Enable logging
logging_setup.enable_logging("ERROR")


def main():
    # --- Объект бота ---
    app = bot_setup.app

    # --- General commands ---
    bot_setup.add_general_commands_to_bot(app)

    # --- User commands ------
    bot_setup.add_user_command_to_bot(app)

    # --- Admin commands -----
    bot_setup.add_admin_commands_to_bot(app)

    app.start_polling()
    app.idle()


if __name__ == "__main__":
    # --- Run server ---
    api.run_zabbix_webhook_handler_server()

    # --- Start bot ---
    main()
