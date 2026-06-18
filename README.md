# PixelPostman

**A free, DIY, build-it-yourself media hub for a young child — powered by a
single Raspberry Pi.**

PixelPostman lets a child play *only* the content you've chosen, by presenting a
physical object instead of using a remote, phone, or streaming-app menu:

1. **Interactive QR book** — the child scans a QR code on a page of a physical
   book (with a dedicated handheld scanner, not a phone), and the matching
   video starts playing on the TV.
2. **Travel postcards** — the child places an NFC-tagged postcard on a reader,
   and a slideshow of your photos (plus an optional short clip filmed at that
   place) plays on the TV.

A physical object is presented to a sensor → the object's code is looked up in
a simple mapping file → the matching **local** media plays fullscreen on the
television. No app, no algorithmic feed, no infinite scroll, no remote in the
child's hands, and no internet needed for playback. The only screen is the
living-room TV, and it only ever shows content you put on the device.

> **This project is free for everyone to build, use, copy, and modify.** It's a
> hobby/DIY guide, not a product — there is nothing to buy from us and no cloud
> service. Grab the parts, follow the wiring, flash the code, and make it your
> own. See [LICENSE](LICENSE) (MIT).

## Why build this?

The goal is to give a child the *experience* of choosing what to watch —
agency, curiosity, a tactile object-to-content connection — while you stay in
full control of the content. Everything that plays is something you recorded or
deliberately selected ahead of time. Great sources of content include:

- **Your own family videos and photos** (trips, birthdays, a grandparent
  reading a bedtime story).
- **Public-domain and Creative-Commons** kids/educational films and animation.
- **Anything you have the right to use** and have copied onto the device.

Please load only content you own or are licensed to use.

---

## What you'll need (shopping list)

Approximate prices are rough and vary by region — treat them as ballpark only.

### Core (required)

| # | Part | Notes |
|---|------|-------|
| 1 | **Raspberry Pi 4** (2GB is plenty, 4GB fine) | The brain. A Pi 400/Pi 5 also work with minor tweaks. |
| 1 | **Official USB-C power supply** (5V / 3A) | Underpowered supplies cause random flakiness — don't skip this. |
| 1 | **microSD card**, 32GB+ (A1/A2, reputable brand) | Holds the OS and your media. |
| 1 | **micro-HDMI → HDMI cable** | The Pi 4 uses *micro*-HDMI, not full-size. |
| 1 | **Raspberry Pi 4 case** | Any case; one with GPIO access is handy. |
| 1 | **USB HID barcode / QR scanner** | Any "keyboard-emulation" (HID) USB scanner. These just "type" the code. |
| 1 | **PN532 NFC reader module** (I2C-capable) | The common red "PN532 NFC V3" boards work great. |
| 1 pack | **NTAG213 or NTAG215 NFC stickers** | One per postcard. |
| 1 | **5mm LED** (any colour) | Scan/playback feedback light. |
| 1 | **330Ω resistor** | In series with the LED. |
| 1 | **Momentary push button** (tactile switch) | Soft power / clean-shutdown button. |
| ~8 | **Female-to-female jumper wires** ("Dupont") | To connect the PN532, LED and button to the GPIO header. |
| 1 | **TV with HDMI-CEC** | Almost all modern TVs. (CEC marketing names: Anynet+, Bravia Sync, SimpLink, etc.) |

### Optional but recommended

| Part | Why |
|------|-----|
| **USB SSD + USB3 adapter** | Store media off the SD card — faster and far more durable for lots of video. |
| **Small solderless breadboard** *or* perfboard | Tidy home for the LED + resistor + button. No soldering needed with a breadboard. |
| **A physical book + a printer** | Print QR codes (any printer) and stick/print them on book pages. |
| **Smart plug + IR blaster** (e.g. Broadlink) | Fallback to power the TV on if its HDMI-CEC is unreliable. |

You'll also need, for the build itself: a computer to flash the SD card, and
(if you choose perfboard over a breadboard) a soldering iron.

---

## Build the hardware

> ⚠️ **Power off the Pi and unplug it before wiring anything to the GPIO
> header.** Double-check every pin against the diagram below — wiring to the
> wrong pin (especially 5V) can damage the Pi or a module.

