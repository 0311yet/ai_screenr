"""测点：classify.merge.classify_one 融合逻辑。
离线、不依赖真 Ollama —— 用标准库 unittest.mock 注入假的 vlm.classify。
"""
from __future__ import annotations

import unittest
from unittest import mock

import config
from classify import merge, vlm
from classify.vlm import VlmResult
from capture.windows import WinSnapshot


def _win(locked=False, screen_off=False, idle=0, title="Code", proc="code.exe"):
    return WinSnapshot(
        ts=1700000000.0, window_title=title, proc_name=proc,
        idle_sec=idle, locked=locked, screen_off=screen_off,
    )


class MergeClassifyTest(unittest.TestCase):

    # 1) 锁屏 -> 直接标空闲，不调 VLM（即使注入的假 vlm 会 raise，也不应被触发）
    def test_locked_does_not_call_vlm(self):
        win = _win(locked=True)
        with mock.patch.object(vlm, "classify") as m:
            res = merge.classify_one(win, b"img")
        self.assertEqual(m.call_count, 0, "锁屏不应触发 vlm.classify")
        self.assertEqual(res.activity, "空闲")
        self.assertEqual(res.source, "system")

    # 2) 屏灭 -> 同锁屏
    def test_screen_off_does_not_call_vlm(self):
        win = _win(screen_off=True)
        with mock.patch.object(vlm, "classify") as m:
            res = merge.classify_one(win, b"img")
        self.assertEqual(m.call_count, 0)
        self.assertEqual(res.activity, "空闲")
        self.assertEqual(res.source, "system")

    # 3) VLM 抛异常 -> 走 fallback，source=fallback，且不报错上抛
    def test_vlm_exception_routes_to_fallback(self):
        win = _win(title="Visual Studio Code", proc="code.exe", idle=0)
        with mock.patch.object(vlm, "classify", side_effect=RuntimeError("boom")):
            res = merge.classify_one(win, b"img")
        self.assertEqual(res.source, "fallback")
        # code.exe 命中工作规则
        self.assertEqual(res.activity, "工作")

    # 4) VLM 正常返回 -> 原样采纳，source=vlm
    def test_vlm_success_passes_through(self):
        win = _win(title="原神", proc="genshin.exe", idle=0)
        expected = VlmResult(activity="游戏", app="genshin.exe",
                             detail="在打原神", raw="{}", source="vlm")
        with mock.patch.object(vlm, "classify", return_value=expected) as m:
            res = merge.classify_one(win, b"img")
        self.assertEqual(m.call_count, 1)
        self.assertEqual(res.activity, "游戏")
        self.assertEqual(res.source, "vlm")

    # 5) image_bytes=None -> 走 fallback（merge 短路，不调 VLM）
    def test_none_image_routes_to_fallback(self):
        win = _win(title="B站", proc="chrome.exe", idle=0)
        with mock.patch.object(vlm, "classify") as m:
            res = merge.classify_one(win, None)
        self.assertEqual(m.call_count, 0, "image=None 时不应调 vlm")
        # chrome + B站标题关键字 -> 视频
        self.assertEqual(res.activity, "视频")
        self.assertEqual(res.source, "fallback")


if __name__ == "__main__":
    unittest.main(verbosity=2)
