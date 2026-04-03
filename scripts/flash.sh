#!/bin/bash
# Usage: ./flash.sh /dev/sdX
# Flashes NestShift OS image to SD card

DEVICE=${1:-""}
IMAGE_PATH="./os/nestshift-os.img"

if [ -z "$DEVICE" ]; then
  echo "Usage: $0 /dev/sdX"
  echo "Available devices:"
  lsblk -d -o NAME,SIZE,MODEL | grep -v loop
  exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
  echo "ERROR: OS image not found at $IMAGE_PATH"
  echo "Build it first with: cd os && ./build.sh"
  exit 1
fi

echo "WARNING: This will ERASE $DEVICE"
read -p "Type YES to continue: " confirm
[ "$confirm" != "YES" ] && exit 1

echo "Flashing $IMAGE_PATH to $DEVICE..."
dd if=$IMAGE_PATH of=$DEVICE bs=4M status=progress conv=fsync
sync
echo "Flash complete. Insert SD card into Raspberry Pi and power on."