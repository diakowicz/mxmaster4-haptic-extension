# MX Master 4 Haptic Extension

Haptic feedback for your Logitech MX Master 4 — both in the browser and system-wide on macOS.

## Requirements

- Logitech MX Master 4 with Bolt receiver
- [Logi Options+](https://www.logitech.com/software/logi-options-plus.html)
- [HapticWeb plugin](https://marketplace.logi.com/plugin/HapticWeb/en) installed in Logi Options+

The HapticWeb plugin exposes a local HTTPS server (`https://local.jmw.nz:41443`) that this project connects to for triggering waveforms.

---

## Part 1 — Browser Extension

Adds haptics to every website: clicks, right-clicks, hovering interactive elements, slider changes, and animation completions.

### Events

| Action | Waveform |
|---|---|
| Left click | `subtle_collision` |
| Right click | `knock` |
| Hover (buttons, links, inputs) | `damp_collision` |
| Slider moved every 5% | `sharp_state_change` |
| CSS animation end | `damp_state_change` |

### Installation

#### Chrome / Edge / Brave

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** and select this folder

#### Firefox

1. Go to `about:debugging` → **This Firefox**
2. Click **Load Temporary Add-on** and select `manifest.json`

> Firefox temporary add-ons are removed on restart. For permanent installation, the extension needs to be signed by Mozilla.

### Test

Click the extension icon — it should show a green dot and `Connected`. Browse any site and feel haptics on clicks and hovers.

---

## Part 2 — macOS System Daemon

Runs in the background (no terminal needed) and adds haptics for **all apps**, not just the browser.

### Events

| Action | Waveform |
|---|---|
| Left click | `subtle_collision` |
| Right click | `knock` |
| Window hover (cursor enters a new window) | `damp_collision` |
| Long press (≥ 0.5s) | `jingle` |

Browser windows are excluded from click and hover haptics to avoid doubling up with the browser extension.

### Installation

**1. Install Python dependencies**

```bash
pip install pyobjc-framework-Quartz requests --break-system-packages
```

**2. Run the install script**

```bash
bash os-haptics/install.sh
```

This copies the plist to `~/Library/LaunchAgents/` and starts the daemon via launchd. It will restart automatically on every login.

**3. Grant Privacy permissions**

The daemon needs two macOS permissions:

**Accessibility** — to monitor global mouse events:
- System Settings → Privacy & Security → Accessibility → `+`
- Add `Python.app` from your Python framework directory (e.g. `/opt/homebrew/Cellar/python@3.13/.../Resources/Python.app`)

**Screen Recording** — to read window positions for hover detection:
- System Settings → Privacy & Security → Screen Recording → `+`
- Add the same `Python.app`

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

## Waveforms

All 15 available waveforms on the MX Master 4:

| Category | Waveforms |
|---|---|
| Precision | `sharp_collision`, `damp_collision`, `subtle_collision`, `damp_state_change` |
| Progress | `sharp_state_change`, `completed`, `mad`, `firework`, `happy_alert`, `wave`, `angry_alert`, `square` |
| Events | `knock`, `ringing`, `jingle` |

---

## Troubleshooting

**No haptics / red dot in popup**
- Make sure Logi Options+ is running
- Check HapticWeb plugin is active (green dot in Logi Options+)
- Test directly: `curl -X POST -d '' https://local.jmw.nz:41443/haptic/sharp_collision`

**Daemon not responding**
- Check logs: `tail -f /tmp/mxmaster4-haptics.log`
- Make sure Accessibility and Screen Recording permissions are granted for `Python.app`
- Restart: `launchctl unload` then `launchctl load -w` on the plist

**Haptics fire too often on hover in browser**
- Increase `HOVER_THROTTLE_MS` in `content.js` (default: `120`)
