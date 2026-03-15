#!/usr/bin/env python3
"""
Unity MMA Demo Launcher
Run this to demo DM Bot, Voice Bot, and Email Bot
"""

import os
import sys

def print_header():
    print("\n" + "="*60)
    print("🥊  UNITY MMA - AI SYSTEMS DEMO")
    print("="*60)
    print("\nThree AI systems for Unity MMA:")
    print()
    print("  1. 💬 DM Bot - Instagram/Facebook messaging")
    print("     - Context-aware (knows current day/time)")
    print("     - Detects members vs new prospects")
    print("     - Answers FAQs, captures leads, books trials")
    print()
    print("  2. 🎙️ Voice Bot - 24/7 Phone receptionist")
    print("     - Natural, coach-like conversation")
    print("     - Books trial sessions via voice")
    print("     - Transfers to coaches when needed")
    print()
    print("  3. 📧 Email Bot - Inbox automation")
    print("     - Auto-replies to common enquiries (70%+)")
    print("     - Escalates cancellations, billing to humans")
    print("     - Professional tone for email, casual for DMs")
    print()
    print("="*60)

def main():
    print_header()

    while True:
        print("\nSelect demo:")
        print("  [1] DM Bot Demo (text chat)")
        print("  [2] Voice Bot Demo (simulated call)")
        print("  [3] Email Bot Demo (inbox automation)")
        print("  [4] View Leads Dashboard")
        print("  [5] View Appointments Dashboard")
        print("  [6] View Email Dashboard")
        print("  [7] Start All Servers (production mode)")
        print("  [q] Quit")
        print()

        choice = input("Enter choice: ").strip().lower()

        if choice == "1":
            print("\n🚀 Starting Unity MMA DM Bot Demo...\n")
            os.system("cd ~/junction-ai/barnaby_dm_bot && python3 demo_chat.py")

        elif choice == "2":
            print("\n🚀 Starting Unity MMA Voice Bot Demo...\n")
            os.system("cd ~/junction-ai/barnaby_voice_bot && python3 demo_call.py")

        elif choice == "3":
            print("\n🚀 Starting Unity MMA Email Bot Demo...\n")
            os.system("cd ~/junction-ai/barnaby_email_bot && python3 demo_email.py")

        elif choice == "4":
            print("\n🚀 Starting Leads Dashboard...")
            print("   Open http://localhost:8501 in browser")
            os.system("cd ~/junction-ai/barnaby_dm_bot && streamlit run leads_dashboard.py")

        elif choice == "5":
            print("\n🚀 Starting Appointments Dashboard...")
            print("   Open http://localhost:8501 in browser")
            os.system("cd ~/junction-ai/barnaby_voice_bot && streamlit run appointments_dashboard.py")

        elif choice == "6":
            print("\n🚀 Starting Email Dashboard...")
            print("   Open http://localhost:8501 in browser")
            os.system("cd ~/junction-ai/barnaby_email_bot && streamlit run email_dashboard.py")

        elif choice == "7":
            print("\n🚀 Starting production servers...")
            print("   DM Bot Webhook: http://localhost:5000/webhook")
            print("   Voice Bot Webhook: http://localhost:5001/vapi/webhook")
            print("\n   Press Ctrl+C to stop\n")

            # Start both servers
            import subprocess
            dm_process = subprocess.Popen(
                ["python3", "meta_webhook.py"],
                cwd=os.path.expanduser("~/junction-ai/barnaby_dm_bot")
            )
            voice_process = subprocess.Popen(
                ["python3", "webhook_server.py"],
                cwd=os.path.expanduser("~/junction-ai/barnaby_voice_bot")
            )

            try:
                dm_process.wait()
                voice_process.wait()
            except KeyboardInterrupt:
                print("\n\nStopping servers...")
                dm_process.terminate()
                voice_process.terminate()

        elif choice == "q":
            print("\n👋 Bye! Good luck with the demo!\n")
            break

        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
