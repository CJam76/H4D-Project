import time
import sys
# Import the tools directly from our mcp_server for this mocked demo
from mcp_server import get_machines, get_recent_telemetry, detect_stalls, predict_maintenance

def mock_llm_agent_loop():
    print("==================================================")
    print("Virtual Manager (Mocked LLM) Initialized")
    print("==================================================")
    print("System Prompt Loaded. Monitoring factory floor...\n")
    
    try:
        while True:
            print("\n[Agent Thought]: I will check if any machines are stalled...")
            stalls = detect_stalls()
            
            if stalls and "status" not in stalls:
                print(f"[Agent Observation]: Stalls detected: {stalls}")
                for machine_id, reason in stalls.items():
                    print(f"    -> WARNING {machine_id}: {reason}")
            else:
                print("[Agent Observation]: No stalls detected.")
            
            print("\n[Agent Thought]: I will check for maintenance predictions on active machines...")
            machines = get_machines()
            if not machines:
                print("[Agent Observation]: No active machines found.")
            
            for machine_id in machines:
                prediction = predict_maintenance(machine_id)
                if "CRITICAL WARNING" in prediction:
                    print(f"[Agent Observation]: {machine_id} - {prediction}")
                    print(f"\n[Agent Action]: Generating Human-In-The-Loop prompt for {machine_id}...")
                    print(f"\n[HITL_REQUIRED] Shut down {machine_id} immediately?")
                    
                    response = input("Approve shutdown? [y/N]: ").strip().lower()
                    if response == 'y':
                        print(f"[Agent Action]: Executing shutdown sequence for {machine_id}...")
                        print(f"SUCCESS: {machine_id} has been safely shut down.")
                    else:
                        print(f"[Agent Action]: Shutdown aborted by manager. Continuing to monitor...")
                        
                elif "WARNING" in prediction:
                    print(f"[Agent Observation]: {machine_id} - {prediction}")
            
            print("\n[Agent]: Floor assessment complete. Waiting for next cycle...")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nVirtual Manager offline.")

if __name__ == "__main__":
    # Wait a few seconds for the simulator to publish some data
    print("Waiting 10 seconds to accumulate some telemetry data before agent starts...")
    time.sleep(10)
    mock_llm_agent_loop()
