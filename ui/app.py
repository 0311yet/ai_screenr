# ai_screenr/ui/app.py
"""NiceGUI 主控台「/」：纯 Python 重建的 Sentinel 风格暗色仪表盘。

区块：
  顶栏          品牌 + 实时时钟 + 齿轮(→ /settings) + 暂停/恢复
  24h 时间轴     144 段（24h×6/h），段高=强度%，颜色=活动类目
  当前活动卡      旋转环 + 图标 + 活动名 + 持续分钟
  活动构成卡     conic 环图 + 中心「总活跃 hh:mm」+ 图例列表
  24h 强度柱图    每小时事件数%柱 + 扫描线背景
  活动日志表     最近 30 条 events

数据走 storage.db 定时拉取，engine 走 engine.get_engine() 单例。
"""
from __future__ import annotations

import datetime
import json
import time
from collections import Counter

from nicegui import ui, app
from fastapi import Query
from starlette.responses import JSONResponse, PlainTextResponse

import config
from storage import db
from engine import get_engine, EngineCallbacks
from report import daily
from ui import theme


# ── 数据辅助 ──────────────────────────────────
def _today_str() -> str:
    return datetime.date.today().isoformat()


def _recent_events(n: int = 30) -> list[dict]:
    until = time.time()
    rows = db.fetch_events_in_range(until - n * 25, until)
    return list(reversed(rows[-n:]))


def _hour_intensity(events: list[dict]) -> list[int]:
    """按小时(0-23)统计事件数 -> 强度百分比（max 归一）。返回 24 个 int 0..100。"""
    cnt = [0] * 24
    for e in events:
        try:
            cnt[datetime.datetime.fromtimestamp(e["ts"]).hour] += 1
        except Exception:
            continue
    top = max(cnt) or 1
    return [int(c * 100 / top) for c in cnt]


def _current_activity(events: list[dict]) -> dict | None:
    """最新一条非 skip 事件；若没了返回 None。"""
    for e in events:
        if e.get("source") != "skip":
            return e
    return None


def _activity_mix_today() -> tuple[Counter, int]:
    """返回 (Counter[活动]=秒数, 总活动秒)。来源：今日 segments 的 breakdown。"""
    secs: Counter[str] = Counter()
    total = 0
    for s in db.fetch_segments_of_day(_today_str()):
        bd = json.loads(s["breakdown"] or "{}")
        for a, v in bd.items():
            secs[a] += v
            total += v
    return secs, total


def _streak_minutes(events: list[dict], cur_act: str) -> int:
    """从最新事件往前数，连续同活动事件数 × 20s = 持续分钟。"""
    if not events or cur_act in ("—", "", None):
        return 0
    n = 0
    for e in events:
        if e.get("activity") == cur_act:
            n += 1
        else:
            break
    return int(round(n * config.VLM_INTERVAL_SEC / 60)) or (1 if n else 0)


# ── 渲染 helper ───────────────────────────────
def _seg_html(idx: int, activity: str, intensity: int) -> str:
    """返回时间轴 144 段之一的 HTML。"""
    color = theme.ACT_COLOR.get(activity, theme.SURFACE_CONTAINER_HIGHEST)
    # 高度用 px（避免 flex container 里 height:% 失效）
    pct = max(10, intensity) if activity != "—" else 10
    h_px = int(round(96 * pct / 100))
    title = activity + " · " + str(intensity) + "%"
    return (
        '<div class="seg" data-idx="' + str(idx) + '" title="' + title + '" '
        'style="height:' + str(h_px) + 'px;background:' + color + '">'
        '<div style="position:absolute;top:0;left:0;width:100%;height:2px;'
        'background:rgba(255,255,255,0.25);border-radius:2px 2px 0 0"></div>'
        '</div>'
    )


def _conic_gradient(mix: Counter) -> str:
    """mix -> conic-gradient(...) 字符串。"""
    if not mix:
        return theme.SURFACE_CONTAINER
    total = sum(mix.values()) or 1
    acc = 0.0
    stops = []
    for a, v in mix.most_common():
        pct = v / total * 100
        stops.append(f"{theme.ACT_COLOR.get(a, '#666')} {acc:.2f}% {acc + pct:.2f}%")
        acc += pct
    return "conic-gradient(" + ",".join(stops) + ")"


