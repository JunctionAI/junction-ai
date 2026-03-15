import os
import glob
import json
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import FSInputFile
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_xai import ChatXAI
from junction_core import app, set_persona, get_current_persona, open_browser_for_manual_control, resume_browser_session, get_browser_session_status
from personas import get_persona, list_personas
import subprocess

# File analysis imports
import PyPDF2
import pandas as pd

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

SCREENSHOT_DIR = os.path.expanduser("~/junction-ai/")
LOG_FILE = os.path.expanduser("~/junction-ai/usage_log.json")
AUTH_FILE = os.path.expanduser("~/junction-ai/authenticated_users.json")

fast_model = ChatXAI(model="grok-3", temperature=0.7)

ALLOWED_USER_IDS = [int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()]
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "junction2025")
ADMIN_ID = 825333001

def load_authenticated_users():
    try:
        with open(AUTH_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_authenticated_users(users):
    with open(AUTH_FILE, "w") as f:
        json.dump(list(users), f)

authenticated_users = load_authenticated_users()

def is_authorized(user_id):
    if ALLOWED_USER_IDS:
        return user_id in ALLOWED_USER_IDS
    return user_id in authenticated_users

def is_admin(user_id):
    return user_id == ADMIN_ID or user_id in ALLOWED_USER_IDS

def log_usage(user_id, goal, output_length, persona, fast_path=False):
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "goal": goal[:200],
            "output_length": output_length,
            "persona": persona,
            "fast_path": fast_path
        })
        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
    except:
        pass

def needs_full_swarm(goal):
    goal_lower = goal.lower()
    triggers = ["thread", "tweet", "post", "create", "make", "write", "generate",
                "research", "find", "search", "look up", "latest", "news",
                "strategy", "plan", "analyze", "browse", "screenshot", "show me",
                "viral", "content", "script", "article", "summary"]
    chat_patterns = [
        r"^(how|what|why|who|where|when)\s+(are|do|is|did|does|can|could|would|should)\s+(you|i|we)",
        r"^(hi|hey|hello|yo|sup)",
        r"^(thanks|thank you|cheers)",
        r"^(how do you feel|what do you think|your opinion)",
        r"^(tell me about yourself|who are you)",
    ]
    for t in triggers:
        if t in goal_lower:
            return True
    for p in chat_patterns:
        if re.match(p, goal_lower):
            return False
    return len(goal) > 80

def is_research_task(goal):
    goal_lower = goal.lower()
    return any(k in goal_lower for k in ["research", "search", "find", "latest", "news", "browse", "screenshot", "show"])

user_personas = {}

WELCOME_MSG = """🔥 Junction AI online!

• Chat fast
• Create threads/content
• Research the web
• Browse & screenshot
• Analyze files (PDF/Excel/CSV)

/persona <name> to switch
/personas to see options

What's the mission? 🎯"""

@dp.message(Command("start"))
async def start(message: types.Message):
    if not is_authorized(message.from_user.id):
        await message.answer("Junction AI is private. Contact @tomhalltaylor")
        return
    await message.answer(WELCOME_MSG)

