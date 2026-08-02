"""测点：aggregator.segment.build 聚合逻辑正确性。
离线、不依赖 VLM/数据库。
"""
from __future__ import annotations

import unittest

from aggregator import segment
from aggregator.segment import STEP_SEC   # = config.VLM_INTERVAL_SEC = 20


def _ev(ts, activity="工作", app="code.exe", source="vlm", skipped=False):
    """构造一条 event dict。"""
    return {
        "ts": ts, "activity": activity, "app": app, "source": source,
        "skipped": int(bool(skipped)), "proc_name": app,
    }


def _seq(n0, n, activity="工作", stride=20, app="code.exe"):
    """从 ts=n0 起 stride 秒一条、共 n 条同一活动的 events。"""
    return [_ev(n0 + i * stride, activity, app=app) for i in range(n)]


class SegmentBuildTest(unittest.TestCase):

    # 1) 同一活动全主力 -> 主标签就是它
    def test_single_activity_main(self):
        evs = _seq(1000.0, 30, "工作")
        seg = segment.build(evs)
        self.assertEqual(seg.main_activity, "工作")
        self.assertEqual(seg.vlm_count, 30)
        self.assertEqual(seg.skip_count, 0)
        self.assertEqual(seg.fallback_count, 0)
        # breakdown 该类应为全部时长 = 30 * STEP_SEC = 600
        self.assertAlmostEqual(seg.breakdown["工作"], 30 * STEP_SEC, places=1)

    # 2) 混合活动：占比最大者为主标签
    def test_mixed_majority_wins(self):
        evs = _seq(1000.0, 20, "工作") + _seq(1000.0 + 20 * 20, 10, "游戏")
        seg = segment.build(evs)
        self.assertEqual(seg.main_activity, "工作")
        self.assertGreater(seg.breakdown["工作"], seg.breakdown["游戏"])

    # 3) skipped 帧不计入 breakdown 活动
    def test_skipped_not_counted_in_breakdown(self):
        evs = _seq(1000.0, 15, "工作") + [
            _ev(1000.0 + 16 * 20, "—", source="skip", skipped=True) for _ in range(15)
        ]
        seg = segment.build(evs)
        self.assertEqual(seg.skip_count, 15)
        # 有 15 条工作，breakdown 只有"工作"
        self.assertNotIn("—", seg.breakdown)
        self.assertAlmostEqual(seg.breakdown["工作"], 15 * STEP_SEC, places=1)

    # 4) 全部 skip 的段 -> 主标签"空闲"
    def test_all_skipped_segment_is_idle(self):
        evs = [_ev(1000.0 + i * 20, "—", source="skip", skipped=True) for i in range(30)]
        seg = segment.build(evs)
        self.assertEqual(seg.main_activity, "空闲")

    # 5) top_apps 取 Top3，按时长降序
    def test_top_apps_top3_descending(self):
        evs = (
            _seq(1000.0, 10, "工作", app="code.exe")
            + _seq(1000.0 + 10 * 20, 8, "浏览", app="chrome.exe")
            + _seq(1000.0 + 18 * 20, 6, "社交", app="wechat.exe")
            + _seq(1000.0 + 24 * 20, 2, "工作", app="terminal.exe")
        )
        seg = segment.build(evs)
        apps = list(seg.top_apps.keys())
        # 期望按秒数降序前 3 个
        self.assertEqual(len(seg.top_apps), 3)
        self.assertEqual(apps[0], "code.exe")
        self.assertGreaterEqual(seg.top_apps[apps[0]], seg.top_apps[apps[1]])

    # 6) source 计数正确
    def test_source_counts(self):
        evs = (
            [_ev(1000.0 + i * 20, "工作", source="vlm") for i in range(10)]
            + [_ev(1000.0 + (10 + i) * 20, "其他", source="fallback") for i in range(5)]
            + [_ev(1000.0 + (15 + i) * 20, "—", source="skip", skipped=True) for i in range(5)]
        )
        seg = segment.build(evs)
        self.assertEqual(seg.vlm_count, 10)
        self.assertEqual(seg.fallback_count, 5)
        self.assertEqual(seg.skip_count, 5)

    # 7) 空段哨兵值
    def test_empty_events_returns_idle(self):
        seg = segment.build([])
        self.assertEqual(seg.main_activity, "空闲")
        self.assertEqual(seg.since, 0.0)
        self.assertEqual(seg.until, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
