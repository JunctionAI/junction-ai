"""
Junction AI Admin Dashboard
Run: streamlit run dashboard.py
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd

# Config
st.set_page_config(
    page_title="Junction AI Dashboard",
    page_icon="🔥",
    layout="wide"
)

# Files
LOG_FILE = os.path.expanduser("~/junction-ai/usage_log.json")
AUTH_FILE = os.path.expanduser("~/junction-ai/authenticated_users.json")
MEMORY_FILE = os.path.expanduser("~/junction-ai/memory.json")

def load_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def load_users():
    try:
        with open(AUTH_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {"history": []}

# Header
st.title("🔥 Junction AI Dashboard")
st.markdown("---")

# Load data
logs = load_logs()
users = load_users()
memory = load_memory()

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Runs", len(logs))

with col2:
    st.metric("Active Users", len(users))

with col3:
    # Runs today
    today = datetime.now().date()
    today_runs = len([l for l in logs if datetime.fromisoformat(l.get("timestamp", "2000-01-01")).date() == today])
    st.metric("Runs Today", today_runs)

with col4:
    # Fast path %
    fast = len([l for l in logs if l.get("fast_path")])
    pct = (fast / len(logs) * 100) if logs else 0
    st.metric("Fast Path %", f"{pct:.0f}%")

st.markdown("---")

# Two columns
left, right = st.columns(2)

with left:
    st.subheader("📊 Recent Activity")

    if logs:
        df = pd.DataFrame(logs[-50:][::-1])  # Last 50, newest first
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["time"] = df["timestamp"].dt.strftime("%m/%d %H:%M")
        df["goal_short"] = df["goal"].str[:50] + "..."

        st.dataframe(
            df[["time", "user_id", "goal_short", "persona", "fast_path"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No activity yet")

with right:
    st.subheader("👥 Users")
    if users:
        for user_id in users:
            user_runs = len([l for l in logs if l.get("user_id") == user_id])
            st.write(f"• `{user_id}` — {user_runs} runs")
    else:
        st.info("No users yet")

    st.markdown("---")

    st.subheader("🧠 Memory")
    history = memory.get("history", [])
    if history:
        for item in history[-5:][::-1]:
            st.write(f"• {item.get('content', '')[:100]}...")
    else:
        st.info("No memory yet")

st.markdown("---")

# Usage over time chart
st.subheader("📈 Usage Over Time")

if logs:
    df = pd.DataFrame(logs)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    daily = df.groupby("date").size().reset_index(name="runs")
    st.line_chart(daily.set_index("date"))
else:
    st.info("No data yet")

# Revenue projection
st.markdown("---")
st.subheader("💰 Revenue Projection")

col1, col2, col3 = st.columns(3)

with col1:
    price_per_user = st.number_input("Monthly price per user ($)", value=97, min_value=0)

with col2:
    target_users = st.number_input("Target users", value=100, min_value=0)

with col3:
    current_users = len(users)
    monthly_revenue = current_users * price_per_user
    target_revenue = target_users * price_per_user

    st.metric("Current MRR", f"${monthly_revenue:,}")
    st.metric("Target MRR", f"${target_revenue:,}")

st.markdown("---")

# Persona breakdown
st.subheader("🎭 Persona Usage")

if logs:
    df = pd.DataFrame(logs)
    persona_counts = df["persona"].value_counts()
    st.bar_chart(persona_counts)
else:
    st.info("No data yet")

# Footer
st.markdown("---")
st.caption("Junction AI v3.0 • Built for domination")
