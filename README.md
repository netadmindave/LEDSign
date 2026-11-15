# LED Sign Studio

A clean, private replacement for the **CoolLED1248** app for CoolLEDX-family Bluetooth LED signs
(tested target: 16×64 7-colour panel, board `16x64SRGB_BK_V1.3`).

* **Library** – 100 built-in animations (Halloween, holidays, reading, optics — including meme-style ones), live previews, favourites,
  one-tap **Show**, adjustable frame time, "Edit a copy".
* **Text** – type, pick a colour (or rainbow), choose still/scroll/snow/laser, live preview.
* **Draw** – 64×16 pixel editor with frames, onion skin, shift tools, save to *My Creations*.
* **Import** – any image or animated GIF, auto-scaled and reduced to the sign's 7 colours.
* **Sign** – scan / connect / auto-reconnect, brightness, display on/off.

**Privacy:** no internet permission, no ads, analytics, accounts, microphone, camera or storage access.

## Build
Every push builds `LedSignStudio.apk` in GitHub Actions (Actions → latest run → Artifacts).

## Protocol
Implements the CoolLEDX ("1248") protocol: service `FFF0`, characteristic `FFF1`,
frames `01 | escape(len16 + payload) | 03`, 128-byte chunks with XOR checksum, 3 colour bit-planes,
column-major. Based on the open-source work in `UpDryTwist/coolledx-driver` and `oe7set/CoolLedDiy`.
CoolLEDM/U/UX signs use a different (LZSS + CRC) protocol and are shown but not supported yet.

## Regenerating the animation library
`tools/anim/export.py <outdir>` writes `animations.json` (copy into `app/src/main/assets/`) plus GIF previews.
