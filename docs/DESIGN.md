# PixelPostman — Technical Design & Scope

This document describes the overall technical design of PixelPostman: what it
is, how the pieces fit together, the decisions behind them, and what is in and
out of scope for the current prototype.

## 1. Product summary

PixelPostman is a **locked-down, content-controlled media appliance** for a
young child, built on a single Raspberry Pi. A physical object — a QR code on a
book page, or an NFC sticker on a travel postcard — is presented to a sensor,
and the matching **local** media plays fullscreen on the living-room TV.

There is no remote in the child's hands, no app, no algorithmic feed, no
autoplay queue, and no internet dependency for playback. The only content that
exists is what a parent has deliberately placed on the device's storage, and
the only way to trigger it is a pre-approved physical object.

The emotional wedge is **personal/curated content** — your own trip photos and
videos, a grandparent reading a story — surfaced through tactile objects.

## 2. Scope

### In scope (this prototype)
- Two input modalities: HID QR scanner (book) and PN532 NFC reader (postcards).
- A single mapping file (`config/mapping.json`) binding codes/UIDs to actions.
- Fullscreen playback of local **video** and **photo slideshows** (with an
  optional closing clip) via `mpv`.
- Automatic TV wake / input switch via HDMI-CEC.
- A persistent **idle screen** so a console is never visible.
- **Mandatory** local feedback LED and a **mandatory** soft power button for
  safe shutdown.
- Headless auto-start on boot (systemd), runnable on Raspberry Pi OS Lite.
- A `--selftest` bring-up mode, a unit-test suite, and CI.

### Explicitly out of scope (for now)
- Any cloud service, account, or network-delivered content.
- A content-authoring app / GUI (today the mapping is edited as JSON and media
  is copied into `content/` by hand). This is the most important *future* item.
- Monetization, licensing, and a content marketplace.
- Screen-time limits / scheduling (daily caps, quiet hours) — noted as a
  near-term roadmap item, not yet built.
- Industrial design / enclosure and a Compute-Module-based production board.

## 3. Architecture

```
 QR scanner (USB/BT, HID)              PN532 NFC reader (I2C)
        |                                      |
        v                                      v
  qr_listener.py (thread)             nfc_listener.py (thread)
        |  on_scan(code)                       |  on_scan(uid)
        +------------------+-------------------+
                           v
                    content_mapper.py
            (resolve code/UID -> action via mapping.json,
                 auto-reloads when the file changes)
                           |
                           v
                   _play_queue (queue.Queue)
                           |
                           v
                 playback worker (single thread)
        acknowledge LED -> wake TV (if needed) -> play -> idle
              /              |             |            \
             v               v             v             v
        feedback.py     tv_control.py   player.py     player.show_idle()
        (LED states)    (HDMI-CEC,      (mpv: video /  (looping idle image)
                         deduped/async)  slideshow)

        power.py (soft power button -> clean shutdown)  [runs alongside]
```

### Threading model
- **Two listener threads** (QR, NFC) only *produce* events; they never touch
  the screen directly.
- **One playback worker thread** consumes a `queue.Queue` and is the *only*
  code path that starts/stops `mpv`. This serialization is the key design
  decision: a QR scan and an NFC tap can never launch two players at once.
- `player.py` additionally guards its current process with a lock, so even the
  worker's stop-then-start is atomic.

### State / playback lifecycle
1. On startup the worker shows the idle screen and sets the LED to *ready*.
2. A scan enqueues an action (or `None` if unmapped).
3. The worker: blinks *acknowledge* → wakes the TV if not woken recently →
   plays the mapped content → sets the LED *steady on*.
4. When the content process exits on its own, the worker detects
   `content_finished()` and returns to the idle screen + *ready* LED.
5. A new scan mid-playback simply stops the current process and starts the new
   one (interrupt-and-replace).

## 4. Components

