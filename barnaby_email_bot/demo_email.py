#!/usr/bin/env python3
"""
Demo Email Bot for Unity MMA
Test email classification and responses without live email server
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_handler import demo_process_email, get_stats, get_escalations

def print_header():
    print("\n" + "="*60)
    print("  Unity MMA Email Bot - Demo Mode")
    print("="*60)
    print("\nTest the email automation without live server connection.")
    print("Type an email to test, or 'preset' for preset tests.\n")

def print_result(result):
    """Pretty print email processing result."""
    print(f"\n{'─'*50}")
    print(f"From: {result['email']['sender']}")
    print(f"Subject: {result['email']['subject']}")
    print(f"{'─'*50}")
    print(f"Intent: {result['intent']}")
    print(f"Action: {result['action'].upper()}")
    print(f"Confidence: {result['confidence']:.0%}")

    if result['action'] == 'auto_reply' and 'draft_response' in result:
        print(f"\n{'─'*25} DRAFT RESPONSE {'─'*25}")
        print(result['draft_response'])
        print(f"{'─'*60}")
    elif result['action'] == 'escalate':
        print("\n[!] This email has been flagged for human review.")

def run_preset_tests():
    """Run preset email scenarios."""
    print("\n" + "="*60)
    print("  Running Preset Tests")
    print("="*60)

    tests = [
        {
            "name": "First-Timer Enquiry",
            "subject": "Interested in joining",
            "body": "Hi, I'm interested in joining Unity MMA. I've never done martial arts before but I'd love to try. What classes do you have for beginners?",
            "sender": "john.smith@gmail.com"
        },
        {
            "name": "Class Schedule Query",
            "subject": "When is the next Jiu Jitsu class?",
            "body": "Hey, can you tell me what days you have BJJ classes? Looking to come in this week.",
            "sender": "sarah@outlook.com"
        },
        {
            "name": "Pricing Question",
            "subject": "Membership costs",
            "body": "What are your membership prices? Do you offer any trials?",
            "sender": "mike.johnson@gmail.com"
        },
        {
            "name": "Cancellation Request",
            "subject": "Cancel my membership",
            "body": "Hi, I need to cancel my membership effective immediately. I'm moving overseas next week. Please confirm cancellation.",
            "sender": "member123@hotmail.com"
        },
        {
            "name": "Payment Issue",
            "subject": "Payment failed",
            "body": "My payment failed this week and I got an error. Can you help me fix this? I don't want to lose access.",
            "sender": "billing.issue@gmail.com"
        },
        {
            "name": "System Noise",
            "subject": "Your receipt from Stripe",
            "body": "This is an automated email. Your payment of $49.99 has been processed. Transaction ID: abc123. Do not reply to this email.",
            "sender": "noreply@stripe.com"
        }
    ]

    for test in tests:
        print(f"\n\n{'='*60}")
        print(f"  TEST: {test['name']}")
        print(f"{'='*60}")

        result = demo_process_email(
            subject=test["subject"],
            body=test["body"],
            sender=test["sender"]
        )
        print_result(result)

        input("\nPress Enter for next test...")


def quick_test(body: str, subject: str = "Test Email"):
    """Quick test with just body text."""
    result = demo_process_email(
        subject=subject,
        body=body,
        sender="test@example.com"
    )
    print_result(result)


def interactive_mode():
    """Interactive email testing mode - simple and direct."""
    print("\n" + "="*60)
    print("  Interactive Mode")
    print("="*60)
    print("\nCommands: 'preset' | 'stats' | 'quit'")
    print("Or just type an email body to test classification:\n")

    while True:
        print("-"*40)
        user_input = input("📧 Enter email body (or command): ").strip()

        if not user_input:
            continue

        # Check for commands
        cmd = user_input.lower()

        if cmd == 'quit' or cmd == 'q':
            break
        elif cmd == 'preset' or cmd == 'presets':
            run_preset_tests()
            print("\nBack to interactive mode. Commands: 'preset' | 'stats' | 'quit'\n")
            continue
        elif cmd == 'stats':
            stats = get_stats()
            print(f"\n📊 Email Statistics:")
            print(f"   Total processed: {stats.get('total', 0)}")
            print(f"   Auto-replied: {stats.get('auto_replied', 0)}")
            print(f"   Escalated: {stats.get('escalated', 0)}")
            print(f"   Ignored: {stats.get('ignored', 0)}\n")
            continue
        elif cmd == 'escalations':
            escalations = get_escalations()
            if escalations:
                print(f"\n⚠️  Escalated Emails ({len(escalations)}):")
                for esc in escalations[-5:]:
                    print(f"   - {esc['subject']} ({esc['intent']})")
            else:
                print("\n✓ No escalations yet.")
            print()
            continue

        # Anything else = treat as email body for quick test
        quick_test(user_input)
        print()


def main():
    print_header()

    print("Enter email body to test, or choose:")
    print("  preset  - Run preset test scenarios")
    print("  quit    - Exit")
    print()

    user_input = input("📧 Email body (or command): ").strip()

    if not user_input:
        print("No input. Starting interactive mode...")
        interactive_mode()
    elif user_input.lower() in ['preset', 'presets', '1']:
        run_preset_tests()
    elif user_input.lower() in ['quit', 'q']:
        print("Bye!")
        return
    else:
        # User typed something - treat as email body
        quick_test(user_input)
        print()
        # Continue to interactive mode
        interactive_mode()

    # Show final stats
    print("\n" + "="*60)
    print("  Session Statistics")
    print("="*60)
    stats = get_stats()
    print(f"  Total processed: {stats.get('total', 0)}")
    print(f"  Auto-replied: {stats.get('auto_replied', 0)}")
    print(f"  Escalated: {stats.get('escalated', 0)}")
    print(f"  Ignored: {stats.get('ignored', 0)}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
