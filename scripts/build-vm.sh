#!/bin/bash -e

# NestShift OS — Virtual Machine (x86_64) Image Builder
# This script generates a .vdi file for VirtualBox.

echo "=========================================="
echo " 🧠 NestShift OS: VM Image Builder (x86_64)"
echo "=========================================="

# 1. Prerequisites Check
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "❌ ERROR: This script must be run inside WSL2 or a Linux environment."
    exit 1
fi

# 2. Setup Build Environment
echo "📦 Installing build dependencies (debos, qemu)..."
sudo apt update && sudo apt install -y debos qemu-user-static qemu-utils binfmt-support

# 3. Create the Image Recipe (YAML)
# This tells 'debos' exactly what goes into the VM image.
cat > nestshift-vm.yaml << EOL
architecture: amd64
filename: nestshift-os-vm.img

stages:
  - action: recipe
    recipe: scripts/vm-recipe-base.yaml

  - action: run
    chroot: true
    command: |
      # Install NestShift code into the VM
      mkdir -p /opt/nestshift
      cp -r /nestshift/* /opt/nestshift/
      cd /opt/nestshift
      ./scripts/install.sh
EOL

# 4. Create the Base Recipe
mkdir -p scripts
cat > scripts/vm-recipe-base.yaml << EOL
architecture: amd64

actions:
  - action: debootstrap
    suite: bookworm
    components:
      - main
      - non-free-firmware

  - action: apt
    packages:
      - sudo
      - python3
      - python3-venv
      - mosquitto
      - influxdb2
      - chromium-browser
      - xserver-xorg
      - lightdm
      - network-manager
      - curl
      - git

  - action: run
    chroot: true
    command: |
      echo "nestshift" > /etc/hostname
      useradd -m -s /bin/bash nestshift
      echo "nestshift:nestshift" | chpasswd
      usermod -aG sudo nestshift
EOL

# 5. Execute the Build
echo "🚀 Building the raw disk image..."
sudo debos --mount .:/nestshift nestshift-vm.yaml

# 6. Convert to VirtualBox VDI
echo "🌀 Converting to VirtualBox VDI format..."
qemu-img convert -f raw -O vdi nestshift-os-vm.img nestshift-os.vdi

echo "=========================================="
echo " ✅ SUCCESS! Image generated: nestshift-os.vdi"
echo " 1. Open VirtualBox on Windows."
echo " 2. Create a New VM (Debian 64-bit)."
echo " 3. Attach 'nestshift-os.vdi' as the Hard Disk."
echo " 4. Enable EFI in System settings."
echo " 5. Start the Brain."
echo "=========================================="
