# PixelPostman

A screen-time-conscious "media hub" for a young child, built around a single
Raspberry Pi 4. It replaces phones, tablets, and streaming-app menus with two
simple physical interactions:

1. **Interactive QR book** — the child scans a QR code on a page of a
   physical book (with a dedicated handheld scanner, not a phone), and the
   corresponding video starts playing on the TV.
2. **Travel postcards** — the child places a postcard from a family trip on
   an NFC reader, and a slideshow of photos (plus a short video clip filmed
   at that location) plays on the TV.

Both features are powered by the same Raspberry Pi and the same underlying
logic: a physical object is presented to a sensor, the object's code is
looked up in a mapping file, and the matching local media file is played
fullscreen on the television. There is no app, no algorithmic feed, no
infinite scroll, and no screen in the child's hands at any point — the only
screen involved is the living-room TV, and it only shows content the parent
has chosen and stored locally.

## Why this exists

The goal is to give a child the *experience* of choosing what to watch —
agency, curiosity, a tactile object-to-content connection — without handing
them a phone or tablet, and without exposing them to recommendation
algorithms, ads, or autoplay queues. Everything that plays is something a
parent recorded or selected ahead of time.

## How it works

```
 QR scanner (USB/Bluetooth, HID)         PN532 NFC reader (I2C)
        |                                        |
        v                                        v
  qr_listener.py                          nfc_listener.py
        |                                        |
        +------------------+---------------------+
                           v
                    content_mapper.py
              (looks up code/UID in mapping.json)
                           |
                           v
                       main.py
                  (dispatches the action)
                       /        \
                      v          v
              tv_control.py    player.py
            (HDMI-CEC: wake TV,   (mpv: plays video
             switch input)         or photo slideshow)
                           |
                           v
                      Television
```

- **QR scanner**: a standard HID barcode scanner. It behaves like a
  keyboard — it "types" the QR payload and presses Enter. `qr_listener.py`
  reads this directly from the input device file, so it works headless,
  without any terminal or desktop in focus.
- **NFC reader**: a PN532 module wired to the Pi's I2C pins. Each postcard
  has a cheap NFC sticker on the back with a unique ID. `nfc_listener.py`
  polls the reader and reports the tag's UID whenever a postcard is placed
  on it.
- **Content mapping**: `config/mapping.json` is the single file that ties a
  QR code or NFC UID to an action — play this video, or show this folder of
  photos followed by this clip. Adding new content (a new book page, a new
  postcard) just means adding one entry to this file plus dropping the
  media into `content/`.
- **TV control**: `tv_control.py` uses HDMI-CEC (`cec-client`) to wake the
  TV and switch it to the Pi's input automatically, so nothing needs to be
  powered on manually.
- **Playback**: `player.py` uses `mpv` to play videos fullscreen, or to run
  a photo slideshow (each image shown for a few seconds) optionally followed
  by a closing video clip.

## Repository structure

```
pixelpostman/
├── main.py                       # entry point — starts both listeners
├── requirements.txt
├── src/
│   ├── config.py                 # paths and tunable settings
│   ├── content_mapper.py         # reads mapping.json, resolves actions
│   ├── player.py                 # mpv wrapper (video + slideshow)
│   ├── tv_control.py             # HDMI-CEC wrapper
│   ├── qr_listener.py            # reads the HID barcode scanner
│   └── nfc_listener.py           # reads the PN532 NFC reader
├── config/
│   └── mapping.example.json      # template — copy to mapping.json and edit
├── scripts/
│   ├── install.sh                # one-time setup on the Pi
│   └── pixelpostman.service       # systemd unit for auto-start on boot
└── content/                      # your actual photos/videos go here (not tracked in git)
```

`config/mapping.json` and the real contents of `content/` are intentionally
excluded from git (see `.gitignore`) — they're personal family media and
specific to each setup, not something to publish.

## Hardware

- Raspberry Pi 4 (4GB recommended) with case, power supply, and a microSD card
- USB or Bluetooth HID barcode/QR scanner
- PN532 NFC reader module (wired via I2C: VCC, GND, SDA, SCL)
- micro-HDMI to HDMI cable (Pi 4 uses micro-HDMI, not full-size)
- NFC stickers (NTAG213/215) for the back of each postcard
- A TV with HDMI-CEC support (most modern TVs); if CEC is unreliable, a
  smart plug + IR blaster can be used as a fallback for power-on

## Setup

1. Flash Raspberry Pi OS (Lite is enough — no desktop environment needed)
   onto the microSD card and boot the Pi.
2. Clone this repository onto the Pi.
3. Run the setup script:
   ```bash
   bash scripts/install.sh
   ```
   This installs system packages (`mpv`, `cec-utils`, `i2c-tools`), enables
   I2C, creates a Python virtual environment, installs dependencies, and
   registers a systemd service so the hub starts automatically on boot.
4. Plug in the QR scanner and find its device path:
   ```bash
   ls /dev/input/by-id/
   ```
   Set `QR_SCANNER_DEVICE` in `src/config.py` (or as an environment
   variable) to match.
5. Wire the PN532 reader to the Pi's I2C pins.
6. Copy `config/mapping.example.json` to `config/mapping.json` (the install
   script does this automatically if the file doesn't exist yet) and fill in
   your real QR codes and NFC tag UIDs, pointing to media inside `content/`.
7. Drop the actual photos/videos into `content/`, following the folder
   structure referenced in `mapping.json`.
8. Start the hub:
   ```bash
   sudo systemctl start pixelpostman
   ```

## Adding new content later

- **New book page**: print a new QR code containing a short unique string
  (e.g. `BOOK-PAGE-07`), add an entry to `mapping.json` pointing to the new
  video file, and drop the video into `content/`.
- **New postcard**: write a fresh NFC sticker (any NFC-writing phone app can
  do this — you only need the UID, not the content written on the tag
  itself), find its UID by scanning it once and checking the hub's logs,
  add an entry to `mapping.json`, and put the photos/clip in `content/`.

## Notes on reliability

- If the TV doesn't respond well to HDMI-CEC, consider adding a smart plug
  with IR blaster (e.g. Broadlink) as a fallback for powering it on.
- Everything runs locally — no internet connection or cloud account is
  required for playback once content is on the Pi's storage.
- For travel use, the same Pi (or a smaller Pi Zero 2W running the same
  code) can be packed with the content pre-loaded, and plugged into any
  HDMI-CEC-capable TV (hotel, rental, etc.).
