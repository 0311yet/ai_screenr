# ai_screenr/ui/autostart.py
"""Windows 开机自启：读写注册表 HKCU\\...\\Run 项。
键名 ai_screenr，值是当前解释器 + main.py 的启动命令。
"""
from __future__ import annotations

import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ai_screenr"


def _command() -> str:
    # 用 pythonw 无窗口启动；main.py 用绝对路径
    exe = sys.executable
    # 若是 python.exe，替换为同目录 pythonw.exe
    pyw = exe.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = exe
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{pyw}" "{main_py}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def enable() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _command())
        return True
    except Exception:
        return False


def disable() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, APP_NAME)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False
