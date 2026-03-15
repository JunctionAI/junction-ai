"""
Meta (Facebook/Instagram) Webhook Handler for Unity MMA DM Bot
Handles incoming messages from Instagram and Facebook Messenger
"""

import os
import json
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()

from conversation_ai import get_ai_response, save_leads_to_file, load_leads_from_file
from config import META_ACCESS_TOKEN, META_VERIFY_TOKEN, META_APP_SECRET, PORT, GYM_INFO, TRIAL_URL

app = Flask(__name__)

# Load existing leads on startup
load_leads_from_file()

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify the request signature from Meta."""
    if not META_APP_SECRET:
        return True  # Skip verification if no secret set (dev mode)

    expected = hmac.new(
        META_APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)

def send_message(recipient_id: str, message_text: str, platform: str = "messenger"):
    """Send a message back to the user via Meta API."""

    if not META_ACCESS_TOKEN:
        print(f"[DEMO MODE] Would send to {recipient_id}: {message_text}")
        return True

    # Determine API endpoint based on platform
    if platform == "instagram":
        url = f"https://graph.facebook.com/v18.0/me/messages"
    else:
        url = f"https://graph.facebook.com/v18.0/me/messages"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }

    headers = {
        "Content-Type": "application/json"
    }

    params = {
        "access_token": META_ACCESS_TOKEN
    }

    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        if response.status_code == 200:
            print(f"Message sent to {recipient_id}")
            return True
        else:
            print(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Webhook verification endpoint for Meta."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        print("Webhook verified!")
        return challenge, 200

    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming messages from Meta."""

    # Verify signature (optional in dev)
    signature = request.headers.get("X-Hub-Signature-256", "")
    if META_APP_SECRET and not verify_signature(request.data, signature):
        return "Invalid signature", 403

    data = request.get_json()

    if not data:
        return "No data", 400

    # Process the webhook event
    try:
        if "entry" in data:
            for entry in data["entry"]:
                # Handle messaging events
                if "messaging" in entry:
                    for event in entry["messaging"]:
                        process_messaging_event(event, platform="messenger")

                # Handle Instagram messaging
                elif "instagram" in entry or "instagram_business_account" in entry:
                    if "messaging" in entry:
                        for event in entry["messaging"]:
                            process_messaging_event(event, platform="instagram")

                # Handle changes (Instagram DMs come through this)
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            value = change.get("value", {})
                            if "messages" in value:
                                for msg in value["messages"]:
                                    process_instagram_message(msg, value)

    except Exception as e:
        print(f"Error processing webhook: {e}")

    # Save leads after each interaction
    save_leads_to_file()

    return "OK", 200

def process_messaging_event(event: dict, platform: str = "messenger"):
    """Process a messaging event from Facebook/Instagram."""

    sender_id = event.get("sender", {}).get("id")
    recipient_id = event.get("recipient", {}).get("id")

    if not sender_id:
        return

    # Handle message
    if "message" in event:
        message = event["message"]

        # Skip if it's an echo of our own message
        if message.get("is_echo"):
            return

        text = message.get("text", "")

        if text:
            print(f"[{platform.upper()}] Received from {sender_id}: {text}")

            # Get AI response
            response = get_ai_response(sender_id, text)

            # Send response
            send_message(sender_id, response, platform)

    # Handle postback (button clicks)
    elif "postback" in event:
        payload = event["postback"].get("payload", "")
        print(f"[{platform.upper()}] Postback from {sender_id}: {payload}")

        if payload == "GET_STARTED":
            welcome = f"Hey there! 🥊 Welcome to {GYM_INFO['name']}! I'm here to help you start your martial arts journey. What can I help you with today?\n\n• Classes & Training\n• Pricing & Memberships\n• Location & Hours\n• Book a FREE Trial"
            send_message(sender_id, welcome, platform)
        else:
            response = get_ai_response(sender_id, payload)
            send_message(sender_id, response, platform)

def process_instagram_message(msg: dict, value: dict):
    """Process Instagram DM from webhook."""

    sender_id = msg.get("from", {}).get("id")
    text = msg.get("text", "")

    if sender_id and text:
        print(f"[INSTAGRAM] Received from {sender_id}: {text}")

        # Get AI response
        response = get_ai_response(sender_id, text)

        # Send response via Instagram API
        send_instagram_reply(sender_id, response, value)

def send_instagram_reply(recipient_id: str, message_text: str, context: dict = None):
    """Send reply to Instagram DM."""

    if not META_ACCESS_TOKEN:
        print(f"[DEMO MODE] Would send to IG {recipient_id}: {message_text}")
        return True

    # Get the Instagram business account ID from context
    ig_id = None
    if context:
        ig_id = context.get("id")

    if not ig_id:
        print("No Instagram account ID found")
        return False

    url = f"https://graph.facebook.com/v18.0/{ig_id}/messages"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    params = {
        "access_token": META_ACCESS_TOKEN
    }

    try:
        response = requests.post(url, json=payload, params=params)
        if response.status_code == 200:
            print(f"IG message sent to {recipient_id}")
            return True
        else:
            print(f"Failed to send IG message: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending IG message: {e}")
        return False

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "unity-mma-dm-bot"})

# Leads dashboard endpoint
@app.route("/leads", methods=["GET"])
def get_leads():
    """Get all captured leads (protected endpoint)."""
    from conversation_ai import get_all_leads
    return jsonify(get_all_leads())

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"🥊 Unity MMA DM Bot Starting...")
    print(f"{'='*50}")
    print(f"Port: {PORT}")
    print(f"Webhook URL: http://localhost:{PORT}/webhook")
    print(f"Meta Token: {'✅ Set' if META_ACCESS_TOKEN else '❌ Not set (Demo Mode)'}")
    print(f"{'='*50}\n")

    app.run(host="0.0.0.0", port=PORT, debug=True)
