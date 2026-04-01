import os
from typing import Annotated, List, TypedDict, Optional
import operator
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from supabase import create_client
from langgraph.graph import StateGraph, START, END

# --- 1. INITIALIZATION ---
load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"), temperature=0)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
search_tool = TavilySearchResults(max_results=3)

# --- 2. DEFINE THE AGENT'S MEMORY (STATE) ---
class AgentState(TypedDict):
    # Core Data
    regulation_id: str
    regulation_text: str
    agency_names: List[str] # List of strings
    is_demo: bool
    
    # PM Metrics (New)
    relevance_score: int       # 0-10: How much does this hit Wealth Management?
    impact_level: str          # Low, Medium, High, Critical
    primary_keywords: List[str]
    is_regime_shift: bool
    
    # Logic & Output
    research_notes: Annotated[List[str], operator.add] # Appends notes as it investigates
    internal_logs: Annotated[List[str], operator.add]  # Appends logs for the Streamlit UI later
    final_summary: str

# --- 3. DEFINE THE NODES (THE ACTIONS) ---
def fetch_node(state: AgentState):
    """Pulls the specific rule from your Milestone 1 Supabase ingestion."""
    res = supabase.table("regulations").select("*").eq("id", state["regulation_id"]).single().execute()
    title = res.data.get("title", "No Title")
    summary = res.data.get("summary", "No summary found")
    text = f"Title: {title}\n\nSummary: {summary}"
    agency_names = res.data.get("agency_names", [])
    return {"regulation_text": text, 
            "agency_names":agency_names, 
            "internal_logs": [f"Fetched rule with {len(agency_names)} agencies."]}

import json
from datetime import datetime, timedelta

def triage_node(state: AgentState):
    """Checks velocity for all agencies and looks for inter-agency coordination."""
    
    # --- STEP 1: LLM "QUICK SCAN" (Qualitative) ---
    # Using a structured prompt to get specific data points
    triage_prompt = f"""
    Analyze the following regulatory abstract for a Wealth Management audience.
    Regulation: {state['regulation_text'][:1000]}
    
    Return ONLY a JSON object with these keys:
    "relevance": (integer 1-10 regarding RIA/Wealth Management impact),
    "impact": ("Low", "Medium", "High", or "Critical"),
    "keywords": [list of 3 specific topics]
    """
    
    # Fast inference via Groq
    llm_res = llm.invoke(triage_prompt)
    try:
        # Clean the output in case the LLM adds markdown backticks
        cleaned_content = llm_res.content.strip().replace("```json", "").replace("```", "")
        analysis = json.loads(cleaned_content)
    except:
        # Fallback if JSON parsing fails
        analysis = {"relevance": 5, "impact": "Medium", "keywords": ["Compliance"]}

# --- 2. MULTI-AGENCY VELOCITY CHECK ---
    one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    max_agency_count = 0
    
    # Loop through EVERY agency involved in this rule
    for agency in state['agency_names']:
        res = supabase.table("regulations") \
            .select("*", count='exact') \
            .contains("agency_names", [agency]) \
            .gt("publication_date", one_week_ago) \
            .execute()
        
        count = res.count if res.count else 0
        if count > max_agency_count:
            max_agency_count = count

    # --- 3. PM LOGIC: COORDINATION SCORE ---
    # In Wealth Management, if 3+ agencies act together, it's almost always a Regime Shift.
    is_joint_action = len(state['agency_names']) >= 3
    is_velocity_spike = max_agency_count >= 5 # 5+ rules from any one of the agencies
    
    # Logic: Trigger research if it's a Joint Action OR high velocity OR high relevance
    if state.get("is_demo", False):
        regime_shift_detected = True
        log_msg = (
            f"Triage: Relevance {analysis['relevance']}/10, Impact: {analysis['impact']}. "
            f"Triage: {len(state['agency_names'])} agencies involved. "
            f"Joint Action: {is_joint_action}. "
            f"Max Agency Velocity: {max_agency_count}. "
            f"DEMO MODE: Forcing Regime Shift detection for showcase."
            f"Regime Shift: {regime_shift_detected}"
        )
    else:
        regime_shift_detected = is_joint_action or is_velocity_spike or (analysis['relevance'] >= 8)
        log_msg = (
            f"Triage: Relevance {analysis['relevance']}/10, Impact: {analysis['impact']}. "
            f"Triage: {len(state['agency_names'])} agencies involved. "
            f"Joint Action: {is_joint_action}. "
            f"Max Agency Velocity: {max_agency_count}. "
            f"Regime Shift: {regime_shift_detected}"
        )

    return {
        "relevance_score": analysis['relevance'],
        "impact_level": analysis['impact'],
        "primary_keywords": analysis['keywords'],
        "is_regime_shift": regime_shift_detected,
        "internal_logs": [log_msg]
    }

