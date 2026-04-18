"""
MX Master 4 haptic daemon — macOS
Requires: pip install pyobjc-framework-Quartz requests --break-system-packages
Run via launchd (see install.sh) or: python3 haptics_daemon.py
"""

import sys
import threading
import requests

try:
    from AppKit import (
        NSApplication, NSEvent, NSWorkspace,
        NSLeftMouseDownMask, NSRightMouseDownMask,
    )
except ImportError:
    print("Install dependencies: pip install pyobjc-framework-Quartz requests --break-system-packages")
    sys.exit(1)

API = "https://local.jmw.nz:41443/haptic"

BROWSER_BUNDLE_IDS = {
    "com.google.Chrome",
    "com.google.Chrome.beta",
    "com.google.Chrome.canary",
    "org.mozilla.firefox",
    "com.apple.Safari",
    "com.microsoft.edgemac",
    "com.brave.Browser",
    "com.operasoftware.Opera",
    "com.vivaldi.Vivaldi",
}


def trigger(waveform):
    try:
        requests.post(f"{API}/{waveform}", data="", timeout=1)
    except Exception:
        pass

def fire(waveform):
    threading.Thread(target=trigger, args=(waveform,), daemon=True).start()

def in_browser():
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return app and app.bundleIdentifier() in BROWSER_BUNDLE_IDS


def start_monitors():

    def on_mouse(event):
        if in_browser():
            return  # extension handles haptics in browser
        t = event.type()
        if t == 1:   fire("subtle_collision")  # left click
        elif t == 3: fire("knock")             # right click

    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSLeftMouseDownMask | NSRightMouseDownMask, on_mouse)


def main():
    print("MX Master 4 haptic daemon — macOS", flush=True)
    print("  Left click   → subtle_collision  (skipped in browser)", flush=True)
    print("  Right click  → knock             (skipped in browser)", flush=True)
    print("Running.\n", flush=True)

    NSApplication.sharedApplication().setActivationPolicy_(2)
    start_monitors()

    from AppKit import NSRunLoop, NSDate
    try:
        while True:
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.5))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
