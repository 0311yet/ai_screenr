# ai_screenr/ui/app.py
"""NiceGUI 页面：黑色极客风活动监控面板。

- 极客暗色主题（注入 CSS：深底 + 霓虹青/绿强调 + 等宽字体）
- 顶部状态栏：运行状态徽标 + 实时时钟 + 当前活动
- 统计卡片：今日活跃分钟 / VLM 帧数 / 跳过错误数 / 当前活动
- ECharts 环图：今日活动占比
- ECharts 24h 色带：10 分钟时间线
- 最近事件流（每 5s 刷新）
- 设置：开机自启开关
数据直接从 storage.db 定时拉取，不解耦线程信号。
"""
from __future__ import annotations

import datetime
import json
import time
from collections import Counter

from nicegui import ui, app

from storage import db
from engine import MonitorEngine, EngineCallbacks
from ollama_runner import ensure_ollama_running
from ui import autostart

# ── 配色 ─────────────────────────────────────
BG = "#0a0e14"
CARD = "#11161f"
ACCENT = "#4ee0c4"
ACCENT2 = "#7cf24a"
TEXT = "#c7cdd7"
SUBTLE = "#6b7480"
DANGER = "#ff6b6b"

ACT_COLOR_HEX = {
    "工作": "#4ee0c4", "游戏": "#ff6b6b", "视频": "#c77dff",
    "社交": "#7cf24a", "浏览": "#a0a8b3", "空闲": "#2a3240",
    "其他": "#5a626f", "—":   "#1a1f28",
}

_THEME_CSS = f"""
<style>
body {{ background:{BG}!important;color:{TEXT};
        font-family:'JetBrains Mono','Cascadia Code','Consolas',monospace!important; }}
.q-card,.nicegui-card {{ background:{CARD}!important;border:1px solid #1e2632!important;
        border-radius:8px!important;box-shadow:0 8px 24px rgba(0,0,0,.4); }}
.q-card .q-card__section,.nicegui-card>* {{ color:{TEXT}; }}
.q-separator {{ background:#1e2632!important; }}
.q-badge {{ background:{ACCENT};color:#0a0e14;font-weight:700; }}
.mono {{ font-family:'JetBrains Mono','Cascadia Code','Consolas',monospace; }}
.accent {{ color:{ACCENT}; }} .accent2 {{ color:{ACCENT2}; }}
.subtle {{ color:{SUBTLE}; }} .danger {{ color:{DANGER}; }}
.big {{ font-size:24px;font-weight:700;letter-spacing:2px; }}
.title {{ font-size:12px;color:{SUBTLE};letter-spacing:2px;text-transform:uppercase; }}
.ticker {{ font-size:11px;color:{SUBTLE}; }}
.stat {{ font-size:28px;font-weight:700;color:{ACCENT}; }}
.stat-unit {{ font-size:12px;color:{SUBTLE}; }}
.ev {{ padding:5px 0;border-bottom:1px dashed #1e2632;font-size:12px;
      font-family:'JetBrains Mono','Cascadia Code','Consolas',monospace; }}
.ev .src {{ color:{SUBTLE}; }}
.ev .act-工作{{color:{ACCENT};}} .ev .act-游戏{{color:{DANGER};}}
.ev .act-视频{{color:#c77dff;}} .ev .act-社交{{color:{ACCENT2};}}
.ev .act-浏览{{color:#a0a8b3;}} .ev .act-空闲{{color:#2a3240;}}
.ev .act-其他{{color:#5a626f;}} .ev .act-—{{color:#1a1f28;}}
.q-toggle__thumb {{ color:{ACCENT}!important; }}
.q-toggle__inner--truthful .q-toggle__track {{ background:{ACCENT}!important; }}
</style>
"""


def _recent_events(n: int = 30):
    until = time.time()
    rows = db.fetch_events_in_range(until - n * 25, until)
    return list(reversed(rows[-n:]))


def _stat_card(title: str, icon_name: str):
    """返回卡片内“数字 label”的引用，刷新时直接 set text。"""
    ui.label(title).classes("title")
    with ui.row().classes("items-end gap-2 q-mt-xs"):
        ui.icon(icon_name).classes("subtle q-mb-sm")
        val = ui.label("--").classes("stat")
        unit = ui.label("").classes("stat-unit q-mb-xs")
    return val, unit


def _update_timeline(chart, tl):
    """tl = [(hhmm, activity)]，横轴时间、每段一个色块。"""
    chart.options["xAxis"]["data"] = [t for t, _ in tl]
    chart.options["series"] = [{
        "type": "bar",
        "data": [{"value": 1,
                  "itemStyle": {"color": ACT_COLOR_HEX.get(a, "#444")},
                  "name": a} for _, a in tl],
        "barWidth": "100%",
        "showBackground": True,
        "backgroundStyle": {"color": "#151a23"},
    }]
    chart.update()


