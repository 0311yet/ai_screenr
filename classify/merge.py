# ai_screenr/classify/merge.py
"""融合逻辑：正常采 VLM；失败/超时采 fallback；锁屏/屏灭 -> 标空闲。"""
from __future__ import annotations

import logging

from classify.vlm import VlmResult
from classify import fallback, vlm
from capture.windows import WinSnapshot

log = logging.getLogger(__name__)


def classify_one(win: WinSnapshot, image_bytes: bytes) -> VlmResult:
    """主路径返回 final VlmResult，source 标注来源。
    - 锁屏/屏灭 -> 直接标空闲，不调 VLM
    - 否则先用 fallback 的标题/进程强信号判，若命中则直接采纳（VLM 对游戏/视频时常睡眼）
    - 否则才调 VLM；异常 -> fallback
    """
    # 1) 锁屏/屏灭 -> 空闲，不付费调 VLM
    if win.locked or win.screen_off:
        return VlmResult(
            activity="空闲",
            app="系统",
            detail="锁屏/屏灭未运行 VLM",
            raw="",
            source="system",
        )
    # 2) 标题/进程强信号：fallback 若命中明确进程分类，直接采纳（VLM 对游戏/视频/社交常睡眼，
    #     对 IDE/Office 工作判别也偏弱；只要 fallback 能判出具体进程/标题，优先走它）
    fb = fallback.from_win(win.window_title, win.proc_name, win.idle_sec)
    if fb and fb.activity in ("游戏", "视频", "社交", "工作", "空闲"):
        fb.source = "fallback"
        return fb
    # 3) 主路径：VLM
    if image_bytes is None:
        return _fallback_with(win)
    try:
        return vlm.classify(image_bytes, win.window_title)
    except Exception as e:
        log.warning("VLM failed -> fallback: %s", e)
        return _fallback_with(win)


def _fallback_with(win: WinSnapshot) -> VlmResult:
    res = fallback.from_win(win.window_title, win.proc_name, win.idle_sec)
    res.source = "fallback"
    return res
