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
    from Quartz import (
        CGEventTapCreate, CGEventTapEnable,
        CFMachPortCreateRunLoopSource, CFRunLoopAddSource,
        CFRunLoopGetCurrent, CFRunLoopRun,
        kCGEventTapOptionDefault, kCGSessionEventTap, kCGHeadInsertEventTap,
        kCGEventLeftMouseDown, kCGEventRightMouseDown, kCGEventScrollWheel,
        CGEventGetIntegerValueField, kCGScrollWheelEventDeltaAxis1,
    )
    from CoreFoundation import kCFRunLoopCommonModes
    import objc
    from Foundation import NSDistributedNotificationCenter, NSObject
    from AppKit import NSWorkspace
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


# ── Mouse event tap ───────────────────────────────────────────────────────────

def mouse_callback(proxy, event_type, event, refcon):
    global last_scroll_edge

    if event_type == kCGEventLeftMouseDown:
        fire("subtle_collision")

    elif event_type == kCGEventRightMouseDown:
        fire("knock")

    elif event_type == kCGEventScrollWheel:
        delta = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis1)
        now = time.time()
        if delta == 0 and now - last_scroll_edge > SCROLL_COOLDOWN:
            last_scroll_edge = now
            fire("sharp_collision")

    return event


def start_mouse_tap():
    mask = (
        (1 << kCGEventLeftMouseDown) |
        (1 << kCGEventRightMouseDown) |
        (1 << kCGEventScrollWheel)
    )
    tap = CGEventTapCreate(
        kCGSessionEventTap, kCGHeadInsertEventTap,
        kCGEventTapOptionDefault, mask, mouse_callback, None,
    )
    if not tap:
        print("[ERROR] Cannot create event tap.")
        print("        Grant Accessibility: System Settings → Privacy & Security → Accessibility")
        sys.exit(1)

    source = CFMachPortCreateRunLoopSource(None, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), source, kCFRunLoopCommonModes)
    CGEventTapEnable(tap, True)


# ── Call / notification observer ──────────────────────────────────────────────

class CallObserver(NSObject):

    def onCall_(self, notification):
        fire("ringing")

    def onAppActivate_(self, notification):
        info = notification.userInfo() or {}
        app = (info.get("NSWorkspaceApplicationKey") or {})
        name = getattr(app, "localizedName", lambda: "")()
        if name == "FaceTime":
            fire("ringing")


def start_observers():
    observer = CallObserver.alloc().init()
    dnc  = NSDistributedNotificationCenter.defaultCenter()
    ws_nc = NSWorkspace.sharedWorkspace().notificationCenter()

    # iPhone Continuity / CallKit incoming call notifications
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

    # FaceTime window coming to front → likely incoming call
    ws_nc.addObserver_selector_name_object_(
        observer,
        objc.selector(observer.onAppActivate_, signature=b"v@:@"),
        "NSWorkspaceDidActivateApplicationNotification", None,
    )

    return observer  # keep reference alive


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("MX Master 4 haptic daemon — macOS")
    print("  Left click      → subtle_collision")
    print("  Right click     → knock")
    print("  Scroll edge     → sharp_collision")
    print("  Incoming call   → ringing  (iPhone Continuity / FaceTime)")
    print("Press Ctrl+C to stop.\n")

    start_mouse_tap()
    _observer = start_observers()

    try:
        CFRunLoopRun()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