def research_node(state: AgentState):
    """
    The Deep Dive: Dynamically searches the web based on the specific 
    agencies involved in the regulation.
    """
    # 1. Extract the agencies from the state (fallback to 'Federal Regulators')
    agencies = state.get('agency_names', [])
    if not agencies:
        agencies_str = "Federal regulators"
    elif len(agencies) == 1:
        agencies_str = agencies[0]
    else:
        # Formats as "SEC, FINRA, and CFTC"
        agencies_str = ", ".join(agencies[:-1]) + f", and {agencies[-1]}"
    
    # 2. Build a high-intent search query
    # We look for: Enforcement + Litigation + Professional Analysis (Client Alerts)
    search_query = (
        f"Recent {agencies_str} enforcement actions, litigation releases, "
        f"and law firm client alerts regarding: {state['regulation_text'][:150]}"
    )
    
    print(f"--- INVESTIGATING: {agencies_str} ---")
    
    # 3. Execute the Tavily search
    try:
        search_results = search_tool.invoke({"query": search_query})
        
        # 4. Clean and format the findings
        formatted_notes = []
        
        for i, res in enumerate(search_results, 1):
            # 1. Clean the content (optional: truncate if too long for a brief)
            # raw_content = res.get('content', 'No content available.')
            clean_content = res.get('content', 'No content available.').replace('#', '').strip()
            
            # Call the LLM to analyze THIS specific source
            analysis_prompt = f"""
            Regulation: {state['regulation_text']}
            Research Source: {res['content'][:1000]}
            
            Briefly explain (1 sentence) how this specific source provides context or 
            evidence of a shift regarding {state.get('primary_keywords', ['the industry'])[0]}.
            """
            dynamic_analysis = llm.invoke(analysis_prompt).content
            
            note = {
                "source_num": i,
                "title": res.get('title', 'Regulatory Reference'),
                "url": res.get('url', '#'),
                "findings": clean_content[:600] + "...", # Truncate to keep UI tight
                #"analysis": f"Evidence of shift in {state.get('primary_keywords', ['this area'])[0]} enforcement."
                "analysis": dynamic_analysis # Now unique for every source
            }
            formatted_notes.append(note)

        log_entry = f"Deep research completed for {agencies_str} using Tavily."
        
    except Exception as e:
        formatted_notes = [f"Search failed: {str(e)}"]
        log_entry = "Research node failed to execute search."

    return {
        "research_notes": formatted_notes,
        "internal_logs": [log_entry]
    }

def writer_node(state: AgentState):
    """
    The Synthesizer: Creates a high-impact Regulatory Heat Map brief
    using all the metadata gathered in the graph.
    """
    # 1. Access the raw lists directly from state
    notes = state.get("research_notes", [])
    agencies = state.get("agency_names", ["Unknown Agencies"])
    
    # 2. Construct the prompt
    # The 'research_context' logic is now handled inside the f-string
    prompt = f"""
    You are a Lead Regulatory Consultant for a Tier-1 Wealth Management firm. 
    Your goal is to brief the Chief Compliance Officer on a new regulatory development.

    --- DATA INPUTS ---
    PRIMARY AGENCIES: {", ".join(agencies)}
    REGULATION TEXT: {state.get('regulation_text', 'No text provided.')}
    
    AI SCORES:
    - Relevance Score: {state.get('relevance_score', 'N/A')}/10
    - Impact Level: {state.get('impact_level', 'Unknown')}
    - Regime Shift Detected: {state.get('is_regime_shift', False)}
    
    EXTERNAL RESEARCH & ENFORCEMENT CONTEXT:
    {
        # Inline transformation: Converts dicts to strings for the LLM
        "\\n\\n".join([f"SOURCE {n['source_num']}: {n['title']}\\nFINDINGS: {n['findings']}\\nANALYSIS: {n['analysis']}" for n in notes]) 
        if notes and isinstance(notes[0], dict) 
        else "\\n".join(notes) if notes 
        else "No external enforcement context found."
    }

    --- INSTRUCTIONS ---
    Format the response as a 'Regulatory Heat Map' with the following sections:
    1. **Risk Rating**: Use the Impact Level and Relevance Score to assign a color (Red/Amber/Green).
    2. **Executive Summary**: 2 sentences on what changed.
    3. **The 'Why Now' (Regime Shift Analysis)**: If 'is_regime_shift' is True, explain the agency velocity or coordination detected.
    4. **Enforcement & Market Context**: Synthesize the research notes (mention specific law firm alerts or SEC/FINRA cases if found).
    5. **Priority Action Items**: 3-4 bullet points for a Wealth Management firm.
    """
    
    # 3. Invoke Groq
    response = llm.invoke(prompt)
    
    # 4. Log the completion
    log_entry = f"Final Report generated for {', '.join(agencies)}. Risk: {state.get('impact_level')}."
    
    return {
        "final_summary": response.content,
        "internal_logs": [log_entry]
    }

# --- 4. WIRE THE GRAPH ---
builder = StateGraph(AgentState)

builder.add_node("fetcher", fetch_node)
builder.add_node("triage", triage_node)
builder.add_node("investigator", research_node)
builder.add_node("writer", writer_node)

builder.add_edge(START, "fetcher")
builder.add_edge("fetcher", "triage")

# The Agentic Decision: Route based on the Triage output
builder.add_conditional_edges(
    "triage",
    lambda x: "investigator" if x["is_regime_shift"] else "writer"
)

builder.add_edge("investigator", "writer")
builder.add_edge("writer", END)

# Compile the final application
app = builder.compile()