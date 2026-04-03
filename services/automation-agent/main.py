import asyncio
import json
import logging
import os
import time
from datetime import datetime
import aiomqtt
import numpy as np
import pandas as pd
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("automation-agent")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")


class BehaviourModel:
    def __init__(self):
        self.patterns = {}
        self.total_events = 0

    def record_event(self, device_id, action, timestamp):
        hour = datetime.fromisoformat(timestamp).hour
        if hour not in self.patterns:
            self.patterns[hour] = {}
        if device_id not in self.patterns[hour]:
            self.patterns[hour][device_id] = {}
        if action not in self.patterns[hour][device_id]:
            self.patterns[hour][device_id][action] = 0
        self.patterns[hour][device_id][action] += 1
        self.total_events += 1

    def get_pattern_confidence(self):
        if self.total_events < 72:
            return 0.0
        return min(1.0, self.total_events / 2000)

    def predict_next_action(self, current_hour, device_states):
        if self.get_pattern_confidence() < 0.3:
            return None

        if current_hour not in self.patterns:
            return None

        # Find most common action for this hour
        best_action = None
        best_prob = 0
        total_actions = sum(
            sum(actions.values()) for actions in self.patterns[current_hour].values()
        )

        for device_id, actions in self.patterns[current_hour].items():
            for action, count in actions.items():
                prob = count / total_actions
                if prob > best_prob and prob > 0.75:
                    best_prob = prob
                    best_action = {
                        "device_id": device_id,
                        "action": action,
                        "confidence": prob,
                    }

        return best_action


class RuleEngine:
    def validate_action(self, action, system_state):
        device_id = action["device_id"]
        action_type = action["action"]
        device = system_state.get("devices", {}).get(device_id, {})

        # Rule 1: Never turn off security devices if occupied
        if action_type in ["turn_off", "disable"] and device.get("type") in [
            "security",
            "alarm",
        ]:
            if system_state.get("occupancy", {}).get("occupied", False):
                logger.warning(
                    f"Blocked {action_type} of security device {device_id} due to occupancy"
                )
                return False

        # Rule 2: Never set HVAC outside 16-26°C
        if device.get("type") == "hvac" and "setpoint" in action:
            setpoint = action["setpoint"]
            if not 16 <= setpoint <= 26:
                logger.warning(
                    f"Blocked HVAC setpoint {setpoint}°C for {device_id} - outside safe range"
                )
                return False

        # Rule 3: Never run more than 3 high-power devices simultaneously
        if action_type in ["turn_on", "start"]:
            running_high_power = sum(
                1
                for d in system_state.get("devices", {}).values()
                if d.get("type") in ["ev_charger", "water_heater", "hvac"]
                and d.get("state") == "on"
            )
            if running_high_power >= 3:
                logger.warning(
                    f"Blocked {action_type} of {device_id} - too many high-power devices running"
                )
                return False

        # Rule 4: Turn off lights if no activity for 30 min and no occupancy
        # This is handled in run_cycle, not here

        return True


class AutomationAgent:
    def __init__(self):
        self.behaviour_model = BehaviourModel()
        self.rule_engine = RuleEngine()
        self.system_state = {}
        self.start_time = time.time()

    async def run_cycle(self, system_state):
        self.system_state = system_state
        current_hour = datetime.now().hour

        prediction = self.behaviour_model.predict_next_action(
            current_hour, system_state.get("devices", {})
        )
        if prediction:
            if self.rule_engine.validate_action(prediction, system_state):
                confidence = self.behaviour_model.get_pattern_confidence()
                alpha = 0.0 if confidence < 0.3 else confidence * 0.8
                logger.info(f"Automation action: {prediction}, alpha: {alpha}")
                return [prediction]

        return []


async def main():
    logger.info("Automation Agent starting")

    # Connect to InfluxDB
    influx_client = influxdb_client.InfluxDBClient(
        url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org="nestshift"
    )

    agent = AutomationAgent()

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        await client.subscribe("nestshift/devices/+/state")
        await client.subscribe("nestshift/sensors/+/reading")
        await client.subscribe("nestshift/agents/automation/preferences")

        logger.info("Connected to MQTT broker")

        # Scheduler
        scheduler_instance = AsyncIOScheduler()
        scheduler_instance.start()

        @scheduler_instance.scheduled_job("interval", minutes=5)
        async def automation_cycle():
            actions = await agent.run_cycle(agent.system_state)
            for action in actions:
                await client.publish(
                    "nestshift/agents/automation/action",
                    json.dumps(
                        {
                            **action,
                            "generated_at": datetime.now().isoformat(),
                            "rule_validated": True,
                        }
                    ),
                )

        @scheduler_instance.scheduled_job("interval", seconds=60)
        async def publish_pattern():
            confidence = agent.behaviour_model.get_pattern_confidence()
            await client.publish(
                "nestshift/agents/automation/learned_pattern",
                json.dumps(
                    {
                        "confidence": confidence,
                        "total_events": agent.behaviour_model.total_events,
                        "hours_of_data": len(agent.behaviour_model.patterns),
                        "alpha": confidence * 0.8 if confidence >= 0.3 else 0.0,
                    }
                ),
            )

            # Write to InfluxDB
            write_api = influx_client.write_api(write_options=SYNCHRONOUS)
            point = (
                influxdb_client.Point("agent_metrics")
                .tag("agent", "automation")
                .field("alpha", confidence * 0.8 if confidence >= 0.3 else 0.0)
                .field("confidence", confidence)
            )
            write_api.write(bucket="nestshift", org="nestshift", record=point)

        @scheduler_instance.scheduled_job("interval", seconds=60)
        async def publish_health():
            uptime = int(time.time() - agent.start_time)
            await client.publish(
                "nestshift/agents/system/health",
                json.dumps(
                    {
                        "agent": "automation",
                        "status": "running",
                        "confidence": agent.behaviour_model.get_pattern_confidence(),
                        "uptime_seconds": uptime,
                    }
                ),
            )

        async for message in client.messages:
            topic = message.topic
            payload = json.loads(message.payload.decode())

            if topic.startswith("nestshift/devices/"):
                device_id = topic.split("/")[2]
                agent.system_state.setdefault("devices", {})[device_id] = payload
                # Record behaviour
                if "action" in payload:
                    agent.behaviour_model.record_event(
                        device_id,
                        payload["action"],
                        payload.get("timestamp", datetime.now().isoformat()),
                    )

            elif topic.startswith("nestshift/sensors/"):
                sensor_id = topic.split("/")[2]
                agent.system_state.setdefault("sensors", {})[sensor_id] = payload


if __name__ == "__main__":
    asyncio.run(main())
