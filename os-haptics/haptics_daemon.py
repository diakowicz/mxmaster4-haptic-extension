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

WINDOW_HOVER_THROTTLE = 0.033  # ~30 Hz — CGWindowList is expensive, don't go faster
SCROLL_H_THROTTLE    = 0.01   # 10 ms — tight crown feel, one haptic per detent


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


def clipboard_screenshot_watcher():
    """Fire haptic when a new image (screenshot) lands in the clipboard."""
    from AppKit import NSPasteboard
    IMAGE_TYPES = {'public.png', 'public.tiff', 'com.apple.pict'}
    pb = NSPasteboard.generalPasteboard()
    last_count = pb.changeCount()
    while True:
        time.sleep(0.25)
        count = pb.changeCount()
        if count == last_count:
            continue
        last_count = count
        types = pb.types()
        if types and IMAGE_TYPES.intersection(types):
            fire("completed")


def start_monitors():
    last_window      = [None]
    last_scroll_h    = [0.0]

    def on_mouse_click(event):
        if in_browser():
            return
        t = event.type()
        if t == 1:   fire("subtle_collision")
        elif t == 3: fire("knock")

    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSLeftMouseDownMask | NSRightMouseDownMask, on_mouse_click)

    last_gesture_event = [0.0]

    def scroll_tap_callback(proxy, event_type, event, refcon):
        if event_type != 29:  # NSEventTypeGesture — Logi Options+ zoom mapping
            return event
        now = time.time()
        gap = now - last_gesture_event[0]
        last_gesture_event[0] = now
        # isolated end-of-gesture marker arrives after >150ms silence — skip it
        if gap > 0.15:
            return event
        if now - last_scroll_h[0] < SCROLL_H_THROTTLE:
            return event
        last_scroll_h[0] = now
        fire("damp_state_change")
        return event

    tap = Quartz.CGEventTapCreate(
        Quartz.kCGHIDEventTap,
        Quartz.kCGHeadInsertEventTap,
        Quartz.kCGEventTapOptionListenOnly,
        Quartz.CGEventMaskBit(29),  # NSEventTypeGesture
        scroll_tap_callback,
        None,
    )
    if tap:
        from CoreFoundation import (
            CFMachPortCreateRunLoopSource, CFRunLoopAddSource,
            CFRunLoopGetCurrent, kCFRunLoopDefaultMode,
        )
        src = CFMachPortCreateRunLoopSource(None, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), src, kCFRunLoopDefaultMode)
        enabled = Quartz.CGEventTapIsEnabled(tap)
        print(f"CGEventTap registered, enabled={enabled}", flush=True)
    else:
        print("WARNING: CGEventTap for scroll failed (check Accessibility permission)", flush=True)

    return last_window  # returned so main loop can poll


def main():
    print("MX Master 4 haptic daemon — macOS", flush=True)
    print("  Left click      → subtle_collision  (skipped in browser)", flush=True)
    print("  Right click     → knock             (skipped in browser)", flush=True)
    print("  Window hover    → damp_collision    (skipped in browser)", flush=True)
    print("  Long press      → jingle            (skipped in browser)", flush=True)
    print("  Horizontal scroll → damp_state_change (crown feel, system-wide)", flush=True)
    print("  Screenshot      → completed         (clipboard image detection)", flush=True)
    print("  Requires: Accessibility + Screen Recording in Privacy settings", flush=True)
    print("Running.\n", flush=True)

    NSApplication.sharedApplication().setActivationPolicy_(2)
    last_window = start_monitors()
    threading.Thread(target=clipboard_screenshot_watcher, daemon=True).start()

    last_check = [0.0]

    # Long press detection
    press_start    = [0.0]
    long_press_fired = [False]
    LONG_PRESS_SEC = 0.5

    def on_down(event):
        if event.type() == 1:
            press_start[0] = time.time()
            long_press_fired[0] = False

    def on_up(event):
        if event.type() == 2 and not long_press_fired[0]:
            pass  # normal click already handled

    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(1 << 1, on_down)   # NSLeftMouseDown
    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(1 << 2, on_up)     # NSLeftMouseUp

    from AppKit import NSRunLoop, NSDate
    try:
        while True:
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.016))

            # Long press check
            if press_start[0] and not long_press_fired[0]:
                if time.time() - press_start[0] >= LONG_PRESS_SEC:
                    long_press_fired[0] = True
                    press_start[0] = 0.0
                    if not in_browser():
                        fire("jingle")

            # Window hover poll
            now = time.time()
            if now - last_check[0] >= WINDOW_HOVER_THROTTLE:
                last_check[0] = now
                loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
                cx, cy = loc.x, loc.y
                wid = get_window_id_under_cursor(cx, cy)
                if wid and wid != last_window[0]:
                    last_window[0] = wid
                    if not in_browser():
                        fire("damp_collision")

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
