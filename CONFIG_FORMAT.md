# Arduino MIDI Controller — Config Format Reference

Version 1.0  
File format: JSON (`.json`)

---

## Overview

A layout file fully describes one controller: its hardware settings, visual
theme, and every page of controls. The code generator reads it and produces
a ready-to-compile Arduino sketch. You never edit the `.ino` by hand.

```
my_layout.json  →  generate.py  →  firmware/firmware.ino  →  (compile + flash)
```

**File structure at a glance:**

```json
{
  "device":  { ... },   // hardware: screen, touch, MIDI
  "theme":   { ... },   // default colors for all controls
  "pages":   [ ... ]    // one or more pages of controls
}
```

---

## `device`

Global hardware settings. These rarely change between layouts.

```json
"device": {
  "name": "DJ Controller",

  "screen": {
    "rotation": 1,
    "width":    320,
    "height":   240
  },

  "touch": {
    "ts_left":      904,
    "ts_right":     214,
    "ts_top":       207,
    "ts_bottom":    832,
    "min_pressure": 8,
    "max_pressure": 1000,
    "pin_xp":       8,
    "pin_xm":       "A2",
    "pin_yp":       "A3",
    "pin_ym":       9,
    "resistance":   300
  },

  "midi": {
    "channel": 1,
    "baud":    31250
  }
}
```

### `screen.rotation`

Controls display orientation. Use the value that matches how the board
sits in your setup:

| Value | Orientation              | Flip 180°?       |
|-------|--------------------------|------------------|
| `0`   | Portrait, USB at top     | use `2` to flip  |
| `1`   | Landscape, USB at right  | use `3` to flip  |
| `2`   | Portrait, USB at bottom  | —                |
| `3`   | Landscape, USB at left   | —                |

> **To flip 180°:** just change `1` → `3` (or `0` → `2`). Everything else
> stays the same — touch calibration and pixel coordinates auto-adapt.

### `touch` calibration values

Run the sketch once with `CALIBRATE_MODE 1` to get your board's exact
values. Every Keyes/MCUFRIEND shield is slightly different.

| Key            | What it is                                      |
|----------------|-------------------------------------------------|
| `ts_left`      | Raw ADC value when touching the LEFT edge       |
| `ts_right`     | Raw ADC value when touching the RIGHT edge      |
| `ts_top`       | Raw ADC value when touching the TOP edge        |
| `ts_bottom`    | Raw ADC value when touching the BOTTOM edge     |
| `min_pressure` | Ignore touches below this Z value (noise filter)|
| `max_pressure` | Ignore touches above this Z value (noise filter)|
| `pin_xp/xm/yp/ym` | Touch resistor pins — do not change unless touch is broken |
| `resistance`   | Panel resistance in ohms — 300 is correct for most shields  |

### `midi.channel`

1–16. All controls on a layout share one MIDI channel. If you need
different controls on different channels, that is a planned future feature.

### `midi.baud`

Always `31250`. This is the MIDI specification baud rate, required by
Hairless MIDI. Do not change this.

---

## `theme`

Default colors used by any control that does not define its own `colors`
block. All colors are `"#RRGGBB"` hex strings. The generator converts them
to RGB565 automatically.

```json
"theme": {
  "background":           "#111318",

  "button_bg":            "#1A1F2E",
  "button_border":        "#3A4055",
  "button_label":         "#C0C8D8",
  "button_active_bg":     "#003800",
  "button_active_border": "#00E000",
  "button_active_label":  "#00E000",

  "toggle_on_bg":         "#003800",
  "toggle_on_border":     "#00E000",
  "toggle_on_label":      "#00FF00",
  "toggle_off_bg":        "#1A1F2E",
  "toggle_off_border":    "#3A4055",
  "toggle_off_label":     "#C0C8D8",

  "slider_track":         "#1A2030",
  "slider_fill":          "#005070",
  "slider_label":         "#C0C8D8",
  "slider_value":         "#00C0FF",

  "nav_bg":               "#0D1018",
  "nav_border":           "#3A4055",
  "nav_active":           "#00C0FF",
  "nav_inactive":         "#3A4055",

  "status_bg":            "#0A0C10",
  "status_text":          "#506070"
}
```

---

## `pages`

An array of page objects. If there is more than one page, a navigation bar
appears at the bottom of the screen showing dot indicators. Tap any dot to
jump to that page directly, or swipe left/right.

```json
"pages": [
  {
    "id":       "deck",
    "label":    "Deck",
    "controls": [ ... ]
  },
  {
    "id":       "fx",
    "label":    "FX",
    "controls": [ ... ]
  }
]
```

| Key        | Required | Description                                      |
|------------|----------|--------------------------------------------------|
| `id`       | yes      | Unique string identifier. Used in logs and by future GUI tools. No spaces. |
| `label`    | yes      | Short text shown in the nav bar dot (keep under 6 chars) |
| `controls` | yes      | Array of control objects (see below)             |

### Navigation bar

The nav bar is 20px tall and appears at the very bottom of the screen when
there are 2 or more pages. Controls should not extend into the bottom 20px
(`y + h <= screen_height - 20`) when multi-page layouts are used, or they
will overlap the nav bar.

