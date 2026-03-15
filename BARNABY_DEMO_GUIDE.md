# Barnaby's Gym - Demo Guide

## Quick Start

```bash
cd ~/junction-ai
python3 barnaby_demo.py
```

This launches the interactive demo menu.

---

## System 1: DM Bot (Instagram/Facebook)

### What It Does
- Answers FAQs about hours, pricing, classes
- Captures leads (name, phone, email, fitness goal)
- Sends booking links for free consultations
- Gym-friendly, motivating tone

### Demo It
```bash
cd ~/junction-ai/barnaby_dm_bot
python3 demo_chat.py
```

### Sample Conversation
```
User: What are your hours?
Bot: Hey there! Barnaby's Gym is open Mon-Thu 5AM-10PM, Friday 5AM-9PM, Saturday 7AM-6PM, and Sunday 8AM-4PM. 💪

User: How much is it?
Bot: Monthly membership is $49/month, or save with annual at $39/month (billed $468/year). Want to book a free tour?

User: I want to lose weight
Bot: Awesome goal! I'd love to help you crush it. What's your name and phone so we can set up a free consultation? 💪

User: I'm Mike, 555-0123
Bot: Great to meet you, Mike! Book your free consultation here: https://calendly.com/barnabys-gym/free-consultation 💪
```

### View Leads
```bash
cd ~/junction-ai/barnaby_dm_bot
streamlit run leads_dashboard.py
```
Open http://localhost:8501

---

## System 2: Voice Bot (24/7 Phone)

### What It Does
- Answers calls automatically 24/7
- Provides gym info via voice
- Books appointments
- Sends SMS booking links
- Transfers to humans when needed

### Demo It
```bash
cd ~/junction-ai/barnaby_voice_bot
python3 demo_call.py
```

### Sample Call
```
Bot: Hey there! Thanks for calling Barnaby's Gym! How can I help you today?

Caller: What time do you open?
Bot: We're open Monday through Thursday from 5 AM to 10 PM, Friday 5 AM to 9 PM...

Caller: I'd like to book a tour
Bot: Awesome! What's your name and the best number to reach you?
```

### View Appointments
```bash
cd ~/junction-ai/barnaby_voice_bot
streamlit run appointments_dashboard.py
```

---

## Production Setup

### DM Bot (Meta API)
1. Create Meta Developer App
2. Add `META_ACCESS_TOKEN` to `.env`
3. Run: `cd barnaby_dm_bot && python meta_webhook.py`
4. Use ngrok to expose webhook
5. Configure webhook in Meta dashboard

### Voice Bot (VAPI)
1. Create VAPI account at https://vapi.ai
2. Add `VAPI_API_KEY` to `.env`
3. Run: `python vapi_assistant.py` to get config
4. Create assistant in VAPI dashboard
5. Buy/import phone number
6. Run: `python webhook_server.py`

---

## Files Created

```
~/junction-ai/
├── barnaby_demo.py              # Main demo launcher
├── BARNABY_DEMO_GUIDE.md        # This guide
│
├── barnaby_dm_bot/
│   ├── config.py                # Gym info & settings
│   ├── conversation_ai.py       # AI response engine
│   ├── meta_webhook.py          # Meta API handler
│   ├── demo_chat.py             # Local demo interface
│   ├── leads_dashboard.py       # Streamlit leads view
│   └── leads.json               # Captured leads
│
└── barnaby_voice_bot/
    ├── config.py                # Gym info & settings
    ├── vapi_assistant.py        # VAPI config generator
    ├── webhook_server.py        # VAPI webhook handler
    ├── demo_call.py             # Local demo interface
    ├── appointments_dashboard.py # Streamlit appointments
    └── appointments.json        # Booked appointments
```

---

## Customization

Edit `config.py` in either bot folder to change:
- Gym hours
- Pricing
- Classes offered
- Booking URL
- Location

---

## Revenue Potential

- Monthly fee: $1,000 - $3,000/month
- Includes: Both systems + maintenance + updates
- ROI: 24/7 availability, never miss a lead, consistent responses

---

Built by Junction AI 🔥
