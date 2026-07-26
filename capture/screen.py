# ai_screenr/capture/screen.py
"""截屏并按配置缩放/JPEG 压缩后返回 bytes，供 VLM 使用。

- 主截屏用 mss（跨平台快速 screenshot），目标主显示器。
- 1080P 直送：不缩放宽度（VLM_SCREEN_MAX_W=1920）。
- 仅对超大宽度做裁：屏高超过 1080P 等比缩到 VLM_SCREEN_MAX_W，
  1080P 及以下原尺寸送，保信息量。
- 以 JPEG q=85 压缩到 bytes，base64 后送 Ollama。
"""
from __future__ import annotations

import io
import time

import mss
from PIL import Image

import config

_monitor_cache: dict = {}


def _get_primary_monitor(sct):
    """取主显示器信息，缓存。"""
    if _monitor_cache:
        return _monitor_cache["mon"]
    mons = sct.monitors  # [0]=全体虚拟屏, [1:]=各物理显示器
    mon = mons[1] if len(mons) > 1 else mons[0]
    _monitor_cache["mon"] = mon
    return mon


def capture_for_vlm() -> bytes:
    """截全屏 -> 按 VLM_SCREEN_MAX_W 等比缩 -> JPEG(q85) -> bytes。

    1080P 直送时不缩，画质与尺寸保真。
    返回 bytes 已是压缩后的 JPEG 原始字节（未 base64）。
    """
    with mss.mss() as sct:
        mon = _get_primary_monitor(sct)
        shot = sct.grab(mon)  # BGRA
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    # 缩放（仅大于配置宽度才缩；1080P 及以下不变）
    w, h = img.size
    max_w = config.VLM_SCREEN_MAX_W
    if w > max_w:
        new_h = int(h * max_w / w)
        img = img.resize((max_w, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=config.VLM_SCREEN_JPEG_Q)
    return buf.getvalue()


if __name__ == "__main__":
    # 单文件自检：截一张图，写出查看
    data = capture_for_vlm()
    import datetime
    out = f"screen_test_{datetime.datetime.now():%H%M%S}.jpg"
    with open(out, "wb") as f:
        f.write(data)
    print(f"saved {out}, {len(data)} bytes, dim via PIL:")
    from io import BytesIO
    Image.open(BytesIO(data)).show()