> **Single-page layouts:** the nav bar is hidden and you get the full screen.

---

## Controls

Every control shares a set of common fields, plus type-specific fields.

### Common fields (all control types)

| Field           | Type    | Required | Description                              |
|-----------------|---------|----------|------------------------------------------|
| `id`            | string  | yes      | Unique within the page. No spaces.       |
| `type`          | string  | yes      | `"button"`, `"toggle"`, or `"slider"`   |
| `label`         | string  | yes      | Text displayed on the control            |
| `label_size`    | int     | yes      | Adafruit GFX text scale: 1=small 2=medium 3=large 4=xlarge |
| `x`             | int     | yes      | Left edge in pixels from screen left     |
| `y`             | int     | yes      | Top edge in pixels from screen top       |
| `w`             | int     | yes      | Width in pixels                          |
| `h`             | int     | yes      | Height in pixels                         |
| `corner_radius` | int     | no       | Rounded corner radius. `0` = square. Default: `8` |
| `midi`          | object  | yes      | MIDI action (see per-type below)         |
| `feedback`      | object  | no       | Listen for PC → Arduino CC to update visual state |
| `colors`        | object  | no       | Per-control color overrides              |

### Pixel coordinate system

```
(0,0) ──────────────────── (319,0)
  │                              │
  │   your controls go here      │
  │                              │
(0,219) ─────────────── (319,219)
(0,220) ── nav bar (20px) ─────── (319,239)
```

Origin is always top-left regardless of rotation. The generator handles
the physical rotation — you always design in the same coordinate space.

**Tip:** sketch your layout on graph paper at 320×220 before writing JSON.

---

## Control type: `button`

Momentary press. Sends a CC value on press, optionally 0 on release.

```json
{
  "id":           "cue",
  "type":         "button",
  "label":        "CUE",
  "label_size":   2,
  "x": 10,  "y": 10,  "w": 90,  "h": 55,
  "corner_radius": 8,

  "midi": {
    "type":         "cc",
    "cc":           23,
    "value":        127,
    "send_release": true
  },

  "feedback": {
    "cc":        21,
    "value_on":  1,
    "value_off": 0
  },

  "colors": {
    "idle_bg":       "#1A1F2E",
    "idle_border":   "#3A4055",
    "idle_label":    "#8090A0",
    "active_bg":     "#003800",
    "active_border": "#00E000",
    "active_label":  "#00FF00"
  }
}
```

### `midi` fields for button

| Field          | Required | Description                                        |
|----------------|----------|----------------------------------------------------|
| `type`         | yes      | Always `"cc"` for now                             |
| `cc`           | yes      | CC number 0–127                                   |
| `value`        | yes      | CC value sent on press (0–127). Usually 127.      |
| `send_release` | no       | If `true`, sends `value=0` when finger lifts. Default: `false` |

### `feedback` fields for button

When the PC sends back a CC, the button visually activates (turns to active
colors) without the user pressing it. Useful for showing DAW state.

| Field       | Required | Description                                          |
|-------------|----------|------------------------------------------------------|
| `cc`        | yes      | Which CC# to listen for from PC                     |
| `value_on`  | no       | CC value that activates the button. Default: `127`  |
| `value_off` | no       | CC value that deactivates. Default: `0`             |

### `colors` for button

All optional — omit any to use the theme default.

| Key              | When used          |
|------------------|--------------------|
| `idle_bg`        | not pressed        |
| `idle_border`    | not pressed        |
| `idle_label`     | not pressed        |
| `active_bg`      | pressed / active   |
| `active_border`  | pressed / active   |
| `active_label`   | pressed / active   |

---

## Control type: `toggle`

Latching. First tap → ON, second tap → OFF. State lives on the Arduino.

```json
{
  "id":           "loop",
  "type":         "toggle",
  "label":        "LOOP",
  "label_size":   2,
  "x": 10,  "y": 10,  "w": 90,  "h": 55,
  "corner_radius": 8,

  "midi": {
    "type":      "cc",
    "cc":        22,
    "value_on":  127,
    "value_off": 0
  },

  "colors": {
    "on_bg":      "#003800",
    "on_border":  "#00C000",
    "on_label":   "#00FF00",
    "off_bg":     "#1A1F2E",
    "off_border": "#3A4055",
    "off_label":  "#8090A0"
  }
}
```

### `midi` fields for toggle

| Field       | Required | Description                                    |
|-------------|----------|------------------------------------------------|
| `type`      | yes      | Always `"cc"`                                 |
| `cc`        | yes      | CC number 0–127                               |
| `value_on`  | yes      | Sent when toggled ON                          |
| `value_off` | yes      | Sent when toggled OFF                         |

### `colors` for toggle

| Key          | When used  |
|--------------|------------|
| `on_bg`      | state = ON |
| `on_border`  | state = ON |
| `on_label`   | state = ON |
| `off_bg`     | state = OFF|
| `off_border` | state = OFF|
| `off_label`  | state = OFF|

---

## Control type: `slider`

