"""
Configuration for Unity MMA Email Bot
IMAP/SMTP integration for Roundcube + FreeParking
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Email Server Configuration (Roundcube / FreeParking)
EMAIL_HOST = os.getenv("EMAIL_HOST", "mail.freeparking.co.nz")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Multi-inbox configuration
EMAIL_ACCOUNTS = [
    {
        "name": "info",
        "user": os.getenv("EMAIL_USER", "info@unitymma.co.nz"),
        "password": os.getenv("EMAIL_PASSWORD", "")
    },
    {
        "name": "hello",
        "user": os.getenv("EMAIL_USER2", "hello@unitymma.co.nz"),
        "password": os.getenv("EMAIL_PASSWORD2", "")
    }
]

# Legacy single-account (for backward compatibility)
EMAIL_USER = os.getenv("EMAIL_USER", "info@unitymma.co.nz")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# AI Model
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Unity MMA Info (shared with other bots)
GYM_INFO = {
    "name": "Unity MMA",
    "tagline": "Auckland's newest and most diverse MMA gym",
    "location": "19B William Pickering Drive, Rosedale, Auckland",
    "phone": "027 200 7776",
    "email": "Info@Unitymma.com",
    "website": "unitymma.co.nz",
    "booking_url": "https://www.unitymma.co.nz/book-appointment",
    "trial_url": "https://unitymma.co.nz/landing-page"
}

# Email Intent Categories
INTENT_CATEGORIES = {
    "auto_reply": [
        "first_timer",           # New member enquiry
        "class_info",            # Timetable/schedule questions
        "promo_clarification",   # Trial/pricing questions
        "booking_confirm",       # Confirming bookings
        "pause_request",         # Membership pause
    ],
    "ai_assisted_notify": [
        "cancellation",          # Membership cancellation
        "billing_issue",         # Payment problems
        "pt_enquiry",            # Personal training
        "complaint",             # Issues/complaints
    ],
    "ignore": [
        "system_noise",          # Automated system emails
        "vendor_email",          # Marketing/vendor spam
        "newsletter",            # Subscriptions
    ]
}

# Email Templates (Natural, coach-like tone - keep short!)
EMAIL_TEMPLATES = {
    "first_timer": """Hi {name},

Thanks for reaching out! We'd love to have you train with us.

Come try a FREE 1-Day Trial - no experience needed, our coaches will look after you: {trial_url}

See you on the mats!

Unity MMA Team
""",

    "class_info": """Hi {name},

Here's our timetable:

{class_info}

Book online: {booking_url}

New here? Grab a FREE trial: {trial_url}

See you soon!

Unity MMA Team
""",

    "promo_clarification": """Hi {name},

Our pricing:
- Adult: $49.99/week ($54.99 with BJJ)
- Youth/Student: $39.99/week
- Casual: $25/session

NEW MEMBERS: FREE 1-Day Trial - book here: {trial_url}

Any questions, just ask!

Unity MMA Team
""",

    "location_info": """Hi {name},

We're at: {location}

Book online: {booking_url}
New here? FREE trial: {trial_url}

See you soon!

Unity MMA Team
""",

    "booking_confirm": """Hi {name},

You're all booked in! See you at {location}.

Arrive 10-15 mins early for your first session. Bring comfy workout clothes and water.

See you on the mats!

Unity MMA Team
""",

    "pause_request": """Hi {name},

Thanks for letting us know. Membership pauses need 2 weeks notice.

Barnaby will be in touch shortly to sort this out for you.

Unity MMA Team
""",

    "personal_question": """Hi {name},

Great question! Barnaby will reply personally to make sure you get the best advice for your situation.

If you need us urgently, call {phone}.

Chat soon!

Unity MMA Team
""",

    "escalation_draft": """Hi {name},

Thanks for getting in touch! Barnaby will reply personally shortly.

Need us urgently? Call {phone}.

Chat soon!

Unity MMA Team
""",

    "escalation_notification": """[ESCALATION REQUIRED]

Email from: {sender}
Subject: {subject}
Intent: {intent}

Original message:
{body}

---
ACTION: Reply personally to {name}. This needs a human touch.
---
""",
}

# Timetable for email responses
TIMETABLE_EMAIL = """
MONDAY:
- 4:00pm: Teens (10-15 years)
- 5:00pm: Adults Beginner Boxing
- 6:00pm: Adults Advanced Boxing
- 7:00pm: Jiu Jitsu (Gi)

TUESDAY:
- 4:00pm: Little Monsters (6-9 years)
- 5:00pm: Teens (10-15 years)
- 6:00pm: Adults Kickboxing
- 7:00pm: Adults MMA

WEDNESDAY:
- 4:00pm: Teens (10-15 years)
- 5:00pm: Sparring
- 6:00pm: MMA Sparring
- 7:00pm: Jiu Jitsu (No Gi)

THURSDAY:
- 4:00pm: Little Monsters (6-9 years)
- 5:00pm: Teens (10-15 years)
- 6:00pm: Adults Kickboxing
- 7:00pm: Adults MMA

FRIDAY:
- 4:00pm: Little Monsters (6-9 years)
- 5:00pm: Teens (10-15 years)
- 6:00pm: Adults MMA
- 7:00pm: BJJ Open Mat

SATURDAY:
- 9:00am: Box Fit
- 10:00am: Teens (10-15 years)
- 12:00pm: Jiu Jitsu (No Gi)
- 2:00pm: Sparring

SUNDAY:
- 10:00am: Youth Boxing Class (6-15 years)
- 11:00am: Adults Boxing
"""

# Server config
DASHBOARD_PORT = int(os.getenv("EMAIL_BOT_PORT", 5002))
