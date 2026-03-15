"""
Leads Dashboard for Unity MMA DM Bot
Run: streamlit run leads_dashboard.py
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# Config
st.set_page_config(
    page_title="Unity MMA - Lead Dashboard",
    page_icon="🥊",
    layout="wide"
)

LEADS_FILE = os.path.expanduser("~/junction-ai/barnaby_dm_bot/leads.json")

def load_leads():
    try:
        with open(LEADS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# Header
st.title("🥊 Unity MMA - Lead Dashboard")
st.markdown("---")

# Load data
leads = load_leads()

# Metrics row
col1, col2, col3, col4 = st.columns(4)

total_leads = len(leads)
complete_leads = len([l for l in leads.values() if l.get("name") and (l.get("phone") or l.get("email"))])
with_phone = len([l for l in leads.values() if l.get("phone")])
with_interest = len([l for l in leads.values() if l.get("interested_in")])

with col1:
    st.metric("Total Conversations", total_leads)

with col2:
    st.metric("Complete Leads", complete_leads)

with col3:
    st.metric("With Phone", with_phone)

with col4:
    st.metric("With Interest", with_interest)

st.markdown("---")

# Leads table
st.subheader("📋 All Leads")

if leads:
    # Convert to dataframe
    lead_list = []
    for user_id, data in leads.items():
        lead_list.append({
            "User ID": user_id[:12] + "...",
            "Name": data.get("name", "—"),
            "Phone": data.get("phone", "—"),
            "Email": data.get("email", "—"),
            "Interest": data.get("interested_in", "—"),
            "Experience": data.get("experience_level", "—"),
            "Messages": len(data.get("messages", [])),
            "Timestamp": data.get("timestamp", "—")
        })

    df = pd.DataFrame(lead_list)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Leads CSV",
        data=csv,
        file_name=f"unity_mma_leads_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.info("No leads captured yet. Start conversations to see leads here!")

st.markdown("---")

# Interest breakdown
st.subheader("🎯 Interest Breakdown")

if leads:
    interests = [l.get("interested_in") for l in leads.values() if l.get("interested_in")]
    if interests:
        interest_counts = pd.Series(interests).value_counts()
        st.bar_chart(interest_counts)
    else:
        st.info("No interests captured yet")

# Recent conversations
st.markdown("---")
st.subheader("💬 Recent Conversations")

if leads:
    for user_id, data in list(leads.items())[-5:]:
        with st.expander(f"{data.get('name', 'Unknown')} - {user_id[:12]}..."):
            st.write(f"**Phone:** {data.get('phone', '—')}")
            st.write(f"**Email:** {data.get('email', '—')}")
            st.write(f"**Interest:** {data.get('interested_in', '—')}")
            st.write(f"**Experience:** {data.get('experience_level', '—')}")
            st.write("**Messages:**")
            for msg in data.get("messages", [])[-10:]:
                st.text(f"  • {msg[:100]}...")

# Footer
st.markdown("---")
st.caption("Unity MMA DM Bot Dashboard • Powered by Junction AI")
