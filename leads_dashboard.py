#!/usr/bin/env python3
"""
Unity MMA - Real-Time Leads Dashboard
Aggregates leads from Email, DM, and Voice bots
"""

import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# Page config
st.set_page_config(
    page_title="Unity MMA Leads",
    page_icon="🥊",
    layout="wide"
)

# Data files
LEADS_FILES = {
    "email": "barnaby_email_bot/email_stats.json",
    "dm": "barnaby_dm_bot/leads.json",
    "voice": "barnaby_voice_bot/calls.json"
}

def load_email_leads():
    """Load leads from email bot."""
    leads = []
    try:
        if os.path.exists(LEADS_FILES["email"]):
            with open(LEADS_FILES["email"], "r") as f:
                data = json.load(f)
                for item in data.get("processed", []):
                    if item.get("action") in ["auto_reply", "escalate"]:
                        leads.append({
                            "source": "📧 Email",
                            "name": item.get("sender_name", "Unknown"),
                            "contact": item.get("sender_email", ""),
                            "intent": item.get("intent", ""),
                            "action": item.get("action", ""),
                            "timestamp": item.get("timestamp", ""),
                            "message": item.get("subject", "")[:50]
                        })
    except Exception as e:
        st.error(f"Error loading email leads: {e}")
    return leads

def load_dm_leads():
    """Load leads from DM bot."""
    leads = []
    try:
        if os.path.exists(LEADS_FILES["dm"]):
            with open(LEADS_FILES["dm"], "r") as f:
                data = json.load(f)
                for user_id, info in data.items():
                    leads.append({
                        "source": "💬 Instagram/FB",
                        "name": info.get("name", "Unknown"),
                        "contact": info.get("phone", info.get("email", user_id)),
                        "intent": info.get("fitness_goal", "Enquiry"),
                        "action": "engaged",
                        "timestamp": info.get("last_interaction", ""),
                        "message": f"{info.get('message_count', 0)} messages"
                    })
    except Exception as e:
        st.error(f"Error loading DM leads: {e}")
    return leads

def load_voice_leads():
    """Load leads from voice bot."""
    leads = []
    try:
        if os.path.exists(LEADS_FILES["voice"]):
            with open(LEADS_FILES["voice"], "r") as f:
                data = json.load(f)
                for call in data:
                    leads.append({
                        "source": "📞 Phone",
                        "name": call.get("caller_name", "Caller"),
                        "contact": call.get("phone_number", ""),
                        "intent": call.get("intent", ""),
                        "action": call.get("outcome", ""),
                        "timestamp": call.get("timestamp", ""),
                        "message": f"{call.get('duration_seconds', 0)}s call"
                    })
    except Exception as e:
        st.error(f"Error loading voice leads: {e}")
    return leads

def main():
    st.title("🥊 Unity MMA - Live Leads Dashboard")
    st.markdown("Real-time leads from Email, Instagram/Facebook, and Phone")

    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=False)

    if auto_refresh:
        st.markdown("*Refreshing every 30 seconds...*")
        import time
        time.sleep(30)
        st.rerun()

    st.divider()

    # Load all leads
    all_leads = []
    all_leads.extend(load_email_leads())
    all_leads.extend(load_dm_leads())
    all_leads.extend(load_voice_leads())

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    email_count = len([l for l in all_leads if "Email" in l["source"]])
    dm_count = len([l for l in all_leads if "Instagram" in l["source"]])
    voice_count = len([l for l in all_leads if "Phone" in l["source"]])

    with col1:
        st.metric("Total Leads", len(all_leads))
    with col2:
        st.metric("📧 Email", email_count)
    with col3:
        st.metric("💬 DM", dm_count)
    with col4:
        st.metric("📞 Phone", voice_count)

    st.divider()

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        source_filter = st.multiselect(
            "Filter by Source",
            ["📧 Email", "💬 Instagram/FB", "📞 Phone"],
            default=["📧 Email", "💬 Instagram/FB", "📞 Phone"]
        )
    with col2:
        action_filter = st.multiselect(
            "Filter by Action",
            ["auto_reply", "escalate", "engaged"],
            default=["auto_reply", "escalate", "engaged"]
        )

    # Filter leads
    filtered_leads = [
        l for l in all_leads
        if l["source"] in source_filter and l["action"] in action_filter
    ]

    # Display leads table
    if filtered_leads:
        df = pd.DataFrame(filtered_leads)

        # Reorder columns
        columns_order = ["source", "name", "contact", "intent", "action", "message", "timestamp"]
        df = df[[c for c in columns_order if c in df.columns]]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "source": st.column_config.TextColumn("Source", width="small"),
                "name": st.column_config.TextColumn("Name", width="medium"),
                "contact": st.column_config.TextColumn("Contact", width="medium"),
                "intent": st.column_config.TextColumn("Intent", width="medium"),
                "action": st.column_config.TextColumn("Action", width="small"),
                "message": st.column_config.TextColumn("Message", width="medium"),
                "timestamp": st.column_config.TextColumn("Time", width="medium")
            }
        )
    else:
        st.info("No leads found. Leads will appear here as they come in from Email, Instagram/Facebook, and Phone.")

    # Escalations section
    st.divider()
    st.subheader("⚠️ Requires Follow-up")

    escalations = [l for l in all_leads if l["action"] == "escalate"]
    if escalations:
        for lead in escalations:
            with st.expander(f"{lead['source']} - {lead['name']} ({lead['intent']})"):
                st.write(f"**Contact:** {lead['contact']}")
                st.write(f"**Message:** {lead['message']}")
                st.write(f"**Time:** {lead['timestamp']}")
                if st.button(f"✅ Mark Resolved", key=lead['contact']):
                    st.success("Marked as resolved!")
    else:
        st.success("No pending escalations!")

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        Unity MMA AI Systems | Powered by Junction AI
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
