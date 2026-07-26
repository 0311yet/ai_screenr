# ai_screenr/report/daily.py
"""日报生成：当天 segments -> Markdown -> config.REPORT_DIR/date.md，并 upsert reports 表。"""
from __future__ import annotations

import datetime
import json
import os
from collections import Counter

import config
from storage import db

ACT_LABELS = config.ACTIVITY_LABELS


def generate(date_str: str | None = None) -> str:
    """生成日报，返回写出的 .md 路径。"""
    today = date_str or datetime.date.today().isoformat()
    segs = db.fetch_segments_of_day(today)
    out_dir = config.REPORT_DIR
    os.makedirs(out_dir, exist_ok=True)

    # 汇总各活动秒数（用 breakdown 求和）
    act_sec: Counter[str] = Counter()
    timeline = []           # [{since, until, main}]
    total_active = 0.0
    for s in segs:
        bd = json.loads(s["breakdown"] or "{}")
        for act, sec in bd.items():
            act_sec[act] += sec
            total_active += sec
        timeline.append({
            "since": s["since"],
            "until": s["until"],
            "main": s["main_activity"],
        })

    # 排序占比
    breakdown = dict(act_sec.most_common())

    # 写 Markdown
    lines = [f"# 活动日报 {today}", ""]
    lines.append("## 占比")
    if total_active:
        for act, sec in breakdown.items():
            pct = sec / total_active * 100
            lines.append(f"- **{act}**: {sec/60:.1f} 分钟 ({pct:.1f}%)")
    else:
        lines.append("- (无活动数据)")
    lines.append("")
    lines.append(f"活跃总时长: {total_active/60:.1f} 分钟")
    lines.append("")
    lines.append("## 时间线（按 10 分钟段）")
    for seg in timeline:
        hhmm = datetime.datetime.fromtimestamp(seg["since"]).strftime("%H:%M")
        lines.append(f"- {hhmm} {seg['main']}")
    md = "\n".join(lines) + "\n"

    out_path = os.path.join(out_dir, f"{today}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    # upsert reports 表
    db.upsert_report(today, int(total_active), breakdown, timeline)
    return out_path
