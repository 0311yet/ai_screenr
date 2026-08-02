# ai_screenr/classify/vlm.py
"""调 Ollama minicpm-v 视觉模型，输入截图+当前窗口标题，输出结构化结论。

- 用 HTTP 直接 POST /api/generate（无 ollama-py 依赖最轻）。
- images 字段为 base64 编码的 JPEG。
- 用 format schema 强制结构化输出（1.3B 小模型不可轻易只回 JSON）。
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

# 换行用 \n 字面（在源码里 \n 是两字符，Python 会解释为换行）
PROMPT_TEMPLATE = (
    "请仔细看这张截图的实际像素内容，按实际占屏最多的那部分应用场景分类。\n"
    "活动类别（7 类）：\n"
    "- 工作：代码编辑器/IDE、终端、Office 应用、专业软件、代码调试。\n"
    "- 学习：课堂视频、课程文档、教程 PDF、学习用记笔记。\n"
    "- 游戏：某款游戏的画面、游戏 HUD、游戏启动器。\n"
    "- 视频：主区域是视频播放器（B 站、爱奇艺、YouTube、直播），人在看视频。\n"
    "- 社交：聊天界面（QQ、微信、Discord、Teams）主区域在交互中。\n"
    "- 浏览：以看为主但没以上明确分类；新闻、搜索结果、通用网页。是默选。\n"
    "- 空闲：屏幕几乎没内容、屏保、控制面板、没人使用。\n"
    "规则：1) 以截图内容为主，窗口标题仅辅助。"
    "2) 先看是不是游戏/视频/社交/工作，都不符合才选浏览；"
    "全黑或屏保才是空闲。3) 不要默认返回同一类，按看到的内容选。\n"
    "输出三个字段：activity（只能选上面七个之一）、"
    "app（当前主程序名）、detail（一句汉语描述你看到的具体内容）。\n"
    "前台窗口标题提示: {title}"
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "activity": {
            "type": "string",
            "enum": ["工作", "学习", "游戏", "视频", "社交", "浏览", "空闲", "其他"],
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
    source: str = "vlm"


def _extract_json(text: str) -> dict:
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
        raw_clean = re.sub(r",(\s*[}\]])", r"\1", raw)
        return json.loads(raw_clean)
    raise ValueError(f"no json in: {text[:120]!r}")


def _normalize(d: dict) -> VlmResult:
    act = str(d.get("activity", "")).strip()
    if act and act not in config.ACTIVITY_LABELS:
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
            "temperature": 0.6,
            "num_predict": 150,
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
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = _extract_json(text)
    return _normalize(parsed)


if __name__ == "__main__":
    from capture.screen import capture_for_vlm
    img = capture_for_vlm()
    import time
    t0 = time.time()
    r = classify(img, "test")
    print(f"[{time.time()-t0:.1f}s] activity={r.activity} app={r.app!r} "
          f"detail={r.detail!r} raw={r.raw}")
