"""
Email Dashboard for Unity MMA Email Bot
Run: streamlit run email_dashboard.py
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# Config
st.set_page_config(
    page_title="Unity MMA - Email Bot Dashboard",
    page_icon="📧",
    layout="wide"
)

EMAIL_LOG_FILE = os.path.expanduser("~/junction-ai/barnaby_email_bot/email_log.json")

def load_email_log():
    try:
        with open(EMAIL_LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"processed": [], "escalations": [], "stats": {"total": 0, "auto_replied": 0, "escalated": 0, "ignored": 0}}

# Header
st.title("📧 Unity MMA - Email Bot Dashboard")
st.markdown("---")

# Load data
log = load_email_log()
stats = log.get("stats", {})
processed = log.get("processed", [])
escalations = log.get("escalations", [])

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Processed", stats.get("total", 0))

with col2:
    st.metric("Auto-Replied", stats.get("auto_replied", 0), delta=None)

with col3:
    st.metric("Escalated", stats.get("escalated", 0), delta=None)

with col4:
    st.metric("Ignored", stats.get("ignored", 0), delta=None)

st.markdown("---")

# Automation rate
if stats.get("total", 0) > 0:
    auto_rate = (stats.get("auto_replied", 0) / stats.get("total", 1)) * 100
    st.progress(auto_rate / 100)
    st.caption(f"Automation Rate: {auto_rate:.1f}% of emails handled automatically")

st.markdown("---")

# Two columns
left, right = st.columns(2)

with left:
    st.subheader("⚠️ Escalations (Needs Human)")

    if escalations:
        for esc in reversed(escalations[-10:]):
            with st.expander(f"{esc.get('subject', 'No subject')[:50]}... ({esc.get('intent', 'unknown')})"):
                st.write(f"**From:** {esc.get('sender', 'Unknown')}")
                st.write(f"**Intent:** {esc.get('intent', 'unknown')}")
                st.write(f"**Time:** {esc.get('timestamp', '')[:19]}")
                st.text_area("Message", esc.get("body", "")[:500], height=100, key=f"esc_{esc.get('timestamp', '')}")
    else:
        st.info("No escalations yet - all emails handled automatically!")

with right:
    st.subheader("📝 Recent Activity")

    if processed:
        recent = processed[-20:][::-1]

        for p in recent:
            email = p.get("email", {})
            action_icon = {"auto_reply": "✅", "escalate": "⚠️", "ignore": "🔇"}.get(p.get("action", ""), "❓")
            confidence = p.get("confidence", 0) * 100

            st.markdown(f"""
            {action_icon} **{p.get('intent', 'unknown')}** ({confidence:.0f}%)
            - From: {email.get('sender_email', 'Unknown')[:30]}
            - Subject: {email.get('subject', 'No subject')[:40]}...
            """)
    else:
        st.info("No emails processed yet.")

st.markdown("---")

# Intent distribution
st.subheader("📊 Intent Distribution")

if processed:
    intents = [p.get("intent", "unknown") for p in processed]
    intent_counts = pd.Series(intents).value_counts()
    st.bar_chart(intent_counts)

# Action distribution pie chart
st.subheader("🎯 Action Breakdown")

if stats.get("total", 0) > 0:
    action_data = {
        "Auto-Replied": stats.get("auto_replied", 0),
        "Escalated": stats.get("escalated", 0),
        "Ignored": stats.get("ignored", 0)
    }
    st.bar_chart(action_data)

st.markdown("---")

# Recent processed emails table
st.subheader("📋 Processed Emails Log")

if processed:
    df_data = []
    for p in processed[-50:]:
        email = p.get("email", {})
        df_data.append({
            "Time": p.get("timestamp", "")[:19],
            "From": email.get("sender_email", "")[:30],
            "Subject": email.get("subject", "")[:50],
            "Intent": p.get("intent", ""),
            "Action": p.get("action", ""),
            "Confidence": f"{p.get('confidence', 0)*100:.0f}%"
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download Log",
        csv,
        f"unity_mma_email_log_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
else:
    st.info("No emails in log yet.")

# Footer
st.markdown("---")
st.caption("Unity MMA Email Bot Dashboard • Powered by Junction AI")
