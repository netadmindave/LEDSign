# LED Sign Studio + Home Assistant integration

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


---

# Home Assistant integration (`coolledx_sign`)

Send warnings, status messages and animations to the sign from Home Assistant. It uses HA's own
Bluetooth stack, so a local adapter **or an ESPHome Bluetooth proxy** near the sign both work.
The transfer method is the same one the stock app uses (default MTU, 20-byte writes, per-chunk acks).
Each update connects, sends and disconnects, so the phone app can still use the sign in between.

## Install
1. HACS → ⋮ → *Custom repositories* → `https://github.com/netadmindave/LEDSign`, type *Integration* → install
   **CoolLEDX LED Sign**. (Or copy `custom_components/coolledx_sign` into `/config/custom_components/`.)
2. Restart Home Assistant. The sign is discovered automatically (*Settings → Devices & services*), or add
   **CoolLEDX LED Sign** by hand. Close the phone app first; password is `000000` unless you changed it.

## What you get
| Entity / action | Does |
|---|---|
| `light.*_display` | on/off + brightness |
| `select.*_animation` | pick any of the 100 animations |
| `button.*_show_idle_animation` | "all clear" animation |
| `coolledx_sign.show_warning` | ⚠ icon + red **WARNING** + scrolling message |
| `coolledx_sign.show_text` | status text: colour, icon (`warning` / `error` / `info` / `ok`), scroll / still |
| `coolledx_sign.show_animation` | by name, e.g. `Frequency Comb` |
| `coolledx_sign.show_idle` | date-aware: holiday season animations (Halloween all October, Thanksgiving week, Christmas, Hanukkah, Diwali, Easter, July 4th …), otherwise reading/optics |
| `coolledx_sign.set_reverse` | rotate the sign 180° |

Options (*Configure*): password, default scroll speed, large/small text, idle choice, mirror.

## Example automations

```yaml
# Warning while something is wrong
- alias: Sign - garage left open
  triggers:
    - trigger: state
      entity_id: cover.garage_door
      to: open
      for: "00:10:00"
  actions:
    - action: coolledx_sign.show_warning
      data:
        message: "Garage door open {{ relative_time(states.cover.garage_door.last_changed) }}"

# Status update
- alias: Sign - washer done
  triggers:
    - trigger: state
      entity_id: sensor.washer_state
      to: finished
  actions:
    - action: coolledx_sign.show_text
      data:
        message: "Laundry is done"
        icon: info
        color: cyan

# Back to a fun animation when nothing is wrong (and refresh it every morning)
- alias: Sign - all clear
  triggers:
    - trigger: state
      entity_id: binary_sensor.anything_wrong     # a template/group of your problem sensors
      to: "off"
    - trigger: time
      at: "07:30:00"
  conditions:
    - condition: state
      entity_id: binary_sensor.anything_wrong
      state: "off"
  actions:
    - action: coolledx_sign.show_idle
```

A handy "anything wrong" helper (Settings → Helpers → Template → Binary sensor):
`{{ is_state('cover.garage_door','open') or is_state('binary_sensor.water_leak','on') }}`

## Tests
`pytest` runs the integration inside Home Assistant against a simulated sign (`tests/`).
