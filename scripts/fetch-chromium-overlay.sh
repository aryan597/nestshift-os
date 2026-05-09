#!/bin/bash
set -euo pipefail

OVERLAY_DIR="/home/aryan597/buildroot-external-nestshift/board/nestshift/rootfs-overlay"
mkdir -p "${OVERLAY_DIR}"

# Hardcoded for now - TODO: make dynamic
DEB_URL="https://archive.raspberrypi.org/debian/pool/main/c/chromium/chromium_147.0.7727.101-1~deb12u1+rpt1_arm64.deb"
SHA256="placeholder"  # Skip check

# Debug
echo "DEB_URL: ${DEB_URL}"
echo "SHA256: ${SHA256}"

# Download
wget -O /tmp/chromium.deb "${DEB_URL}"

# Unpack to overlay
dpkg-deb -x /tmp/chromium.deb "${OVERLAY_DIR}"

echo "Chromium overlay fetched and unpacked."