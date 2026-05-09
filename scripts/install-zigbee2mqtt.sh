#!/bin/bash
set -euo pipefail

# Install Zigbee2MQTT in Buildroot target
TARGET_DIR="${1}"
Z2M_DIR="${TARGET_DIR}/opt/zigbee2mqtt"
HOST_NODE="/usr/bin/node"
HOST_NPM="/usr/bin/npm"

echo "Installing Zigbee2MQTT..."

# Download and extract
wget -O /tmp/zigbee2mqtt.tar.gz https://github.com/Koenkk/zigbee2mqtt/archive/refs/tags/1.40.0.tar.gz
mkdir -p "${Z2M_DIR}"
tar -xzf /tmp/zigbee2mqtt.tar.gz -C "${Z2M_DIR}" --strip-components=1

# Install deps using host node/npm
cd "${Z2M_DIR}"
"${HOST_NPM}" ci --production

# Create config
mkdir -p "${TARGET_DIR}/etc/zigbee2mqtt"
cat > "${TARGET_DIR}/etc/zigbee2mqtt/configuration.yaml" << 'EOF'
homeassistant: true
permit_join: false
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://localhost:1883
serial:
  port: /dev/ttyUSB0
  adapter: auto
frontend: false
advanced:
  log_level: warning
EOF

echo "Zigbee2MQTT installed."