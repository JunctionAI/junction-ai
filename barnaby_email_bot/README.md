# Unity MMA Email Bot

AI-powered email automation for Unity MMA. Handles inbox enquiries with professional auto-replies, smart escalation, and noise filtering.

## Quick Start (Demo Mode)

```bash
cd ~/junction-ai/barnaby_email_bot
python demo_email.py
```

This lets you test email classification and responses without live email server.

## Features

### Intent Classification
- **Auto-Reply (70%+)**: First-timer enquiries, class info, pricing, trial questions
- **Escalate (20%)**: Cancellations, billing issues, complaints, PT requests
- **Ignore (10%)**: System emails, vendor spam, newsletters

### Professional Email Tone
Unlike the casual DM bot, emails are:
- Formal greetings: "Dear [Name]"
- Professional sign-off: "Warm regards, The Unity MMA Team"
- Concise, helpful, branded

### Dashboard
```bash
streamlit run email_dashboard.py
```

View:
- Automation rate metrics
- Escalation queue
- Intent distribution
- Email processing log

## Production Setup (Roundcube/FreeParking)

### 1. Environment Variables

Add to `.env`:
```bash
EMAIL_HOST=mail.freeparking.co.nz
IMAP_PORT=993
SMTP_PORT=465
EMAIL_USER=info@unitymma.co.nz
EMAIL_PASSWORD=your_password
```

### 2. Run Email Processor

```python
from email_handler import EmailBot

bot = EmailBot()
bot.connect_imap()
results = bot.process_inbox(limit=10)
bot.disconnect()
```

### 3. Scheduled Processing

Use cron or a scheduler to check inbox every 5-10 minutes:
```bash
*/5 * * * * cd ~/junction-ai/barnaby_email_bot && python3 -c "from email_handler import EmailBot; b = EmailBot(); b.process_inbox()" >> /var/log/email_bot.log 2>&1
```

## Email Response Templates

Located in `config.py`:
- `first_timer`: Welcome + trial info
- `class_info`: Full timetable
- `promo_clarification`: Pricing breakdown
- `booking_confirm`: Booking confirmation
- `pause_request`: Pause instructions

## Integration with Other Bots

| Channel | Bot | Tone |
|---------|-----|------|
| Instagram/Facebook DM | DM Bot | Casual, coach-like |
| Phone Calls | Voice Bot | Warm, energetic |
| Email | Email Bot | Professional, concise |

All three bots share the same Unity MMA knowledge base (timetable, pricing, coaches).

## Test Scenarios

Run preset tests:
```bash
python demo_email.py
# Choose option 1 for preset tests
```

Test scenarios included:
- First-timer enquiry → Auto-reply
- Class schedule query → Auto-reply
- Cancellation request → Escalate
- Payment issue → Escalate
- System notification → Ignore
