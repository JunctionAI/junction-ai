"""
Configuration for Unity MMA Voice Receptionist
"""

import os
from dotenv import load_dotenv
load_dotenv()

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID", "")

# OpenAI for voice (VAPI uses OpenAI by default)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Booking URLs
BOOKING_URL = "https://www.unitymma.co.nz/book-appointment"
TRIAL_URL = "https://www.unitymma.co.nz/landing-page"

# Gym Info - UNITY MMA (Real data from unitymma.co.nz)
GYM_INFO = {
    "name": "Unity MMA",
    "tagline": "Auckland's newest and most diverse MMA gym",
    "location": "19B William Pickering Drive, Rosedale, Albany, Auckland",
    "phone": "027 200 7776",
    "email": "Info@unitymma.co.nz",
    "website": "unitymma.co.nz",

    "pricing": {
        "weekly_adult": "49.99 dollars per week, or 54.99 with Jiu Jitsu",
        "weekly_student": "39.99 dollars per week for students, or 49.99 with Jiu Jitsu",
        "casual": "25 dollars per session",
        "personal_training": "40 dollars per hour"
    },

    "classes": [
        "MMA",
        "Kickboxing",
        "Boxing",
        "Women's Boxing and Bootcamp",
        "Kids Kickboxing",
        "Jiu Jitsu",
        "Wrestling",
        "Bootcamp",
        "Move and Flow mobility classes"
    ],

    "trial": {
        "offer": "1-Day FREE Trial",
        "details": "Train with Auckland's best MMA and BJJ coaches - no experience needed"
    },

    "coaches": [
        {"name": "Ollie", "role": "Head Coach", "specialty": "MMA", "fact": "Nearly 50 fights"},
        {"name": "Levente", "role": "Coach", "specialty": "MMA"},
        {"name": "Barnaby", "role": "Coach", "specialty": "Boxing and CrossFit"},
        {"name": "Brooke", "role": "Coach", "specialty": "Kickboxing and BJJ"},
        {"name": "Andre", "role": "Coach", "specialty": "Jiu Jitsu"}
    ],

    "features": [
        "State-of-the-art facilities",
        "Over 130 members training weekly",
        "Beginner friendly",
        "Great community"
    ]
}

# FULL TIMETABLE - Extracted from official Unity MMA schedule
TIMETABLE = {
    "monday": {
        "4:00pm-4:50pm": "Teens (10-15 years)",
        "5:00pm-5:50pm": "Adults Beginner Boxing",
        "6:00pm-6:50pm": "Adults Advanced Boxing",
        "7:00pm-8:00pm": "Jiu Jitsu (Gi)"
    },
    "tuesday": {
        "4:00pm-4:50pm": "Little Monsters (6-9 years)",
        "5:00pm-5:50pm": "Teens (10-15 years)",
        "6:00pm-6:50pm": "Adults Kickboxing",
        "7:00pm-8:00pm": "Adults MMA"
    },
    "wednesday": {
        "4:00pm-4:50pm": "Teens (10-15 years)",
        "5:00pm-5:50pm": "Sparring",
        "6:00pm-6:50pm": "MMA Sparring",
        "7:00pm-8:00pm": "Jiu Jitsu (No Gi)"
    },
    "thursday": {
        "4:00pm-4:50pm": "Little Monsters (6-9 years)",
        "5:00pm-5:50pm": "Teens (10-15 years)",
        "6:00pm-6:50pm": "Adults Kickboxing",
        "7:00pm-8:00pm": "Adults MMA"
    },
    "friday": {
        "4:00pm-4:50pm": "Little Monsters (6-9 years)",
        "5:00pm-5:50pm": "Teens (10-15 years)",
        "6:00pm-6:50pm": "Adults MMA",
        "7:00pm-8:00pm": "BJJ Open Mat"
    },
    "saturday": {
        "9:00am-9:50am": "Box Fit",
        "10:00am-10:50am": "Teens (10-15 years)",
        "12:00pm-1:00pm": "Jiu Jitsu (No Gi)",
        "2:00pm-3:00pm": "Sparring"
    },
    "sunday": {
        "10:00am-10:50am": "Youth Boxing Class (6-15 years)",
        "11:00am-11:50am": "Adults Boxing"
    }
}

# Class descriptions for quick lookup
CLASS_SCHEDULE_BY_TYPE = {
    "jiu_jitsu": [
        {"day": "Monday", "time": "7:00pm-8:00pm", "type": "Jiu Jitsu (Gi)"},
        {"day": "Wednesday", "time": "7:00pm-8:00pm", "type": "Jiu Jitsu (No Gi)"},
        {"day": "Friday", "time": "7:00pm-8:00pm", "type": "BJJ Open Mat"},
        {"day": "Saturday", "time": "12:00pm-1:00pm", "type": "Jiu Jitsu (No Gi)"}
    ],
    "mma": [
        {"day": "Tuesday", "time": "7:00pm-8:00pm", "type": "Adults MMA"},
        {"day": "Thursday", "time": "7:00pm-8:00pm", "type": "Adults MMA"},
        {"day": "Friday", "time": "6:00pm-6:50pm", "type": "Adults MMA"},
        {"day": "Wednesday", "time": "6:00pm-6:50pm", "type": "MMA Sparring"}
    ],
    "kickboxing": [
        {"day": "Tuesday", "time": "6:00pm-6:50pm", "type": "Adults Kickboxing"},
        {"day": "Thursday", "time": "6:00pm-6:50pm", "type": "Adults Kickboxing"}
    ],
    "boxing": [
        {"day": "Monday", "time": "5:00pm-5:50pm", "type": "Adults Beginner Boxing"},
        {"day": "Monday", "time": "6:00pm-6:50pm", "type": "Adults Advanced Boxing"},
        {"day": "Sunday", "time": "11:00am-11:50am", "type": "Adults Boxing"},
        {"day": "Saturday", "time": "9:00am-9:50am", "type": "Box Fit"}
    ],
    "kids": [
        {"day": "Monday", "time": "4:00pm-4:50pm", "type": "Teens (10-15 years)"},
        {"day": "Tuesday", "time": "4:00pm-4:50pm", "type": "Little Monsters (6-9 years)"},
        {"day": "Tuesday", "time": "5:00pm-5:50pm", "type": "Teens (10-15 years)"},
        {"day": "Wednesday", "time": "4:00pm-4:50pm", "type": "Teens (10-15 years)"},
        {"day": "Thursday", "time": "4:00pm-4:50pm", "type": "Little Monsters (6-9 years)"},
        {"day": "Thursday", "time": "5:00pm-5:50pm", "type": "Teens (10-15 years)"},
        {"day": "Friday", "time": "4:00pm-4:50pm", "type": "Little Monsters (6-9 years)"},
        {"day": "Friday", "time": "5:00pm-5:50pm", "type": "Teens (10-15 years)"},
        {"day": "Saturday", "time": "10:00am-10:50am", "type": "Teens (10-15 years)"},
        {"day": "Sunday", "time": "10:00am-10:50am", "type": "Youth Boxing Class (6-15 years)"}
    ],
    "sparring": [
        {"day": "Wednesday", "time": "5:00pm-5:50pm", "type": "Sparring"},
        {"day": "Wednesday", "time": "6:00pm-6:50pm", "type": "MMA Sparring"},
        {"day": "Saturday", "time": "2:00pm-3:00pm", "type": "Sparring"}
    ]
}

# Server config
PORT = int(os.getenv("VOICE_BOT_PORT", 5001))
