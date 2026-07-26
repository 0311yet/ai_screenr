# ai_screenr/classify/fallback.py
"""Win 接口规则兜底：进程名/窗口标题 -> activity。

当 VLM 失败/超时使用，保证不留空窗。
匹配优先级：先按 idle（>阈值 -> 空闲），再按进程名精确匹配，
再按窗口标题关键词模糊匹配，未命中默认"其他"。
"""
from __future__ import annotations

from classify.vlm import VlmResult
import config

# 进程名 -> activity 映射（小写精确匹配。可按需扩展）
PROC_RULES: dict[str, str] = {
    # 工作 / 开发
    "code.exe": "工作",
    "code - insiders.exe": "工作",
    "devenv.exe": "工作",          # Visual Studio
    "idea64.exe": "工作",          # IntelliJ
    "pycharm64.exe": "工作",
    "windsurf.exe": "工作",
    "cursor.exe": "工作",
    "sublime_text.exe": "工作",
    "windowsTerminal.exe": "工作",
    "powershell.exe": "工作",
    "cmd.exe": "工作",
    "wt.exe": "工作",
    "obsidian.exe": "工作",
    "notion.exe": "工作",
    "winword.exe": "工作",         # Word
    "excel.exe": "工作",
    "powerpnt.exe": "工作",
    "outlook.exe": "工作",
    "wps.exe": "工作",
    "fusion.exe": "工作",
    "blender.exe": "工作",
    # 游戏（按你装的常见作添补）
    # 注意游戏最好靠 VLM；这里只兜底几个明显的单进程全屏游戏
    # 浏览 -> 默认 chrome 等
    "chrome.exe": "浏览",
    "msedge.exe": "浏览",
    "firefox.exe": "浏览",
    "brave.exe": "浏览",
    # 社交
    "wechat.exe": "社交",
    "wechatappex.exe": "社交",
    "qq.exe": "社交",
    "tim.exe": "社交",
    "telegram.exe": "社交",
    "slack.exe": "社交",
    "dingtalk.exe": "社交",
    # 视频
    "cloudmusic.exe": "视频",       # 网易云算听，先归视频
    "spotify.exe": "视频",
    # 系统类：留空让"其他"吃掉
}

# 窗口标题关键词 -> activity （标题包含关键词则命中，优先级低于进程精确）
TITLE_KEYWORDS: list[tuple[str, str]] = [
    ("B站", "视频"),
    ("哔哩哔哩", "视频"),
    ("bilibili", "视频"),
    ("YouTube", "视频"),
    ("Netflix", "视频"),
    ("爱奇艺", "视频"),
    ("腾讯视频", "视频"),
    ("优酷", "视频"),
    ("原神", "游戏"),
    ("genshin", "游戏"),
    ("steam", "游戏"),
    ("Steam", "游戏"),
]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def from_win(window_title: str, proc_name: str, idle_sec: int) -> VlmResult:
    """匹配规则给出 activity。
    顺序：
      1) 键鼠空闲 >= IDLE_THRESHOLD_SEC -> '空闲'
      2) 进程名精确匹配 PROC_RULES
      3) 窗口标题含 TITLE_KEYWORDS 关键词
      4) 未命中 -> '其他'
    """
    detail = f"{proc_name or '未知进程'} / {window_title or '无标题'}"
    # 1) 空闲
    if idle_sec >= config.IDLE_THRESHOLD_SEC:
        return VlmResult(activity="空闲", app=proc_name or "系统", detail=f"空闲 {idle_sec}s", raw="")
    # 2) 进程精确
    proc_norm = _norm(proc_name)
    if proc_norm and proc_norm in PROC_RULES:
        return VlmResult(activity=PROC_RULES[proc_norm], app=proc_name, detail=detail, raw="")
    # 3) 标题关键词
    for kw, act in TITLE_KEYWORDS:
        if kw.lower() in (window_title or "").lower():
            return VlmResult(activity=act, app=proc_name or window_title, detail=detail, raw="")
    # 4) 其他
    return VlmResult(activity="其他", app=proc_name or "未知", detail=detail, raw="")
