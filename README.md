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

## macOS system-level daemon

Runs in the background (no terminal needed) and adds haptics for **all apps**, not just the browser.

### Events

| Action | Waveform |
|---|---|
| Left click | `subtle_collision` |
| Right click | `knock` |
| Scroll to edge | `sharp_collision` |
| Incoming call (iPhone Continuity / FaceTime) | `ringing` |

### Installation

**1. Install dependencies**
```bash
pip install pyobjc-framework-Quartz requests --break-system-packages
```

**2. Run install script**
```bash
bash os-haptics/install.sh
```

This registers a launchd service that starts automatically on every login.

**3. Grant Accessibility permission**

The daemon needs Accessibility to monitor global mouse events. macOS requires two separate entries:

- **`python3.13`** (for running interactively from terminal)
  - System Settings → Privacy & Security → Accessibility → `+`
  - Press **Cmd+Shift+G** → paste `/opt/homebrew/bin`
  - Drag `python3` onto the list (the `+` picker greys out symlinks — drag & drop works)

- **`Python.app`** (for launchd background service)
  - System Settings → Privacy & Security → Accessibility → `+`
  - Press **Cmd+Shift+G** → paste:
    `/opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/Resources/`
  - Select `Python.app` and click Open

**4. Restart the daemon**
```bash
launchctl unload ~/Library/LaunchAgents/com.mxmaster4.haptics.plist
launchctl load -w ~/Library/LaunchAgents/com.mxmaster4.haptics.plist
```

**5. Verify**
```bash
tail -f /tmp/mxmaster4-haptics.log
```
You should see `Running. Press Ctrl+C to stop.` with no errors.

### Daemon management

```bash
# Stop
launchctl unload ~/Library/LaunchAgents/com.mxmaster4.haptics.plist

# Start
launchctl load -w ~/Library/LaunchAgents/com.mxmaster4.haptics.plist

# Remove completely
launchctl unload ~/Library/LaunchAgents/com.mxmaster4.haptics.plist
rm ~/Library/LaunchAgents/com.mxmaster4.haptics.plist
```

---

## Troubleshooting

**No haptics / red dot in popup**
- Make sure Logi Options+ is running
- Check HapticWebPlugin is active (green in Logi Options+)
- Run in terminal: `curl -X POST -d '' https://local.jmw.nz:41443/haptic/sharp_collision` — if you feel it, the plugin works fine

**Haptics fire too often on hover**
- Increase `HOVER_THROTTLE_MS` in `content.js` (default: `120`)