@ui.page("/")
def main_page():
    state = {"status": "未知", "paused": False, "vlm": 0, "err": 0, "engine": None}

    ui.add_head_html(_THEME_CSS)

    # 状态回调
    def on_event(ev):
        if ev.get("source") == "vlm":
            state["vlm"] += 1
        if ev.get("skipped"):
            state["err"] += 1

    def on_status(s):
        state["status"] = s
        state["paused"] = (s == "paused")

    # ── 顶栏 ──
    with ui.row().classes("w-full items-center justify-between q-pa-md"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("monitor_heart").classes("accent")
            ui.label("AI_SCREENR").classes("accent big")
            status_badge = ui.badge("INIT").props("outline")
        with ui.row().classes("items-center gap-3"):
            cur_label = ui.label("当前: —").classes("ticker")
            clock_label = ui.label("--:--:--").classes("ticker")

    ui.separator()

    # ── 统计卡片 ──
    active_val, _u1 = _stat_card("今日活跃", "schedule")
    cur_val, _u2 = _stat_card("当前活动", "sports_esports")
    vlm_val, _u3 = _stat_card("VLM 帧", "memory")
    err_val, _u4 = _stat_card("跳过/错误", "warning")

    # ── 图表 ──
    with ui.row().classes("w-full q-pa-md gap-3"):
        with ui.card().classes("col"):
            ui.label("今日活动占比").classes("title")
            pie = ui.echart({
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "item"},
                "legend": {"bottom": 0, "textStyle": {"color": TEXT}, "textStyle": {"color": TEXT}},
                "series": [{"type": "pie", "radius": ["45%", "72%"],
                            "label": {"color": TEXT},
                            "itemStyle": {"borderColor": CARD, "borderWidth": 2},
                            "data": []}],
            }).classes("w-full h-64")
        with ui.card().classes("col-7"):
            ui.label("24h 时间线").classes("title")
            timeline = ui.echart({
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "item", "formatter": "{b}"},
                "grid": {"left": 20, "right": 10, "top": 8, "bottom": 24},
                "xAxis": {"type": "category", "data": [],
                          "axisLabel": {"color": SUBTLE, "fontSize": 10,
                                        "interval": 5},
                          "axisLine": {"lineStyle": {"color": "#2a3240"}}},
                "yAxis": {"type": "category", "data": [""], "show": False},
                "series": [{"type": "bar", "data": []}],
            }).classes("w-full h-64")

    # ── 事件流 ──
    with ui.card().classes("w-full q-ma-md"):
        ui.label("最近事件流").classes("title")
        ev_list = ui.column().classes("w-full q-mt-sm")

    # ── 设置 ──
    with ui.card().classes("w-full q-ma-md"):
        ui.label("设置").classes("title")
        with ui.row().classes("items-center justify-between q-mt-sm"):
            ui.label("开机自启动").classes("subtle")
            autostart_toast = ui.label("").classes("ticker")
            ui.switch("", value=autostart.is_enabled(),
                      on_change=lambda e: _toggle_autostart(e.value, autostart_toast))

    def _toggle_autostart(v, toast):
        ok = autostart.enable() if v else autostart.disable()
        toast.text = ("✓ 已开启开机自启" if (v and ok) else
                      "✓ 已关闭开机自启" if (not v and ok) else
                      "× 操作失败，请检查权限")
        toast.classes(remove="accent2 danger")
        toast.classes(add="accent2" if ok else "danger")

    # ── 主刷新 ──
    def refresh():
        clock_label.text = datetime.datetime.now().strftime("%H:%M:%S")
        segs = db.fetch_segments_of_day(datetime.date.today().isoformat())
        act_sec: Counter[str] = Counter()
        total = 0.0
        tl = []
        for s in segs:
            for a, sec in json.loads(s["breakdown"] or "{}").items():
                act_sec[a] += sec
                total += sec
            tl.append((datetime.datetime.fromtimestamp(s["since"]).strftime("%H:%M"),
                       s["main_activity"]))
        # 状态徽标
        status_badge.text = ("运行中" if state["status"] == "running"
                             else "已暂停" if state["status"] == "paused"
                             else str(state["status"]))
        # 当前活动
        recent = _recent_events(1)
        cur = recent[0] if recent else None
        if cur:
            cur_label.text = f"当前: {cur['activity']} · {cur['app']}"
            cur_label.style(f"color: {ACT_COLOR_HEX.get(cur['activity'], TEXT)}")
            cur_val.text = cur["activity"]
            cur_val.style(f"color: {ACT_COLOR_HEX.get(cur['activity'], ACCENT)}")
        # 统计卡
        active_val.text = f"{total/60:.1f}"
        active_val.classes("stat-unit", remove=True) if False else None
        # 想给 active_val 也带个单位"分钟"，借助返回的 unit label
        vlm_val.text = str(state["vlm"])
        err_val.text = str(state["err"])
        # 饼图
        pie.options["series"][0]["data"] = [
            {"name": a, "value": round(sec / 60, 1),
             "itemStyle": {"color": ACT_COLOR_HEX.get(a, "#888")}}
            for a, sec in act_sec.most_common() if sec > 0]
        pie.update()
        # 时间线
        _update_timeline(timeline, tl)
        # 事件流
        ev_list.clear()
        with ev_list:
            for ev in _recent_events(20):
                hhmm = datetime.datetime.fromtimestamp(ev["ts"]).strftime("%H:%M:%S")
                tail = (f' <span class="ticker">skip:{ev["note"]}</span>'
                        if ev["skipped"] else "")
                ui.html(
                    f'<div class="ev">'
                    f'<span class="src">[{hhmm}][{ev["source"]}]</span> '
                    f'<span class="act-{ev["activity"]}">{ev["activity"]}</span> '
                    f'<span>{ev["app"]}</span> '
                    f'<span class="subtle">{ev["detail"]}</span>{tail}</div>'
                )

    ui.timer(5.0, refresh)
    refresh()

    # 启动引擎
    if not ensure_ollama_running():
        ui.notify("Ollama 未运行或模型未安装，请先启动 ollama serve 并 pull minicpm-v4.6",
                  type="warning", position="top", timeout=0)
        state["status"] = "error"
    else:
        state["engine"] = MonitorEngine(EngineCallbacks(on_event=on_event,
                                                         on_segment=None,
                                                         on_status=on_status))
        state["engine"].start()

    def _on_disconnect():
        if state["engine"]:
            state["engine"].stop()
    app.on_disconnect(_on_disconnect)
