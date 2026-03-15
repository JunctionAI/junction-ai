"""
Appointments Dashboard for Unity MMA Voice Bot
Run: streamlit run appointments_dashboard.py
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# Config
st.set_page_config(
    page_title="Unity MMA - Voice Bot Dashboard",
    page_icon="🥊",
    layout="wide"
)

APPOINTMENTS_FILE = os.path.expanduser("~/junction-ai/barnaby_voice_bot/appointments.json")
CALL_LOG_FILE = os.path.expanduser("~/junction-ai/barnaby_voice_bot/call_log.json")

def load_json(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return []

# Header
st.title("🥊 Unity MMA - Voice Bot Dashboard")
st.markdown("---")

# Load data
appointments = load_json(APPOINTMENTS_FILE)
call_log = load_json(CALL_LOG_FILE)

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Calls", len(call_log))

with col2:
    st.metric("Trials Booked", len(appointments))

with col3:
    pending = len([a for a in appointments if a.get("status") == "pending"])
    st.metric("Pending Follow-ups", pending)

with col4:
    # Calls today
    today = datetime.now().date().isoformat()
    today_calls = len([c for c in call_log if c.get("timestamp", "").startswith(today)])
    st.metric("Calls Today", today_calls)

st.markdown("---")

# Two columns
left, right = st.columns(2)

with left:
    st.subheader("📅 Trial Bookings")

    if appointments:
        df = pd.DataFrame(appointments)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["booked_at"] = df["timestamp"].dt.strftime("%m/%d %H:%M")

        st.dataframe(
            df[["name", "phone", "type", "date", "time", "status", "booked_at"]],
            use_container_width=True,
            hide_index=True
        )

        # Export
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Bookings",
            csv,
            f"unity_mma_bookings_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    else:
        st.info("No bookings yet")

with right:
    st.subheader("📞 Recent Calls")

    if call_log:
        df = pd.DataFrame(call_log[-20:][::-1])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["time"] = df["timestamp"].dt.strftime("%m/%d %H:%M")

        st.dataframe(
            df[["time", "caller", "event", "duration"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No calls logged yet")

# Appointment Types breakdown
st.markdown("---")
st.subheader("📊 Booking Types")

if appointments:
    types = [a.get("type", "unknown") for a in appointments]
    type_counts = pd.Series(types).value_counts()
    st.bar_chart(type_counts)

# Call volume over time
st.markdown("---")
st.subheader("📈 Call Volume")

if call_log:
    df = pd.DataFrame(call_log)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # Only count call starts
    starts = df[df["event"] == "started"]
    if not starts.empty:
        daily = starts.groupby("date").size().reset_index(name="calls")
        st.line_chart(daily.set_index("date"))
    else:
        st.info("No call data to chart")

# Footer
st.markdown("---")
st.caption("Unity MMA Voice Bot Dashboard • Powered by Junction AI + VAPI")
