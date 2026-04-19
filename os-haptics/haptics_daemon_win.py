"""
MX Master 4 haptic daemon - Windows
Requires: pip install requests
Run: pythonw haptics_daemon_win.py    (no console window)
  or: python haptics_daemon_win.py   (with console, for debugging)

Install as a logon task via install.ps1.
"""

import sys
import time
import threading
import ctypes
from ctypes import wintypes
import requests

API = "https://local.jmw.nz:41443/haptic"

BROWSER_PROCS = {
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
    "opera.exe", "opera_gx.exe", "vivaldi.exe", "iexplore.exe",
    "chromium.exe", "thorium.exe", "arc.exe", "zen.exe",
}

HOVER_THROTTLE = 0.033   # ~30 Hz, WindowFromPoint is cheap but WM_MOUSEMOVE fires often
LONG_PRESS_SEC = 0.5

# Horizontal scroll (MX Master 4 thumb wheel) -> Apple Watch crown-style ticks.
# One WHEEL_DELTA (120) = one notch in ratchet mode. In free-spin mode we get
# many smaller events, so we accumulate abs(delta) and fire one tick per
# HSCROLL_TICK units, rate-capped by HSCROLL_MIN_SEC.
WHEEL_DELTA       = 120
HSCROLL_TICK      = 120
HSCROLL_MIN_SEC   = 0.05

# --- Win32 bindings ---
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_MOUSEMOVE   = 0x0200
WM_MOUSEHWHEEL = 0x020E
GA_ROOT = 2
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

LRESULT = ctypes.c_ssize_t

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

LowLevelMouseProc = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.restype  = wintypes.HANDLE
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, LowLevelMouseProc, wintypes.HINSTANCE, wintypes.DWORD]
user32.CallNextHookEx.restype  = LRESULT
user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.GetCursorPos.argtypes   = [ctypes.POINTER(POINT)]
user32.WindowFromPoint.restype = wintypes.HWND
user32.WindowFromPoint.argtypes = [POINT]
user32.GetAncestor.restype  = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetMessageW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.UINT]

kernel32.GetModuleHandleW.restype  = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.OpenProcess.restype  = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

# --- Haptic trigger ---
def trigger(waveform):
    try:
        requests.post(f"{API}/{waveform}", data="", timeout=1, verify=False)
    except Exception:
        pass

def fire(waveform):
    threading.Thread(target=trigger, args=(waveform,), daemon=True).start()

# --- Process name cache (hwnd -> name) ---
_proc_cache = {}

def process_name_for_hwnd(hwnd):
    if not hwnd:
        return ""
    cached = _proc_cache.get(hwnd)
    if cached is not None:
        return cached
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        _proc_cache[hwnd] = ""
        return ""
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    name = ""
    if h:
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                name = buf.value.rsplit("\\", 1)[-1].lower()
        finally:
            kernel32.CloseHandle(h)
    # Small cache, prune occasionally
    if len(_proc_cache) > 256:
        _proc_cache.clear()
    _proc_cache[hwnd] = name
    return name

def top_window_under_cursor():
    p = POINT()
    if not user32.GetCursorPos(ctypes.byref(p)):
        return None
    hwnd = user32.WindowFromPoint(p)
    if not hwnd:
        return None
    return user32.GetAncestor(hwnd, GA_ROOT)

def is_browser_hwnd(hwnd):
    return process_name_for_hwnd(hwnd) in BROWSER_PROCS

# --- State ---
state = {
    "last_window": None,
    "last_hover_check": 0.0,
    "press_start": 0.0,
    "long_press_fired": False,
    "hscroll_acc": 0,
    "last_hscroll_tick": 0.0,
}

def _hwheel_delta(lParam):
    """Extract signed 16-bit wheel delta from MSLLHOOKSTRUCT.mouseData high word."""
    info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT))[0]
    raw = (info.mouseData >> 16) & 0xFFFF
    if raw & 0x8000:
        raw -= 0x10000
    return raw

def on_mouse_event(msg, lParam):
    if msg == WM_LBUTTONDOWN:
        state["press_start"] = time.time()
        state["long_press_fired"] = False
        if not is_browser_hwnd(top_window_under_cursor()):
            fire("subtle_collision")
    elif msg == WM_LBUTTONUP:
        state["press_start"] = 0.0
    elif msg == WM_RBUTTONDOWN:
        if not is_browser_hwnd(top_window_under_cursor()):
            fire("knock")
    elif msg == WM_MOUSEMOVE:
        now = time.time()
        if now - state["last_hover_check"] < HOVER_THROTTLE:
            return
        state["last_hover_check"] = now
        hwnd = top_window_under_cursor()
        if hwnd and hwnd != state["last_window"]:
            state["last_window"] = hwnd
            if not is_browser_hwnd(hwnd):
                fire("damp_collision")
    elif msg == WM_MOUSEHWHEEL:
        # System-wide: fire in every app (browser included), since no other
        # layer in this project emits horizontal-scroll haptics.
        delta = _hwheel_delta(lParam)
        if not delta:
            return
        state["hscroll_acc"] += abs(delta)
        now = time.time()
        if (state["hscroll_acc"] >= HSCROLL_TICK
                and now - state["last_hscroll_tick"] >= HSCROLL_MIN_SEC):
            state["hscroll_acc"] = 0
            state["last_hscroll_tick"] = now
            fire("sharp_state_change")

def _hook_proc(nCode, wParam, lParam):
    if nCode == 0:
        try:
            on_mouse_event(wParam, lParam)
        except Exception as e:
            print(f"hook error: {e}", flush=True)
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

HOOK_PROC = LowLevelMouseProc(_hook_proc)

def long_press_watcher():
    while True:
        time.sleep(0.05)
        ps = state["press_start"]
        if ps and not state["long_press_fired"]:
            if time.time() - ps >= LONG_PRESS_SEC:
                state["long_press_fired"] = True
                state["press_start"] = 0.0
                if not is_browser_hwnd(top_window_under_cursor()):
                    fire("jingle")

def main():
    # Silence urllib3 warning about the HapticWeb self-signed cert
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass

    print("MX Master 4 haptic daemon - Windows", flush=True)
    print("  Left click      -> subtle_collision    (skipped in browser)", flush=True)
    print("  Right click     -> knock               (skipped in browser)", flush=True)
    print("  Window hover    -> damp_collision      (skipped in browser)", flush=True)
    print("  Long press      -> jingle              (skipped in browser)", flush=True)
    print("  Horizontal scr. -> sharp_state_change  (crown-style, system-wide)", flush=True)
    print("Running.\n", flush=True)

    threading.Thread(target=long_press_watcher, daemon=True).start()

    hmod = kernel32.GetModuleHandleW(None)
    hook = user32.SetWindowsHookExW(WH_MOUSE_LL, HOOK_PROC, hmod, 0)
    if not hook:
        err = ctypes.get_last_error()
        print(f"SetWindowsHookExW failed, error {err}", flush=True)
        sys.exit(1)

    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        user32.UnhookWindowsHookEx(hook)

if __name__ == "__main__":
    main()
