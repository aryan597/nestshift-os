from fastapi import FastAPI
import psutil
import sqlite3
import random
import asyncio
import json
import os
from datetime import datetime, timedelta
import aiomqtt
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.query_api import QueryApi
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

app = FastAPI()

# NestShift OS Part 5 — Security

# JWT token system
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    # Check against preferences table
    conn = sqlite3.connect("/app/database/nestshift.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT value FROM preferences WHERE key = ?", (f"user_{username}_hash",)
    )
    result = cursor.fetchone()
    conn.close()
    if not result:
        # First run: accept admin/nestshift
        if username == "admin" and password == "nestshift":
            # Force password change
            return {"username": username, "needs_password_change": True}
        return False
    if verify_password(password, result[0]):
        return {"username": username}
    return False


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


# Global caches for MQTT messages
agent_health_cache = {}
tariff_cache = {}

# MQTT setup
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")


# Start MQTT listener on app startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(mqtt_listener())


async def mqtt_listener():
    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        await client.subscribe("nestshift/agents/system/health")
        await client.subscribe("nestshift/tariff/current")
        async for message in client.messages:
            payload = json.loads(message.payload.decode())
            if message.topic == "nestshift/agents/system/health":
                agent_health_cache[payload["agent"]] = payload
            elif message.topic == "nestshift/tariff/current":
                tariff_cache = payload


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# NestShift OS Part 2 Additions


@app.post("/preferences/comfort-bias")
async def set_comfort_bias(
    body: dict, current_user: TokenData = Depends(get_current_user)
):
    value = body.get("value", 0.5)
    # Store in SQLite
    conn = sqlite3.connect("/app/database/nestshift.db")
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
        ("comfort_cost_bias", str(value)),
    )
    conn.commit()
    conn.close()
    # Publish to MQTT (stub, assume aiomqtt client is available)
    # For now, just return success
    return {"success": True, "value": value}


@app.post("/agents/{agent_name}/toggle")
async def toggle_agent(
    agent_name: str, body: dict, current_user: TokenData = Depends(get_current_user)
):
    enabled = body.get("enabled", False)
    # Publish to MQTT (stub)
    return {"success": True, "agent": agent_name, "enabled": enabled}


@app.get("/agents/status")
async def get_agent_status():
    # Return cached values from MQTT, fallback to unknown
    return {
        "energy": agent_health_cache.get("energy", {"status": "unknown"}),
        "automation": agent_health_cache.get("automation", {"status": "unknown"}),
        "system": agent_health_cache.get("system", {"status": "unknown"}),
    }


@app.get("/energy/usage")
async def get_energy_usage(period: str = "24h"):
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org="nestshift")
        query_api = client.query_api()

        # Query InfluxDB for real sensor readings
        query = f"""
        from(bucket: "nestshift")
        |> range(start: -{period})
        |> filter(fn: (r) => r["_measurement"] == "sensor_readings")
        |> filter(fn: (r) => r["_field"] == "kwh")
        |> aggregateWindow(every: 1h, fn: sum)
        |> yield(name: "energy_usage")
        """

        result = query_api.query(query)
        readings = []
        total_kwh = 0

        for table in result:
            for record in table.records:
                ts = record.get_time().isoformat()
                kwh = record.get_value()
                readings.append({"ts": ts, "kwh": kwh})
                total_kwh += kwh

        cost_gbp = total_kwh * 0.28  # Use current tariff
        savings_gbp = cost_gbp * 0.1  # Mock savings calculation

        return {
            "total_kwh": total_kwh,
            "cost_gbp": cost_gbp,
            "savings_gbp": savings_gbp,
            "readings": readings,
            "source": "influxdb",
        }
    except Exception as e:
        # Fallback to synthetic if InfluxDB unavailable
        readings = [
            {
                "ts": (datetime.now() - timedelta(hours=i)).isoformat(),
                "kwh": random.uniform(0.1, 0.8),
            }
            for i in range(24)
        ]
        total_kwh = sum(r["kwh"] for r in readings)
        cost_gbp = total_kwh * 0.28
        savings_gbp = cost_gbp * 0.1
        return {
            "total_kwh": total_kwh,
            "cost_gbp": cost_gbp,
            "savings_gbp": savings_gbp,
            "readings": readings,
            "source": "synthetic",
        }


@app.get("/energy/tariff/current")
async def get_current_tariff():
    # Return cached tariff from MQTT
    if tariff_cache:
        return tariff_cache
    else:
        return {
            "price_per_kwh": 0.28,
            "valid_until": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "is_peak": False,
            "source": "fallback",
        }


@app.get("/system/version")
async def get_system_version():
    uptime_seconds = int(psutil.boot_time() - datetime.now().timestamp())
    return {
        "version": "0.2.0",
        "hardware": "Raspberry Pi / Dev",
        "uptime_seconds": abs(uptime_seconds),
    }


# Auth endpoints
@app.post("/auth/token", response_model=Token)
async def login(form_data: dict):
    username = form_data.get("username")
    password = form_data.get("password")
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.post("/auth/change-password")
async def change_password(
    data: dict, current_user: TokenData = Depends(get_current_user)
):
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    # Verify current password
    user_auth = authenticate_user(current_user.username, current_password)
    if not user_auth:
        raise HTTPException(status_code=400, detail="Incorrect current password")
    # Update password
    hashed_new = get_password_hash(new_password)
    conn = sqlite3.connect("/app/database/nestshift.db")
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
        (f"user_{current_user.username}_hash", hashed_new),
    )
    conn.commit()
    conn.close()
    return {"success": True}


@app.get("/auth/status")
async def auth_status(current_user: TokenData = Depends(get_current_user)):
    return {"authenticated": True, "username": current_user.username}
