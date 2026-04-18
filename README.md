# MX Master 4 Haptic Extension

Browser extension that adds haptic feedback to clicks and hovers on every website, using the Logitech MX Master 4 haptic motor.

## Requirements

- Logitech MX Master 4
- [Logi Options+](https://www.logitech.com/software/logi-options-plus.html)
- [HapticWebPlugin](https://marketplace.logi.com/plugin/HapticWeb/en) installed in Logi Options+

## How it works

The extension connects to a local server (`https://local.jmw.nz:41443`) provided by HapticWebPlugin and triggers waveforms on:

- **Click** (`mousedown`) → `subtle_collision`
- **Hover** over buttons, links, inputs → `damp_collision` (throttled to 120ms)

It uses WebSocket for low latency with automatic fallback to HTTP fetch.

## Installation

### Step 1 — Install HapticWebPlugin

1. Open **Logi Options+**
2. Go to your MX Master 4 → **Haptic Feedback** → **Manage Plugins**
3. Find **HapticWeb** in the marketplace and install it
4. Verify it's active (green dot)

### Step 2 — Install the browser extension

#### Chrome / Edge / Brave

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `mxmaster4-haptic-extension` folder

#### Firefox

1. Go to `about:debugging`
2. Click **This Firefox**
3. Click **Load Temporary Add-on**
4. Select the `manifest.json` file inside the folder

> Note: Firefox temporary add-ons are removed on browser restart. For permanent installation, the extension would need to be signed by Mozilla.

### Step 3 — Test

Click the extension icon in your toolbar — it should show a green dot and `Connected`. Browse any website and feel haptics on clicks and hovers.

## Waveforms

All 15 available waveforms from the MX Master 4:

| Category | Waveforms |
|---|---|
| Precision | `sharp_collision`, `damp_collision`, `subtle_collision`, `damp_state_change` |
| Progress | `sharp_state_change`, `completed`, `mad`, `firework`, `happy_alert`, `wave`, `angry_alert`, `square` |
| Events | `knock`, `ringing`, `jingle` |

To change the waveform for clicks or hovers, edit `content.js`:

```js
// click
trigger('subtle_collision');

// hover
trigger('damp_collision');
```

## Troubleshooting

**No haptics / red dot in popup**
- Make sure Logi Options+ is running
- Check HapticWebPlugin is active (green in Logi Options+)
- Run in terminal: `curl -X POST -d '' https://local.jmw.nz:41443/haptic/sharp_collision` — if you feel it, the plugin works fine

**Haptics fire too often on hover**
- Increase `HOVER_THROTTLE_MS` in `content.js` (default: `120`)
