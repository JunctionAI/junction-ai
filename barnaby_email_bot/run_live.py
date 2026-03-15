#!/usr/bin/env python3
"""
Unity MMA Email Bot - LIVE MODE (Multi-Inbox)
Continuously monitors info@ and hello@ inboxes
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_handler import EmailBot, get_stats
from config import EMAIL_ACCOUNTS

# Check interval (seconds) - 30s for testing, increase to 60s for production
CHECK_INTERVAL = 30

def print_banner():
    print("\n" + "="*60)
    print("  UNITY MMA EMAIL BOT - MULTI-INBOX MODE")
    print("="*60)
    print(f"\n  Monitoring {len(EMAIL_ACCOUNTS)} inbox(es):")
    for acc in EMAIL_ACCOUNTS:
        if acc.get("password"):
            print(f"    - {acc['user']}")
    print(f"\n  Check interval: {CHECK_INTERVAL} seconds")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n  Actions:")
    print("    - AUTO-REPLY: First-timers, class info, pricing")
    print("    - ESCALATE: Cancellations, billing, complaints")
    print("    - IGNORE: System emails, receipts, spam")
    print("\n  Press Ctrl+C to stop")
    print("="*60 + "\n")

def run_live():
    """Run the live email processor for multiple inboxes."""
    print_banner()

    # Create bot instances for each configured account
    bots = []
    for acc in EMAIL_ACCOUNTS:
        if not acc.get("password"):
            print(f"[SKIP] {acc['name']} - no password configured")
            continue

        bot = EmailBot(
            email_user=acc["user"],
            email_password=acc["password"],
            account_name=acc["name"]
        )

        # Test connections
        print(f"[{acc['name']}] Connecting to IMAP...")
        if not bot.connect_imap():
            print(f"[{acc['name']}] IMAP FAILED - skipping this inbox")
            continue

        print(f"[{acc['name']}] IMAP OK!")
        print(f"[{acc['name']}] Connecting to SMTP...")

        if not bot.connect_smtp():
            print(f"[{acc['name']}] SMTP FAILED - auto-replies disabled for this inbox")
        else:
            print(f"[{acc['name']}] SMTP OK!")

        bots.append(bot)

    if not bots:
        print("\n[ERROR] No inboxes configured! Check EMAIL_USER/EMAIL_PASSWORD env vars.")
        return

    print(f"\n[LIVE] Monitoring {len(bots)} inbox(es)... (checking every {CHECK_INTERVAL}s)\n")

    cycle = 0
    try:
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            total_results = []

            # Process each inbox
            for bot in bots:
                try:
                    results = bot.process_inbox(limit=10)

                    if results:
                        print(f"\n[{timestamp}] [{bot.account_name}] Processed {len(results)} email(s):")
                        for result in results:
                            email_data = result["email"]
                            action_symbol = {
                                "auto_reply": "REPLY",
                                "escalate": "ESCALATE",
                                "ignore": "IGNORE"
                            }.get(result["action"], "???")

                            sent_status = " [SENT]" if result.get("response_sent") else ""
                            inbox_tag = f"[{email_data.get('inbox', 'unknown')}]"
                            print(f"  {inbox_tag} [{action_symbol}]{sent_status} {result['intent']}: {email_data['subject'][:35]}...")
                            print(f"           From: {email_data['sender_email']}")

                        total_results.extend(results)

                except Exception as e:
                    print(f"[{timestamp}] [{bot.account_name}] Error: {type(e).__name__}: {e}")
                    # Try to reconnect this bot
                    bot.disconnect()
                    time.sleep(2)
                    bot.connect_imap()

            # Heartbeat every 5 cycles if no emails processed
            if not total_results and cycle % 5 == 0:
                stats = get_stats()
                inbox_names = ", ".join([b.account_name for b in bots])
                print(f"[{timestamp}] Waiting... ({inbox_names}) | processed: {stats.get('total', 0)}, replied: {stats.get('auto_replied', 0)}, escalated: {stats.get('escalated', 0)}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping email bot...")
        for bot in bots:
            bot.disconnect()

        # Final stats
        stats = get_stats()
        print("\n" + "="*60)
        print("  SESSION SUMMARY")
        print("="*60)
        print(f"  Inboxes monitored: {len(bots)}")
        print(f"  Total processed: {stats.get('total', 0)}")
        print(f"  Auto-replied: {stats.get('auto_replied', 0)}")
        print(f"  Escalated: {stats.get('escalated', 0)}")
        print(f"  Ignored: {stats.get('ignored', 0)}")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/junction-ai/.env"))

    run_live()
