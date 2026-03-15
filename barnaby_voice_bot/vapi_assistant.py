"""
VAPI Voice Assistant Configuration for Unity MMA
This creates and configures the AI voice assistant
"""

import os
import json
import requests
from datetime import datetime
from config import VAPI_API_KEY, GYM_INFO, TRIAL_URL, BOOKING_URL, TIMETABLE, CLASS_SCHEDULE_BY_TYPE

VAPI_BASE_URL = "https://api.vapi.ai"

# Day name mapping for schedule lookups
DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

def get_current_context():
    """Get current date/time context for schedule awareness."""
    now = datetime.now()
    current_day = now.strftime("%A").lower()
    current_time = now.strftime("%I:%M %p").lstrip("0").lower()
    current_hour = now.hour

    return {
        "day": current_day,
        "day_name": now.strftime("%A"),
        "time": current_time,
        "hour": current_hour,
        "date": now.strftime("%B %d, %Y"),
        "year": now.year
    }

def get_next_class_for_type(class_type: str) -> str:
    """Find the next occurrence of a class type based on current day/time."""
    ctx = get_current_context()
    current_day = ctx["day"]
    current_hour = ctx["hour"]

    # Get schedule for this class type
    schedule_key = class_type.lower().replace(" ", "_").replace("/", "_")
    if "jiu" in schedule_key or "bjj" in schedule_key:
        schedule_key = "jiu_jitsu"
    elif "mma" in schedule_key:
        schedule_key = "mma"
    elif "kickbox" in schedule_key:
        schedule_key = "kickboxing"
    elif "box" in schedule_key:
        schedule_key = "boxing"
    elif "kid" in schedule_key or "teen" in schedule_key or "monster" in schedule_key or "youth" in schedule_key:
        schedule_key = "kids"
    elif "spar" in schedule_key:
        schedule_key = "sparring"

    classes = CLASS_SCHEDULE_BY_TYPE.get(schedule_key, [])
    if not classes:
        return None

    # Find current day index
    current_idx = DAY_ORDER.index(current_day)

    # Check today first (if class hasn't started yet)
    for cls in classes:
        if cls["day"].lower() == current_day:
            # Parse class start time
            time_str = cls["time"].split("-")[0]
            hour = int(time_str.split(":")[0])
            if "pm" in time_str.lower() and hour != 12:
                hour += 12
            if hour > current_hour:
                return f"today at {cls['time']} ({cls['type']})"

    # Check upcoming days
    for i in range(1, 8):
        check_day = DAY_ORDER[(current_idx + i) % 7]
        for cls in classes:
            if cls["day"].lower() == check_day:
                if i == 1:
                    return f"tomorrow at {cls['time']} ({cls['type']})"
                else:
                    return f"{cls['day']} at {cls['time']} ({cls['type']})"

    return None

