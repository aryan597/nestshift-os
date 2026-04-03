#!/bin/bash
FIRST_RUN_FLAG="/var/lib/nestshift/.first-run-complete"

if [ -f "$FIRST_RUN_FLAG" ]; then
  echo "First run already completed. Exiting."
  exit 0
fi

echo "Running NestShift first-run setup..."

# 1. Set hostname
hostnamectl set-hostname nestshift

# 2. Enable avahi for nestshift.local mDNS
systemctl enable avahi-daemon
systemctl start avahi-daemon

# 3. Generate unique device ID
DEVICE_ID=$(cat /proc/cpuinfo | grep Serial | awk '{print $3}')
if [ -z "$DEVICE_ID" ]; then
  DEVICE_ID=$(uuidgen)
fi
echo $DEVICE_ID > /var/lib/nestshift/device-id

# 4. Generate MQTT credentials
MQTT_PASS=$(openssl rand -hex 16)
mosquitto_passwd -b /etc/mosquitto/passwd nestshift $MQTT_PASS
echo "MQTT_PASSWORD=$MQTT_PASS" >> /opt/nestshift/.env

# 5. Wait for API to be ready, then seed database
sleep 10
curl -s -X POST http://localhost:8000/system/init \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$DEVICE_ID\"}" \
  && echo "Database seeded OK" \
  || echo "WARNING: Database seed failed — retry on next boot"

# 6. Mark first run complete
touch $FIRST_RUN_FLAG
echo "First-run setup complete. Device ID: $DEVICE_ID"