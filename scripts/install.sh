#!/usr/bin/env bash
# One-time setup script. Run this directly on the Raspberry Pi 4,
# from inside the cloned repo folder:  bash scripts/install.sh
set -e

echo "==> Installing system dependencies (mpv, HDMI-CEC, I2C tools)..."
sudo apt update
sudo apt install -y python3-pip python3-venv mpv cec-utils i2c-tools

echo "==> Enabling I2C (needed for the PN532 NFC reader)..."
sudo raspi-config nonint do_i2c 0

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
sudo cp scripts/pixelpostman.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pixelpostman.service

echo ""
echo "Setup complete. Next steps:"
echo "  1. Plug in the QR scanner and run 'ls /dev/input/by-id/' to find its path,"
echo "     then set QR_SCANNER_DEVICE in src/config.py (or as an env var) accordingly."
echo "  2. Wire the PN532 reader to the Pi's I2C pins (see README)."
echo "  3. Edit config/mapping.json with your real QR codes / NFC tag UIDs and media paths."
echo "  4. Drop your videos/photos into the content/ folder."
echo "  5. Start the hub:  sudo systemctl start pixelpostman"
