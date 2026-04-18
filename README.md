# MX Master 4 Haptic Extension

Browser extension that adds configurable haptic feedback to web interactions, using the Logitech MX Master 4 haptic motor. Every event type has its own waveform, toggled and customized via a popup UI.

## Requirements

- Logitech MX Master 4
- [Logi Options+](https://www.logitech.com/software/logi-options-plus.html)
- [HapticWebPlugin](https://marketplace.logi.com/plugin/HapticWeb/en) installed in Logi Options+

## How it works

The extension injects a content script into every page. When a tracked event fires, it sends a waveform name to the background service worker via a persistent port connection. The service worker calls the local HapticWebPlugin API (`https://local.jmw.nz:41443/haptic/<waveform>`) which drives the haptic motor.

Settings are stored in `chrome.storage.local` and applied instantly — no page reload needed after changing them in the popup.

## Tracked events

| Event | Default waveform | Notes |
|---|---|---|
| Hover — link | `damp_collision` | Throttled to 1 per 120 ms |
| Hover — button / menu item / tab | `subtle_collision` | Throttled to 1 per 120 ms |
| Hover — input / select / textarea | `subtle_collision` | Off by default |
| Focus on form field | `subtle_collision` | |
| Form submit | `completed` | |
| Form validation error | `angry_alert` | |
| Slider drag | `damp_state_change` | Fires every 5% of range |
| CSS animation / transition end | `subtle_collision` | Throttled to 1 per element per 200 ms |
| Scroll to page edge | `sharp_collision` | Top or bottom 40 px, cooldown 600 ms |

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

> Note: Firefox temporary add-ons are removed on browser restart. For permanent installation the extension would need to be signed by Mozilla.

### Step 3 — Test

Click the extension icon — it should show a green dot and `Connected`. Browse any website and feel haptics on hover and click.

## Configuring waveforms

Click the extension icon to open the popup. Each event has an independent toggle and a waveform dropdown. Changes take effect immediately on all open tabs.

## Available waveforms

All 15 waveforms exposed by the MX Master 4:

| Category | Waveforms |
|---|---|
| Collision | `sharp_collision`, `damp_collision`, `subtle_collision` |
| State change | `damp_state_change`, `sharp_state_change` |
| Alerts | `completed`, `happy_alert`, `angry_alert`, `mad` |
| Rhythmic | `firework`, `wave`, `square`, `knock`, `ringing`, `jingle` |

---

## macOS system-level daemon

Runs in the background and adds haptics for **all apps**, not just the browser. The daemon skips haptics when a browser is in the foreground (the extension handles those).

### Events

| Action | Waveform |
|---|---|
| Left click | `subtle_collision` |
| Right click | `knock` |

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
You should see `Running.` with no errors.

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
- Test the plugin directly:
  ```bash
  curl -X POST -d '' https://local.jmw.nz:41443/haptic/sharp_collision
  ```
  If you feel it, the plugin works — the issue is in the extension.

**Waveform changes in popup don't take effect**
- Close and reopen the popup after changing a setting
- If still not working, refresh the tab (F5)

**Scroll haptic fires too often**
- Increase `SCROLL_EDGE_PX` in `content.js` (default: `40`) to require being closer to the edge before firing
- Increase `SCROLL_COOLDOWN_MS` (default: `600`) to add more time between triggers

**Hover haptic fires too often**
- Increase `HOVER_THROTTLE_MS` in `content.js` (default: `120`)
