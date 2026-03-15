# Unity MMA AI Systems - Procfile
# For Heroku-style deployments (Render also supports this)

# Email Bot Worker
email: python barnaby_email_bot/run_live.py

# Telegram Bot Worker
telegram: python telegram_bot/telegram_bot.py

# Combined runner (runs both bots in one process)
worker: python cloud_runner.py
