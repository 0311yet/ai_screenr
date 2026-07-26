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
    - 否则试 VLM；异常 -> 走 fallback（基于 Win 标题/进程/空闲）
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
    # 2) 主路径：VLM
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
