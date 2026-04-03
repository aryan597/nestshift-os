import asyncio
import json
import logging
import os
import random
from datetime import datetime, timedelta
import aiomqtt
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor
import joblib
import httpx
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("energy-agent")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
ENV = os.getenv("ENV", "dev")
MODEL_DIR = "/tmp/nestshift/models" if ENV == "dev" else "/opt/nestshift/models"
os.makedirs(MODEL_DIR, exist_ok=True)


class TariffFetcher:
    def __init__(self, influx_client):
        self.influx_client = influx_client
        self.cache = []

    async def fetch_agile_tariffs(self):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/"
                    "electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-A/standard-unit-rates/"
                )
                if response.status_code == 200:
                    data = response.json()
                    tariffs = [
                        {
                            "valid_from": r["valid_from"],
                            "valid_to": r["valid_to"],
                            "value_inc_vat": r["value_inc_vat"],
                        }
                        for r in data["results"][:48]  # Next 48 half-hours
                    ]
                    await self.cache_tariffs(tariffs, "octopus")
                    return tariffs
                else:
                    logger.warning("Octopus API failed, using cache")
                    return await self.get_cached_tariffs()
        except Exception as e:
            logger.error(f"Network failure: {e}, using cache")
            return await self.get_cached_tariffs()

    async def get_cached_tariffs(self):
        if self.cache:
            return self.cache
        # Fallback to flat rate
        now = datetime.now()
        return [
            {
                "valid_from": (now + timedelta(minutes=i * 30)).isoformat(),
                "valid_to": (now + timedelta(minutes=(i + 1) * 30)).isoformat(),
                "value_inc_vat": 0.28,
            }
            for i in range(48)
        ]

    async def cache_tariffs(self, tariffs, source):
        self.cache = tariffs
        # Write to InfluxDB
        write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        for tariff in tariffs:
            point = (
                influxdb_client.Point("tariff_rates")
                .tag("source", source)
                .field("price_per_kwh", tariff["value_inc_vat"])
                .time(tariff["valid_from"])
            )
            write_api.write(bucket="nestshift", org="nestshift", record=point)


class DemandForecaster:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(MODEL_DIR, "demand_forecaster.pkl")

    def train(self, history_df):
        features = [
            "hour_of_day",
            "day_of_week",
            "month",
            "lag_1h",
            "lag_24h",
            "rolling_mean_6h",
            "rolling_mean_24h",
        ]
        target = "kwh_consumption"

        X = history_df[features]
        y = history_df[target]

        self.model = LGBMRegressor(n_estimators=100, learning_rate=0.1)
        self.model.fit(X, y)
        joblib.dump(self.model, self.model_path)
        logger.info("Demand forecaster trained and saved")

    def predict(self, hours_ahead=24):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            logger.warning("Model file missing, using flat prediction")
            return [0.4] * hours_ahead

        # Generate features for next 24 hours
        now = datetime.now()
        features = []
        for h in range(hours_ahead):
            dt = now + timedelta(hours=h)
            features.append(
                {
                    "hour_of_day": dt.hour,
                    "day_of_week": dt.weekday(),
                    "month": dt.month,
                    "lag_1h": 0.4,  # Simplified
                    "lag_24h": 0.4,
                    "rolling_mean_6h": 0.4,
                    "rolling_mean_24h": 0.4,
                }
            )
        X_pred = pd.DataFrame(features)
        return self.model.predict(X_pred).tolist()

    def should_retrain(self, current_mae):
        return current_mae > 0.15


class LoadScheduler:
    def generate_schedule(self, tariffs, forecast, comfort_bias, devices):
        schedule = []
        for device in devices:
            if device.get("type") in [
                "washing_machine",
                "dishwasher",
                "ev_charger",
                "water_heater",
            ]:
                # Simple scheduling: find lowest cost window
                runtime_hours = device.get("estimated_runtime_hours", 2)
                best_window = self.find_best_window(
                    tariffs, runtime_hours, comfort_bias
                )
                if best_window:
                    schedule.append(
                        {
                            "device_id": device["id"],
                            "scheduled_start": best_window["start"],
                            "estimated_cost_gbp": best_window["cost"],
                            "saving_vs_now_gbp": best_window["saving"],
                            "reason": "cost_optimization",
                        }
                    )
        return schedule

    def find_best_window(self, tariffs, runtime_hours, comfort_bias):
        # Simplified: find lowest average price window
        window_size = int(runtime_hours * 2)  # Half-hour slots
        best_cost = float("inf")
        best_window = None

        for i in range(len(tariffs) - window_size + 1):
            window = tariffs[i : i + window_size]
            avg_price = np.mean([t["value_inc_vat"] for t in window])
            if avg_price < best_cost:
                best_cost = avg_price
                best_window = {
                    "start": window[0]["valid_from"],
                    "cost": avg_price * runtime_hours,
                    "saving": 0.05,  # Mock saving
                }
        return best_window