def _fmt_hhmm(total_sec: int) -> str:
    h, m = divmod(int(total_sec) // 60, 60)
    return f"{h}h {m:02d}m"


# ── 页面 ──────────────────────────────────────
@ui.page("/")
def main_page():
    theme.inject()
    state = {"st": "init", "vlm": 0, "err": 0, "paused": False}

    def on_event(ev: dict):
        if ev.get("source") == "vlm":
            state["vlm"] += 1
        if ev.get("skipped"):
            state["err"] += 1

    def on_status(s: str):
        state["st"] = s
        state["paused"] = (s == "paused")

    # ── 顶栏 ──
    with ui.element("div").classes("topbar"):
        ui.html(
            f'<span class="brand">'
            f'<span class="brand-mark">π</span>AI SCREENR</span>', sanitize=False)
        clock = ui.html(
            f'<span class="caps" style="margin-right:10px">'
            f'<span class="live-dot"></span>RUNTIME · --:--:--</span>', sanitize=False)
        pause_btn = ui.button("暂停", on_click=lambda: _toggle_pause()).props(
            "flat dense unelevated"
        ).classes("btn-ghost")

        def _toggle_pause():
            eng = get_engine()
            if state["paused"]:
                eng.resume()
                pause_btn.text = "暂停"
            else:
                eng.pause()
                pause_btn.text = "恢复"

        ui.button(icon="description", on_click=lambda: None
                  ).props("flat dense unelevated").classes("act-btn report-btn")
        ui.button(icon="settings", on_click=lambda: ui.navigate.to("/settings")
                  ).props("flat dense unelevated").classes("act-btn")

    # ── 24h 时间轴 ──
    with ui.element("div").style("padding:0 24px 8px"):
        with ui.element("div").classes("glass").style("margin-bottom:16px"):
            with ui.element("div").classes("cols-x"):
                ui.html(
                    '<div><div class="h2">24H 实时时间轴</div>'
                    '<div class="caps" style="margin-top:4px">'
                    '个柱 = 10 分钟段 · 高 = 活动强度</div></div>', sanitize=False)
                ui.html('<span class="chip">在线监听</span>', sanitize=False)
            timeline_html = ui.html('<div class="timeline-wrap"></div>', sanitize=False)
            ui.html(
                '<div class="timeline-axis">'
                + "".join(f'<span>{h:02d}</span>' for h in [0, 4, 8, 12, 16, 20, 23])
                + '</div>', sanitize=False)

    # ── 中部三卡 ──
    with ui.element("div").classes("grid-12").style("padding:0 24px"):
        # 当前活动
        with ui.element("div").classes("span-4 glass").style("margin-bottom:16px"):
            ui.html('<div class="caps">当前活动</div>', sanitize=False)
            orbit_html = ui.html('<div class="row" style="justify-content:center;margin:10px 0">'
                    '<div class="orbit"><div class="ring"></div>'
                    '<span class="material-symbols-outlined core" id="cur-icon">'
                    f'{theme.ACT_ICON["—"]}</span></div></div>', sanitize=False)
            cur_title = ui.html(
                '<div class="h3" style="text-align:center" id="cur-title">—</div>', sanitize=False)
            cur_meta = ui.html(
                '<div class="data" style="text-align:center;color:var(--on-surface-variant);'
                'margin-top:4px" id="cur-meta">启动中</div>', sanitize=False)

        # 活动构成
        with ui.element("div").classes("span-4 glass").style("margin-bottom:16px"):
            ui.html('<div class="caps">今日活动构成</div>', sanitize=False)
            donut_html = ui.html(
                '<div class="conic-donut">'
                '<div class="hole"><div class="big" id="mix-big">0h 00m</div>'
                '<div class="sub" id="mix-sub">总活跃</div></div></div>', sanitize=False)
            mix_list = ui.html('<div style="margin-top:10px" id="mix-list"></div>', sanitize=False)

        # 24h 强度柱图
        with ui.element("div").classes("span-4 glass").style("margin-bottom:16px"):
            ui.html('<div class="caps">24H 活动强度</div>', sanitize=False)
            bars_html = ui.html('<div class="bars"></div>', sanitize=False)
            ui.html(
                '<div class="timeline-axis" style="margin-top:6px">'
                + "".join(f'<span>{h:02d}</span>' for h in [0, 4, 8, 12, 16, 20, 23])
                + '</div>', sanitize=False)

    # ── 活动日志 ──
    with ui.element("div").style("padding:0 24px 24px"):
        with ui.element("div").classes("glass"):
            with ui.element("div").classes("cols-x").style("margin-bottom:10px"):
                ui.html('<div class="h3">活动日志</div>', sanitize=False)
                log_meta = ui.html(
                    '<div class="caps" id="log-meta">'
                    f'<span class="live-dot"></span>VLM · {state["vlm"]} 帧 · '
                    f'跳过 {state["err"]}</div>', sanitize=False)
            log_table = ui.html(
                '<table class="log-table"><thead><tr>'
                '<th>时间戳</th><th>事件</th><th>详情</th></tr></thead>'
                '<tbody id="log-body"></tbody></table>', sanitize=False)

    # ── 刷新 ──
    def refresh():
        now = datetime.datetime.now()
        clock.set_content(
            f'<span class="caps" style="margin-right:10px">'
            f'<span class="live-dot"></span>'
            f'{"已暂停" if state["paused"] else "RUNTIME"} · '
            f'{now.strftime("%H:%M:%S")}</span>'
        )
        if state["paused"]:
            pause_btn.text = "恢复"
        else:
            pause_btn.text = "暂停"

        # 144 段时间轴：今日 segments（since 距凌晨分钟 / 10 = 索引）
        segs = db.fetch_segments_of_day(_today_str())
        today0 = datetime.datetime.combine(now.date(), datetime.time.min).timestamp()
        slots = [None] * 144   # 24h × 6 段
        for s in segs:
            idx = int((s["since"] - today0) // 600)
            if 0 <= idx < 144:
                # 段强度 = 该段非空闲秒数比
                bd = json.loads(s["breakdown"] or "{}")
                total_sec = sum(bd.values()) or 600
                idle_sec = bd.get("空闲", 0)
                intensity = int((1 - idle_sec / total_sec) * 100)
                slots[idx] = (s["main_activity"], max(20, intensity))
        tls = "".join(
            _seg_html(i, *s) if s is not None else _seg_html(i, "—", 10)
            for i, s in enumerate(slots)
        )
        timeline_html.set_content(f'<div class="timeline-wrap">{tls}</div>')

        # 当前活动
        recent = _recent_events(60)
        cur = _current_activity(recent)
        if cur:
            act = cur["activity"]
            icon = theme.ACT_ICON.get(act, theme.ACT_ICON["其他"])
            color = theme.ACT_COLOR.get(act, theme.SURFACE_CONTAINER_HIGHEST)
            mins = _streak_minutes(recent, act)
            # 通过覆盖 orbit 块整体 set_html 重设颜色，不走 JS
            orbit_html.set_content(
                '<div class="row" style="justify-content:center;margin:10px 0">'
                '<div class="orbit" style="--orbit-c:' + color + '">'
                '<div class="ring" style="border-color:' + color + ' ' + color
                + ' ' + color + ' transparent;">'
                '<span class="material-symbols-outlined core" '
                'style="color:' + color + '">' + icon + '</span></div></div></div>'
            )
            cur_title.set_content(f'<div class="h3" style="text-align:center">{act}</div>')
            cur_meta.set_content(
                '<div class="data" style="text-align:center;'
                'color:var(--on-surface-variant);margin-top:4px">'
                f'已持续 {mins} 分钟 · {cur["app"]}</div>'
            )

        # 活动构成
        mix, total = _activity_mix_today()
        # conic gradient 直写在 style 上
        if mix:
            stops = []
            acc = 0.0
            tot = total or 1
            for a, v in mix.most_common():
                pct = v / tot * 100
                stops.append(
                    f"{theme.ACT_COLOR.get(a, '#666')} {acc:.2f}% {acc + pct:.2f}%"
                )
                acc += pct
            grad = "conic-gradient(" + ",".join(stops) + ")"
        else:
            grad = theme.SURFACE_CONTAINER
        donut_html.set_content(
            f'<div class="conic-donut" style="background:{grad}">'
            '<div class="hole"><div class="big" id="mix-big">'
            f'{_fmt_hhmm(total)}</div>'
            '<div class="sub" id="mix-sub">总活跃</div></div></div>'
        )
        rows_html = "".join(
            f'<div class="mix-row"><span>'
            f'<span class="swatch" style="background:{theme.ACT_COLOR.get(a, "#666")}"></span>'
            f'{a}</span><span>{_fmt_hhmm(v)}</span></div>'
            for a, v in mix.most_common() if v > 0
        ) or '<div class="caps" style="opacity:.6;padding:6px 0">暂无数据</div>'
        mix_list.set_content(rows_html)

        # 24h 强度柱图
        intensity = _hour_intensity(recent)
        bars = "".join(
            f'<div class="bar" style="height:{max(8, v)}%">'
            f'<div class="cap"></div></div>'
            for v in intensity
        )
        bars_html.set_content('<div class="bars">' + bars + '</div>')

        # 活动日志表
        rows = _recent_events(30)
        body = ""
        for e in rows:
            t = datetime.datetime.fromtimestamp(e["ts"]).strftime("%H:%M:%S")
            a = e["activity"]
            icon = theme.ACT_ICON.get(a, theme.ACT_ICON["其他"])
            color = theme.ACT_COLOR.get(a, "#888")
            body += (
                f'<tr><td style="color:var(--on-surface-variant)">{t}</td>'
                f'<td style="color:{color}">'
                f'<span class="material-symbols-outlined ev-icon">{icon}</span>{a}</td>'
                f'<td>{e["app"] or ""} · {e["detail"] or ""}</td></tr>'
            )
        log_table.set_content(
            '<table class="log-table"><thead><tr>'
            '<th>时间戳</th><th>事件</th><th>详情</th></tr></thead>'
            f'<tbody>{body or "<tr><td colspan=3 class=\"caps\" "
            "style=\"opacity:.6;padding:10px\">暂无事件</td></tr>"}</tbody></table>'
        )
        # log-meta 重建到当前统计数（纯 set_html）
        log_meta.set_content(
            f'<span class="live-dot"></span>VLM · {state["vlm"]} 帧 · '
            f'跳过 {state["err"]}'
        )

    from ui import _seg_detail
    _seg_detail.inject()
    from ui import _report_modal
    _report_modal.inject()

    ui.timer(5.0, refresh)
    refresh()

    # ── 启动单例 engine ──
    try:
        get_engine(EngineCallbacks(on_event=on_event, on_status=on_status))
    except Exception:
        # 即便 Ollama 没起，也要让页面可看
        ui.notify("后端引擎初始化失败，数据为空。请检查 Ollama。",
                  type="warning", position="top")

    # 退出页面不 stop engine（单例随进程生命）
    app.on_disconnect(lambda: None)


# ── 段详情 JSON 端点 ──────────────────────
@app.get("/segment_info")
async def _segment_info(idx: int = Query(..., ge=0, lt=144)):
    """返回指定 144 段位置的详情 JSON。点 .seg 时调用。"""
    import datetime as _dt
    now = _dt.datetime.now()
    today0 = _dt.datetime.combine(now.date(), _dt.time.min).timestamp()
    since = today0 + idx * 600     # 10 分钟一段
    until = since + 600
    segs = db.fetch_segments_of_day(now.date().isoformat())
    seg = None
    for s in segs:
        if s["since"] >= since and s["since"] < until:
            seg = s
            break
    if seg is None:
        return JSONResponse({
            "empty": True, "idx": idx,
            "since_str": _dt.datetime.fromtimestamp(since).strftime("%H:%M"),
            "until_str": _dt.datetime.fromtimestamp(until).strftime("%H:%M"),
        })
    bd = json.loads(seg["breakdown"] or "{}")
    top_apps_raw = json.loads(seg["top_apps"] or "{}")
    def _to_min(sec):
        m = float(sec) / 60.0
        if m < 60:
            return str(int(m)) + "分"
        return str(int(m/60)) + "h" + str(int(m%60)).zfill(2) + "m"
    breakdown = [{"activity": k, "sec": round(v, 1), "mins": _to_min(v),
                  "color": theme.ACT_COLOR.get(k, "#666666")}
                 for k, v in sorted(bd.items(), key=lambda x:-x[1]) if v > 0]
    top_apps = [{"app": k, "sec": round(v, 1), "mins": _to_min(v)}
                for k, v in sorted(top_apps_raw.items(), key=lambda x:-x[1]) if v > 0]
    summary = seg["main_activity"]
    if top_apps:
        summary = ("这段主要在「" + top_apps[0]["app"] + "」里"
                   + seg["main_activity"] + "，挂了约" + top_apps[0]["mins"])
    return JSONResponse({
        "empty": False, "idx": idx,
        "since_str": _dt.datetime.fromtimestamp(seg["since"]).strftime("%H:%M"),
        "until_str": _dt.datetime.fromtimestamp(seg["until"]).strftime("%H:%M"),
        "main_activity": seg["main_activity"],
        "icon": theme.ACT_ICON.get(seg["main_activity"], "apps"),
        "color": theme.ACT_COLOR.get(seg["main_activity"], "#666666"),
        "summary": summary,
        "breakdown": breakdown,
        "top_apps": top_apps,
        "vlm_count": seg["vlm_count"],
        "skip_count": seg["skip_count"],
        "fallback_count": seg["fallback_count"],
    })


# ── 日报端点 ───────────────────
@app.post("/generate_report")
async def _generate_report(date: str = Query(None)):
    """生成指定日期（默认今天）的日报，返回 md 文本。"""
    import os
    d = date or datetime.date.today().isoformat()
    try:
        out_path = daily.generate(d)
        with open(out_path, encoding="utf-8") as f:
            md = f.read()
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})
    return JSONResponse({"ok": True, "date": d, "md": md})


@app.get("/report_file")
async def _report_file(date: str = Query(...)):
    """下载指定日期的 .md 日报。"""
    import os
    out_path = os.path.join(config.REPORT_DIR, f"{date}.md")
    if not os.path.exists(out_path):
        daily.generate(date)  # 现场生成
    with open(out_path, encoding="utf-8") as f:
        md = f.read()
    from starlette.responses import Response
    return Response(
        md, media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ai_screenr_{date}.md"'},
    )