Sends continuous CC values 0–127 as you drag. Can be horizontal or vertical.

```json
{
  "id":           "volume",
  "type":         "slider",
  "label":        "VOL",
  "label_size":   1,
  "x": 10,  "y": 10,  "w": 200,  "h": 40,
  "orientation":  "horizontal",
  "corner_radius": 6,

  "midi": {
    "type":      "cc",
    "cc":        7,
    "value_min": 0,
    "value_max": 127
  },

  "default_value": 100,

  "feedback": { "cc": 7 },

  "colors": {
    "track":      "#1A2030",
    "fill":       "#005070",
    "label":      "#8090A0",
    "value_text": "#00C0FF"
  }
}
```

### `midi` fields for slider

| Field       | Required | Description                                    |
|-------------|----------|------------------------------------------------|
| `type`      | yes      | Always `"cc"`                                 |
| `cc`        | yes      | CC number 0–127                               |
| `value_min` | yes      | CC value at the left/bottom of the slider     |
| `value_max` | yes      | CC value at the right/top of the slider       |

### `orientation`

| Value          | Drag direction                        |
|----------------|---------------------------------------|
| `"horizontal"` | left = value_min, right = value_max  |
| `"vertical"`   | bottom = value_min, top = value_max  |

### `default_value`

CC value (0–127) the slider starts at on boot. Default: `0`.

### `feedback` for slider

If the PC sends back the same CC, the slider position updates visually.
Only needs `"cc"` — the value is used directly as the new position.

```json
"feedback": { "cc": 7 }
```

### `colors` for slider

| Key          | What it colors                                  |
|--------------|-------------------------------------------------|
| `track`      | the unfilled background of the slider track    |
| `fill`       | the filled portion up to the current value     |
| `label`      | the label text above the slider                |
| `value_text` | the numeric value shown inside the slider      |

---

## Color format

All colors are `"#RRGGBB"` strings. The generator converts them to RGB565
(16-bit) for the TFT library automatically.

```json
"#FF0000"   → red
"#00FF00"   → green
"#0000FF"   → blue
"#111318"   → very dark blue-grey (good background)
"#C0C8D8"   → light blue-grey (good default text)
```

You can use any HTML color picker to find values.

> **RGB565 rounding:** the TFT display uses 16-bit color, so colors are
> rounded to the nearest representable value. Very subtle color differences
> (e.g. `#010101` vs `#020202`) may appear identical on screen.

---

## Complete minimal example

The smallest valid layout — one page, one button:

```json
{
  "device": {
    "name": "My Controller",
    "screen":  { "rotation": 1, "width": 320, "height": 240 },
    "touch":   { "ts_left": 904, "ts_right": 214, "ts_top": 207, "ts_bottom": 832,
                 "min_pressure": 8, "max_pressure": 1000,
                 "pin_xp": 8, "pin_xm": "A2", "pin_yp": "A3", "pin_ym": 9, "resistance": 300 },
    "midi":    { "channel": 1, "baud": 31250 }
  },
  "theme": {
    "background": "#111318",
    "button_bg": "#1A1F2E", "button_border": "#3A4055", "button_label": "#C0C8D8",
    "button_active_bg": "#003800", "button_active_border": "#00E000", "button_active_label": "#00E000",
    "toggle_on_bg": "#003800", "toggle_on_border": "#00E000", "toggle_on_label": "#00FF00",
    "toggle_off_bg": "#1A1F2E", "toggle_off_border": "#3A4055", "toggle_off_label": "#C0C8D8",
    "slider_track": "#1A2030", "slider_fill": "#005070", "slider_label": "#C0C8D8", "slider_value": "#00C0FF",
    "nav_bg": "#0D1018", "nav_border": "#3A4055", "nav_active": "#00C0FF", "nav_inactive": "#3A4055",
    "status_bg": "#0A0C10", "status_text": "#506070"
  },
  "pages": [
    {
      "id": "main", "label": "Main",
      "controls": [
        {
          "id": "btn1", "type": "button", "label": "GO",  "label_size": 3,
          "x": 60, "y": 60, "w": 200, "h": 100, "corner_radius": 12,
          "midi": { "type": "cc", "cc": 10, "value": 127, "send_release": false }
        }
      ]
    }
  ]
}
```

---

## Tips for designing layouts

- **Sketch first.** Draw your 320×220 grid on paper, place your buttons,
  measure pixel positions, then type the JSON.
- **Label sizes:** size 1 = tiny (debug), size 2 = readable for normal buttons,
  size 3 = large (main action button), size 4 = very large (one big label per screen).
- **Nav bar clearance:** keep all controls above y=220 when using multiple pages.
- **Avoid overlapping controls.** The generator does not detect overlaps —
  overlapping controls will both respond to the same touch.
- **MIDI CC numbers:** standard assignments to be aware of:
  - CC 7 = Channel Volume
  - CC 10 = Pan
  - CC 64 = Sustain Pedal
  - CC 1 = Modulation
  - CC 120–127 = reserved channel mode messages — avoid these.
  - Use CC 20–119 freely for custom mappings.
