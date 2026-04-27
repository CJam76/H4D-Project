import time
import json
import random
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "affi/telemetry/JUKI-001"
MACHINE_ID = "JUKI-001"

# Simulation state
rpm = 0
stitch_count = 0
motor_temp = 35.0
status = "Idle"
fault_state = "None" # "None", "Thread Break", "Motor Overheating"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{MACHINE_ID}] Connected to MQTT Broker!")
    else:
        print(f"[{MACHINE_ID}] Failed to connect, return code {rc}")

client = mqtt.Client(client_id=f"sim_{MACHINE_ID}_{random.randint(1000,9999)}")
client.on_connect = on_connect

print(f"Connecting to {BROKER}...")
client.connect(BROKER, PORT, 60)
client.loop_start()

def simulate_step():
    global rpm, stitch_count, motor_temp, status, fault_state
    
    # State transitions
    if random.random() < 0.05 and fault_state == "None":
        faults = ["Thread Break", "Motor Overheating"]
        fault_state = random.choice(faults)
        print(f"\n--- [!] INJECTING FAULT: {fault_state} ---\n")
    elif random.random() < 0.05 and fault_state != "None":
        # Resolve fault occasionally
        fault_state = "None"
        motor_temp = 35.0
        print(f"\n--- [*] FAULT RESOLVED ---\n")

    if fault_state == "None":
        status = "Active"
        rpm = random.randint(3500, 4000)
        stitch_count += int((rpm / 60) * 1) # roughly stitches per second
        # Normal temp fluctuates around 35-45
        motor_temp = max(30.0, min(50.0, motor_temp + random.uniform(-0.5, 0.5)))
        
    elif fault_state == "Thread Break":
        status = "Active"
        rpm = random.randint(3500, 4000)
        # Stitch count does NOT increase because thread is broken
        motor_temp = max(30.0, min(50.0, motor_temp + random.uniform(-0.5, 0.5)))
        
    elif fault_state == "Motor Overheating":
        status = "Active"
        rpm = random.randint(4000, 4500) # running hot
        stitch_count += int((rpm / 60) * 1)
        # Temp continuously rises
        motor_temp += random.uniform(0.5, 2.0)

def main():
    print(f"[{MACHINE_ID}] Starting simulation. Press Ctrl+C to stop.")
    try:
        while True:
            simulate_step()
            
            payload = {
                "machine_id": MACHINE_ID,
                "timestamp": int(time.time()),
                "rpm": rpm,
                "stitch_count": stitch_count,
                "motor_temp": round(motor_temp, 2),
                "status": status
            }
            
            client.publish(TOPIC, json.dumps(payload))
            print(f"Published: {payload}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping simulation...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
