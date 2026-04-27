# Implementation Guide: Above Factory Floor Intelligence (AFFI)
**Project Stage:** Post-Initialization / Development Phase
**Context:** Hacking for Defense (H4D) MVP for Tier 1 Cut-and-Sew Factories

Following the initialization of the project structure, this document serves as the roadmap for implementing the logic within each module.

---

## 1. Executive Summary & Strategy
The goal is to prove that "above floor" intelligence can reduce downtime and improve throughput by bridging the data gap between textile machinery and human decision-makers. The solution uses a **Digital Twin** approach to simulate real-world factory conditions and an **MCP Server** to allow an AI agent to act as a virtual floor manager.

---

## 2. Technical Stack
* **Backend & Logic:** Python 3.10+
* **API Framework:** FastAPI (for data serving and internal endpoints)
* **Message Broker:** MQTT (Eclipse Mosquitto) for real-time machine telemetry
* **Database:** InfluxDB (Time-series storage for high-frequency sensor data)
* **Intelligence Bridge:** FastMCP (Model Context Protocol) for LLM tool integration
* **Visualization:** Grafana (for real-time OEE and bottleneck dashboards)
* **Containerization:** Docker & Docker Compose (for infrastructure management)

---

## 3. Module Breakdown & Implementation Logic

### `/edge` - Machine Simulation & Gateway
* **`base_machine.py`**: Contains the abstract logic for any machine (Sewing or CNC). It manages state (Active, Idle, Fault).
* **`simulator.py`**: Implements specific logic for:
    * *Sewing Machines:* Random thread breaks, needle RPM fluctuations.
    * *CNC Mills:* Spindle vibration levels and material feed rates.
* **`gateway.py`**: The "Bridge." It collects local data from the simulators and publishes it to the MQTT broker under the topic `factory/machine/{machine_id}/telemetry`.

### `/transport` - Ingestion & Normalization
* **`ingestor.py`**: An asynchronous MQTT client. It listens for all telemetry messages, validates them against a Pydantic model, and prepares them for the database.
* **`broker_config.py`**: Centralized settings for MQTT connection strings and authentication.

### `/persistence` - Data Storage
* **`db_client.py`**: A wrapper for the InfluxDB Python client. It includes methods for `write_point()` and `query_recent_metrics()`.
* **`schema.sql`**: (Optional reference) or InfluxDB bucket configuration scripts.

### `/intelligence` - The "Brain"
* **`analytics.py`**: Contains the mathematical logic for:
    * **OEE Calculation:** Availability x Performance x Quality.
    * **Stall Detection:** Flagging if a machine is "Active" but the stitch count is zero.
* **`mcp_server.py`**: The interface for the AI. It exposes the analytics functions as "Tools" so a Gemini/Claude agent can answer questions like: *"Which machine is likely to fail next?"*

---

## 4. Intelligence Implementation Methodology
The intelligence is implemented in two layers:

1.  **Deterministic (Hard-coded):** Rules in `analytics.py` that trigger alerts based on set thresholds (e.g., Vibration > 0.8).
2.  **Probabilistic (Agentic):** The **MCP Server** allows an LLM to look at the historical data retrieved from InfluxDB and perform trend analysis that simple code might miss, such as identifying a specific operator who consistently experiences more thread breaks.

---

## 5. Development Workflow (Bit-by-Bit)
1.  **Phase 1 (Data Flow):** Run the `simulator.py` and verify `ingestor.py` is successfully writing to InfluxDB.
2.  **Phase 2 (Dashboard):** Connect Grafana to InfluxDB to visualize the "Machine Heartbeat."
3.  **Phase 3 (MCP Bridge):** Boot the `mcp_server.py` and connect it to your AI agent.
4.  **Phase 4 (Validation):** Inject a "Fault" into the simulator and see if the AI Agent correctly identifies and explains the issue.

---

## 6. Testing the MVP
* **Scenario A:** CNC Mill output drops by 15%. 
    * *Expected:* Intelligence layer flags "Downstream Starvation" for the sewing line.
* **Scenario B:** Sewing machine motor temperature hits 50°C.
    * *Expected:* MCP tool `predict_maintenance` returns a "High Risk" warning.
