"""
VAPI Webhook Server for Unity MMA Voice Bot
Handles function calls from VAPI (booking, SMS, transfers)
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()

from config import PORT, GYM_INFO, TRIAL_URL

app = Flask(__name__)

# Store appointments/leads
APPOINTMENTS_FILE = os.path.expanduser("~/junction-ai/barnaby_voice_bot/appointments.json")
CALL_LOG_FILE = os.path.expanduser("~/junction-ai/barnaby_voice_bot/call_log.json")

def load_json(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return []

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

@app.route("/vapi/webhook", methods=["POST"])
def vapi_webhook():
    """Handle VAPI webhook events."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data"}), 400

    event_type = data.get("type", "")
    print(f"[VAPI] Event: {event_type}")

    # Handle different event types
    if event_type == "function-call":
        return handle_function_call(data)

    elif event_type == "call-started":
        log_call_event(data, "started")
        return jsonify({"status": "ok"})

    elif event_type == "call-ended":
        log_call_event(data, "ended")
        return jsonify({"status": "ok"})

    elif event_type == "transcript":
        # Real-time transcript updates
        return jsonify({"status": "ok"})

    elif event_type == "status-update":
        return jsonify({"status": "ok"})

    return jsonify({"status": "received"})

def handle_function_call(data):
    """Handle function calls from VAPI assistant."""
    function_call = data.get("functionCall", {})
    function_name = function_call.get("name", "")
    parameters = function_call.get("parameters", {})

    print(f"[VAPI] Function call: {function_name}")
    print(f"[VAPI] Parameters: {parameters}")

    if function_name == "book_trial":
        return book_trial(parameters)

    elif function_name == "send_trial_link":
        return send_trial_link(parameters)

    elif function_name == "transfer_to_coach":
        return transfer_to_coach(parameters)

    return jsonify({
        "result": "I'm sorry, I couldn't process that request. Let me take your information and have one of our coaches call you back."
    })

def book_trial(params):
    """Handle trial booking."""
    appointment = {
        "name": params.get("name", "Unknown"),
        "phone": params.get("phone", ""),
        "experience": params.get("experience", "beginner"),
        "interest": params.get("interest", "General"),
        "type": "free_trial",
        "date": "To be scheduled",
        "time": "To be scheduled",
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }

    # Save appointment
    appointments = load_json(APPOINTMENTS_FILE)
    appointments.append(appointment)
    save_json(APPOINTMENTS_FILE, appointments)

    print(f"[VAPI] Trial booked: {appointment}")

    response = f"Awesome, {appointment['name']}! I've got you down for a FREE trial. We'll text you at {appointment['phone']} with all the details. Can't wait to see you on the mats!"

    return jsonify({"result": response})

def send_trial_link(params):
    """Send trial booking link via SMS."""
    phone = params.get("phone", "")

    if not phone:
        return jsonify({
            "result": "I need your phone number to send you the trial booking link. What's the best number to text?"
        })

    # In production, integrate with Twilio here
    print(f"[VAPI] Would send SMS to {phone}: Book your FREE trial at {TRIAL_URL}")

    return jsonify({
        "result": f"I've sent a text to your phone with our free trial booking link. You can use that to schedule your session at your convenience. Is there anything else I can help with?"
    })

def transfer_to_coach(params):
    """Handle transfer to coach."""
    reason = params.get("reason", "Caller requested to speak with a coach")

    print(f"[VAPI] Transfer requested: {reason}")

    return jsonify({
        "result": "Let me connect you with one of our coaches. Please hold for just a moment."
    })

def log_call_event(data, event_type):
    """Log call events."""
    call_log = load_json(CALL_LOG_FILE)

    log_entry = {
        "call_id": data.get("callId", ""),
        "event": event_type,
        "timestamp": datetime.now().isoformat(),
        "duration": data.get("duration"),
        "caller": data.get("customer", {}).get("number", "Unknown")
    }

    call_log.append(log_entry)
    save_json(CALL_LOG_FILE, call_log)

    print(f"[VAPI] Call {event_type}: {log_entry}")

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "unity-mma-voice-bot"})

# View appointments
@app.route("/appointments", methods=["GET"])
def get_appointments():
    return jsonify(load_json(APPOINTMENTS_FILE))

# View call log
@app.route("/calls", methods=["GET"])
def get_calls():
    return jsonify(load_json(CALL_LOG_FILE))

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"🥊 Unity MMA Voice Bot Webhook Server")
    print(f"{'='*60}")
    print(f"Port: {PORT}")
    print(f"Webhook URL: http://localhost:{PORT}/vapi/webhook")
    print(f"{'='*60}\n")

    app.run(host="0.0.0.0", port=PORT, debug=True)