def get_system_prompt():
    """Generate the system prompt for the voice assistant."""
    coaches_list = ", ".join([c["name"] for c in GYM_INFO["coaches"]])
    ctx = get_current_context()

    # Build next class hints
    next_bjj = get_next_class_for_type("bjj")
    next_mma = get_next_class_for_type("mma")
    next_boxing = get_next_class_for_type("boxing")
    next_kickboxing = get_next_class_for_type("kickboxing")

    return f"""You are the friendly AI receptionist for {GYM_INFO['name']} - {GYM_INFO['tagline']}. You answer phone calls 24/7.

VOICE GUIDELINES:
- Speak naturally and conversationally
- Be warm, energetic, and fighter-friendly
- Keep responses SHORT (1-2 sentences per turn)
- Pause briefly between thoughts
- Use positive, martial arts language

=== UNITY MMA INFO ===

LOCATION: {GYM_INFO['location']} - that's in Rosedale, Albany, Auckland

CONTACT:
- Phone: {GYM_INFO['phone']}
- Email: {GYM_INFO['email']}
- Website: {GYM_INFO['website']}

=== FULL TIMETABLE ===

MONDAY:
- 4:00pm-4:50pm: Teens (10-15 years)
- 5:00pm-5:50pm: Adults Beginner Boxing
- 6:00pm-6:50pm: Adults Advanced Boxing
- 7:00pm-8:00pm: Jiu Jitsu (Gi)

TUESDAY:
- 4:00pm-4:50pm: Little Monsters (6-9 years)
- 5:00pm-5:50pm: Teens (10-15 years)
- 6:00pm-6:50pm: Adults Kickboxing
- 7:00pm-8:00pm: Adults MMA

WEDNESDAY:
- 4:00pm-4:50pm: Teens (10-15 years)
- 5:00pm-5:50pm: Sparring
- 6:00pm-6:50pm: MMA Sparring
- 7:00pm-8:00pm: Jiu Jitsu (No Gi)

THURSDAY:
- 4:00pm-4:50pm: Little Monsters (6-9 years)
- 5:00pm-5:50pm: Teens (10-15 years)
- 6:00pm-6:50pm: Adults Kickboxing
- 7:00pm-8:00pm: Adults MMA

FRIDAY:
- 4:00pm-4:50pm: Little Monsters (6-9 years)
- 5:00pm-5:50pm: Teens (10-15 years)
- 6:00pm-6:50pm: Adults MMA
- 7:00pm-8:00pm: BJJ Open Mat

SATURDAY:
- 9:00am-9:50am: Box Fit
- 10:00am-10:50am: Teens (10-15 years)
- 12:00pm-1:00pm: Jiu Jitsu (No Gi)
- 2:00pm-3:00pm: Sparring

SUNDAY:
- 10:00am-10:50am: Youth Boxing Class (6-15 years)
- 11:00am-11:50am: Adults Boxing

=== CLASS SCHEDULE BY TYPE ===

JIU JITSU / BJJ:
- Monday 7:00pm-8:00pm: Jiu Jitsu (Gi)
- Wednesday 7:00pm-8:00pm: Jiu Jitsu (No Gi)
- Friday 7:00pm-8:00pm: BJJ Open Mat
- Saturday 12:00pm-1:00pm: Jiu Jitsu (No Gi)

MMA:
- Tuesday 7:00pm-8:00pm: Adults MMA
- Thursday 7:00pm-8:00pm: Adults MMA
- Friday 6:00pm-6:50pm: Adults MMA
- Wednesday 6:00pm-6:50pm: MMA Sparring

KICKBOXING:
- Tuesday 6:00pm-6:50pm: Adults Kickboxing
- Thursday 6:00pm-6:50pm: Adults Kickboxing

BOXING:
- Monday 5:00pm-5:50pm: Adults Beginner Boxing
- Monday 6:00pm-6:50pm: Adults Advanced Boxing
- Sunday 11:00am-11:50am: Adults Boxing
- Saturday 9:00am-9:50am: Box Fit

KIDS CLASSES:
- Little Monsters (6-9 years): Tue/Thu/Fri 4:00pm-4:50pm
- Teens (10-15 years): Mon/Wed 4:00pm, Tue/Thu/Fri 5:00pm, Sat 10:00am
- Youth Boxing (6-15 years): Sunday 10:00am-10:50am

SPARRING:
- Wednesday 5:00pm-5:50pm: Sparring
- Wednesday 6:00pm-6:50pm: MMA Sparring
- Saturday 2:00pm-3:00pm: Sparring

PRICING (Weekly memberships):
- Adult: {GYM_INFO['pricing']['weekly_adult']}
- Students: {GYM_INFO['pricing']['weekly_student']}
- Casual session: {GYM_INFO['pricing']['casual']}
- Personal Training: {GYM_INFO['pricing']['personal_training']}

FREE TRIAL: We offer a 1-Day FREE Trial!
- No experience needed
- Train with Auckland's best MMA and BJJ coaches
- Book online at {TRIAL_URL}

OUR COACHES: {coaches_list}
- Head Coach Ollie has nearly 50 fights under his belt!

WHY UNITY MMA:
- State-of-the-art facilities
- Over 130 members training weekly
- Beginner friendly - all skill levels welcome
- Great community vibe, no egos
- Learn real self-defense skills

=== CURRENT DATE/TIME CONTEXT ===

RIGHT NOW: {ctx['day_name']}, {ctx['date']} at {ctx['time']}
YEAR: {ctx['year']}

=== QUICK NEXT CLASS REFERENCE ===
(Use these for "when is next..." questions - say "today" or "tomorrow" when applicable!)

- Next Jiu Jitsu/BJJ: {next_bjj or 'Check schedule above'}
- Next MMA: {next_mma or 'Check schedule above'}
- Next Boxing: {next_boxing or 'Check schedule above'}
- Next Kickboxing: {next_kickboxing or 'Check schedule above'}

=== CALL FLOW ===

1. Greet caller warmly
2. Ask how you can help
3. FIND OUT: Are they a member or new? Ask naturally: "Are you already training with us?"
4. Answer questions about classes, pricing, location - USE CURRENT DAY CONTEXT
5. For NEW callers: offer the FREE 1-Day Trial
6. For MEMBERS: help with class info, don't push trials
7. Collect name and phone for trial booking (new callers)
8. End warmly - "See you on the mats!"

=== IMPORTANT RULES ===

1. BE CONTEXT-AWARE: Use the current day/time above. Say "today at 7pm" not just "Wednesday 7pm" if it's Wednesday.
2. ASK IF MEMBER OR NEW: If unknown, ask naturally: "Are you already training with us, or looking to start?"
3. BE CONVERSATIONAL: Sound like a real coach! Examples:
   - "Awesome, BJJ's my fave! Next one's tonight at 7pm - wanna come try it out?"
   - "Oh nice, you're already a member? Sweet, which class you looking for?"
4. For timetable questions, give EXACT times from the schedule above
5. Push FREE TRIAL for NEW callers only (not members!)
6. If they ask about kids, mention Little Monsters (6-9), Teens (10-15), or Youth Boxing
7. BJJ membership costs slightly more (54.99 vs 49.99)
8. Never make up times - use ONLY the schedule above
9. If unsure, offer to have a coach call them back
10. Be encouraging about their martial arts journey
11. If caller seems frustrated, stay calm and helpful
"""

