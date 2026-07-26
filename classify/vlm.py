# ai_screenr/classify/vlm.py
"""调 Ollama minicpm-v 视觉模型，输入截图+当前窗口标题，输出结构化结论。

- 用 HTTP 直接 POST /api/generate（无 ollama-py 依赖最轻）。
- images 字段为 base64 编码的 JPEG。
- 固定 prompt 强制只回 JSON。
- 解析取首个 {...} 块，失败抛异常由 merge 走 fallback。
- 超时由 config.VLM_TIMEOUT_SEC 控制。
"""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

import requests

import config

PROMPT_TEMPLATE = (
    "你在看用户电脑屏幕的截图。判断用户当前在做什么。"
    "前台窗口标题提示: {title}"
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "activity": {
            "type": "string",
            "enum": ["工作", "游戏", "视频", "社交", "浏览", "空闲", "其他"],
        },
        "app": {"type": "string"},
        "detail": {"type": "string"},
    },
    "required": ["activity", "app", "detail"],
}

_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
_JSON_GREEDY_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class VlmResult:
    activity: str
    app: str
    detail: str
    raw: str = ""
    source: str = "vlm"   # fallback 实现那侧会覆盖为 'fallback'


def _extract_json(text: str) -> dict:
    """从模型输出里鲁棒提取 JSON：先找最小 {...}，再退回贪婪。"""
    if not text:
        raise ValueError("empty text")
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    m = _JSON_GREEDY_RE.search(text)
    if m:
        raw = m.group(0)
        # 去掉可能的尾随逗号
        raw_clean = re.sub(r",(\s*[}\]])", r"\1", raw)
        return json.loads(raw_clean)
    raise ValueError(f"no json in: {text[:120]!r}")


def _normalize(d: dict) -> VlmResult:
    """把解析出的 dict 映射为 VlmResult。非法 activity 兜底为 '其他'。"""
    act = str(d.get("activity", "")).strip()
    if act and act not in config.ACTIVITY_LABELS:
        # 模型有时回 "工作/写作" 这种，取第一个匹配的 label
        act = next((lab for lab in config.ACTIVITY_LABELS if lab in act), "其他")
    if not act:
        act = "其他"
    return VlmResult(
        activity=act,
        app=str(d.get("app", "")).strip(),
        detail=str(d.get("detail", "")).strip(),
        raw=json.dumps(d, ensure_ascii=False),
        source="vlm",
    )


def classify(image_bytes: bytes, window_title: str) -> VlmResult:
    """送 Ollama，返回 VlmResult。
    超时/网络/解析失败 raise Exception，由上层 merge 走 fallback。
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = PROMPT_TEMPLATE.replace("{title}", window_title or "(无)")
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "images": [b64],
        "stream": False,
        "format": RESPONSE_SCHEMA,
        "options": {
            "temperature": 0.1,
            "num_predict": 120,
        },
    }
    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json=payload,
        timeout=config.VLM_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data.get("response", "") or ""
    # format=json 模式下 response 应已经是合法 JSON；仍容错解析
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = _extract_json(text)
    return _normalize(parsed)


if __name__ == "__main__":
    # 自检：截一张图送 VLM，打印结论。
    from capture.screen import capture_for_vlm
    img = capture_for_vlm()
    import time
    t0 = time.time()
    r = classify(img, "test")
    print(f"[{time.time()-t0:.1f}s] activity={r.activity} app={r.app!r} detail={r.detail!r} raw={r.raw}")
