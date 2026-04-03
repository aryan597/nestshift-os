#!/bin/bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 8000/tcp   # API
ufw allow 3000/tcp   # Dashboard
ufw allow 1883/tcp   # MQTT (local network only)
ufw allow 9001/tcp   # MQTT WebSocket
ufw allow 1880/tcp   # Node-RED
ufw enable