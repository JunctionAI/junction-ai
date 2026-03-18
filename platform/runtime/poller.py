"""
Multi-tenant Telegram poller — one shared @JunctionAIBot.
Routes messages to the correct agent based on chat_id → agent_channels mapping.
Handles /start (verification), /link (agent connection), and regular messages.
"""

import os
import asyncio
import logging
import random
import string
from datetime import datetime, timedelta, timezone

import requests

import db
from orchestrator import handle_message

logger = logging.getLogger("runtime")

BOT_TOKEN = None


def get_bot_token():
    global BOT_TOKEN
    if not BOT_TOKEN:
        BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    return BOT_TOKEN


def send_telegram(chat_id: str, text: str):
    """Send a message via Telegram Bot API."""
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Split long messages (Telegram limit: 4096 chars)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        try:
            resp = requests.post(url, json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
            }, timeout=10)
            if not resp.ok:
                # Retry without markdown
                requests.post(url, json={
                    "chat_id": chat_id,
                    "text": chunk,
                }, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")


async def handle_start(chat_id: str, telegram_user_id: str):
    """Handle /start — generate verification code."""
    code = ''.join(random.choices(string.digits, k=6))
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    await db.create_verification_code(telegram_user_id, code, expires)

    send_telegram(chat_id,
        f"Welcome to Junction AI!\n\n"
        f"Your verification code is: *{code}*\n\n"
        f"Enter this code on getjunction.ai to link your Telegram account.\n"
        f"This code expires in 15 minutes."
    )
    logger.info(f"/start from telegram_user={telegram_user_id}, code generated")


async def handle_link(chat_id: str, telegram_user_id: str, text: str):
    """Handle /link [agent-slug] — connect an agent to this group chat."""
    # Find the Junction user for this Telegram user
    tg_user = await db.get_telegram_user(telegram_user_id)
    if not tg_user:
        send_telegram(chat_id,
            "You haven't linked your Telegram account yet.\n"
            "Send /start in a private chat with me first, then enter the code on getjunction.ai."
        )
        return

    user_id = tg_user["user_id"]

    # Parse agent slug from command
    parts = text.strip().split()
    if len(parts) < 2:
        # No slug provided — link to the most recently created unlinked agent
        pool = await db.get_pool()
        row = await pool.fetchrow("""
            SELECT id, slug, display_name FROM agents
            WHERE user_id = $1 AND is_active = true
              AND id NOT IN (SELECT agent_id FROM agent_channels)
            ORDER BY created_at DESC LIMIT 1
        """, user_id)
        if not row:
            send_telegram(chat_id,
                "No unlinked agents found. Create an agent on getjunction.ai first, "
                "or specify the agent: /link agent-slug"
            )
            return
        agent = dict(row)
    else:
        slug = parts[1].lower().strip()
        pool = await db.get_pool()
        row = await pool.fetchrow("""
            SELECT id, slug, display_name FROM agents
            WHERE user_id = $1 AND slug = $2
        """, user_id, slug)
        if not row:
            send_telegram(chat_id, f"Agent '{slug}' not found. Check the slug on your dashboard.")
            return
        agent = dict(row)

    # Check if this chat is already linked
    pool = await db.get_pool()
    existing = await pool.fetchrow(
        "SELECT agent_id FROM agent_channels WHERE channel_id = $1", str(chat_id)
    )
    if existing:
        send_telegram(chat_id, "This group is already linked to an agent. Unlink it from the dashboard first.")
        return

    # Create the link
    await pool.execute("""
        INSERT INTO agent_channels (agent_id, user_id, channel_type, channel_id)
        VALUES ($1, $2, 'telegram', $3)
    """, agent["id"], user_id, str(chat_id))

    logger.info(f"/link: agent={agent['slug']} chat={chat_id} user={str(user_id)[:8]}...")

    # Check for a pending first message in context_md
    agent_row = await pool.fetchrow("SELECT context_md FROM agents WHERE id = $1", agent["id"])
    context_md = agent_row["context_md"] or "" if agent_row else ""

    MARKER = "### PENDING_FIRST_MESSAGE\n"
    if MARKER in context_md:
        # Extract the first message
        start = context_md.index(MARKER) + len(MARKER)
        end = context_md.find("\n\n", start)
        first_message = context_md[start:end].strip() if end != -1 else context_md[start:].strip()

        # Remove the marker from context_md
        cleaned = context_md.replace(context_md[context_md.index(MARKER):end + 2], "").strip()
        await pool.execute("UPDATE agents SET context_md = $1 WHERE id = $2", cleaned, agent["id"])

        # Send the agent's intro immediately
        send_telegram(chat_id, first_message)
    else:
        # No pending first message — send a simple confirmation
        send_telegram(chat_id,
            f"✓ *{agent['display_name']}* is connected. Send a message to start."
        )


async def handle_regular_message(chat_id: str, telegram_user_id: str, text: str):
    """Route a regular message to the correct agent."""
    logger.info(f"handle_regular_message: chat={chat_id} tg_user={telegram_user_id} text={text[:60]}")

    # Look up agent for this chat
    agent_data = await db.get_agent_by_channel(str(chat_id))
    if not agent_data:
        logger.info(f"No agent linked to chat {chat_id}")
        tg_user = await db.get_telegram_user(telegram_user_id)
        if tg_user:
            send_telegram(chat_id,
                "This group isn't linked to an agent yet.\n"
                "Use /link to connect it, or create an agent at getjunction.ai."
            )
        return

    logger.info(f"Agent found: {agent_data['slug']} (active={agent_data['is_active']})")

    if not agent_data["is_active"]:
        send_telegram(chat_id, "This agent is currently paused.")
        return

    # Verify the sender is the owner
    tg_user = await db.get_telegram_user(telegram_user_id)
    logger.info(f"tg_user lookup: found={tg_user is not None}")
    if not tg_user:
        logger.warning(f"Unknown Telegram user {telegram_user_id} in chat {chat_id}")
        send_telegram(chat_id, "I don't recognise you. Send /start to @JunctionAIBot to link your account.")
        return

    agent_user_id = str(agent_data["user_id"])
    tg_user_id = str(tg_user["user_id"])
    logger.info(f"Owner check: agent_user={agent_user_id[:8]}... tg_user={tg_user_id[:8]}... match={agent_user_id == tg_user_id}")

    if agent_user_id != tg_user_id:
        logger.warning(f"Owner mismatch: agent={agent_user_id[:8]} tg={tg_user_id[:8]}")
        return

    # Process through orchestrator
    logger.info(f"Routing to orchestrator for agent {agent_data['slug']}")
    try:
        response = await handle_message(
            user_id=str(agent_data["user_id"]),
            agent_id=str(agent_data["agent_id"]),
            agent_data=agent_data,
            message=text,
            channel_id=str(chat_id),
        )
        logger.info(f"Got response ({len(response) if response else 0} chars), sending...")
        if response:
            send_telegram(chat_id, response)
        else:
            logger.warning(f"Empty response from handle_message for chat {chat_id}")
    except Exception as e:
        logger.error(f"Error handling message in chat {chat_id}: {e}", exc_info=True)
        send_telegram(chat_id, "Something went wrong. Please try again.")


OFFSET_FILE = "/tmp/tg_offset.txt"

def load_offset() -> int:
    try:
        with open(OFFSET_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_offset(offset: int):
    try:
        with open(OFFSET_FILE, "w") as f:
            f.write(str(offset))
    except Exception:
        pass


async def poll_loop():
    """Long-polling loop for Telegram updates."""
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = load_offset()

    logger.info(f"Starting multi-tenant Telegram polling (offset={offset})...")

    # Verify bot
    me = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()
    if me.get("ok"):
        bot_name = me["result"].get("username", "unknown")
        logger.info(f"Bot: @{bot_name}")
    else:
        logger.error(f"Bot verification failed: {me}")
        return

    while True:
        try:
            resp = requests.get(url, params={
                "offset": offset,
                "timeout": 30,
            }, timeout=35)

            data = resp.json()
            if not data.get("ok") or not data.get("result"):
                await asyncio.sleep(1)
                continue

            for update in data["result"]:
                offset = update["update_id"] + 1
                save_offset(offset)

                message = update.get("message")
                if not message:
                    continue

                text = message.get("text", "")
                chat_id = str(message.get("chat", {}).get("id", ""))
                telegram_user_id = str(message.get("from", {}).get("id", ""))

                if not text or not chat_id:
                    continue

                logger.info(f"Message: chat={chat_id} user={telegram_user_id} text={text[:60]}")

                # Route commands
                if text.startswith("/start"):
                    await handle_start(chat_id, telegram_user_id)
                elif text.startswith("/link"):
                    await handle_link(chat_id, telegram_user_id, text)
                elif text.startswith("/"):
                    # Ignore other commands for now
                    pass
                else:
                    await handle_regular_message(chat_id, telegram_user_id, text)

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)
            await asyncio.sleep(5)
