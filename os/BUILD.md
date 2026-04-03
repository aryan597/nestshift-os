# Building NestShift OS Image

This guide explains how to build a flashable Raspberry Pi OS image with NestShift OS pre-installed.

## 1. Prerequisites

You need a Linux machine (Ubuntu/Debian recommended) with at least 50GB free disk space.

Install required packages:
```bash
sudo apt update
sudo apt install -y git curl wget unzip qemu-user-static binfmt-support parted kpartx zerofree zip dosfstools bsdtar libcap2-bin grep awk xargs
```

## 2. Clone and Setup pi-gen

```bash
git clone https://github.com/RPi-Distro/pi-gen.git
cd pi-gen
git checkout arm64  # For Raspberry Pi 4/5
```

Copy the NestShift stage:
```bash
cp -r ../nest-shift-os/os/stage-nestshift stage-nestshift
```

## 3. Build Command

Run the build with the correct stage flags:
```bash
sudo ./build.sh -c config  # Use config file for customization
# Or manually:
sudo CLEAN=1 IMG_NAME=nestshift-os ./build.sh
```

The build will run these stages:
- stage0: Bootstrap
- stage1: Base OS
- stage2: Firmware
- stage-nestshift: NestShift packages and config

## 4. Expected Build Time

- On a modern 8-core CPU with SSD: 30-45 minutes
- On slower hardware: 1-2 hours
- The build downloads ~2GB of packages

## 5. Output Location

The finished image will be in the `deploy/` directory:
- `nestshift-os.img` — Raw disk image (~4GB)
- `nestshift-os.zip` — Compressed version for distribution

## 6. Flashing the Image

Use the flash helper script:
```bash
./scripts/flash.sh /dev/sdX
```

Replace `/dev/sdX` with your SD card device (check with `lsblk`).

## 7. First Boot Sequence

1. Insert flashed SD card into Raspberry Pi
2. Power on — first boot takes 2-3 minutes
3. The system runs `scripts/first-run.sh` which:
   - Sets hostname to "nestshift"
   - Enables mDNS (nestshift.local)
   - Generates unique device ID
   - Creates MQTT credentials
   - Seeds initial database

## 8. Accessing the System

After first boot, access via:
- Dashboard: http://nestshift.local:3000
- SSH: `ssh nestshift@nestshift.local`
  - Default password: (set during first-run, check logs)

Monitor logs with:
```bash
journalctl -u nestshift-api
journalctl -f  # Follow all logs
```

If issues occur, check `/var/log/nestshift/` for service-specific logs.