| Module | Responsibility |
| --- | --- |
| `main.py` | Wiring, the playback worker, argument parsing (`--selftest`), signal handling, and mandatory-hardware startup checks. |
| `src/config.py` | All paths and tunables, each overridable via environment variable. |
| `src/content_mapper.py` | Loads `mapping.json`, resolves QR codes / NFC UIDs to actions, and hot-reloads when the file's mtime changes. |
| `src/qr_listener.py` | Reads the HID scanner from the raw input device (with `grab()`), decodes keystrokes (incl. Shift/case) into a code, fires `on_scan`. |
| `src/nfc_listener.py` | Polls the PN532; fires `on_scan` once per *presentation* (re-fires only after the tag is removed/swapped). |
| `src/player.py` | `mpv` wrapper: thread-safe video / slideshow playback, idle screen, DRM/KMS output for headless Lite. |
| `src/tv_control.py` | HDMI-CEC wake + active-source, de-duplicated and run in the background so playback is never gated on a slow TV. |
| `src/feedback.py` | **Required** LED feedback (ready / acknowledge / playing / error). |
| `src/power.py` | **Required** soft power button → clean shutdown. |
| `src/selftest.py` | Independent PASS/FAIL probes of every subsystem for bring-up. |

## 5. Data model

`config/mapping.json` is the single source of truth:

```json
{
  "qr":  { "BOOK-PAGE-01": { "type": "video", "path": "stories/page01.mp4" } },
  "nfc": { "04A3B2C1D2E380": { "type": "slideshow",
                               "folder": "trips/venice",
                               "video":  "trips/venice/clip.mp4" } }
}
```

- Action `type: "video"` → plays `path`.
- Action `type: "slideshow"` → plays every image in `folder`, then the optional
  closing `video`, as a single `mpv` playlist.
- Paths are relative to `content/` (or absolute).
- NFC UIDs are matched case-insensitively (stored uppercase); they are the
  full factory UID hex (NTAG213/215 are 7 bytes, e.g. `04A3B2C1D2E380`).

## 6. Key design decisions

- **Single playback worker + queue.** Eliminates the race between the two
  listeners and makes "interrupt current, play next" deterministic.
- **Slideshow as one mpv playlist.** Avoids a blocking `wait()` on a listener
  thread and the flicker/loop bug of launching a second process for the
  closing clip.
- **Fire-once-per-presentation NFC.** A postcard left resting on the reader
  must not loop; re-triggering requires lifting it off and back on.
- **De-duplicated, async CEC.** CEC is slow and flaky; re-sending it on every
  scan added latency a child reads as "broken". We send it at most once per
  `CEC_RESEND_SECONDS`, in the background.
- **DRM/KMS video output.** Raspberry Pi OS Lite has no compositor, so `mpv`
  must render straight to the framebuffer.
- **Idle screen always present.** The child should never see a Linux console.
- **Mandatory LED + power button.** For an appliance a child uses unattended,
  instant feedback and corruption-safe shutdown are not optional. The hub
  fails fast if they can't be initialized.
- **Lazy hardware imports.** `gpiozero`, `board`/`busio`, `adafruit_pn532` and
  `evdev` are imported only when used, so the whole codebase is importable and
  unit-testable on a developer machine and in CI without a Pi.
- **Configuration via env vars.** The same code runs on a laptop (tests) and on
  the Pi without source edits.

## 7. Reliability & power resilience

- **Safe shutdown** via the GPIO power button (passwordless `sudo shutdown`).
- **Overlay/read-only root filesystem** (recommended) so a hard power cut can't
  corrupt the OS; keep media on a writable partition / USB SSD.
- **Clean signal handling** (`SIGTERM`/`SIGINT`) stops `mpv` and releases GPIO.
- **systemd** restarts the hub on failure and starts it on boot.
- **Graceful degradation** of non-mandatory pieces (e.g. a missing idle image
  yields a black screen rather than a crash).

## 8. Testing & CI

- Pure logic is factored out of hardware I/O (`_consume`, `_decide`,
  `play_action`, `_process`, `ensure_on`) so it can be tested directly.
- The `pytest` suite mocks `subprocess`/GPIO and injects fakes; it runs with no
  hardware attached.
- GitHub Actions runs `ruff` plus the suite on Python 3.9 and 3.11 for every
  push/PR to `main`.
- `python main.py --selftest` is the on-device counterpart for real-hardware
  bring-up.

## 9. Known limitations / next steps

- **Content authoring** is manual (JSON + file copy). A phone/web app to bind
  an object to media in ~60 seconds is the single highest-value next step.
- **No screen-time controls** yet (daily caps, quiet hours, auto-off).
- **End-to-end hardware validation** (real `mpv` on Lite, CEC across TV brands,
  PN532 read range, the LED/button wiring) still needs a pass on the Pi itself;
  the unit tests cover logic, not the physical I/O.
- **QR scanner ergonomics**: a handheld trigger-gun is acceptable for the
  prototype but not toddler-ideal; an NFC-first or embedded-imager form is the
  likely product direction.
