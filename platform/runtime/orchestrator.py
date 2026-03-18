"""
Multi-tenant orchestrator — handles messages for all Junction AI customers.
Calls Claude with the full agent brain, saves messages, extracts facts.
"""

import os
import json
import logging
from datetime import datetime, timezone

import anthropic

import db
from brain_loader import load_agent_brain

logger = logging.getLogger("runtime")

# Model cost rates (per token)
MODEL_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00000025, "output": 0.00000125},
    "claude-sonnet-4-6": {"input": 0.000003, "output": 0.000015},
    "claude-opus-4-6": {"input": 0.000015, "output": 0.000075},
}


async def handle_message(user_id: str, agent_id: str, agent_data: dict,
                          message: str, channel_id: str) -> str:
    """
    Handle a user message to an agent:
    1. Load full brain
    2. Load conversation history
    3. Call Claude
    4. Save messages
    5. Log usage
    6. Extract facts (async, non-blocking)
    """
    # Load brain
    system_prompt = await load_agent_brain(agent_id, user_id, agent_data)
    if not system_prompt:
        return "I'm having trouble loading my configuration. Please try again."

    # Load conversation history
    history = await db.get_recent_messages(user_id, agent_id, limit=20)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    # Call Claude (async client — required in async event loop)
    model = agent_data.get("model", "claude-sonnet-4-6")
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    logger.info(f"Calling Claude {model} for agent {agent_id[:8]}...")
    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    logger.info(f"Claude responded ({response.usage.output_tokens} output tokens)")

    response_text = response.content[0].text

    # Save messages
    await db.save_messages(user_id, agent_id, channel_id, message, response_text)

    # Log usage
    costs = MODEL_COSTS.get(model, {"input": 0.000003, "output": 0.000015})
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost_usd = input_tokens * costs["input"] + output_tokens * costs["output"]

    await db.log_usage(user_id, agent_id, "anthropic", model,
                       input_tokens, output_tokens, cost_usd)

    # Extract facts in background (non-blocking)
    try:
        await extract_facts(user_id, agent_id, message, response_text)
    except Exception as e:
        logger.warning(f"Fact extraction failed (non-fatal): {e}")

    return response_text


async def extract_last_commitment(user_id: str, agent_id: str, anthropic_client) -> str:
    """Use Haiku to extract what the user last committed to doing."""
    try:
        pool = await db.get_pool()
        rows = await pool.fetch("""
            SELECT role, content FROM messages
            WHERE user_id = $1 AND agent_id = $2
            ORDER BY created_at DESC LIMIT 10
        """, user_id, agent_id)

        if not rows:
            return "No previous conversations yet."

        conversation = "\n".join([f"{r['role'].upper()}: {r['content']}" for r in reversed(rows)])

        response = await anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"From this conversation, extract in one sentence what the user said they would do before next check-in. If nothing was committed to, say 'No specific commitment made yet.'\n\nConversation:\n{conversation}"
            }]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Commitment extraction failed: {e}")
        return "No previous commitment found."


async def handle_scheduled_task(schedule: dict) -> str:
    """
    Execute a scheduled task:
    1. Load agent brain
    2. Build dynamic check-in prompt using last commitment + days since contact
    3. Call Claude with dynamic prompt
    4. Return response (caller sends to Telegram)
    """
    agent_id = schedule["agent_id"]
    user_id = schedule["user_id"]
    model = schedule.get("model", "claude-sonnet-4-6")
    task_prompt = schedule["task_prompt"]

    # Load brain (need to fetch agent data)
    pool = await db.get_pool()
    row = await pool.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
    if not row:
        logger.error(f"Schedule: agent {agent_id} not found")
        return ""
    agent_data = dict(row)

    system_prompt = await load_agent_brain(agent_id, user_id, agent_data)
    if not system_prompt:
        return ""

    # Load last message timestamp to calculate days since contact
    last_msg = await pool.fetchrow("""
        SELECT created_at FROM messages
        WHERE user_id = $1 AND agent_id = $2
        ORDER BY created_at DESC LIMIT 1
    """, user_id, agent_id)

    # Use async client for commitment extraction (Haiku call)
    async_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Extract last commitment (Haiku, fast)
    last_commitment = await extract_last_commitment(user_id, agent_id, async_client)

    # Calculate days since last contact
    if last_msg:
        last_contact = last_msg["created_at"]
        if last_contact.tzinfo is None:
            last_contact = last_contact.replace(tzinfo=timezone.utc)
        days_since = (datetime.now(timezone.utc) - last_contact).days
        days_text = f"{days_since} day{'s' if days_since != 1 else ''} ago"
    else:
        days_text = "first contact"

    # Build dynamic check-in instruction
    dynamic_instruction = f"""It is time for a scheduled check-in.

LAST COMMITMENT: {last_commitment}
LAST CONTACT: {days_text}

Your job:
- If there was a commitment, reference it naturally. Ask if they did it. If it's been more than 2 days, acknowledge the gap without judgment — then ask what happened.
- Ask one question that moves them forward today.
- Do not summarise who you are or repeat the goal. They know. Just talk.
- Maximum 4 sentences. Mobile-readable. Feel like a message from someone who actually knows them.
- Style hint: {task_prompt}"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": dynamic_instruction}],
    )

    response_text = response.content[0].text

    # Log usage
    costs = MODEL_COSTS.get(model, {"input": 0.000003, "output": 0.000015})
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost_usd = input_tokens * costs["input"] + output_tokens * costs["output"]

    await db.log_usage(user_id, agent_id, "anthropic", model,
                       input_tokens, output_tokens, cost_usd)

    # Save as messages
    await db.save_messages(user_id, agent_id, "scheduled",
                           f"[Scheduled: {schedule.get('task_name', 'task')}] {task_prompt}",
                           response_text)

    return response_text


async def extract_facts(user_id: str, agent_id: str,
                         user_message: str, assistant_response: str):
    """
    After every conversation, use Haiku to extract facts about the user.
    Same pattern as tom-command-center's user_memory.py.
    """
    # Get existing facts to avoid duplicates
    existing = await db.get_user_facts(user_id, limit=200)
    existing_text = "\n".join(f"- {f['fact']}" for f in existing) if existing else "(none yet)"

    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Extract facts about this user from the conversation below.
Only extract PERMANENT facts (preferences, identity, goals, relationships) — not temporary states.

EXISTING FACTS (do not duplicate):
{existing_text}

CONVERSATION:
User: {user_message}
Assistant: {assistant_response}

For each new fact, output JSON array:
[{{"action": "add", "fact": "...", "category": "identity|business|goals|preferences|relationships|general"}}]

If no new facts, output: []
Only output the JSON array, nothing else."""
        }],
    )

    text = response.content[0].text.strip()
    if text == "[]" or not text:
        return

    try:
        facts = json.loads(text)
        new_facts = [f for f in facts if f.get("action") == "add" and f.get("fact")]
        if new_facts:
            await db.save_facts(user_id, agent_id, new_facts)
            logger.info(f"Extracted {len(new_facts)} facts for user {user_id[:8]}...")
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse fact extraction response: {text[:100]}")

    # Log Haiku usage
    costs = MODEL_COSTS["claude-haiku-4-5-20251001"]
    await db.log_usage(
        user_id, agent_id, "anthropic", "claude-haiku-4-5-20251001",
        response.usage.input_tokens, response.usage.output_tokens,
        response.usage.input_tokens * costs["input"] + response.usage.output_tokens * costs["output"]
    )
