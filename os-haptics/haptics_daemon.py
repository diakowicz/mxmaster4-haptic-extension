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
    from AppKit import (
        NSApplication, NSEvent, NSWorkspace, NSScreen,
        NSLeftMouseDownMask, NSRightMouseDownMask, NSMouseMovedMask,
    )
    import Quartz
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

WINDOW_HOVER_THROTTLE = 0.1   # seconds between window-enter checks


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


def get_window_id_under_cursor(cx, cy):
    """Return the kCGWindowNumber of the topmost window under (cx, cy)."""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    if not windows:
        return None
    for w in windows:
        b = w.get("kCGWindowBounds", {})
        x, y = b.get("X", 0), b.get("Y", 0)
        width, height = b.get("Width", 0), b.get("Height", 0)
        if x <= cx <= x + width and y <= cy <= y + height:
            layer = w.get("kCGWindowLayer", 999)
            if layer <= 0:   # skip menu bar, overlays
                return w.get("kCGWindowNumber")
    return None


def start_monitors():
    last_window   = [None]
    last_checked  = [0.0]

    def on_mouse_click(event):
        if in_browser():
            return
        t = event.type()
        if t == 1:   fire("subtle_collision")
        elif t == 3: fire("knock")

    def on_mouse_move(event):
        now = time.time()
        if now - last_checked[0] < WINDOW_HOVER_THROTTLE:
            return
        last_checked[0] = now

        # NSEvent uses bottom-left origin; CGWindowList uses top-left
        pos = NSEvent.mouseLocation()
        screen_h = NSScreen.mainScreen().frame().size.height
        cx, cy = pos.x, screen_h - pos.y

        wid = get_window_id_under_cursor(cx, cy)
        if wid and wid != last_window[0]:
            last_window[0] = wid
            if not in_browser():
                fire("damp_collision")

    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSLeftMouseDownMask | NSRightMouseDownMask, on_mouse_click)
    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSMouseMovedMask, on_mouse_move)


def main():
    print("MX Master 4 haptic daemon — macOS", flush=True)
    print("  Left click      → subtle_collision  (skipped in browser)", flush=True)
    print("  Right click     → knock             (skipped in browser)", flush=True)
    print("  Window hover    → damp_collision    (skipped in browser)", flush=True)
    print("  Requires: Accessibility + Screen Recording in Privacy settings", flush=True)
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
