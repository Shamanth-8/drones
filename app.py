import streamlit as st
import pandas as pd
from src.data_handler import DataHandler
from src.agent import DroneAgent
from src.logic import ConflictDetector
import os
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Page Config
st.set_page_config(page_title="Skylark Drones Agent", layout="wide", page_icon="🚁")

# Custom CSS for Dark Theme and Card Styling
st.markdown(
    """
<style>
    /* Dark Theme Background */
    .stApp {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ff4b4b; /* Accent Color */
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Cards */
    .css-1r6slb0, .css-12oz5g7 {
        background-color: #16213e;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #e94560;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ff2e63;
    }
    
    /* Chat Input */
    .stTextInput>div>div>input {
        background-color: #0f3460;
        color: white;
        border-radius: 10px;
    }
    
    /* Dataframes */
    .stDataFrame {
        border: 1px solid #0f3460;
    }
    
    /* Sidebar hidden/minimal */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
        border-right: 1px solid #16213e;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Main Header
st.title("🚁 Skylark Drone Operations")
st.markdown(
    "<p style='text-align: center; color: #a0a0a0;'>AI-Powered Pilot & Fleet Management System</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Initialize Data Handler
sheet_mapping = {
    "pilots": "Pilot Roster",
    "drones": "Drone Fleet",
    "missions": "Missions",
}

data_handler = DataHandler(
    pilot_file="pilot_roster.csv",
    drone_file="drone_fleet.csv",
    mission_file="missions.csv",
    gsheets_creds="credentials.json",
    sheet_mapping=sheet_mapping,
)

agent = DroneAgent(data_handler, api_key)
conflict_detector = ConflictDetector(data_handler)

# Layout: Split Screen
col1, col2 = st.columns([1, 1], gap="large")

# --- LEFT COLUMN: OPERATIONS COMMAND (CHAT) ---
with col1:
    st.subheader("💬 Operations Command")

    # Chat Container
    chat_container = st.container(height=500, border=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Welcome! I'm your Drone Operations Coordinator.\n\nTry asking me about:\n- Available pilots or drones\n- Check for conflicts\n- Urgent reassignments",
            }
        ]

    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # Quick Actions Row
    qc1, qc2, qc3, qc4 = st.columns(4)
    if qc1.button("👨‍✈️ Pilots"):
        prompt = "Show me the pilot roster"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        with chat_container.chat_message("assistant"):
            response = agent.process_query(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    if qc2.button("🛸 Drones"):
        prompt = "Show me the drone fleet"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        with chat_container.chat_message("assistant"):
            response = agent.process_query(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    if qc3.button("⚠️ Conflicts"):
        # Custom logic for conflicts check via button
        prompt = "Check for any active conflicts"
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Simulate AI response for this specific check if standard prompt fails
        # But let's try the agent first
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        with chat_container.chat_message("assistant"):
            # We can manually trigger conflict check here or ask agent
            # Creating a manual summary string
            conflicts = []
            pilots = data_handler.get_pilots()
            assigned = pilots[pilots["current_assignment"] != "-"]
            for _, p in assigned.iterrows():
                mid = p["current_assignment"]
                # Finding drone is hard without direct link in data, assuming logic holds
                # For prototype, let's just use the conflict detector on known pairs
                # This part is a bit tricky without a proper 'Assignment' table
                pass

            # Let's just ask the agent
            response = agent.process_query(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    if qc4.button("🚨 Urgent"):
        prompt = "I have an urgent reassignment request"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        with chat_container.chat_message("assistant"):
            response = agent.process_query(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Chat Input
    if prompt := st.chat_input("Type your command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        with chat_container.chat_message("assistant"):
            response = agent.process_query(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- RIGHT COLUMN: LIVE DATA DASHBOARD ---
with col2:
    st.subheader("📊 Live Data")

    tab_pilots, tab_drones, tab_missions = st.tabs(
        ["👨‍✈️ Pilots", "🛸 Drones", "🎯 Missions"]
    )

    with tab_pilots:
        st.dataframe(data_handler.get_pilots(), use_container_width=True, height=400)

    with tab_drones:
        st.dataframe(data_handler.get_drones(), use_container_width=True, height=400)

    with tab_missions:
        st.dataframe(data_handler.get_missions(), use_container_width=True, height=400)
