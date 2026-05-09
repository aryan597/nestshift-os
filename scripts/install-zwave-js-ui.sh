#!/bin/bash
set -euo pipefail

# Install zwave-js-ui in Buildroot target
TARGET_DIR="${1}"
ZWAVE_DIR="${TARGET_DIR}/opt/zwave-js-ui"

echo "Installing zwave-js-ui..."

# Download pre-built binary
wget -O /tmp/zwave-js-ui.tar.gz https://github.com/zwave-js/zwave-js-ui/releases/download/v9.14.0/zwave-js-ui-v9.14.0-linux-arm64.tar.gz
mkdir -p "${ZWAVE_DIR}"
tar -xzf /tmp/zwave-js-ui.tar.gz -C "${ZWAVE_DIR}" --strip-components=1

# Create config dir
mkdir -p "${TARGET_DIR}/etc/zwave-js-ui"

echo "zwave-js-ui installed."