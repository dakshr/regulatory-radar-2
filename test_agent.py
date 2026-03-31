from agent import app  # Imports your compiled graph

def run_test(reg_id: str):
    print(f"\n" + "="*50)
    print(f"🚀 STARTING REGULATORY RADAR: ID {reg_id}")
    print("="*50)
    
    # Initialize the state with the new list-based attributes
    initial_state = {
        "regulation_id": reg_id,
        "agency_names": [], # Will be populated by fetch_node
        "research_notes": [],
        "internal_logs": [],
        "relevance_score": 0,
        "impact_level": "Unknown"
    }
    
    # Stream the agent's thought process
    for event in app.stream(initial_state):
        for node_name, state_update in event.items():
            print(f"\n✅ NODE COMPLETED: {node_name}")
            
            # Print the specific 'Internal Logs' we added to each node
            if "internal_logs" in state_update:
                print(f"   📝 Log: {state_update['internal_logs'][-1]}")
            
            # --- NEW: "Spy" on the PM Metrics after Triage ---
            if node_name == "triage":
                print(f"   📊 METRICS CAPTURED:")
                print(f"      - Relevance: {state_update.get('relevance_score')}/10")
                print(f"      - Impact:    {state_update.get('impact_level')}")
                print(f"      - Shift:     {'🚨 REGIME SHIFT DETECTED' if state_update.get('is_regime_shift') else '✅ Business as Usual'}")

            # --- NEW: See which agencies were identified ---
            if node_name == "fetcher":
                print(f"   🏢 Target Agencies: {state_update.get('agency_names')}")

    # Final Output Extraction
    # We look for the 'writer' node's output in the final event
    final_node_output = list(event.values())[0]
    
    print("\n" + "═"*50)
    print("📋 FINAL REGULATORY HEAT MAP BRIEF")
    print("═"*50)
    print(final_node_output.get("final_summary"))
    print("═"*50)

if __name__ == "__main__":
    # Ensure ID 681 exists in your 'regulations' table
    run_test(680)