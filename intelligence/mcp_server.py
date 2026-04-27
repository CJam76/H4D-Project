import time
import json
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import paho.mqtt.client as mqtt

# --- Telemetry Storage ---
# We store the last 60 data points (approx 1 min) for each machine
HISTORY_LENGTH = 60
telemetry_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=HISTORY_LENGTH))

# --- MQTT Setup ---
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "affi/telemetry/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MCP MQTT] Connected to broker. Subscribing to {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"[MCP MQTT] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        machine_id = payload.get("machine_id")
        if machine_id:
            telemetry_history[machine_id].append(payload)
    except json.JSONDecodeError:
        pass

def start_mqtt_client():
    client = mqtt.Client(client_id=f"mcp_sub_{time.time()}")
    client.on_connect = on_connect
    client.on_message = on_message
    print(f"Connecting to {BROKER}...")
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

# Start MQTT client in a background thread
mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
mqtt_thread.start()

# --- FastMCP Server Setup ---
mcp = FastMCP("AFFI Virtual Manager Server")

@mcp.tool()
def get_machines() -> List[str]:
    """Returns a list of all active machine IDs."""
    return list(telemetry_history.keys())

@mcp.tool()
def get_recent_telemetry(machine_id: str, count: int = 5) -> List[dict]:
    """Returns the most recent telemetry data points for a specific machine."""
    if machine_id not in telemetry_history:
        return []
    history = list(telemetry_history[machine_id])
    return history[-count:]

@mcp.tool()
def detect_stalls() -> Dict[str, str]:
    """
    Checks all machines to see if they are stalled.
    A machine is stalled if it is 'Active' with RPM > 0, but the stitch_count 
    has not increased over the last 10 seconds.
    """
    stalled_machines = {}
    for machine_id, history in telemetry_history.items():
        if len(history) < 10:
            continue
        
        recent = list(history)[-10:]
        latest = recent[-1]
        oldest = recent[0]
        
        if latest["status"] == "Active" and latest["rpm"] > 0:
            if latest["stitch_count"] == oldest["stitch_count"]:
                stalled_machines[machine_id] = "Stalled: RPM is active but stitch count is not increasing (Possible Thread Break)."
    
    return stalled_machines if stalled_machines else {"status": "No stalls detected."}

@mcp.tool()
def predict_maintenance(machine_id: str) -> str:
    """
    Analyzes recent telemetry for a specific machine to predict impending failures.
    Specifically looks for rising motor temperatures while RPM remains high.
    """
    if machine_id not in telemetry_history:
        return f"Error: No data for {machine_id}"
    
    history = list(telemetry_history[machine_id])
    if len(history) < 20:
        return "Insufficient data to predict maintenance. Need at least 20 seconds of data."
        
    recent_temps = [p["motor_temp"] for p in history[-20:]]
    temp_trend = recent_temps[-1] - recent_temps[0]
    avg_temp = sum(recent_temps) / len(recent_temps)
    
    if temp_trend > 5.0 and avg_temp > 50.0:
        return "CRITICAL WARNING: Motor temperature is rapidly rising and exceeds safe thresholds. Impending motor failure detected. Recommendation: Shut down machine immediately."
    elif avg_temp > 45.0:
        return "WARNING: Motor temperature is running high. Recommend inspection at next shift change."
    else:
        return "Machine is operating within normal parameters."

if __name__ == "__main__":
    # In a real environment, this is run via the MCP CLI or stdio.
    print("MCP Server initialized. Run via MCP client (stdio or SSE).")
    mcp.run(transport="stdio")
