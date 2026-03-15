# Unity MMA Voice Receptionist

AI-powered 24/7 phone receptionist using VAPI. Answers calls, provides gym info, and books free trials.

## Quick Start (Demo Mode)

```bash
cd ~/junction-ai/barnaby_voice_bot
pip install -r requirements.txt
python demo_call.py
```

This simulates phone conversations without needing VAPI setup.

## Full Setup (Production with VAPI)

### 1. Create VAPI Account

1. Go to https://vapi.ai/
2. Create an account
3. Get your API key from the dashboard

### 2. Environment Variables

Add to your `.env`:
```bash
VAPI_API_KEY=your_vapi_api_key
OPENAI_API_KEY=your_openai_key  # VAPI uses this for voice
```

### 3. Create Assistant in VAPI

Run this to generate the config:
```bash
python vapi_assistant.py
```

This outputs the system prompt and config. Either:
- Copy to VAPI dashboard manually, OR
- Set VAPI_API_KEY to auto-create via API

### 4. Get a Phone Number

In VAPI dashboard:
1. Go to Phone Numbers
2. Buy or import a number
3. Assign your assistant to the number

### 5. Set Up Webhooks

Run the webhook server:
```bash
python webhook_server.py
```

Expose with ngrok:
```bash
ngrok http 5001
```

In VAPI dashboard:
- Set webhook URL to: `https://your-ngrok-url/vapi/webhook`

## Appointments Dashboard

View booked trials:
```bash
streamlit run appointments_dashboard.py
```

## Features

- **24/7 Availability**: AI answers calls anytime
- **FAQ Handling**: Classes, pricing, location, coaches
- **Trial Booking**: Captures name, phone, experience, interest
- **SMS Trial Link**: Sends booking link via text
- **Coach Transfer**: Escalates when needed
- **Call Logging**: Records all calls and bookings

## Unity MMA Info

- **Location**: 19B William Pickering Drive, Rosedale, Albany, Auckland
- **Phone**: 027 200 7776
- **Email**: Info@unitymma.co.nz
- **Website**: unitymma.co.nz

## Voice Configuration

The bot uses:
- OpenAI GPT-4 Turbo for conversation
- ElevenLabs for voice synthesis (Rachel voice)
