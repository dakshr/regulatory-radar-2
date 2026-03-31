import streamlit as st
from supabase import create_client
import os
from agent import app  # Importing your Milestone 2 "Brain"

# st.markdown("""
#     <style>
#     div.stButton > button:first-child {
#         background-color: #0066cc;
#         color: white;
#         border-radius: 5px;
#     }
#     div.stButton > button:hover {
#         background-color: #0052a3;
#         color: white;
#     }
#     </style>""", unsafe_allow_html=True)

# 1. Professional Blue Styling
st.markdown("""
    <style>
    /* Professional Blue Button */
    .stButton>button {
        background-color: #004a99;
        color: white;
        border-radius: 6px;
        border: none;
        height: 3em;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
        color: white;
    }
    /* Subtitle styling */
    .hero-subtitle {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# st.markdown("""
#     <style>
#     /* Target the primary button specifically */
#     .stButton>button[kind="primary"] {
#         background-color: #004a99; /* Professional Navy Blue */
#         border-color: #004a99;
#         color: white;
#         width: 100%; /* Ensures it fills the column as requested */
#     }
#     .stButton>button[kind="primary"]:hover {
#         background-color: #003366; /* Darker blue on hover */
#         border-color: #003366;
#     }
#     </style>
# """, unsafe_allow_html=True)

# --- 1. SETUP & CONFIG ---
# Added initial_sidebar_state for a cleaner default look
st.set_page_config(page_title="Regulatory Radar", layout="wide", initial_sidebar_state="collapsed")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- 2. HELPER FUNCTIONS ---
def get_recent_regulations():
    """Retrieves the last 30 regulations from Supabase"""
    response = supabase.table("regulations").select("*").order("publication_date", desc=True).limit(30).execute()
    return response.data

# # --- 3. UI UPGRADE: THE MODAL WAR ROOM ---
# # The @st.dialog decorator turns this entire function into a pop-up overlay
# @st.dialog("🔍 Active Investigation: Agent War Room", width="large")
# def run_investigation_modal(reg_id, title, is_demo):
#     st.markdown(f"**Target:** {title}")
    
#     # 1. The Thinking Trace (Now full width inside the modal)
#     with st.status("🧠 Agent Reasoning Trace...", expanded=True) as status:
#         inputs = {
#             "regulation_id": str(reg_id),
#             "is_demo": is_demo
#         }

#         final_state = {}
        
#         for event in app.stream(inputs):
#             for node, state in event.items():
#                 final_state = state 
#                 if "internal_logs" in state:
#                     # Formatted as code blocks for a cooler "terminal" aesthetic
#                     st.markdown(f"**`[{node.upper()}]`** ➔ {state['internal_logs'][-1]}")
#                 status.update(label=f"Current Node: {node.title()}...")
        
#         status.update(label="✅ Investigation Complete", state="complete")
        
#     # 2. Display the final results below the trace
#     display_executive_brief(final_state)

@st.dialog("🔍 Active Investigation: Agent War Room", width="large")

def run_investigation_modal(reg_id, title, is_demo):
    st.markdown(f"**Target:** {title}")
    
    # We use a container to manage the visibility of the status box
    status_placeholder = st.empty()
    
    with status_placeholder.status("🧠 Agent Reasoning Trace...", expanded=True) as status:
        inputs = {"regulation_id": str(reg_id), "is_demo": is_demo}
        final_state = {}
        
        for event in app.stream(inputs):
            for node, state in event.items():
                # Update our tracking state
                for key, value in state.items():
                    final_state[key] = value
                
                if "internal_logs" in state:
                    st.markdown(f"**`[{node.upper()}]`** ➔ {state['internal_logs'][-1]}")
                # status.update(label=f"Current Node: {node.title()}...")
        
        # KEY CHANGE: Collapse the status box now that we are done
        status.update(label="✅ Investigation Complete", state="complete", expanded=False)
        
    # Now display the brief below the collapsed logs
    if final_state:
        display_executive_brief(final_state)

def display_executive_brief(state):
    """Formats the final output as a professional Wealth Management report."""
    st.divider()
    
    # Risk Rating Banner
    impact = state.get("impact_level", "Low")
    if impact in ["Critical", "High"]:
        st.error(f"🚨 **RISK RATING: RED ({impact})**")
    elif impact == "Medium":
        st.warning(f"⚠️ **RISK RATING: AMBER (Medium)**")
    else:
        st.success(f"✅ **RISK RATING: GREEN (Low)**")

    st.subheader("Key Topics")
    # Display tags horizontally using markdown instead of buttons for a cleaner look
    tags = state.get("primary_keywords", [])
    if tags:
        tag_html = " ".join([f"<span style='background-color: #0066cc; padding: 4px 8px; border-radius: 4px; margin-right: 5px; color: white; font-size: 14px;'>🏷️ {tag}</span>" for tag in tags])
        st.markdown(tag_html, unsafe_allow_html=True)
    else:
        # Fallback if no keywords were generated
        st.caption("Standard Regulatory Review")


    st.subheader("Executive Summary")
    st.info(state.get("final_summary", "No summary generated."))

    # # Layout adjustment: 60/40 split for better readability
    # col1, col2 = st.columns([9, 1])
    # with col1:
    #     st.subheader("Executive Summary")
    #     st.info(state.get("final_summary", "No summary generated."))
    # with col2:
    #     st.subheader("Key Topics")
    #     # Display tags horizontally using markdown instead of buttons for a cleaner look
    #     tags = state.get("primary_keywords", [])
    #     if tags:
    #         tag_html = " ".join([f"<span style='background-color: #0066cc; padding: 4px 8px; border-radius: 4px; margin-right: 5px; color: white; font-size: 14px;'>🏷️ {tag}</span>" for tag in tags])
    #         st.markdown(tag_html, unsafe_allow_html=True)
    #     else:
    #         # Fallback if no keywords were generated
    #         st.caption("Standard Regulatory Review")

    # Deep Research Section
    if state.get("is_regime_shift") and state.get("research_notes"):
        st.divider()
        st.subheader("🕵️ Deep Research: Regime Shift Analysis")
        st.caption("System detected a policy shift or joint-agency action. Automated research triggered.")
        
        # # Use a container with a border to make the research stand out
        # with st.container(border=True):
        #     for note in state.get("research_notes", []):
        #         st.markdown(note)
        
        for note in state.get("research_notes", []):
            # Using a bordered container for each source to keep them distinct
            with st.container(border=True):
                # Header row with Source Number and Link
                col_a, col_b = st.columns([4, 1])
                col_a.markdown(f"**🔍 Source {note['source_num']}: {note['title']}**")
                col_b.page_link(note['url'], label="Visit Source", icon="🌐")
                
                # Findings Section with a lighter font/style
                st.markdown("**Key Findings:**")
                st.caption(note['findings']) 
                
                # Agent Analysis Section with unique background
                st.success(f"**Agent Analysis:** {note['analysis']}")

# --- 4. MAIN UI LOOP ---
# st.title("🛡️ Regulatory Radar")
# st.markdown("Monitoring US Federal Agencies for new regulations impacting the financial services industry. Click **Investigate** to trigger the AI agent.")

# --- top of dashboard.py (Inside Main UI Loop) ---

# Create a clean header row for title and info
head_col1, head_col2 = st.columns([9.6, 0.4])

with head_col1:
    st.title("🛡️ Regulatory Radar: Agentic Intelligence")
    st.markdown("_Detecting regulatory regime shifts across US Federal Agencies. Don't just monitor the news - analyze the impact._")
    #st.markdown("Choose a recent regulation to begin a live autonomous investigation.")
    st.info("💡 **Getting Started:** Choose a regulation from the list below."
            "The AI Agent will autonomously triage the risk and conduct deep research if a policy shift is detected.")

with head_col2:
    st.write("##") # Alignment spacer
    # Use a popover for a modern, sleek "Info" feel
    with st.popover("ℹ️", use_container_width=True):
        st.markdown("### Welcome to Regulatory Radar")
        st.write("""
        This tool uses **Agentic AI** to monitor federal regulations. 
        Unlike a standard search, it performs autonomous multi-step reasoning.
                 
        The agencies monitored are: SEC, OCC, CFPB, FRB, FDIC, and Treasury.
                 
        Enabling Demo Mode simulates a high-velocity regulatory environment with regime shifts, allowing you to see the agent's full capabilities in action, regarless of the current news cycle.
        """)
        
        st.subheader("🚀 How to Start")
        st.markdown("""
        1. **Select a Regulation:** Browse the live feed from the Federal Register.
        2. **Launch Agent Analysis:** This wakes up the AI Agent to analyze the regulation.
        3. **Watch the Trace:** See the 'Thinking Trace' as the agent moves through nodes.
        """)
        
        st.subheader("🧠 The Reasoning Engine")
        st.write("This system uses a **State-Driven Agentic Graph** (LangGraph) to process data:")
        
        # Using a structured list to explain the 'Behind the Scenes'
        st.markdown("""
        - **1. Triage Node:** Analyzes text for 0-10 relevance to RIAs.
        - **2. Logic Gate:** If 'Regime Shift' signals are high, it triggers the **Investigator**.
        - **3. Investigator Node:** Uses **Tavily Search** to find law firm alerts & enforcement history.
        - **4. Writer Node:** Synthesizes all data into a 'Heat Map' brief.
        """)
        st.divider()
        st.caption("Powered by Llama-3.3-70b on Groq for sub-second inference.")

# --- end of info section ---

# Header layout with the Demo toggle integrated cleanly
header_col1, header_col2 = st.columns([9, 1])
with header_col2:
    demo_mode = st.toggle("Enable Demo Mode")
if demo_mode:
    st.warning("🧪 Demo Mode Active: Simulating Regime Shift and high-velocity agency activity.")

# Fetch data for the Live Feed 
regs = get_recent_regulations()

if not regs:
    st.info("No regulations found in the database. Check with Administrator if the data pipeline is running.")
else:
    # Build the table container
    with st.container(border=True):
        # Table Header
        cols = st.columns([4, 2, 1])
        cols[0].markdown("**Regulation Title**")
        cols[1].markdown("**Agencies**")
        cols[2].markdown("**Action**")
        st.divider()

        # Table Rows
        for reg in regs:
            row_cols = st.columns([4, 2, 1], vertical_alignment="center")
            with row_cols[0]:
                st.write(reg['title'])
                st.caption(f"Published: {reg['publication_date']}")
            with row_cols[1]:
                # Display agencies as clean markdown text
                st.markdown(f"🏦 {', '.join(reg['agency_names'])}")
            with row_cols[2]:
                # use_container_width makes the button fill its column space nicely
                if st.button("Launch AI Analysis", key=f"reg_{reg['id']}", use_container_width=True):
                    # Trigger the modal!
                    run_investigation_modal(reg['id'], reg['title'], demo_mode)