import os
import json
import asyncio
import concurrent.futures
from dotenv import load_dotenv
load_dotenv()

from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from typing import TypedDict, Annotated
import operator

from browser_manager import get_browser_manager

# Memory
MEMORY_FILE = os.path.expanduser("~/junction-ai/memory.json")

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {"history": [], "context": ""}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

# Persona
CURRENT_PERSONA = """You are Junction AI — a sharp, rebellious sidekick that gets shit done.
Voice: Raw, direct, no fluff.
Format: ONLY deliver what's asked. Never cut off."""

def set_persona(p):
    global CURRENT_PERSONA
    CURRENT_PERSONA = p

def get_current_persona():
    return CURRENT_PERSONA

# Screenshot directory
SCREENSHOT_DIR = os.path.expanduser("~/junction-ai/")

# Thread pool for browser operations (sync playwright needs its own thread)
browser_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

def _browser_navigate_screenshot(url: str, filename: str) -> dict:
    """Run browser screenshot using persistent browser manager."""
    manager = get_browser_manager()
    return manager.navigate_and_screenshot(url, filename)

def _browser_take_control(url: str = None) -> dict:
    """Open visible browser for manual control."""
    manager = get_browser_manager()
    return manager.open_for_manual_control(url)

def _browser_resume() -> dict:
    """Resume headless mode after manual intervention."""
    manager = get_browser_manager()
    return manager.resume_headless()

def _browser_status() -> dict:
    """Get browser status."""
    manager = get_browser_manager()
    return manager.get_status()

# Tavily fallback search
def _tavily_search(query: str) -> str:
    """Sync Tavily search for fallback."""
    try:
        tavily = TavilySearch(max_results=5)
        return str(tavily.invoke(query))
    except Exception as e:
        return f"Search error: {e}"

# Tools
@tool
async def web_search(query: str) -> str:
    """Search the web for current information using Tavily."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _tavily_search, query)
        return result
    except Exception as e:
        return f"Search error: {e}"

@tool
async def browse_and_screenshot(url: str) -> str:
    """Navigate to a URL and take a screenshot using persistent browser."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            browser_executor,
            _browser_navigate_screenshot,
            url,
            "screenshot.png"
        )

        if result.get("barrier"):
            return f"BARRIER_DETECTED: Captcha or login required on {url}. Use /takecontrol to solve manually, then /resume. Falling back to text search."

        if result.get("success"):
            return f"SUCCESS: Screenshot saved to {result.get('path')}"

        return f"Browse failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"Browse/screenshot failed: {e}"

@tool
async def search_screenshot(query: str) -> str:
    """Search the web and take a screenshot of results. Uses persistent browser."""
    try:
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&t=h_&ia=web"
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            browser_executor,
            _browser_navigate_screenshot,
            search_url,
            "screenshot.png"
        )

        if result.get("barrier"):
            # Barrier detected - auto fallback to Tavily
            tavily_result = await loop.run_in_executor(None, _tavily_search, query)
            return f"BARRIER_DETECTED: Captcha hit. Use /takecontrol to solve, then /resume.\n\nFallback text results:\n{tavily_result}"

        if result.get("success"):
            return f"SUCCESS: Search screenshot saved to {result.get('path')}"

        # Browser failed - fallback
        tavily_result = await loop.run_in_executor(None, _tavily_search, query)
        return f"Browser issue, text results:\n{tavily_result}"

    except Exception as e:
        try:
            loop = asyncio.get_event_loop()
            tavily_result = await loop.run_in_executor(None, _tavily_search, query)
            return f"Screenshot failed ({e}), text results:\n{tavily_result}"
        except:
            return f"Search screenshot failed: {e}"

# Tool list
tools = [web_search, browse_and_screenshot, search_screenshot]

# Model
model = ChatXAI(model="grok-3", temperature=0.7)
model_with_tools = model.bind_tools(tools)

# State
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    sender: str
    original_goal: str
    tool_used: bool
    research_results: str
    barrier_hit: bool

