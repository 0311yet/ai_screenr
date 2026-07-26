# ai_screenr/ui/tray.py
"""托盘（pystray）+ 原生窗口（pywebview）+ NiceGUI 服务三者衔接。

主线程：pystray 事件循环（托盘菜单）
背景线程：uvicorn 跑 NiceGUI（ui.run 阻塞，所以放线程）
独立线程：pywebview 创建并阻塞管理原生窗口
"""
from __future__ import annotations

import logging
import os
import threading
import time

import webview
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

log = logging.getLogger(__name__)

_stop_event = threading.Event()


def _cfg():
    """取 host/port，从 config 读。"""
    import config
    return config.NICEGUI_HOST, config.NICEGUI_PORT


def _make_icon():
    """生成一个霓虹青方块 logo（无外部资源依赖）。"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 6, 58, 58], radius=10, fill=(10, 14, 20))
    d.rounded_rectangle([14, 14, 50, 50], radius=6,
                       fill=(78, 224, 196))
    d.text((22, 18), "π", fill=(10, 14, 20))
    return img


def _nicegui_server():
    """在子线程跑 NiceGUI 服务（阻塞）。"""
    from nicegui import ui as ngui
    # 触发 @ui.page 注册
    __import__("ui.app", fromlist=["main_page"])
    host, port = _cfg()
    try:
        ngui.run(host=host, port=port, reload=False, show=False,
                 favicon=False, native=False, title="ai_screenr",
                 dark=True)
    except Exception:
        log.exception("nicegui server crashed")


def _start_server_thread():
    t = threading.Thread(target=_nicegui_server, name="nicegui_server", daemon=True)
    t.start()
    # 等服务起来
    import requests
    host, port = _cfg()
    url = f"http://{host}:{port}/"
    for _ in range(40):
        try:
            requests.get(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.25)
    log.error("nicegui 服务未启动")
    return False


def _open_window():
    """用 pywebview 开原生窗口指向 NiceGUI 服务（**只能在主线程**）。"""
    host, port = _cfg()
    webview.create_window(
        title="AI_SCREENR",
        url=f"http://{host}:{port}/",
        width=1080, height=780,
        min_size=(820, 600),
        frameless=False,
        easy_drag=False,
        background_color="#0a0e14",
    )
    webview.start(debug=False)  # 阻塞主线程


def _on_show(icon, item):
    """托盘“显示窗口”：把隐藏的 webview 窗口显示出来。"""
    try:
        wins = webview.windows
        if wins:
            w = wins[0]
            w.show()
            w.restore()
    except Exception:
        log.exception("show window")


def _on_hide(icon, item):
    try:
        wins = webview.windows
        if wins:
            wins[0].hide()
    except Exception:
        log.exception("hide window")


def _on_quit(icon, item):
    log.info("quit requested")
    _stop_event.set()
    try:
        for w in webview.windows:
            w.destroy()
    except Exception:
        pass
    icon.stop()
    # 给一点时间让服务退
    time.sleep(0.5)
    os._exit(0)  # ui.run 卡线程的强制收尾


def _tray_loop(stop_event):
    """跑托盘图标（子线程）。退出时置位 stop_event 让主线程的 webview 退出。"""
    menu = Menu(
        MenuItem("显示窗口", _on_show, default=True),
        MenuItem("隐藏窗口", _on_hide),
        Menu.SEPARATOR,
        MenuItem("退出", _on_quit),
    )
    tray = Icon("ai_screenr", _make_icon(),
                "AI_SCREENR 监控运行中", menu)
    tray.run()
    stop_event.set()


def run() -> None:
    global _stop_event
    threading.current_thread()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # 1) NiceGUI 服务线程 + 等待就绪
    if not _start_server_thread():
        log.error("启动失败：NiceGUI 服务未就绪，退出。")
        return

    # 2) 托盘子线程
    tray_stop = threading.Event()
    t = threading.Thread(target=_tray_loop, args=(tray_stop,), name="tray", daemon=True)
    t.start()

    # 3) webview 原生窗口（主线程，阻塞）
    _open_window()
    # webview.start 退出 -> 下来贴托盘退出事件
    _stop_event.set()


if __name__ == "__main__":
    run()
