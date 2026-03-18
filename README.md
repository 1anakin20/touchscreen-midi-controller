# Arduino MIDI Controller Toolkit

Generate and flash custom MIDI controller firmware from a JSON layout file.
No Arduino IDE needed after initial setup.

```
my_layout.json  →  generate.py  →  firmware.ino  →  flash.py  →  Arduino
```

---

## Files

| File                | Purpose                                              |
|---------------------|------------------------------------------------------|
| `my_layout.json`    | Your controller layout (edit this)                  |
| `generate.py`       | Converts JSON → Arduino .ino sketch                 |
| `flash.py`          | Generates + compiles + uploads in one command        |
| `CONFIG_FORMAT.md`  | Full documentation of every config option           |

---

## Quick start

### 1. Install arduino-cli (one time)

Download from https://arduino.github.io/arduino-cli/latest/installation/

Then run these once to install the board core and libraries:

```bash
arduino-cli core update-indexarduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib install "MCUFRIEND_kbv" "Adafruit GFX Library" "TouchScreen"
```

### 2. Edit your layout

Open `my_layout.json` and edit it. See `CONFIG_FORMAT.md` for every option.

**To flip the screen 180°:** change `"rotation": 1` to `"rotation": 3` in the
`device.screen` block.

**To change MIDI channel:** change `"channel": 1` in `device.midi`.

### 3. Flash

```bash
# Auto-detect Arduino port and flash
python flash.py --config my_layout.json

# Specify port manually
python flash.py --config my_layout.json --port COM3           # Windows
python flash.py --config my_layout.json --port /dev/cu.usbmodem14101  # Mac

# Just generate the .ino without flashing (useful for inspecting)
python flash.py --config my_layout.json --generate-only

# List connected Arduino boards
python flash.py --list-ports
```

The generated sketch is saved to `firmware/<config_name>/firmware.ino`.

---

## Calibrate touch (first time or after changing rotation)

1. Open `firmware/<name>/firmware.ino` in Arduino IDE
2. Change `#define CALIBRATE_MODE 0` to `1`
3. Upload, open Serial Monitor at 115200 baud
4. Tap each corner crosshair when prompted
5. Copy the four numbers back into your JSON config under `device.touch`
6. Regenerate and flash: `python flash.py --config my_layout.json`

---

## Control types

### Button (momentary)
Sends a CC value on press. Optionally sends 0 on release (`send_release: true`).
Can receive feedback from the PC to light up without being pressed.

### Toggle (latching)
Tap once → ON (sends `value_on`). Tap again → OFF (sends `value_off`).
State is kept on the Arduino.

### Slider
Drag to send CC values from `value_min` to `value_max`.
Supports `horizontal` or `vertical` orientation.
Can receive feedback from the PC to update its position.

---

## MIDI bridge setup

The Arduino Uno has no USB-MIDI. Use Hairless MIDI to bridge:

1. **Windows:** install loopMIDI → create a port named `Arduino MIDI`
   **Mac:** Audio MIDI Setup → IAC Driver → add a bus named `Arduino MIDI`

2. Open Hairless MIDI:
   - Serial port: your Arduino COM/USB port
   - MIDI out: `Arduino MIDI`
   - MIDI in: `Arduino MIDI` (for feedback from your DAW)
   - Edit → Preferences → Baud rate: **31250**

3. Connect in Hairless, then open VirtualDJ (or any DAW) and map
   `Arduino MIDI` as a controller device.

> ⚠️ Close Hairless MIDI before flashing. They share the serial port.

---

## Sharing layouts

A layout is just a `.json` file — share it like any other file.
Recipients need the same calibration values for their specific shield,
but everything else (controls, MIDI CCs, colors, pages) is portable.

---

## Planned features

- Visual GUI editor that reads/writes the same JSON format
- Multiple MIDI channels per layout
- Page-transition animations
- Swipe gesture navigation between pages
