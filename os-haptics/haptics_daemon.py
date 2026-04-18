"""
MX Master 4 haptic daemon — macOS
Requires: pip install pyobjc-framework-Quartz requests --break-system-packages
Run via launchd (see install.sh) or: python3 haptics_daemon.py
"""

import sys
import time
import threading
import requests

try:
    from Foundation import NSObject
    from AppKit import (
        NSApplication, NSEvent, NSWorkspace,
        NSLeftMouseDownMask, NSRightMouseDownMask, NSScrollWheelMask,
    )
except ImportError:
    print("Install dependencies: pip install pyobjc-framework-Quartz requests --break-system-packages")
    sys.exit(1)

API             = "https://local.jmw.nz:41443/haptic"
SCROLL_COOLDOWN = 0.6

last_scroll_edge = 0


def trigger(waveform):
    try:
        requests.post(f"{API}/{waveform}", data="", timeout=1)
    except Exception:
        pass

def fire(waveform):
    threading.Thread(target=trigger, args=(waveform,), daemon=True).start()


def start_monitors():
    global last_scroll_edge

    def on_mouse(event):
        t = event.type()
        if t == 1:    fire("subtle_collision")   # left click
        elif t == 3:  fire("knock")              # right click

    def on_scroll(event):
        global last_scroll_edge
        now = time.time()
        if event.scrollingDeltaY() == 0 and now - last_scroll_edge > SCROLL_COOLDOWN:
            last_scroll_edge = now
            fire("sharp_collision")

    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSLeftMouseDownMask | NSRightMouseDownMask, on_mouse)
    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSScrollWheelMask, on_scroll)


def main():
    print("MX Master 4 haptic daemon — macOS", flush=True)
    print("  Left click   → subtle_collision", flush=True)
    print("  Right click  → knock", flush=True)
    print("  Scroll edge  → sharp_collision", flush=True)
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
