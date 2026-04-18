# Windows system-level haptic daemon
# Listens to global mouse events via ctypes WH_MOUSE_LL hook
# Requirements: pip install requests  (ctypes is built-in)
#
# Run: python os-haptics\haptics_daemon.py

import sys
import ctypes
import ctypes.wintypes
import threading
import time
import requests

if sys.platform != "win32":
    print("This script is for Windows only.")
    sys.exit(1)

API = "https://local.jmw.nz:41443/haptic"
SCROLL_EDGE_COOLDOWN = 0.6

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_MOUSE_LL   = 14
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MOUSEWHEEL  = 0x020A

WHEEL_DELTA = 120

last_scroll_edge = 0


def trigger(waveform):
    try:
        requests.post(f"{API}/{waveform}", data="", timeout=1)
    except Exception:
        pass


def trigger_async(waveform):
    threading.Thread(target=trigger, args=(waveform,), daemon=True).start()


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",      ctypes.wintypes.POINT),
        ("mouseData", ctypes.wintypes.DWORD),
        ("flags",   ctypes.wintypes.DWORD),
        ("time",    ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)


def hook_callback(nCode, wParam, lParam):
    global last_scroll_edge

    if nCode >= 0:
        if wParam == WM_LBUTTONDOWN:
            trigger_async("subtle_collision")

        elif wParam == WM_RBUTTONDOWN:
            trigger_async("knock")

        elif wParam == WM_MOUSEWHEEL:
            ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            delta = ctypes.c_short(ms.mouseData >> 16).value
            now = time.time()
            if delta == 0 and now - last_scroll_edge > SCROLL_EDGE_COOLDOWN:
                last_scroll_edge = now
                trigger_async("sharp_collision")

    return user32.CallNextHookEx(None, nCode, wParam, lParam)


def main():
    callback = HOOKPROC(hook_callback)
    hook = user32.SetWindowsHookExA(WH_MOUSE_LL, callback, kernel32.GetModuleHandleW(None), 0)

    if not hook:
        print("Failed to install mouse hook.")
        sys.exit(1)

    print("MX Master 4 haptic daemon running (Windows)")
    print("  Left click  → subtle_collision")
    print("  Right click → knock")
    print("  Scroll edge → sharp_collision")
    print("Press Ctrl+C to stop.")

    msg = ctypes.wintypes.MSG()
    try:
        while user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageA(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(hook)


if __name__ == "__main__":
    main()