def get_assistant_config():
    """Get the full VAPI assistant configuration."""
    return {
        "name": "Unity MMA Receptionist",
        "model": {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "systemPrompt": get_system_prompt(),
            "temperature": 0.7
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel - friendly female voice
            "stability": 0.5,
            "similarityBoost": 0.75
        },
        "firstMessage": f"Hey there! Thanks for calling {GYM_INFO['name']}! I'm your AI assistant. How can I help you today?",
        "endCallMessage": "Thanks for calling Unity MMA! We can't wait to see you on the mats. Have an awesome day!",
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600,  # 10 min max call
        "backgroundSound": "off",
        "recordingEnabled": True,
        "functions": [
            {
                "name": "book_trial",
                "description": "Book a free trial session at Unity MMA",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Caller's name"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Callback phone number"
                        },
                        "experience": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced"],
                            "description": "Caller's experience level"
                        },
                        "interest": {
                            "type": "string",
                            "enum": ["MMA", "Boxing", "Kickboxing", "BJJ", "Kids", "Women's", "General"],
                            "description": "What they're interested in"
                        }
                    },
                    "required": ["name", "phone"]
                }
            },
            {
                "name": "transfer_to_coach",
                "description": "Transfer call to a coach or staff member",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for transfer"
                        }
                    }
                }
            },
            {
                "name": "send_trial_link",
                "description": "Send the caller a text with the free trial booking link",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "Phone number to send SMS to"
                        }
                    },
                    "required": ["phone"]
                }
            }
        ]
    }

def create_assistant():
    """Create a new VAPI assistant."""
    if not VAPI_API_KEY:
        print("VAPI_API_KEY not set - returning config for manual setup")
        return get_assistant_config()

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    config = get_assistant_config()

    response = requests.post(
        f"{VAPI_BASE_URL}/assistant",
        headers=headers,
        json=config
    )

    if response.status_code == 201:
        assistant = response.json()
        print(f"Assistant created: {assistant.get('id')}")
        return assistant
    else:
        print(f"Error creating assistant: {response.text}")
        return None

def list_assistants():
    """List all VAPI assistants."""
    if not VAPI_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}"
    }

    response = requests.get(f"{VAPI_BASE_URL}/assistant", headers=headers)

    if response.status_code == 200:
        return response.json()
    return []

def delete_assistant(assistant_id: str):
    """Delete a VAPI assistant."""
    if not VAPI_API_KEY:
        return False

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}"
    }

    response = requests.delete(f"{VAPI_BASE_URL}/assistant/{assistant_id}", headers=headers)
    return response.status_code == 200

if __name__ == "__main__":
    # Print config for manual VAPI dashboard setup
    config = get_assistant_config()
    print("\n" + "="*60)
    print("VAPI Assistant Configuration - Unity MMA")
    print("="*60)
    print("\nSystem Prompt:\n")
    print(config["model"]["systemPrompt"])
    print("\n" + "="*60)
    print("\nFirst Message:", config["firstMessage"])
    print("End Call Message:", config["endCallMessage"])
    print("\nFull config saved to vapi_config.json")

    with open("vapi_config.json", "w") as f:
        json.dump(config, f, indent=2)
