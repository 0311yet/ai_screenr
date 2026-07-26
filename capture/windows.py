# ai_screenr/capture/windows.py
"""Win32 辅信号采集：前台窗口标题、进程名、键鼠空闲秒数、锁屏判断。

实现要点（参考 pi 扩展 smart-notify 的空闲检测思路，改用 ctypes 直调，
更轻、零子进程，并修正了两个细节）：
- 用 GetTickCount64 而非 GetTickCount，避免 ~49.7 天回绕出负值。
- 检测失败时保留上次 idle_sec（不同于 smart-notify 的 resolve(0)），
  避免"人在/不在"被误反转，影响后续 VLM 决策。
- 锁屏判：OpenInputDesktop 若要 OpenInputDesktop 之外，改用 win32 API
  EnumDesktops/GetCurrentThreadId 关联——这里使用 GetUserObjectInformation
  上的 desktop 名 == "Winlogon" 判定锁屏（详见 is_locked_desktop）。
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import time

import psutil
import win32gui
import win32process

import config

# ── Win32 绑定 ──────────────────────────────────────────────
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


_last_idle_sec: int | None = None  # 失败回退用


@dataclass
class WinSnapshot:
    ts: float
    window_title: str      # GetForegroundWindow + GetWindowTextW
    proc_name: str         # 该窗口进程名（GetWindowThreadProcessId + psutil）
    idle_sec: int          # GetLastInputInfo 推导的空闲秒数
    locked: bool           # 是否锁屏（desktop 名 == Winlogon 判定）
    screen_off: bool       # 显示器是否关闭（电源状态/事件，PI 差距预留）


def get_idle_sec() -> int:
    """返回键鼠空闲秒数。失败保留上次值（首次失败返回 0 不变激进）。"""
    global _last_idle_sec
    try:
        lii = _LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if not user32.GetLastInputInfo(ctypes.byref(lii)):
            # 调用失败：保持上次值
            return _last_idle_sec if _last_idle_sec is not None else 0
        now_ms = kernel32.GetTickCount64()  # 64 位，无回绕
        idle_ms = now_ms - lii.dwTime
        if idle_ms < 0:
            # 仍保护一次（防御性）
            idle_ms = 0
        sec = int(idle_ms // 1000)
        _last_idle_sec = sec
        return sec
    except Exception:
        return _last_idle_sec if _last_idle_sec is not None else 0


def get_foreground_window() -> tuple[int, str]:
    """返回 (hwnd, window_title)；none 则 ("")。"""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return 0, ""
    try:
        title = win32gui.GetWindowText(hwnd)
    except Exception:
        title = ""
    return int(hwnd), title


def get_proc_name(hwnd: int) -> str:
    """从 hwnd 取所在进程名。失败回 ""。"""
    if not hwnd:
        return ""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return ""
        try:
            return psutil.Process(pid).name()
        except Exception:
            # 进程可能已退出
            return ""
    except Exception:
        return ""


def is_locked_desktop() -> bool:
    """锁屏判定：当前活动 desktop 是否为 'Winlogon'。
    锁屏时 Windows 切到 Winlogon desktop；活动 desktop 名 == Winlogon 即锁。
    """
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x0080)  # DESKTOP_READOBJECTS=0x0080
        if not hdesk:
            return True
        try:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetUserObjectInformationW(hdesk, 2, buf, 256)  # UOI_NAME=2
            name = buf.value
            return name == "Winlogon"
        finally:
            user32.CloseDesktop(hdesk)
    except Exception:
        return False


def snapshot() -> WinSnapshot:
    """取当前一帧 Win32 状态。非阻塞，每秒调用一次。"""
    now = time.time()
    hwnd, title = get_foreground_window()
    proc = get_proc_name(hwnd) if hwnd else ""
    idle = get_idle_sec()
    locked = is_locked_desktop()
    return WinSnapshot(
        ts=now,
        window_title=title,
        proc_name=proc,
        idle_sec=idle,
        locked=locked,
        screen_off=False,  # TODO: 后续接电源事件/电源状态检测；现在先置 False
    )


def is_idle(snap: WinSnapshot) -> bool:
    """仅看键鼠空闲是否超过 IDLE_THRESHOLD_SEC。"""
    return snap.idle_sec >= config.IDLE_THRESHOLD_SEC
