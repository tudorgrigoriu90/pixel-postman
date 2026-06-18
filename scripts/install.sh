#!/usr/bin/env bash
# One-time setup script. Run this directly on the Raspberry Pi 4,
# from inside the cloned repo folder:  bash scripts/install.sh
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-$USER}"

echo "==> Installing system dependencies (mpv, HDMI-CEC, I2C tools)..."
sudo apt update
sudo apt install -y python3-pip python3-venv mpv cec-utils i2c-tools

echo "==> Enabling I2C (needed for the PN532 NFC reader)..."
sudo raspi-config nonint do_i2c 0

echo "==> Adding '$SERVICE_USER' to the input/i2c/video/gpio groups..."
# Needed to read the QR scanner (input), the NFC reader (i2c), send HDMI-CEC
# (video) and drive the LED / power button (gpio) without running as root.
sudo usermod -aG input,i2c,video,gpio "$SERVICE_USER"

echo "==> Allowing '$SERVICE_USER' to shut down without a password..."
# Lets the soft power button trigger a clean shutdown.
echo "$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/shutdown" | \
  sudo tee /etc/sudoers.d/pixelpostman-shutdown >/dev/null
sudo chmod 440 /etc/sudoers.d/pixelpostman-shutdown

echo "==> Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f config/mapping.json ]; then
  echo "==> Creating config/mapping.json from the example template..."
  cp config/mapping.example.json config/mapping.json
fi

echo "==> Installing systemd service (auto-start on boot)..."
# Render the unit with this repo's actual path and service user.
sed -e "s#@REPO_DIR@#${REPO_DIR}#g" -e "s#@USER@#${SERVICE_USER}#g" \
  scripts/pixelpostman.service | sudo tee /etc/systemd/system/pixelpostman.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable pixelpostman.service

echo ""
echo "Setup complete. NOTE: log out and back in (or reboot) so the new group"
echo "memberships take effect. Next steps:"
echo "  1. Plug in the QR scanner and run 'ls /dev/input/by-id/' to find its path,"
echo "     then set QR_SCANNER_DEVICE in src/config.py (or as an env var) accordingly."
echo "  2. Wire the PN532 reader to the Pi's I2C pins (see README)."
echo "  3. Wire the REQUIRED feedback LED (GPIO17) and soft power button (GPIO3)."
echo "     The hub will not start without them (see README)."
echo "  4. Edit config/mapping.json with your real QR codes / NFC tag UIDs and media paths."
echo "  5. Drop your videos/photos into the content/ folder (and an idle.png if you like)."
echo "  6. Verify the wiring/config:  python main.py --selftest"
echo "  7. For maximum power resilience, consider enabling the read-only overlay"
echo "     filesystem:  sudo raspi-config  ->  Performance  ->  Overlay File System."
echo "  8. Log out/in (for the new groups) then start:  sudo systemctl start pixelpostman"