async def main():
    logger.info("Energy Agent starting")

    # Connect to InfluxDB
    influx_client = influxdb_client.InfluxDBClient(
        url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org="nestshift"
    )

    tariff_fetcher = TariffFetcher(influx_client)
    forecaster = DemandForecaster()
    scheduler = LoadScheduler()

    comfort_bias = 0.5
    devices = []  # Will be populated from MQTT

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        await client.subscribe("nestshift/sensors/+/reading")
        await client.subscribe("nestshift/agents/system/drift_alert")
        await client.subscribe("nestshift/agents/automation/preferences")

        logger.info("Connected to MQTT broker")

        # Scheduler for periodic tasks
        scheduler_instance = AsyncIOScheduler()
        scheduler_instance.start()

        @scheduler_instance.scheduled_job("interval", minutes=30)
        async def periodic_tasks():
            # Fetch tariffs
            tariffs = await tariff_fetcher.fetch_agile_tariffs()
            current_tariff = (
                tariffs[0]
                if tariffs
                else {
                    "value_inc_vat": 0.28,
                    "valid_from": datetime.now().isoformat(),
                    "valid_to": (datetime.now() + timedelta(minutes=30)).isoformat(),
                    "is_peak": False,
                }
            )
            await client.publish(
                "nestshift/tariff/current",
                json.dumps(
                    {
                        "price_per_kwh": current_tariff["value_inc_vat"],
                        "valid_until": current_tariff["valid_to"],
                        "is_peak": False,  # Simplified
                    }
                ),
            )

            # Forecast demand
            predictions = forecaster.predict()
            await client.publish(
                "nestshift/agents/energy/forecast",
                json.dumps(
                    {
                        "predictions": predictions,
                        "generated_at": datetime.now().isoformat(),
                        "model_mae": 0.1,  # Mock
                        "horizon_hours": 24,
                    }
                ),
            )

            # Generate schedule
            schedule = scheduler.generate_schedule(
                tariffs, predictions, comfort_bias, devices
            )
            await client.publish(
                "nestshift/agents/energy/schedule",
                json.dumps(
                    {"schedule": schedule, "generated_at": datetime.now().isoformat()}
                ),
            )

        # Health publisher
        @scheduler_instance.scheduled_job("interval", seconds=60)
        async def publish_health():
            await client.publish(
                "nestshift/agents/system/health",
                json.dumps(
                    {
                        "agent": "energy",
                        "status": "running",
                        "last_forecast_mae": 0.1,
                        "uptime_seconds": 0,  # Simplified
                    }
                ),
            )

        async for message in client.messages:
            topic = message.topic
            payload = json.loads(message.payload.decode())

            if topic.startswith("nestshift/sensors/"):
                # Store to InfluxDB
                write_api = influx_client.write_api(write_options=SYNCHRONOUS)
                point = (
                    influxdb_client.Point("sensor_readings")
                    .field("kwh", payload.get("value", 0))
                    .tag("sensor_id", topic.split("/")[2])
                )
                write_api.write(bucket="nestshift", org="nestshift", record=point)

            elif topic == "nestshift/agents/system/drift_alert":
                if payload.get("agent") == "energy":
                    # Retrain model
                    # Query InfluxDB for history (simplified)
                    history_df = pd.DataFrame(
                        {
                            "hour_of_day": range(24),
                            "day_of_week": [0] * 24,
                            "month": [4] * 24,
                            "lag_1h": [0.4] * 24,
                            "lag_24h": [0.4] * 24,
                            "rolling_mean_6h": [0.4] * 24,
                            "rolling_mean_24h": [0.4] * 24,
                            "kwh_consumption": [
                                random.uniform(0.1, 0.8) for _ in range(24)
                            ],
                        }
                    )
                    forecaster.train(history_df)
                    await client.publish(
                        "nestshift/agents/energy/forecast",
                        json.dumps(
                            {
                                "predictions": forecaster.predict(),
                                "generated_at": datetime.now().isoformat(),
                                "retrained": True,
                            }
                        ),
                    )

            elif topic == "nestshift/agents/automation/preferences":
                comfort_bias = payload.get("comfort_cost_bias", 0.5)


if __name__ == "__main__":
    asyncio.run(main())
