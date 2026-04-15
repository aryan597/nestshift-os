import asyncio
import json
import time
import random

MQTT_HOST = "localhost"
MQTT_PORT = 1883

async def simulate():
    print("🚀 NestShift Neural Core Simulator Starting...")
    print("This will simulate real human behavior for the Brain to learn.")
    
    # 1. Connect to local MQTT
    import aiomqtt
    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        
        sensors = ["hallway_motion", "kitchen_motion", "front_door"]
        devices = ["hallway_light", "kitchen_light", "foyer_light"]
        
        for i in range(10): # Simulate 10 'learning' events
            # Pick a random pairing
            idx = random.randint(0, 2)
            sensor = sensors[idx]
            device = devices[idx]
            
            print(f"\n[EVENT {i+1}]")
            # Step 1: Sensor spikes
            print(f"📡 Spike: {sensor} detected motion.")
            await client.publish(f"nestshift/sensors/{sensor}/reading", json.dumps({
                "type": "motion",
                "value": 1,
                "timestamp": time.time()
            }))
            
            # Step 2: Human delay (random 1-3 seconds)
            delay = random.uniform(1.0, 3.0)
            await asyncio.sleep(delay)
            
            # Step 3: Human manual override (turns on light)
            print(f"👤 Human: Manually turned on {device} after {delay:.2f}s.")
            await client.publish(f"nestshift/devices/{device}/state", json.dumps({
                "state": "on",
                "source": "manual",
                "timestamp": time.time()
            }))
            
            # Wait for next event
            await asyncio.sleep(2)

        print("\n✅ Simulation complete. The Brain should now have formed strong synapses.")

if __name__ == "__main__":
    asyncio.run(simulate())