### Raspberry Pi GPIO pins we use

Pins are referenced by **physical position** (the number on the 40-pin header)
and by **BCM/GPIO number** (what the software uses).

| Signal | Physical pin | BCM / GPIO |
|--------|--------------|------------|
| 3.3V power (PN532 VCC) | 1 | — |
| I2C SDA (PN532 SDA) | 3 | GPIO2 |
| I2C SCL (PN532 SCL) | 5 | GPIO3 |
| Ground (shared) | 6 / 9 / 39 | — |
| LED output | 11 | GPIO17 |
| Power-button input | 37 | GPIO26 |

> The power button is on **GPIO26**, not the "classic" GPIO3 power pin, because
> GPIO3 is already used here as the I2C clock for the NFC reader.

### 1. PN532 NFC reader (I2C — 4 wires)

First, set the module to **I2C mode** (the red PN532 V3 boards have two small
DIP switches / a selector — follow the silkscreen labels for I2C). Then wire:

| PN532 pin | → Raspberry Pi |
|-----------|----------------|
| VCC | 3.3V — physical pin 1 *(use 5V only if your module's docs require it)* |
| GND | GND — physical pin 6 |
| SDA | GPIO2 / SDA — physical pin 3 |
| SCL | GPIO3 / SCL — physical pin 5 |

### 2. Feedback LED (2 wires + resistor)

LEDs are polarised — the **long leg is the anode (+)**, the short leg is the
cathode (–).

```
GPIO17 (pin 11) ──► [330Ω resistor] ──► LED long leg (+)
LED short leg (–) ──────────────────────► GND (e.g. pin 9)
```

The resistor protects the LED; it can go on either leg. Either order
(GPIO→resistor→LED→GND) works.

### 3. Soft power button (2 wires)

A plain momentary push button between **GPIO26 and GND** — no resistor needed
(the Pi's internal pull-up is used in software):

```
GPIO26 (pin 37) ──► button ──► GND (pin 39)
```

Holding this button for ~2 seconds shuts the Pi down cleanly. (To turn it back
on after a shutdown, briefly unplug and replug the power.)

### 4. Plug in the rest

- USB QR scanner → any USB port.
- micro-HDMI → TV.
- microSD (flashed in the next section) → card slot.
- USB-C power → last.

A breadboard makes the LED + resistor + button tidy and solder-free; perfboard
+ soldering gives a permanent build. Either is fine.

---

## Install the software

### 1. Flash Raspberry Pi OS

Use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash
**Raspberry Pi OS Lite (64-bit)** to the microSD card — Lite (no desktop) is
all you need. In the Imager's settings, enable **SSH** and set a username /
Wi-Fi so you can log in headlessly. Boot the Pi and log in (over SSH or a
keyboard).

### 2. Get the code

Clone this repository onto the Pi:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/tudorgrigoriu90/pixel-postman.git
cd pixel-postman
```

### 3. Run the one-time setup script

```bash
bash scripts/install.sh
```

This installs the system packages (`mpv`, `cec-utils`, `i2c-tools`), enables
I2C, adds your user to the `input`/`i2c`/`video`/`gpio` groups, allows a
passwordless clean shutdown (for the power button), creates a Python virtual
environment, installs the Python dependencies, copies the example mapping, and
registers a systemd service so the hub starts automatically on boot.

> The Python packages it installs (from `requirements.txt`) are: `evdev` (QR
> scanner), `adafruit-blinka` + `adafruit-circuitpython-pn532` (NFC reader),
> and `gpiozero` (LED + button). To install them manually instead:
> `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

### 4. Point the code at your QR scanner

With the scanner plugged in, list the input devices:

```bash
ls /dev/input/by-id/
```

Find the entry for your scanner (often ends in `-event-kbd`) and set it via an
environment variable (or edit `QR_SCANNER_DEVICE` in `src/config.py`):

```bash
export QR_SCANNER_DEVICE=/dev/input/by-id/usb-<your-scanner>-event-kbd
```

### 5. Verify the build with the self-test

```bash
source venv/bin/activate
python main.py --selftest
```

This independently probes the mapping file, `mpv`, HDMI-CEC, the QR scanner
device, the LED (it blinks it — watch for the flash), the power button, and the
PN532, and prints a `PASS`/`FAIL` report. Fix anything marked `FAIL` before
continuing.

### 6. Log out / reboot, then start the hub

The new group memberships take effect after a fresh login:

```bash
sudo reboot
# after it comes back up:
sudo systemctl start pixelpostman      # (it also auto-starts on every boot)
sudo systemctl status pixelpostman     # check it's running
journalctl -u pixelpostman -f          # watch the logs live
```

---

## Add your content

All content lives in the `content/` folder, and the file `config/mapping.json`
ties each QR code / NFC tag to what should play. (Both are kept out of git —
they're your personal media.)

### The mapping file

Copy the template (the install script does this for you) and edit it:

```bash
cp config/mapping.example.json config/mapping.json
nano config/mapping.json
```

```json
{
  "qr": {
    "BOOK-PAGE-01": { "type": "video", "path": "stories/page01.mp4" }
  },
  "nfc": {
    "04A3B2C1D2E380": {
      "type": "slideshow",
      "folder": "trips/venice",
      "video":  "trips/venice/clip.mp4"
    }
  }
}
```

- `type: "video"` → plays the single file at `path`.
- `type: "slideshow"` → shows every photo in `folder`, then the optional
  closing `video`.
- All paths are relative to `content/`.
- Edits take effect on the next scan — no restart needed.

Then drop your media into `content/` to match (e.g.
`content/stories/page01.mp4`, `content/trips/venice/*.jpg`). Optionally add
`content/idle.png` to use as the idle/attract screen shown between plays.

### Make a QR book page

Print a QR code that encodes a **short, unique string** (e.g. `BOOK-PAGE-07`) —
any free QR generator works — and stick it on a book page. Add a matching entry
under `"qr"` and drop the video in `content/`.

### Make an NFC postcard

Stick an NTAG213/215 sticker on the back of a postcard. You only need the tag's
**UID** (not anything written to it). To find the UID, run the hub, tap the tag
on the reader, and read it from the logs:

```bash
journalctl -u pixelpostman -f
# tap the postcard — you'll see:  NFC tag scanned: 04A3B2C1D2E380
```

Add that UID under `"nfc"` in the mapping, with the photos/clip in `content/`,
and you're done.

---

## How it works

```
 QR scanner (USB, HID)                   PN532 NFC reader (I2C)
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
                   single playback worker
        (LED feedback -> wake TV -> play -> idle screen)
                       /        \
                      v          v
              tv_control.py    player.py
            (HDMI-CEC: wake TV,  (mpv: video / slideshow,
             switch input)        plus the looping idle screen)
                           |
                           v
                      Television
```

- **QR scanner**: a standard HID scanner that "types" the QR payload + Enter.
  `qr_listener.py` reads the raw input device, so it works headless.
- **NFC reader**: a PN532 on I2C. Each postcard has a cheap NFC sticker;
  `nfc_listener.py` reports its UID once per placement (no looping while it
  rests on the reader).
- **Content mapping**: `config/mapping.json` ties a code/UID to an action;
  it hot-reloads when you edit it.
- **TV control**: `tv_control.py` uses HDMI-CEC to wake the TV and switch
  input — sent at most once per window, in the background, so playback is never
  blocked on a slow TV.
- **Playback**: `player.py` uses `mpv` for fullscreen video and slideshows. A
  single worker serializes everything, so a QR scan and an NFC tap can never
  start two players at once.
- **Idle screen**: a looping `content/idle.png` (if present) shows whenever
  nothing is playing, so the child never sees a Linux console.
- **Feedback LED** (required): blinks to confirm a scan, stays on while
  playing, flashes fast on an unknown code / missing file.
- **Safe shutdown** (required): the power button triggers a clean shutdown.

For the full architecture, design decisions, and project scope, see
[docs/DESIGN.md](docs/DESIGN.md).

## Repository structure

```
pixel-postman/
├── main.py                       # entry point (run the hub, or --selftest)
├── requirements.txt              # Raspberry Pi runtime dependencies
├── requirements-dev.txt          # test/lint dependencies
├── src/
│   ├── config.py                 # paths, pins and tunable settings
│   ├── content_mapper.py         # reads mapping.json, resolves actions
│   ├── player.py                 # mpv wrapper (video + slideshow + idle)
│   ├── tv_control.py             # HDMI-CEC wrapper
│   ├── qr_listener.py            # reads the HID barcode scanner
│   ├── nfc_listener.py           # reads the PN532 NFC reader
│   ├── feedback.py               # LED feedback
│   ├── power.py                  # safe-shutdown power button
│   └── selftest.py               # on-Pi bring-up diagnostics
├── config/
│   └── mapping.example.json      # template — copy to mapping.json and edit
├── scripts/
│   ├── install.sh                # one-time setup on the Pi
│   └── pixelpostman.service      # systemd unit for auto-start on boot
├── docs/DESIGN.md                # architecture, decisions, scope
├── tests/                        # unit tests (run on a dev machine / CI)
├── .github/workflows/ci.yml      # CI: lint + tests on push / PR
└── content/                      # your photos/videos go here (not tracked in git)
```

## Local feedback & power resilience

The feedback LED and power button are **required** parts of the appliance, not
optional add-ons: the hub refuses to start if either can't be initialized (run
`python main.py --selftest` to diagnose). Once running, individual runtime LED
glitches are swallowed so they can never interrupt playback.

### Feedback LED

| State | LED behaviour |
| --- | --- |
| Idle / ready | off |
| Scan/tap acknowledged | two quick blinks |
| Content playing | steady on |
| Unknown code / missing media | rapid burst of blinks |

### Safe shutdown

Unclean shutdowns are the number-one cause of SD-card corruption on a Pi. Two
layers protect against it:

1. **Soft power button** (GPIO26) — hold ~2s to shut down cleanly. The install
   script adds a passwordless `sudo shutdown` rule so this works without
   running the hub as root.
2. **Read-only / overlay root filesystem** (recommended) — enable via
   `sudo raspi-config` → *Performance* → *Overlay File System*. Then even a
   hard power cut can't corrupt the OS. Keep `content/` and
   `config/mapping.json` on a writable partition / USB SSD if you update media
   in place.

The hub also handles `SIGTERM`/`SIGINT` (so `systemctl stop` and Ctrl+C) by
stopping mpv and releasing the GPIO cleanly.

## Development & tests

The Raspberry Pi hardware libraries are imported lazily, so the code can be
imported and unit-tested on any machine — no Pi required:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Continuous integration (`.github/workflows/ci.yml`) runs the linter and the
full test suite on every push and pull request to `main`, across Python 3.9 and
3.11 (matching Raspberry Pi OS).

## Troubleshooting

- **Self-test shows a `FAIL`** — start there; the message tells you what's
  missing (a package, a wrong device path, or unconnected hardware).
- **QR scanner not found** — recheck `QR_SCANNER_DEVICE` against
  `ls /dev/input/by-id/`, and make sure you logged out/in after `install.sh`
  (for the `input` group).
- **NFC reader not detected** — confirm the module is set to **I2C** mode, then
  run `sudo i2cdetect -y 1` (the PN532 usually shows at address `0x24`).
- **TV won't wake** — make sure HDMI-CEC is enabled in the TV's settings (it
  has a brand-specific name), or use the smart-plug + IR-blaster fallback.
- **Video won't show on Pi OS Lite** — the code renders via DRM/KMS by default;
  if your setup differs, override `MPV_VIDEO_OUTPUT` / `MPV_GPU_CONTEXT`.

## Notes

- Everything runs locally — no internet connection or cloud account is required
  for playback once content is on the Pi's storage.
- For travel, the same Pi (or a smaller Pi Zero 2 W running the same code) can
  be pre-loaded with content and plugged into any HDMI-CEC TV (hotel, rental).
- This is a community DIY project — improvements and pull requests are welcome.

## License

Released under the [MIT License](LICENSE) — free to use, build, copy, modify,
and share. Provided as-is, with no warranty.
