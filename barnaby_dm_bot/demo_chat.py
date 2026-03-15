"""
Demo Chat Interface for Unity MMA DM Bot
Run this to test the bot locally without Meta API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conversation_ai import get_ai_response, get_lead_data, is_lead_complete, save_leads_to_file
from config import GYM_INFO, BOOKING_URL, TRIAL_URL

def print_header():
    print("\n" + "="*60)
    print("🥊  UNITY MMA DM BOT - DEMO MODE")
    print("="*60)
    print("This simulates Instagram/Facebook DM conversations")
    print("Type 'quit' to exit, 'leads' to see captured leads")
    print("="*60 + "\n")

def print_bot_message(msg):
    print(f"\n💬 Bot: {msg}\n")

def print_lead_status(user_id):
    lead = get_lead_data(user_id)
    if lead:
        print("\n📋 Lead Data Captured:")
        print(f"   Name: {lead.get('name', '—')}")
        print(f"   Phone: {lead.get('phone', '—')}")
        print(f"   Email: {lead.get('email', '—')}")
        print(f"   Interest: {lead.get('interested_in', '—')}")
        print(f"   Experience: {lead.get('experience_level', '—')}")
        print(f"   Goal: {lead.get('fitness_goal', '—')}")
        if is_lead_complete(user_id):
            print("   ✅ Ready for follow-up!")
        print()

def main():
    print_header()

    # Simulate a user ID (like a real DM conversation would have)
    user_id = "demo_user_001"

    # Opening message
    opening = f"Hey there! 🥊 Welcome to {GYM_INFO['name']} - {GYM_INFO['tagline']}! How can I help you today?"
    print_bot_message(opening)

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'quit':
                save_leads_to_file()
                print("\n👊 Thanks for checking out Unity MMA! See you on the mats!\n")
                break

            if user_input.lower() == 'leads':
                print_lead_status(user_id)
                continue

            if user_input.lower() == 'newuser':
                import random
                user_id = f"demo_user_{random.randint(100, 999)}"
                print(f"\n🔄 Switched to new user: {user_id}\n")
                continue

            # Get AI response
            response = get_ai_response(user_id, user_input)
            print_bot_message(response)

            # Show lead status if we captured something
            lead = get_lead_data(user_id)
            if lead and any([lead.get('name'), lead.get('phone'), lead.get('email')]):
                print_lead_status(user_id)

        except KeyboardInterrupt:
            save_leads_to_file()
            print("\n\n👋 Bye!\n")
            break

if __name__ == "__main__":
    main()
