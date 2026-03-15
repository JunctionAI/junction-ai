"""
AI Conversation Handler for Unity MMA DM Bot
Uses Grok-3 for intelligent, MMA-friendly responses
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from config import GYM_INFO, BOOKING_URL, TRIAL_URL, XAI_API_KEY, TIMETABLE, CLASS_SCHEDULE_BY_TYPE

# Initialize model
model = ChatXAI(model="grok-3", temperature=0.7, api_key=XAI_API_KEY)

# Conversation memory per user
conversations: Dict[str, list] = {}
lead_data: Dict[str, Dict[str, Any]] = {}
user_profiles: Dict[str, Dict[str, Any]] = {}  # Track if user is member/new

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

# Build coaches string
coaches_str = "\n".join([f"  - {c['name']} ({c['role']}): {c['specialty']}" for c in GYM_INFO['coaches']])

# Build timetable string for AI
def format_timetable():
    lines = []
    for day, classes in TIMETABLE.items():
        day_classes = [f"{time}: {cls}" for time, cls in classes.items()]
        lines.append(f"{day.upper()}: {', '.join(day_classes)}")
    return "\n".join(lines)

TIMETABLE_STR = format_timetable()

def build_system_prompt(user_id: str = None):
    """Build dynamic system prompt with current context."""
    ctx = get_current_context()

    # Get user profile if known
    user_info = ""
    if user_id and user_id in user_profiles:
        profile = user_profiles[user_id]
        if profile.get("is_member"):
            user_info = f"\nUSER STATUS: This is a current member named {profile.get('name', 'unknown')}. Don't push trials - help with class info."
        elif profile.get("name"):
            user_info = f"\nUSER STATUS: You've chatted with {profile['name']} before. They're interested in {profile.get('interested_in', 'training')}."

    # Build next class hints for common queries
    next_bjj = get_next_class_for_type("bjj")
    next_mma = get_next_class_for_type("mma")
    next_boxing = get_next_class_for_type("boxing")
    next_kickboxing = get_next_class_for_type("kickboxing")

    return f"""You are the friendly AI assistant for {GYM_INFO['name']} - {GYM_INFO['tagline']}.

Your job is to:
1. Answer questions about the gym (classes, pricing, location, coaches, timetable)
2. Capture leads (name, phone, email, experience level)
3. Promote and book FREE TRIALS
4. Give ACCURATE timetable/schedule information

TONE: Energetic, welcoming, martial arts vibe. Keep responses SHORT (2-3 sentences max). Be warm - "no egos, just a friendly supportive team."

=== UNITY MMA INFO ===

LOCATION: {GYM_INFO['location']}
PHONE: {GYM_INFO['phone']}
EMAIL: {GYM_INFO['email']}
WEBSITE: {GYM_INFO['website']}

=== FULL TIMETABLE ===

{TIMETABLE_STR}

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

=== PRICING ===

- Adult: $49.99/week (or $54.99/week with Jiu Jitsu)
- Youth/Student: $39.99/week (or $49.99/week with Jiu Jitsu)
- Casual: $25 per session
- Personal Training: $40/hour

FREE TRIAL: 1-Day FREE Trial - no experience needed!
Book at: {TRIAL_URL}

=== COACHES ===
{coaches_str}

=== CURRENT DATE/TIME CONTEXT ===

RIGHT NOW: {ctx['day_name']}, {ctx['date']} at {ctx['time']}
YEAR: {ctx['year']}
{user_info}

=== QUICK NEXT CLASS REFERENCE ===
(Use these for "when is next..." questions)

- Next Jiu Jitsu/BJJ: {next_bjj or 'Check schedule above'}
- Next MMA: {next_mma or 'Check schedule above'}
- Next Boxing: {next_boxing or 'Check schedule above'}
- Next Kickboxing: {next_kickboxing or 'Check schedule above'}

=== CONVERSATION RULES ===

1. BE CONTEXT-AWARE: Use the current day/time above. Say "today at 7pm" not just "Wednesday 7pm" if it's Wednesday.
2. ASK IF MEMBER OR NEW: If unknown, ask naturally: "Are you already training with us, or looking to start?"
3. REMEMBER CONTEXT: If they said their name or interest earlier, use it!
4. BE CONVERSATIONAL: Sound like a real coach, not a bot. Examples:
   - "Awesome, BJJ's my fave! Next one's tonight at 7pm - wanna come try it out?"
   - "Oh nice, you're already a member? Sweet, what class you looking for?"
5. For timetable questions, give EXACT times from the schedule above
6. Push FREE 1-Day Trial for NEW prospects (not members!)
7. Collect: name, phone, experience level from new prospects
8. For BJJ, mention it costs slightly more ($54.99 vs $49.99/week)
9. Never make up times - use ONLY the schedule above
10. Use emojis sparingly: 🥊💪🔥👊
11. End with a call to action: "Want to book a spot?" or "See you on the mats!"

