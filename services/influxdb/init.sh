#!/bin/bash
# InfluxDB initialization script
influx setup \
  --org nestshift \
  --bucket nestshift \
  --username nestshift \
  --password changeme123 \
  --forceCreate

# Create additional measurements via Flux (if needed)
influx write \
  --org nestshift \
  --bucket nestshift \
  "system_init status=1"