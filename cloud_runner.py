#!/usr/bin/env python3
"""
Unity MMA AI Systems - Cloud Runner
Runs Email Bot + Telegram Bot in parallel for 24/7 operation
Deploy on Render.com as a single background worker
"""

import os
import sys
import threading
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_email_bot():
    """Run the email bot in a thread."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Email Bot...")
    try:
        from barnaby_email_bot.run_live import run_live
        run_live()
    except Exception as e:
        print(f"[EMAIL BOT ERROR] {type(e).__name__}: {e}")
        # Keep trying to restart
        time.sleep(30)
        run_email_bot()

def run_telegram_bot():
    """Run the telegram bot in a thread."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Telegram Bot...")
    try:
        from telegram_bot.telegram_bot import main
        main()
    except Exception as e:
        print(f"[TELEGRAM BOT ERROR] {type(e).__name__}: {e}")
        # Keep trying to restart
        time.sleep(30)
        run_telegram_bot()

def main():
    """Main entry point - runs both bots."""
    print("\n" + "=" * 60)
    print("  UNITY MMA AI SYSTEMS - CLOUD RUNNER")
    print("=" * 60)
    print(f"\n  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Services:")
    print("    - Email Bot (info@unitymma.co.nz)")
    print("    - Telegram Bot (@UnityMMABot)")
    print("\n" + "=" * 60 + "\n")

    # Check which services to run based on env vars
    run_email = os.getenv("EMAIL_PASSWORD") is not None
    run_telegram = os.getenv("TELEGRAM_BOT_TOKEN") is not None

    threads = []

    if run_email:
        email_thread = threading.Thread(target=run_email_bot, daemon=True)
        email_thread.start()
        threads.append(("Email Bot", email_thread))
        print("[OK] Email Bot thread started")
    else:
        print("[SKIP] Email Bot - no EMAIL_PASSWORD configured")

    if run_telegram:
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
        threads.append(("Telegram Bot", telegram_thread))
        print("[OK] Telegram Bot thread started")
    else:
        print("[SKIP] Telegram Bot - no TELEGRAM_BOT_TOKEN configured")

    if not threads:
        print("\n[ERROR] No services configured! Check environment variables.")
        print("Required: EMAIL_PASSWORD and/or TELEGRAM_BOT_TOKEN")
        return

    # Keep main thread alive and monitor worker threads
    try:
        while True:
            time.sleep(60)
            # Health check
            for name, thread in threads:
                if not thread.is_alive():
                    print(f"[WARNING] {name} thread died, restarting...")
                    if "Email" in name:
                        new_thread = threading.Thread(target=run_email_bot, daemon=True)
                    else:
                        new_thread = threading.Thread(target=run_telegram_bot, daemon=True)
                    new_thread.start()
                    threads = [(n, new_thread if n == name else t) for n, t in threads]

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping all services...")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