@dp.message(Command("auth"))
async def auth(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/auth <password>")
        return
    if parts[1].strip() == BOT_PASSWORD:
        authenticated_users.add(message.from_user.id)
        save_authenticated_users(authenticated_users)
        await message.answer("You're in! 🔥\n\n" + WELCOME_MSG)
    else:
        await message.answer("Wrong password.")

@dp.message(Command("invite"))
async def invite_user(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Admin only.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/invite <user_id>")
        return
    try:
        new_id = int(parts[1].strip())
        authenticated_users.add(new_id)
        save_authenticated_users(authenticated_users)
        await message.answer(f"✅ Added {new_id}")
    except:
        await message.answer("Invalid ID")

@dp.message(Command("users"))
async def list_users(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    users = list(authenticated_users)
    await message.answer(f"Users: {len(users)}\n" + "\n".join(str(u) for u in users) if users else "None")

@dp.message(Command("personas"))
async def show_personas(message: types.Message):
    if not is_authorized(message.from_user.id):
        return
    await message.answer("Personas: " + ", ".join(list_personas()) + "\n\n/persona <name>")

@dp.message(Command("persona"))
async def switch_persona(message: types.Message):
    if not is_authorized(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(f"Current: {user_personas.get(message.from_user.id, 'default')}")
        return
    name = parts[1].strip().lower()
    if name in list_personas():
        user_personas[message.from_user.id] = name
        set_persona(get_persona(name))
        await message.answer(f"🔄 {name}")
    else:
        await message.answer(f"Unknown. Try: {', '.join(list_personas())}")

@dp.message(Command("memory"))
async def show_memory(message: types.Message):
    if not is_authorized(message.from_user.id):
        return
    try:
        with open(os.path.expanduser("~/junction-ai/memory.json"), "r") as f:
            memory = json.load(f)
        history = memory.get("history", [])
        if history:
            text = "🧠 Memory:\n"
            for item in history[-3:]:
                text += f"• {item.get('content', '')[:100]}...\n"
            await message.answer(text)
        else:
            await message.answer("Empty")
    except:
        await message.answer("No memory")

@dp.message(Command("usage"))
async def show_usage(message: types.Message):
    if not is_authorized(message.from_user.id):
        return
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
        user_logs = [l for l in logs if l.get("user_id") == message.from_user.id]
        await message.answer(f"📊 {len(user_logs)} runs")
    except:
        await message.answer("No data")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await start(message)

@dp.message(Command("takecontrol"))
async def take_control(message: types.Message):
    """Open a visible browser for manual captcha/login solving."""
    if not is_admin(message.from_user.id):
        await message.answer("Admin only — this opens a browser on the server.")
        return

    parts = message.text.split(maxsplit=1)
    url = parts[1].strip() if len(parts) > 1 else None  # Use current URL if none specified

    await message.answer("🖥️ Opening browser for manual control...")

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, open_browser_for_manual_control, url)
        await message.answer(f"🖥️ Browser window opened!\n\n{result}\n\n👉 Solve the captcha/login\n👉 Then send /resume to continue")
    except Exception as e:
        await message.answer(f"Couldn't open browser: {e}")

@dp.message(Command("resume"))
async def resume_control(message: types.Message):
    """Resume bot control after manual intervention."""
    if not is_admin(message.from_user.id):
        await message.answer("Admin only.")
        return

    await message.answer("🔄 Resuming control...")

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, resume_browser_session)
        await message.answer(f"✅ Back in control!\n\n{result}\n\nSend your next goal — I'll use the authenticated session.")
    except Exception as e:
        await message.answer(f"Resume failed: {e}")

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    """Show bot status and capabilities."""
    if not is_authorized(message.from_user.id):
        return

    # Get browser status
    try:
        browser_status = get_browser_session_status()
        browser_info = f"Browser: {'Running' if browser_status.get('running') else 'Stopped'}"
        if browser_status.get('running'):
            browser_info += f" ({'visible' if not browser_status.get('headless') else 'background'})"
            if browser_status.get('current_url'):
                browser_info += f"\nLast URL: {browser_status.get('current_url')[:50]}"
    except:
        browser_info = "Browser: Unknown"

    status = f"""🔥 Junction AI v3.2 Status

✅ Chat (fast path)
✅ Content creation (threads, tweets)
✅ Web search (Tavily)
✅ Browser screenshots (persistent session)
✅ File analysis (PDF/Excel/CSV)
✅ Barrier detection + auto-fallback
✅ Human takeover mode

{browser_info}

⚠️ If captcha hit:
1. /takecontrol - Opens visible browser
2. Solve captcha/login manually
3. /resume - Bot takes back control

Admin: /invite, /users, /takecontrol, /resume"""

    await message.answer(status)

# File analysis functions
def extract_pdf_text(file_path: str, max_pages: int = 10) -> str:
    """Extract text from PDF file."""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for i, page in enumerate(reader.pages[:max_pages]):
                text += page.extract_text() + "\n"
            if len(reader.pages) > max_pages:
                text += f"\n... [{len(reader.pages) - max_pages} more pages]"
            return text
    except Exception as e:
        return f"PDF extraction error: {e}"

def extract_excel_data(file_path: str, max_rows: int = 100) -> str:
    """Extract data from Excel file."""
    try:
        df = pd.read_excel(file_path, nrows=max_rows)
        summary = f"Columns: {', '.join(df.columns)}\n"
        summary += f"Rows: {len(df)} (showing up to {max_rows})\n\n"
        summary += df.to_string()
        return summary
    except Exception as e:
        return f"Excel extraction error: {e}"

def extract_csv_data(file_path: str, max_rows: int = 100) -> str:
    """Extract data from CSV file."""
    try:
        df = pd.read_csv(file_path, nrows=max_rows)
        summary = f"Columns: {', '.join(df.columns)}\n"
        summary += f"Rows: {len(df)} (showing up to {max_rows})\n\n"
        summary += df.to_string()
        return summary
    except Exception as e:
        return f"CSV extraction error: {e}"

@dp.message(F.document)
async def handle_document(message: types.Message):
    """Handle file uploads - PDF, Excel, CSV."""
    if not is_authorized(message.from_user.id):
        await message.answer("Not authorized. Contact @tomhalltaylor")
        return

    doc = message.document
    file_name = doc.file_name.lower()
    caption = message.caption or "Summarize this file"

    # Check supported formats
    if not any(file_name.endswith(ext) for ext in ['.pdf', '.xlsx', '.xls', '.csv']):
        await message.answer("📄 I can analyze PDF, Excel (.xlsx/.xls), and CSV files.\nSend one of those!")
        return

    status_msg = await message.answer("📄 Analyzing file...")

    try:
        # Download file
        file = await bot.get_file(doc.file_id)
        file_path = os.path.join(SCREENSHOT_DIR, f"upload_{doc.file_id}_{doc.file_name}")
        await bot.download_file(file.file_path, file_path)

        # Extract content based on type
        if file_name.endswith('.pdf'):
            content = extract_pdf_text(file_path)
            file_type = "PDF"
        elif file_name.endswith(('.xlsx', '.xls')):
            content = extract_excel_data(file_path)
            file_type = "Excel"
        elif file_name.endswith('.csv'):
            content = extract_csv_data(file_path)
            file_type = "CSV"

        # Clean up
        try:
            os.remove(file_path)
        except:
            pass

        # Analyze with AI
        current_persona = user_personas.get(message.from_user.id, "default")
        set_persona(get_persona(current_persona))
        persona_text = get_current_persona()

        response = fast_model.invoke([
            SystemMessage(content=persona_text + f"\n\nYou received a {file_type} file. Analyze it based on the user's request."),
            HumanMessage(content=f"User request: {caption}\n\nFile content:\n{content[:8000]}")
        ])

        await status_msg.delete()
        await message.answer(f"📄 {file_type} Analysis:\n\n{response.content}")
        log_usage(message.from_user.id, f"File: {doc.file_name}", len(response.content), current_persona, True)

    except Exception as e:
        await status_msg.delete()
        await message.answer(f"Error analyzing file: {str(e)[:100]}")

@dp.message(F.text)
async def handle(message: types.Message):
    if not is_authorized(message.from_user.id):
        await message.answer("Not authorized. Contact @tomhalltaylor")
        return

    goal = message.text
    current_persona = user_personas.get(message.from_user.id, "default")
    set_persona(get_persona(current_persona))
    persona_text = get_current_persona()

    # FAST PATH
    if not needs_full_swarm(goal):
        try:
            response = fast_model.invoke([
                SystemMessage(content=persona_text + "\n\nBe concise, cheeky. 1-3 sentences."),
                HumanMessage(content=goal)
            ])
            await message.answer(response.content)
            log_usage(message.from_user.id, goal, len(response.content), current_persona, True)
            return
        except Exception as e:
            await message.answer(f"Error: {e}")
            return

    # FULL SWARM
    if is_research_task(goal):
        status_msg = await message.answer("🔍 Searching the web...")
    else:
        status_msg = await message.answer("🔥 On it...")

    # Clear screenshot
    screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot.png")
    try:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
    except:
        pass

    try:
        final = ""

        async for chunk in app.astream(
            {"messages": [HumanMessage(content=goal)], "original_goal": goal, "tool_used": False},
            {"recursion_limit": 100}
        ):
            # Update status for tool use
            if "tools" in str(chunk):
                try:
                    await status_msg.edit_text("🌐 Browsing... screenshot incoming")
                except:
                    pass

            if "creator" in str(chunk):
                for v in chunk.values():
                    if isinstance(v, dict) and "messages" in v:
                        for m in v["messages"]:
                            if hasattr(m, "content") and m.content:
                                final += m.content + "\n\n"

        # Delete status
        try:
            await status_msg.delete()
        except:
            pass

        log_usage(message.from_user.id, goal, len(final), current_persona, False)

        # Screenshots - check for screenshot.png
        screenshot_path = os.path.join(SCREENSHOT_DIR, "screenshot.png")
        screenshot_sent = False

        if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 1000:
            try:
                # Dynamic caption based on goal
                if "search" in goal.lower() or "research" in goal.lower():
                    caption = "📸 Live search results"
                elif "browse" in goal.lower() or "show" in goal.lower():
                    caption = "📸 Live page capture"
                else:
                    caption = "📸 Here's what I found"

                await message.answer_photo(
                    photo=FSInputFile(screenshot_path),
                    caption=caption
                )
                screenshot_sent = True
            except Exception as e:
                await message.answer(f"📸 Screenshot captured but couldn't send: {str(e)[:100]}")

        # Fallback message if screenshot was expected but failed
        if not screenshot_sent and "screenshot" in goal.lower():
            await message.answer("📸 Screenshot failed — here's the summary instead:")

        if final.strip():
            for part in [final[i:i+4000] for i in range(0, len(final), 4000)]:
                await message.answer(part)
        else:
            await message.answer("Done — try a clearer goal?")

        await message.answer("🎯 Next?")

    except Exception as e:
        try:
            await status_msg.delete()
        except:
            pass
        await message.answer(f"Error: {str(e)[:150]}")

async def main():
    print("Junction AI Sidekick v3.2", flush=True)
    print(f"Admin: {ADMIN_ID}", flush=True)
    print("Features: Persistent Browser, Human Takeover, Files", flush=True)
    print("Starting...", flush=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
