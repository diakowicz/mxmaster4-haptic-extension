# macOS system-level haptic daemon
# Listens to global mouse events via Quartz and triggers MX Master 4 haptics
# Requirements: pip install pyobjc-framework-Quartz requests
#
# Run: python3 os-haptics/haptics_daemon.py

import sys
import time
import threading
import requests

try:
    from Quartz import (
        CGEventTapCreate, CGEventTapEnable, CFMachPortCreateRunLoopSource,
        CFRunLoopAddSource, CFRunLoopGetCurrent, CFRunLoopRun,
        kCGEventTapOptionDefault, kCGSessionEventTap, kCGHeadInsertEventTap,
        kCGEventLeftMouseDown, kCGEventRightMouseDown,
        kCGEventMouseMoved, kCGEventScrollWheel,
        CGEventGetIntegerValueField, kCGScrollWheelEventDeltaAxis1,
    )
    from CoreFoundation import kCFRunLoopCommonModes
except ImportError:
    print("Install dependencies: pip install pyobjc-framework-Quartz")
    sys.exit(1)

API = "https://local.jmw.nz:41443/haptic"
HOVER_THROTTLE = 0.12   # seconds between hover haptics
SCROLL_EDGE_COOLDOWN = 0.6

last_hover = 0
last_scroll_edge = 0
scroll_accum = 0
SCROLL_EDGE_TICKS = 8   # ticks without movement = edge


def trigger(waveform):
    try:
        requests.post(f"{API}/{waveform}", data="", timeout=1)
    except Exception:
        pass


def trigger_async(waveform):
    threading.Thread(target=trigger, args=(waveform,), daemon=True).start()


def callback(proxy, event_type, event, refcon):
    global last_hover, last_scroll_edge, scroll_accum

    if event_type == kCGEventLeftMouseDown:
        trigger_async("subtle_collision")

    elif event_type == kCGEventRightMouseDown:
        trigger_async("knock")

    elif event_type == kCGEventMouseMoved:
        # No per-element detection at OS level — throttled ambient hover
        pass

    elif event_type == kCGEventScrollWheel:
        delta = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis1)
        now = time.time()
        if delta == 0 and now - last_scroll_edge > SCROLL_EDGE_COOLDOWN:
            last_scroll_edge = now
            trigger_async("sharp_collision")

    return event


def main():
    mask = (
        (1 << kCGEventLeftMouseDown) |
        (1 << kCGEventRightMouseDown) |
        (1 << kCGEventScrollWheel)
    )

    tap = CGEventTapCreate(
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        mask,
        callback,
        None,
    )

    if not tap:
        print("Could not create event tap.")
        print("Grant Accessibility access: System Settings → Privacy & Security → Accessibility")
        sys.exit(1)

    source = CFMachPortCreateRunLoopSource(None, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), source, kCFRunLoopCommonModes)
    CGEventTapEnable(tap, True)

    print("MX Master 4 haptic daemon running (macOS)")
    print("  Left click  → subtle_collision")
    print("  Right click → knock")
    print("  Scroll edge → sharp_collision")
    print("Press Ctrl+C to stop.")
    CFRunLoopRun()


if __name__ == "__main__":
    main()
