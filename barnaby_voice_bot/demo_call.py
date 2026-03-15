"""
Demo/Test Interface for Unity MMA Voice Bot
Simulates voice interactions for testing
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to use OpenAI for better voice simulation
try:
    from openai import OpenAI
    client = OpenAI()
    USE_OPENAI = True
except:
    USE_OPENAI = False
    print("OpenAI not available, using simple mode")

from config import GYM_INFO, TRIAL_URL, BOOKING_URL
from datetime import datetime

# Simulated conversation state
appointments = []

SYSTEM_PROMPT = f"""You are the friendly AI receptionist for {GYM_INFO['name']} - {GYM_INFO['tagline']}. You answer phone calls 24/7.

VOICE GUIDELINES:
- Speak naturally and conversationally
- Be warm, energetic, and fighter-friendly
- Keep responses SHORT (1-2 sentences per turn)
- Use positive, martial arts language

=== UNITY MMA INFO ===

LOCATION: {GYM_INFO['location']} - Rosedale, Albany, Auckland
PHONE: {GYM_INFO['phone']}
EMAIL: {GYM_INFO['email']}

CLASSES: {', '.join(GYM_INFO['classes'])}

PRICING:
- Adult: {GYM_INFO['pricing']['weekly_adult']}
- Students: {GYM_INFO['pricing']['weekly_student']}
- Casual: {GYM_INFO['pricing']['casual']}
- Personal Training: {GYM_INFO['pricing']['personal_training']}

FREE TRIAL: 1-Day FREE Trial - no experience needed!

COACHES: Ollie (Head Coach, nearly 50 fights), Levente, Barnaby, Brooke, Andre

Keep responses SHORT for voice!
"""

conversation = []

def get_response(user_input):
    """Get AI response for simulated call."""

    if USE_OPENAI:
        conversation.append({"role": "user", "content": user_input})

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )

        ai_response = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": ai_response})

        return ai_response
    else:
        # Simple fallback responses with Unity MMA info
        user_lower = user_input.lower()

        if "class" in user_lower or "offer" in user_lower:
            return "We offer MMA, Kickboxing, Boxing, Jiu Jitsu, Wrestling, and more! We also have Kids Kickboxing and Women's Boxing classes. Would you like to try a FREE 1-day trial?"

        elif "price" in user_lower or "cost" in user_lower or "member" in user_lower or "much" in user_lower:
            return "Adult membership is 49.99 per week, or 54.99 if you want to include Jiu Jitsu. Students get a discount at 39.99 per week. We also have casual sessions for 25 dollars. Want to try a FREE trial first?"

        elif "where" in user_lower or "location" in user_lower or "address" in user_lower:
            return "We're at 19B William Pickering Drive in Rosedale, Albany, Auckland. Easy to find with free parking. Want me to book you in for a free trial?"

        elif "trial" in user_lower or "free" in user_lower or "try" in user_lower:
            return "Awesome! Our 1-Day Free Trial lets you train with Auckland's best MMA and BJJ coaches - no experience needed! What's your name so I can get you booked in?"

        elif "coach" in user_lower or "trainer" in user_lower:
            return "Our head coach Ollie has nearly 50 fights under his belt! We also have Levente, Barnaby, Brooke for kickboxing and BJJ, and Andre for Jiu Jitsu. All world-class trainers!"

        elif "kid" in user_lower or "child" in user_lower:
            return "We have a great Kids Kickboxing program! It builds confidence and discipline while teaching them real martial arts skills. Parents love it!"

        elif "women" in user_lower or "ladies" in user_lower:
            return "We have Women's Boxing and Bootcamp classes - super popular! Great workout, learn self-defense, and awesome supportive community. Want to try it?"

        elif "bjj" in user_lower or "jiu jitsu" in user_lower or "grappling" in user_lower:
            return "Our Jiu Jitsu program is run by Coach Andre - great for self-defense and competition. BJJ membership is 54.99 per week. Want to book a trial?"

        elif "yes" in user_lower or "sure" in user_lower or "yeah" in user_lower:
            return "Great! What's your name?"

        elif "hour" in user_lower or "open" in user_lower or "time" in user_lower:
            return "We have classes running throughout the day - check our timetable on unitymma.co.nz. Want me to text you the link?"

        elif "what gym" in user_lower or "which gym" in user_lower or "name" in user_lower:
            return "This is Unity MMA! We're Auckland's newest and most diverse MMA gym, located in Rosedale, Albany. Would you like to know more about our classes or book a FREE trial?"

        else:
            return "I'd love to help! You've reached Unity MMA - Auckland's newest MMA gym with world-class coaches. We offer MMA, Boxing, Kickboxing, BJJ, and more. Would you like to book a FREE trial?"

def main():
    print("\n" + "="*60)
    print("🥊  UNITY MMA VOICE BOT - DEMO MODE")
    print("="*60)
    print("This simulates a phone call to Unity MMA")
    print("Type 'quit' to end the call")
    print("Type 'book' to simulate trial booking flow")
    print("="*60 + "\n")

    # Opening
    opening = f"Hey there! Thanks for calling {GYM_INFO['name']}! I'm your AI assistant. How can I help you today?"
    print(f"🤖 Bot: {opening}\n")

    if USE_OPENAI:
        conversation.append({"role": "assistant", "content": opening})

    while True:
        try:
            user_input = input("📞 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'quit':
                print("\n🤖 Bot: Thanks for calling Unity MMA! We can't wait to see you on the mats. Have an awesome day!\n")
                break

            if user_input.lower() == 'book':
                print("\n🤖 Bot: Awesome, let's get you set up for a FREE trial! What's your name?")
                name = input("📞 You: ").strip()
                print(f"\n🤖 Bot: Great to meet you, {name}! And what's the best phone number to reach you?")
                phone = input("📞 You: ").strip()
                print(f"\n🤖 Bot: Perfect! Have you trained martial arts before, or are you a complete beginner?")
                exp = input("📞 You: ").strip()
                print(f"\n🤖 Bot: And what are you most interested in - MMA, Boxing, Kickboxing, or BJJ?")
                interest = input("📞 You: ").strip()

                appointments.append({
                    "name": name,
                    "phone": phone,
                    "experience": exp,
                    "interest": interest,
                    "timestamp": datetime.now().isoformat()
                })

                print(f"\n🤖 Bot: You're all set, {name}! I've got you down for a FREE trial. We'll text you at {phone} with all the details. Can't wait to see you on the mats!\n")
                continue

            response = get_response(user_input)
            print(f"\n🤖 Bot: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Call ended!\n")
            break

    if appointments:
        print("\n📋 Trials booked this session:")
        for apt in appointments:
            print(f"  • {apt['name']} - {apt['phone']} - {apt.get('interest', 'General')}")

if __name__ == "__main__":
    main()
