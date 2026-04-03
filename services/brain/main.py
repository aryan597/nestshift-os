import asyncio
import aiomqtt
import os


async def main():
    MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        await client.subscribe("#")
        async for message in client.messages:
            print(f"Received: {message.payload.decode()}")


if __name__ == "__main__":
    asyncio.run(main())