BOOKING LINKS:
- Free Trial: {TRIAL_URL}
- Book Classes: {BOOKING_URL}
"""

def detect_user_type(user_id: str, message: str):
    """Detect if user is a member or new based on their message."""
    message_lower = message.lower()

    if user_id not in user_profiles:
        user_profiles[user_id] = {"is_member": None, "name": None, "interested_in": None}

    profile = user_profiles[user_id]

    # Detect if they're a member
    member_phrases = ["i'm a member", "i am a member", "already a member", "i train here",
                      "i already train", "current member", "my membership"]
    new_phrases = ["looking to start", "want to try", "never been", "first time",
                   "thinking about joining", "interested in joining", "new to"]

    if any(phrase in message_lower for phrase in member_phrases):
        profile["is_member"] = True
    elif any(phrase in message_lower for phrase in new_phrases):
        profile["is_member"] = False

    # Update from lead data if available
    if user_id in lead_data:
        lead = lead_data[user_id]
        if lead.get("name") and not profile.get("name"):
            profile["name"] = lead["name"]
        if lead.get("interested_in") and not profile.get("interested_in"):
            profile["interested_in"] = lead["interested_in"]

def get_ai_response(user_id: str, message: str) -> str:
    """Generate AI response for user message."""

    # Detect user type from message
    detect_user_type(user_id, message)

    # Get or create conversation history
    if user_id not in conversations:
        conversations[user_id] = []

    history = conversations[user_id]

    # Build messages with dynamic system prompt
    messages = [SystemMessage(content=build_system_prompt(user_id))]

    # Add conversation history (last 10 exchanges)
    for msg in history[-20:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=message))

    try:
        response = model.invoke(messages)
        ai_response = response.content

        # Save to history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": ai_response})

        # Keep history manageable
        if len(history) > 30:
            conversations[user_id] = history[-20:]

        # Try to extract lead info from conversation
        extract_lead_info(user_id, message)

        return ai_response

    except Exception as e:
        print(f"AI Error: {e}")
        return f"Hey! Thanks for reaching out to {GYM_INFO['name']}! 🥊 We'd love to get you on the mats. Claim your FREE 1-Day Trial here: {TRIAL_URL} - no experience needed!"

def extract_lead_info(user_id: str, message: str):
    """Try to extract lead information from messages."""

    if user_id not in lead_data:
        lead_data[user_id] = {
            "name": None,
            "phone": None,
            "email": None,
            "fitness_goal": None,
            "experience_level": None,
            "interested_in": None,
            "timestamp": datetime.now().isoformat(),
            "messages": []
        }

    lead = lead_data[user_id]
    lead["messages"].append(message)

    # Simple extraction patterns
    message_lower = message.lower()

    # Phone detection (NZ format)
    import re
    phone_match = re.search(r'[\d\-\(\)\s]{7,}', message)
    if phone_match and not lead["phone"]:
        lead["phone"] = phone_match.group().strip()

    # Email detection
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
    if email_match and not lead["email"]:
        lead["email"] = email_match.group()

    # Name detection
    if "my name is" in message_lower or "i'm " in message_lower or "i am " in message_lower:
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"this is (\w+)",
            r"^(\w+) here"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match and not lead["name"]:
                lead["name"] = match.group(1).title()
                break

    # Experience level detection
    if not lead["experience_level"]:
        if any(w in message_lower for w in ["beginner", "never", "new to", "first time", "no experience"]):
            lead["experience_level"] = "beginner"
        elif any(w in message_lower for w in ["some experience", "trained before", "used to", "few years"]):
            lead["experience_level"] = "intermediate"
        elif any(w in message_lower for w in ["experienced", "compete", "fought", "professional", "years of"]):
            lead["experience_level"] = "advanced"

    # Interest detection
    interest_keywords = {
        "MMA": ["mma", "mixed martial"],
        "Boxing": ["boxing", "box"],
        "Kickboxing": ["kickboxing", "kick boxing", "muay thai"],
        "BJJ": ["jiu jitsu", "bjj", "grappling", "submissions"],
        "Kids": ["kid", "child", "son", "daughter", "children"],
        "Fitness": ["fitness", "weight loss", "get fit", "cardio", "bootcamp"]
    }

    if not lead["interested_in"]:
        for interest, keywords in interest_keywords.items():
            if any(kw in message_lower for kw in keywords):
                lead["interested_in"] = interest
                break

    # Goal detection
    goal_keywords = {
        "self-defense": ["self defense", "self-defense", "protect", "safety"],
        "fitness": ["lose weight", "get fit", "fitness", "health", "cardio", "tone"],
        "competition": ["compete", "fight", "amateur", "professional"],
        "skill building": ["learn", "technique", "skill", "train"]
    }

    if not lead["fitness_goal"]:
        for goal, keywords in goal_keywords.items():
            if any(kw in message_lower for kw in keywords):
                lead["fitness_goal"] = goal
                break

def get_lead_data(user_id: str) -> Optional[Dict]:
    """Get captured lead data for a user."""
    return lead_data.get(user_id)

def get_all_leads() -> Dict[str, Dict]:
    """Get all captured leads."""
    return lead_data

def is_lead_complete(user_id: str) -> bool:
    """Check if we have enough info to follow up."""
    lead = lead_data.get(user_id, {})
    return bool(lead.get("name") and (lead.get("phone") or lead.get("email")))

def save_leads_to_file():
    """Save leads to JSON file."""
    filepath = os.path.expanduser("~/junction-ai/barnaby_dm_bot/leads.json")
    with open(filepath, "w") as f:
        json.dump(lead_data, f, indent=2, default=str)

def load_leads_from_file():
    """Load leads from JSON file."""
    global lead_data
    filepath = os.path.expanduser("~/junction-ai/barnaby_dm_bot/leads.json")
    try:
        with open(filepath, "r") as f:
            lead_data = json.load(f)
    except:
        lead_data = {}
