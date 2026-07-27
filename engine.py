# ai_screenr/engine.py
"""后台调度引擎：纯 Python 线程循环，无 Qt 依赖。

- win_loop     : 1Hz 取 WinSnapshot 缓存到 self.latest_win
- vlm_loop     : 每 VLM_INTERVAL_SEC 强制一次推理
                 - 上一帧仍在推理 -> 跳过此 tick（记 skip）
                 - 锁屏/屏灭 -> 直接写空闲事件，不截图不调 VLM
- segment_loop : 每 SEGMENT_AGGREGATE_MIN 聚合一次
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import config
from capture import windows, screen
from classify import merge
from storage import db
from aggregator import segment as seg_mod
from ollama_runner import ensure_ollama_running

log = logging.getLogger(__name__)


@dataclass
class EngineCallbacks:
    on_event: callable | None = None   # 每条 20s 事件完成
    on_segment: callable | None = None
    on_status: callable | None = None  # 'running'/'paused'/'error'/'stopped'


class MonitorEngine:

    def __init__(self, cb: EngineCallbacks | None = None):
        self.cb = cb or EngineCallbacks()
        self.latest_win = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._vlm_running = threading.Lock()  # 互斥，跳过策略

    def start(self) -> None:
        self._stop.clear()
        self._pause.clear()
        for tgt, name in [
            (self._win_loop, "win_loop"),
            (self._vlm_loop, "vlm_loop"),
            (self._segment_loop, "seg_loop"),
        ]:
            t = threading.Thread(target=tgt, name=name, daemon=True)
            t.start()
        self._emit_status("running")

    def stop(self) -> None:
        self._stop.set()
        self._emit_status("stopped")
        db.close()

    def pause(self) -> None:
        self._pause.set()
        self._emit_status("paused")

    def resume(self) -> None:
        self._pause.clear()
        self._emit_status("running")

    # ── 工具 ──────────────────────────────────
    def _emit_status(self, s):
        if self.cb.on_status:
            try: self.cb.on_status(s)
            except Exception: log.exception("on_status")

    def _emit_event(self, ev: dict):
        if self.cb.on_event:
            try: self.cb.on_event(ev)
            except Exception: log.exception("on_event")

    def _emit_segment(self, seg):
        if self.cb.on_segment:
            try: self.cb.on_segment(seg)
            except Exception: log.exception("on_segment")

    @staticmethod
    def _align_next_tick(now: float, interval: float) -> float:
        """对齐到 interval 整数边界。"""
        return interval - (now % interval)

    # ── 线程循环 ──────────────────────────────
    def _win_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.latest_win = windows.snapshot()
            except Exception:
                log.exception("win snapshot")
            time.sleep(config.WIN_SAMPLE_INTERVAL_SEC)

    def _vlm_loop(self) -> None:
        while not self._stop.is_set():
            wait = self._align_next_tick(time.time(), config.VLM_INTERVAL_SEC)
            if self._stop.wait(wait):
                break
            if self._pause.is_set():
                continue
            win = self.latest_win
            if win is None:
                continue
            # 锁屏/屏灭 或 键鼠静止超过阈值 -> 空闲，不调 VLM
            if win.locked or win.screen_off:
                ev = self._make_event(win, activity="空闲", app="系统",
                                      detail="锁屏", source="system", skipped=False)
                self._write_event(ev)
                continue
            if win.idle_sec and win.idle_sec >= config.IDLE_THRESHOLD_SEC:
                ev = self._make_event(win, activity="空闲", app=win.proc_name or "系统",
                                      detail=f"键鼠静止 {int(win.idle_sec)}s",
                                      source="system", skipped=False)
                self._write_event(ev)
                continue
            # 跳过策略：上一帧仍在推理 -> skip
            if not self._vlm_running.acquire(blocking=False):
                ev = self._make_event(win, activity="—", app="", detail="",
                                      source="skip", skipped=True,
                                      note="prev vlm still running")
                self._write_event(ev)
                continue
            try:
                img = screen.capture_for_vlm()
                res = merge.classify_one(win, img)
                ev = self._make_event(
                    win, activity=res.activity, app=res.app, detail=res.detail,
                    source=res.source, skipped=False, raw=res.raw)
                self._write_event(ev)
            except Exception:
                log.exception("vlm tick")
                ev = self._make_event(win, activity="其他", app=win.proc_name,
                                      detail="vlm error", source="fallback",
                                      skipped=True, note="exception")
                self._write_event(ev)
            finally:
                self._vlm_running.release()

    def _segment_loop(self) -> None:
        seg_sec = config.SEGMENT_AGGREGATE_MIN * 60
        while not self._stop.is_set():
            wait = self._align_next_tick(time.time(), seg_sec)
            if self._stop.wait(wait):
                break
            self._do_aggregate()
        self._do_aggregate()

    def _do_aggregate(self) -> None:
        seg_sec = config.SEGMENT_AGGREGATE_MIN * 60
        until = time.time()
        since = until - seg_sec
        try:
            rows = db.fetch_events_in_range(since, until)
            if not rows:
                return
            seg = seg_mod.build(rows)
            if seg.since == 0.0 and seg.until == 0.0:
                return
            db.insert_segment(seg)
            self._emit_segment(seg)
        except Exception:
            log.exception("aggregate")

    # ── 事件构造 ───────────────────────────────
    def _make_event(self, win, *, activity, app, detail, source, skipped,
                    raw="", note="") -> dict:
        return {
            "ts": win.ts,
            "activity": activity or "其他",
            "app": app,
            "detail": detail,
            "source": source,
            "win_title": win.window_title,
            "proc_name": win.proc_name,
            "idle_sec": win.idle_sec,
            "skipped": int(skipped or 0),
            "note": note,
            "raw": raw,
        }

    def _write_event(self, ev: dict) -> None:
        try:
            db.insert_event(
                ts=ev["ts"], activity=ev["activity"], app=ev["app"],
                detail=ev["detail"], source=ev["source"],
                win_title=ev["win_title"], proc_name=ev["proc_name"],
                idle_sec=ev["idle_sec"], skipped=ev["skipped"], note=ev["note"],
            )
            self._emit_event(ev)
        except Exception:
            log.exception("write event")


def init_storage() -> None:
    db.init_db()


# ── 模块级单例（避免多页面各起一个 engine 导致双调 VLM）─
_engine: MonitorEngine | None = None
_engine_lock = threading.Lock()


def get_engine(cb: EngineCallbacks | None = None) -> MonitorEngine:
    """返回单例 engine。首次调用会初始化。传 cb 也只在首次生效。"""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                init_storage()
                ensure_ollama_running()   # 启动期同步拉起 Ollama + 校验模型
                _engine = MonitorEngine(cb or EngineCallbacks())
                _engine.start()
    return _engine
