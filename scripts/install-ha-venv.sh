#!/bin/bash
set -euo pipefail

# Install Home Assistant Core venv in Buildroot target
TARGET_DIR="${1}"
HA_DIR="${TARGET_DIR}/srv/homeassistant"
HOST_PYTHON="/usr/bin/python3"
TEMP_VENV="/tmp/ha-venv"

echo "Installing Home Assistant Core venv..."

# Create temp venv on host
"${HOST_PYTHON}" -m venv "${TEMP_VENV}"

# Install HA in temp venv
"${TEMP_VENV}/bin/pip" install --upgrade pip setuptools wheel
"${TEMP_VENV}/bin/pip" install \
    homeassistant==2024.12.0 \
    zha-quirks \
    aiohttp \
    pyyaml \
    cryptography \
    python-slugify \
    pillow \
    pyserial

# Create target venv directory
mkdir -p "${HA_DIR}/bin" "${HA_DIR}/lib" "${HA_DIR}/include" "${HA_DIR}/share"

# Copy python binary from target
cp "${TARGET_DIR}/usr/bin/python3" "${HA_DIR}/bin/python3"

# Copy site-packages from temp venv
cp -r "${TEMP_VENV}/lib/python3."* "${HA_DIR}/lib/"

# Copy pip and other scripts
cp "${TEMP_VENV}/bin/pip" "${HA_DIR}/bin/"
# Create hass script
cat > "${HA_DIR}/bin/hass" << 'EOF'
#!/bin/bash
exec python3 -m homeassistant "$@"
EOF
chmod +x "${HA_DIR}/bin/hass"

# Clean up temp
rm -rf "${TEMP_VENV}"

echo "Home Assistant Core venv installed."