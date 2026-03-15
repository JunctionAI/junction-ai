"""
Configuration for Unity MMA DM Bot
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Meta API (Facebook/Instagram)
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "unity_mma_2024")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")

# AI Model
XAI_API_KEY = os.getenv("XAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Booking link - Unity MMA's booking page
BOOKING_URL = "https://www.unitymma.co.nz/book-appointment"
TRIAL_URL = "https://www.unitymma.co.nz/landing-page"

# Gym Info - UNITY MMA (Real data from unitymma.co.nz)
GYM_INFO = {
    "name": "Unity MMA",
    "tagline": "Auckland's newest and most diverse MMA gym",
    "location": "19B William Pickering Drive, Rosedale, Auckland",
    "phone": "027 200 7776",
    "email": "Info@Unitymma.com",
    "website": "unitymma.co.nz",

    "pricing": {
        "weekly_adult": "$49.99/week (excluding Jiu Jitsu)",
        "weekly_adult_with_bjj": "$54.99/week (with Jiu Jitsu)",
        "weekly_youth_student": "$39.99/week (excluding Jiu Jitsu)",
        "weekly_youth_student_with_bjj": "$49.99/week (with Jiu Jitsu)",
        "casual_session": "$25 per session",
        "personal_training": "$40/hour"
    },

    "classes": [
        "Adults MMA",
        "Adults Kickboxing",
        "Adults Beginner Boxing",
        "Adults Advanced Boxing",
        "Jiu Jitsu (Gi)",
        "Jiu Jitsu (No Gi)",
        "BJJ Open Mat",
        "MMA Sparring",
        "Sparring",
        "Box Fit",
        "Teens (10-15 years)",
        "Little Monsters (6-9 years)",
        "Youth Boxing Class (6-15 years)"
    ],

    "trial": {
        "offer": "1-Day FREE Trial",
        "details": "Train with Auckland's best MMA & BJJ coaches - no experience needed",
        "url": "https://www.unitymma.co.nz/landing-page"
    },

    "coaches": [
        {"name": "Ollie", "role": "Head Coach", "specialty": "MMA", "experience": "Nearly 50 fights, multiple amateur titles, now professional"},
        {"name": "Levente", "role": "Coach", "specialty": "MMA", "experience": "7 amateur MMA fights"},
        {"name": "Barnaby", "role": "Coach", "specialty": "Boxing, MMA, Calisthenics, CrossFit", "experience": "Amateur fighter"},
        {"name": "Brooke", "role": "Coach", "specialty": "Kickboxing, Boxing, Wrestling, BJJ, MMA", "experience": "6+ years"},
        {"name": "Andre", "role": "Coach", "specialty": "Jiu Jitsu"}
    ],

    "features": [
        "State-of-the-art facilities",
        "World-class trainers",
        "Beginner friendly - all levels welcome",
        "130+ members training weekly",
        "Supportive community - no egos",
        "Self-defense training",
        "High-intensity calorie-burning workouts"
    ],

    "cancellation_policy": "All cancellations require 2 weeks' notice"
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

# Lead capture fields
LEAD_FIELDS = ["name", "phone", "email", "fitness_goal", "experience_level"]

# Server config
PORT = int(os.getenv("DM_BOT_PORT", 5000))
