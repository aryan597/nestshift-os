# NestShift OS Stage

This pi-gen stage installs all dependencies required for the NestShift OS edge AI operating system.

## Core Python Environment
python3, python3-pip, python3-venv, python3-dev: Base Python runtime with development headers for compiling extensions like numpy/scipy.

## Development Tools
git, curl, wget, build-essential, libssl-dev, libffi-dev: Essential tools for cloning repos, downloading dependencies, and compiling software.

## Messaging & Database
mosquitto, mosquitto-clients: MQTT broker for inter-service communication, as specified in CONTRACTS.md.
sqlite3, libsqlite3-dev: SQLite database for local data persistence.
influxdb2, influxdb2-cli: Time-series database for telemetry and sensor data storage.

## Web Technologies
nodejs, npm: Node.js runtime for the React dashboard and build tools.

## Containerization
docker.io, docker-compose: Container runtime for development and potential service isolation.

## Hardware Interfaces
libgpiod2, python3-lgpio: GPIO access for relay control and sensor reading on Raspberry Pi.
i2c-tools, libi2c-dev: I2C bus communication for connected sensors and devices.

## Security & Networking
ufw, fail2ban: Firewall and intrusion prevention.
openssh-server: Secure remote access.
network-manager, avahi-daemon: Network configuration and mDNS discovery (nestshift.local).
ntpdate: Time synchronization for accurate sensor timestamps.

These packages provide the foundation for the three AI agents (energy forecasting, automation learning, system monitoring) as described in the technical architecture paper.