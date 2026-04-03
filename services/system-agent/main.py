import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
import aiomqtt
import psutil
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("system-agent")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
ENV = os.getenv("ENV", "dev")


class ResourceMonitor:
    @staticmethod
    def get_snapshot():
        cpu_temp = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                cpu_temp = int(f.read().strip()) / 1000
        except:
            pass

        return {
            "cpu_pct": psutil.cpu_percent(),
            "ram_pct": psutil.virtual_memory().percent,
            "disk_pct": psutil.disk_usage("/").percent,
            "cpu_temp": cpu_temp,
            "uptime_seconds": int(time.time() - psutil.boot_time()),
        }


class DriftDetector:
    def __init__(self):
        self.errors = {"energy": [], "automation": []}

    def record_prediction_error(self, agent, error):
        self.errors[agent].append(error)
        if len(self.errors[agent]) > 100:
            self.errors[agent].pop(0)

    def check_drift(self, agent):
        if len(self.errors[agent]) < 10:
            return False
        mean_error = sum(self.errors[agent]) / len(self.errors[agent])
        threshold = 0.15 if agent == "energy" else 0.25
        return mean_error > threshold

    def get_drift_status(self):
        return {
            "energy": self.check_drift("energy"),
            "automation": self.check_drift("automation"),
        }


class ModelLifecycleManager:
    @staticmethod
    def check_model_freshness():
        model_path = (
            "/tmp/nestshift/models/demand_forecaster.pkl"
            if ENV == "dev"
            else "/opt/nestshift/models/demand_forecaster.pkl"
        )
        if os.path.exists(model_path):
            mtime = os.path.getmtime(model_path)
            age_days = (time.time() - mtime) / (24 * 3600)
            return {"energy": "fresh" if age_days < 7 else "stale"}
        return {"energy": "missing"}

    async def trigger_retrain(self, agent, client):
        await client.publish(
            "nestshift/agents/system/drift_alert",
            json.dumps(
                {
                    "agent": agent,
                    "drift_detected": True,
                    "reason": "model_stale",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        )


async def main():
    logger.info("System Agent starting")

    # Connect to InfluxDB
    influx_client = influxdb_client.InfluxDBClient(
        url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org="nestshift"
    )

    resource_monitor = ResourceMonitor()
    drift_detector = DriftDetector()
    lifecycle_manager = ModelLifecycleManager()

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        await client.subscribe("nestshift/agents/energy/forecast")
        await client.subscribe("nestshift/agents/automation/learned_pattern")
        await client.subscribe("nestshift/system/log")

        logger.info("Connected to MQTT broker")

        # Scheduler
        scheduler_instance = AsyncIOScheduler()
        scheduler_instance.start()

        @scheduler_instance.scheduled_job("interval", seconds=30)
        async def publish_health():
            snapshot = resource_monitor.get_snapshot()
            drift_status = drift_detector.get_drift_status()
            model_freshness = lifecycle_manager.check_model_freshness()

            health_payload = {
                **snapshot,
                "drift_status": drift_status,
                "model_freshness": model_freshness,
            }

            await client.publish(
                "nestshift/agents/system/health", json.dumps(health_payload)
            )

            # Write to InfluxDB
            write_api = influx_client.write_api(write_options=SYNCHRONOUS)
            point = (
                influxdb_client.Point("system_metrics")
                .field("cpu_pct", snapshot["cpu_pct"])
                .field("ram_pct", snapshot["ram_pct"])
                .field("disk_pct", snapshot["disk_pct"])
            )
            if snapshot["cpu_temp"]:
                point = point.field("cpu_temp", snapshot["cpu_temp"])
            write_api.write(bucket="nestshift", org="nestshift", record=point)

        @scheduler_instance.scheduled_job("interval", minutes=5)
        async def check_drift():
            drift_status = drift_detector.get_drift_status()
            for agent, drifted in drift_status.items():
                if drifted:
                    await client.publish(
                        "nestshift/agents/system/drift_alert",
                        json.dumps(
                            {
                                "agent": agent,
                                "drift_detected": True,
                                "mean_error": sum(drift_detector.errors[agent][-10:])
                                / 10,
                                "threshold": 0.15 if agent == "energy" else 0.25,
                            }
                        ),
                    )

        @scheduler_instance.scheduled_job("interval", hours=1)
        async def check_model_freshness():
            freshness = lifecycle_manager.check_model_freshness()
            if freshness["energy"] == "stale":
                await lifecycle_manager.trigger_retrain("energy", client)

        # Prune old data
        @scheduler_instance.scheduled_job("interval", hours=24)
        async def prune_data():
            # InfluxDB delete query (simplified)
            logger.info("Pruning old data (>180 days)")
            # delete_api = influx_client.delete_api()
            # delete_api.delete(
            #     start="1970-01-01T00:00:00Z",
            #     stop=(datetime.now() - timedelta(days=180)).isoformat(),
            #     bucket="nestshift",
            #     org="nestshift",
            #     predicate='_measurement="sensor_readings"'
            # )

        async for message in client.messages:
            topic = message.topic
            payload = json.loads(message.payload.decode())

            if topic == "nestshift/agents/energy/forecast":
                mae = payload.get("model_mae", 0)
                drift_detector.record_prediction_error("energy", mae)

            elif topic == "nestshift/agents/automation/learned_pattern":
                confidence = payload.get("confidence", 0)
                # Use inverse confidence as proxy error
                error = 1 - confidence
                drift_detector.record_prediction_error("automation", error)

            elif topic == "nestshift/system/log":
                # Store log entries to InfluxDB
                write_api = influx_client.write_api(write_options=SYNCHRONOUS)
                point = (
                    influxdb_client.Point("system_logs")
                    .field("message", json.dumps(payload))
                    .tag("level", payload.get("level", "info"))
                )
                write_api.write(bucket="nestshift", org="nestshift", record=point)


if __name__ == "__main__":
    asyncio.run(main())
