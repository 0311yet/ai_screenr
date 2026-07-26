# ai_screenr 入口：启动托盘 + 原生 webview 窗口 + NiceGUI 服务 + 后台引擎
"""直接运行：python main.py
或模块运行：python -m main
"""
from __future__ import annotations


def main() -> None:
    from ui.tray import run
    run()


if __name__ == "__main__":
    main()
