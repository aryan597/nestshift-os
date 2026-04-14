#!/bin/bash -e

# 1. Setup NestShift directory structure
install -v -d "${ROOTFS_DIR}/opt/nestshift"
install -v -d "${ROOTFS_DIR}/var/log/nestshift"
install -v -d "${ROOTFS_DIR}/var/lib/nestshift/db"

# 2. Copy the entire codebase into the image
# We use the absolute path from your home directory
cp -rv /home/aryan597/os-image/* "${ROOTFS_DIR}/opt/nestshift/"

# 3. Setup Python Virtual Environment
on_chroot << EOF
cd /opt/nestshift
python3 -m venv venv
venv/bin/pip install -r services/api/requirements.txt
venv/bin/pip install -r services/brain/requirements.txt
venv/bin/pip install -r services/energy-agent/requirements.txt
venv/bin/pip install -r services/automation-agent/requirements.txt
venv/bin/pip install -r services/system-agent/requirements.txt
EOF

# 4. Install Dashboard dependencies and build
on_chroot << EOF
cd /opt/nestshift/dashboard
npm install
npm run build # Generate the production static files
EOF

# 5. Install Systemd Services
install -v -m 644 /opt/nestshift/systemd/*.service "${ROOTFS_DIR}/etc/systemd/system/"

# 6. Enable Services
on_chroot << EOF
systemctl enable mosquitto
systemctl enable influxdb
systemctl enable nestshift-api
systemctl enable nestshift-brain
systemctl enable nestshift-energy-agent
systemctl enable nestshift-automation-agent
systemctl enable nestshift-system-agent
systemctl enable nestshift-dashboard
systemctl enable nestshift-kiosk # Our new local display service
EOF

# 7. Setup local user permissions
on_chroot << EOF
useradd -r -s /bin/bash -m -d /home/nestshift nestshift || true
usermod -aG gpio,i2c,spi,dialout,video nestshift
chown -R nestshift:nestshift /opt/nestshift
chown -R nestshift:nestshift /var/log/nestshift
chown -R nestshift:nestshift /var/lib/nestshift
EOF

# 8. Configure Auto-login for Kiosk mode
mkdir -p "${ROOTFS_DIR}/etc/systemd/system/getty@tty1.service.d"
cat > "${ROOTFS_DIR}/etc/systemd/system/getty@tty1.service.d/autologin.conf" << EOL
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin nestshift --noclear %I \$TERM
EOL
