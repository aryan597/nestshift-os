#!/bin/bash
set -e

NESTSHIFT_VERSION="0.3.0"
INSTALL_DIR="/opt/nestshift"
NESTSHIFT_USER="nestshift"
REPO_URL="https://github.com/YOUR_USERNAME/nest-shift-os"

echo "======================================"
echo " NestShift OS Installer v${NESTSHIFT_VERSION}"
echo "======================================"

# 1. Create nestshift system user
if ! id "$NESTSHIFT_USER" &>/dev/null; then
  useradd -r -s /bin/bash -m -d /home/nestshift $NESTSHIFT_USER
  usermod -aG gpio,i2c,spi,dialout $NESTSHIFT_USER
  echo "Created user: $NESTSHIFT_USER"
fi

# 2. Clone repo to install dir
git clone $REPO_URL $INSTALL_DIR
chown -R $NESTSHIFT_USER:$NESTSHIFT_USER $INSTALL_DIR

# 3. Create Python venv and install all dependencies
python3 -m venv $INSTALL_DIR/venv
for service in api brain gpio energy-agent automation-agent system-agent; do
  $INSTALL_DIR/venv/bin/pip install -r \
    $INSTALL_DIR/services/$service/requirements.txt --quiet
done

# 4. Create runtime directories
mkdir -p /opt/nestshift/models
mkdir -p /var/log/nestshift
mkdir -p /var/lib/nestshift/db
chown -R $NESTSHIFT_USER:$NESTSHIFT_USER /opt/nestshift /var/log/nestshift \
  /var/lib/nestshift

# 5. Install systemd services
cp $INSTALL_DIR/systemd/*.service /etc/systemd/system/
systemctl daemon-reload

# 6. Copy sysctl tuning
cp $INSTALL_DIR/os/stage-nestshift/01-sys-tweaks/files/10-nestshift-sysctl.conf \
  /etc/sysctl.d/
sysctl --system

# 7. Configure firewall
bash $INSTALL_DIR/os/stage-nestshift/01-sys-tweaks/files/nestshift-ufw-rules.sh

# 8. Enable and start services in dependency order
for service in mosquitto influxdb nestshift-api nestshift-brain \
  nestshift-gpio nestshift-energy-agent nestshift-automation-agent \
  nestshift-system-agent nestshift-dashboard; do
  systemctl enable $service
  systemctl start $service
  sleep 2
  systemctl is-active $service && echo "STARTED: $service" \
    || echo "FAILED: $service — check: journalctl -u $service"
done

# 9. Run InfluxDB init
bash $INSTALL_DIR/services/influxdb/init.sh

echo ""
echo "======================================"
echo " NestShift OS installed successfully"
echo " Dashboard: http://nestshift.local:3000"
echo " API docs:  http://nestshift.local:8000/docs"
echo "======================================"