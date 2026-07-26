# ai_screenr/aggregator/segment.py
"""10 分钟段聚合：把最近约 30 条 20s 事件聚合成一段。

统计型聚合（无额外模型）：
- 被跳过的 skipped=1 帧不计入 breakdown（事件缺失，不该计为活动秒数）
- 主标签 = 占比最大的 activity（同占比取靠前顺序）
- breakdown:{activity: 秒数}
- top_apps: 按 app 出现时长 Top3
- vlm_count/skip_count/fallback_count: 段内来源计数
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from aggregator import STEP_SEC   # 来自 __init__.py 中 = config.VLM_INTERVAL_SEC


@dataclass
class Segment:
    since: float
    until: float
    main_activity: str
    breakdown: dict        # {activity: 秒数}
    top_apps: dict         # {app: 秒数}  Top3
    vlm_count: int
    skip_count: int
    fallback_count: int


def build(events: list[dict]) -> Segment:
    """events 一组 event dict（含字段 ts, activity, app, source, skipped）。"""
    if not events:
        # 无事件空段，记为"空闲"
        return Segment(
            since=0.0, until=0.0, main_activity="空闲",
            breakdown={"空闲": STEP_SEC * 30},
            top_apps={"": 0}, vlm_count=0, skip_count=0, fallback_count=0,
        )
    act_sec: Counter[str] = Counter()
    app_sec: Counter[str] = Counter()
    vlm_n = skip_n = fb_n = 0
    # 每条事件贡献 STEP_SEC；末条用下一条 ts - 本条 ts 推导更准，没下条用 STEP_SEC
    for i, e in enumerate(events):
        ts = e["ts"]
        next_ts = events[i + 1]["ts"] if i + 1 < len(events) else ts + STEP_SEC
        dur = max(0.0, min(next_ts - ts, STEP_SEC))
        if e.get("skipped"):
            skip_n += 1
            continue
        act_sec[e["activity"]] = act_sec.get(e["activity"], 0) + dur
        app = e.get("app") or e.get("proc_name") or "未知"
        app_sec[app] = app_sec.get(app, 0) + dur
        if e.get("source") == "vlm":
            vlm_n += 1
        elif e.get("source") == "fallback":
            fb_n += 1
    if not act_sec:
        # 全被 skip 的段 -> 主标签空闲
        main = "空闲"
        act_sec[main] = min(seg_seconds(events), STEP_SEC * 30)
    else:
        main = act_sec.most_common(1)[0][0]
    top_apps = dict(sorted(app_sec.items(), key=lambda x: -x[1])[:3])
    return Segment(
        since=events[0]["ts"],
        until=events[-1]["ts"] + STEP_SEC,
        main_activity=main,
        breakdown={k: round(v, 1) for k, v in act_sec.items()},
        top_apps={k: round(v, 1) for k, v in top_apps.items()},
        vlm_count=vlm_n,
        skip_count=skip_n,
        fallback_count=fb_n,
    )


def seg_seconds(events: list[dict]) -> float:
    if len(events) < 2:
        return STEP_SEC * len(events)
    return events[-1]["ts"] - events[0]["ts"]
