import json
import time
import threading
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- InfluxDB Configuration ---
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "my-super-secret-auth-token"
INFLUXDB_ORG = "h4d"
INFLUXDB_BUCKET = "affi"

# Setup InfluxDB Client
db_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = db_client.write_api(write_options=SYNCHRONOUS)

# --- MQTT Configuration ---
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "affi/telemetry/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[Ingestor] Connected to MQTT broker. Subscribing to {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"[Ingestor] Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        machine_id = payload.get("machine_id")
        
        if not machine_id:
            return
            
        # Create InfluxDB Point
        point = Point("telemetry") \
            .tag("machine_id", machine_id) \
            .tag("status", payload.get("status", "Unknown")) \
            .field("rpm", float(payload.get("rpm", 0))) \
            .field("stitch_count", float(payload.get("stitch_count", 0))) \
            .field("motor_temp", float(payload.get("motor_temp", 0))) \
            .time(int(payload.get("timestamp", time.time())) * 1000000000) # Convert to nanoseconds
            
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print(f"[Ingestor] Wrote data for {machine_id} to InfluxDB.")
        
    except json.JSONDecodeError:
        print("[Ingestor] Error decoding JSON payload.")
    except Exception as e:
        print(f"[Ingestor] Error writing to InfluxDB: {e}")

def main():
    mqtt_client = mqtt.Client(client_id=f"affi_ingestor_{time.time()}")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    print(f"Starting Ingestor service...")
    print(f"Connecting to MQTT Broker: {BROKER}")
    
    # Simple retry logic for InfluxDB to allow it time to start up if using docker-compose
    while True:
        try:
            health = db_client.ping()
            if health:
                print(f"Connected to InfluxDB at {INFLUXDB_URL}")
                break
        except Exception as e:
            print(f"Waiting for InfluxDB to start... ({e})")
            time.sleep(5)
            
    mqtt_client.connect(BROKER, PORT, 60)
    
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("Stopping ingestor...")
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
