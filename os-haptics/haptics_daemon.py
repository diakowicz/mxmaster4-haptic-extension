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
    import objc
    from Foundation import NSDistributedNotificationCenter, NSObject, NSLog
    from AppKit import (
        NSApplication, NSApp, NSEvent,
        NSLeftMouseDownMask, NSRightMouseDownMask, NSScrollWheelMask,
        NSWorkspace,
    )
    from Quartz import CGEventGetIntegerValueField, kCGScrollWheelEventDeltaAxis1
except ImportError:
    print("Install dependencies: pip install pyobjc-framework-Quartz requests --break-system-packages")
    sys.exit(1)

API             = "https://local.jmw.nz:41443/haptic"
SCROLL_COOLDOWN = 0.6

last_scroll_edge = 0


# ── HTTP trigger ──────────────────────────────────────────────────────────────

def trigger(waveform):
    try:
        requests.post(f"{API}/{waveform}", data="", timeout=1)
    except Exception:
        pass

def fire(waveform):
    threading.Thread(target=trigger, args=(waveform,), daemon=True).start()


# ── NSEvent global monitors ───────────────────────────────────────────────────

def start_monitors():
    global last_scroll_edge

    def on_mouse(event):
        etype = event.type()
        if etype == 1:   # NSLeftMouseDown
            fire("subtle_collision")
        elif etype == 3: # NSRightMouseDown
            fire("knock")

    def on_scroll(event):
        global last_scroll_edge
        dy = event.scrollingDeltaY()
        now = time.time()
        if dy == 0 and now - last_scroll_edge > SCROLL_COOLDOWN:
            last_scroll_edge = now
            fire("sharp_collision")

    mask_click  = NSLeftMouseDownMask | NSRightMouseDownMask
    mask_scroll = NSScrollWheelMask

    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask_click,  on_mouse)
    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask_scroll, on_scroll)


# ── Call observer ─────────────────────────────────────────────────────────────

class CallObserver(NSObject):

    def onCall_(self, notification):
        fire("ringing")

    def onAppActivate_(self, notification):
        info = notification.userInfo() or {}
        app  = info.get("NSWorkspaceApplicationKey")
        name = app.localizedName() if app else ""
        if name == "FaceTime":
            fire("ringing")


def start_observers():
    observer = CallObserver.alloc().init()
    dnc   = NSDistributedNotificationCenter.defaultCenter()
    ws_nc = NSWorkspace.sharedWorkspace().notificationCenter()

    for name in [
        "com.apple.CTCall.callstate",
        "com.apple.telephonyutilities.phoneCallState",
        "com.apple.callkit.callobserver.callchanged",
    ]:
        dnc.addObserver_selector_name_object_(
            observer,
            objc.selector(observer.onCall_, signature=b"v@:@"),
            name, None,
        )

    ws_nc.addObserver_selector_name_object_(
        observer,
        objc.selector(observer.onAppActivate_, signature=b"v@:@"),
        "NSWorkspaceDidActivateApplicationNotification", None,
    )
    return observer


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("MX Master 4 haptic daemon — macOS")
    print("  Left click      → subtle_collision")
    print("  Right click     → knock")
    print("  Scroll edge     → sharp_collision")
    print("  Incoming call   → ringing  (iPhone Continuity / FaceTime)")
    print()

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(2)  # NSApplicationActivationPolicyProhibited — no Dock icon

    start_monitors()
    _observer = start_observers()

    from AppKit import NSRunLoop, NSDate
    run_loop = NSRunLoop.currentRunLoop()
    print("Running. Press Ctrl+C to stop.")
    try:
        while True:
            run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.5))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
