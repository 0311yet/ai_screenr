# ai_screenr/storage/db.py
"""SQLite schema + 写入 + 段聚合查询。

三张表：
- events : 20s 级瞬时事件
- segments : 10min 聚合段
- reports : 日报
"""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import time
from typing import Any

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS events(
  ts REAL PRIMARY KEY,
  activity TEXT NOT NULL,
  app TEXT,
  detail TEXT,
  source TEXT,
  win_title TEXT,
  proc_name TEXT,
  idle_sec INTEGER,
  skipped INTEGER DEFAULT 0,
  note TEXT
);
CREATE INDEX IF NOT EXISTS events_ts ON events(ts);

CREATE TABLE IF NOT EXISTS segments(
  since REAL PRIMARY KEY,
  until REAL NOT NULL,
  main_activity TEXT NOT NULL,
  breakdown TEXT,
  top_apps TEXT,
  vlm_count INTEGER DEFAULT 0,
  skip_count INTEGER DEFAULT 0,
  fallback_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS segments_since ON segments(since);

CREATE TABLE IF NOT EXISTS reports(
  date TEXT PRIMARY KEY,
  total_active_sec INTEGER,
  breakdown TEXT,
  timeline TEXT,
  created_at TEXT
);
"""

_conn: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    """单连接进程级缓存。check_same_thread=False 让 sqlite 跨线程安全；写操作靠 GIL 串行化。"""
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.row_factory = sqlite3.Row
    return _conn


def init_db() -> None:
    """建表（幂等）。"""
    conn = _connect()
    conn.executescript(SCHEMA)
    conn.commit()


def insert_event(
    ts: float,
    activity: str,
    app: str,
    detail: str,
    source: str,
    win_title: str,
    proc_name: str,
    idle_sec: int,
    skipped: int = 0,
    note: str = "",
) -> None:
    """写一条 20s 级事件。冲突用 REPLACE（同一 ts 重采样覆盖）。"""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO events
           (ts, activity, app, detail, source, win_title, proc_name, idle_sec, skipped, note)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (ts, activity, app, detail, source, win_title, proc_name, idle_sec, skipped, note),
    )
    conn.commit()


def fetch_events_in_range(since: float, until: float) -> list[dict[str, Any]]:
    """取 [since, until) 内所有事件，按 ts 升序。"""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM events WHERE ts >= ? AND ts < ? ORDER BY ts",
        (since, until),
    ).fetchall()
    return [dict(r) for r in rows]


def insert_segment(seg) -> None:
    """段聚合结果写入。seg: aggregator.segment.Segment（鸭子类型）。"""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO segments
           (since, until, main_activity, breakdown, top_apps,
            vlm_count, skip_count, fallback_count)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            seg.since,
            seg.until,
            seg.main_activity,
            json.dumps(seg.breakdown, ensure_ascii=False),
            json.dumps(seg.top_apps, ensure_ascii=False),
            seg.vlm_count,
            seg.skip_count,
            seg.fallback_count,
        ),
    )
    conn.commit()


def fetch_segments_of_day(date_str: str) -> list[dict[str, Any]]:
    """取某一天的所有段。date_str 形如 'YYYY-MM-DD'。"""
    d = datetime.date.fromisoformat(date_str)
    start = datetime.datetime.combine(d, datetime.time.min).timestamp()
    end = datetime.datetime.combine(d + datetime.timedelta(days=1), datetime.time.min).timestamp()
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM segments WHERE since >= ? AND since < ? ORDER BY since",
        (start, end),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_report(date_str: str, total_active_sec: int, breakdown: dict, timeline: list) -> None:
    """写/更新日报。"""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO reports (date, total_active_sec, breakdown, timeline, created_at)
           VALUES (?,?,?,?,?)""",
        (
            date_str,
            total_active_sec,
            json.dumps(breakdown, ensure_ascii=False),
            json.dumps(timeline, ensure_ascii=False),
            time.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()


def close() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