# Check if last message has tool calls
def has_tool_calls(state):
    msgs = state.get("messages", [])
    if msgs:
        last = msgs[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return True
    return False

# Check if last message is tool result
def is_tool_result(state):
    msgs = state.get("messages", [])
    if msgs:
        return isinstance(msgs[-1], ToolMessage)
    return False

# Nodes
def supervisor(state):
    if state.get("tool_used") or is_tool_result(state):
        return {"messages": [AIMessage(content="-> creator")], "sender": "supervisor", "next": "creator"}

    if state.get("sender") == "creator":
        return {"messages": [AIMessage(content="-> FINISH")], "sender": "supervisor", "next": "FINISH"}

    goal = state.get("original_goal", "").lower()

    if any(k in goal for k in ["research", "search", "find", "latest", "news", "browse", "screenshot", "show"]):
        return {"messages": [AIMessage(content="-> researcher")], "sender": "supervisor", "next": "researcher"}

    return {"messages": [AIMessage(content="-> creator")], "sender": "supervisor", "next": "creator"}

async def researcher(state):
    """Async researcher node that calls tools."""
    goal = state.get("original_goal", "")

    prompt = f"""Research this: {goal}

Available tools:
- web_search: Search for current information (text results, always works)
- search_screenshot: Search the web and capture screenshot (may hit captcha, will auto-fallback)
- browse_and_screenshot: Navigate to specific URL and screenshot

If goal mentions screenshot of search results, use search_screenshot.
If goal mentions browsing a specific site, use browse_and_screenshot.
Always use web_search for factual information.

Do your research now."""

    response = await model_with_tools.ainvoke(state["messages"] + [
        SystemMessage(content="You are a researcher. Always use the tools provided."),
        HumanMessage(content=prompt)
    ])

    return {"messages": [response], "sender": "researcher", "tool_used": has_tool_calls({"messages": [response]})}

async def run_tools(state):
    """Async tool executor with barrier detection."""
    msgs = state.get("messages", [])
    last_msg = msgs[-1] if msgs else None

    if not last_msg or not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return {"messages": [], "tool_used": False}

    tool_results = []
    tool_map = {t.name: t for t in tools}
    barrier_hit = False

    for tool_call in last_msg.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name in tool_map:
            try:
                result = await tool_map[tool_name].ainvoke(tool_args)
                result_str = str(result)

                if "BARRIER_DETECTED" in result_str:
                    barrier_hit = True

                tool_results.append(ToolMessage(content=result_str, tool_call_id=tool_id))
            except Exception as e:
                tool_results.append(ToolMessage(content=f"Tool error: {e}", tool_call_id=tool_id))
        else:
            tool_results.append(ToolMessage(content=f"Unknown tool: {tool_name}", tool_call_id=tool_id))

    research_text = "\n".join([m.content for m in tool_results])

    return {
        "messages": tool_results,
        "tool_used": True,
        "research_results": research_text,
        "barrier_hit": barrier_hit
    }

def creator(state):
    goal = state.get("original_goal", "")
    research = state.get("research_results", "")
    barrier_hit = state.get("barrier_hit", False)

    fmt = ""
    if "3-tweet" in goal.lower() or "3 tweet" in goal.lower():
        fmt = "Output EXACTLY 3 tweets numbered 1/, 2/, 3/. Nothing else."
    elif "thread" in goal.lower():
        fmt = "Output a Twitter thread with numbered tweets."
    elif "summary" in goal.lower():
        fmt = "Output bullet-point summary."
    else:
        fmt = "Output only what was asked, concisely."

    context = ""
    if research:
        context = f"\n\nResearch findings:\n{research[:2000]}"

    barrier_note = ""
    if barrier_hit:
        barrier_note = "\n\nNote: A captcha/barrier was encountered. Text search results were used. User can use /takecontrol to solve manually."

    response = model.invoke(state["messages"] + [
        SystemMessage(content=get_current_persona() + f"\n\nFORMAT: {fmt}"),
        HumanMessage(content=f"Final output for: {goal}{context}{barrier_note}\n\nDeliver ONLY what was asked. Complete it fully.")
    ])

    memory = load_memory()
    memory["history"].append({"role": "creator", "content": response.content[:500]})
    memory["history"] = memory["history"][-10:]
    save_memory(memory)

    return {"messages": [response], "sender": "creator"}

def route_after_researcher(state):
    if has_tool_calls(state):
        return "tools"
    return "supervisor"

# Graph
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor)
workflow.add_node("researcher", researcher)
workflow.add_node("creator", creator)
workflow.add_node("tools", run_tools)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda x: x.get("next", "FINISH"),
    {
        "researcher": "researcher",
        "creator": "creator",
        "FINISH": END
    }
)

workflow.add_conditional_edges(
    "researcher",
    route_after_researcher,
    {
        "tools": "tools",
        "supervisor": "supervisor"
    }
)

workflow.add_edge("tools", "creator")
workflow.add_edge("creator", END)

app = workflow.compile()

# Exports for telegram bot
def open_browser_for_manual_control(url: str = None) -> str:
    """Open visible browser for manual control. Called from telegram bot."""
    result = _browser_take_control(url)
    return result.get("message", "Browser control initiated")

def resume_browser_session() -> str:
    """Resume headless mode after manual intervention."""
    result = _browser_resume()
    return result.get("message", "Session resumed")

def get_browser_session_status() -> dict:
    """Get current browser session status."""
    return _browser_status()
