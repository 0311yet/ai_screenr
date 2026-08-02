"""测点：classify.fallback 规则表覆盖常见程序命中。
离线、不依赖 VLM。
"""
from __future__ import annotations

import unittest

import config
from classify import fallback


class FallbackRulesTest(unittest.TestCase):

    def _call(self, title, proc, idle=0):
        return fallback.from_win(title, proc, idle)

    # 1) 空闲优先级最高：超过阈值直接空闲，不看进程/标题
    def test_idle_over_threshold_wins_over_proc(self):
        r = self._call("原神", "genshin.exe", idle=config.IDLE_THRESHOLD_SEC + 1)
        self.assertEqual(r.activity, "空闲")

    def test_idle_over_threshold_wins_over_title_keyword(self):
        r = self._call("B站 - 视频播放", "chrome.exe", idle=config.IDLE_THRESHOLD_SEC + 1)
        self.assertEqual(r.activity, "空闲")

    # 2) 标题关键词强信号优先于进程精确匹配：
    #    chrome 进程默认"浏览"，但若窗口标题含"B站"应判视频
    def test_title_keyword_beats_proc_rule(self):
        r = self._call("B站 - 某视频", "chrome.exe", idle=0)
        self.assertEqual(r.activity, "视频")

    def test_title_keyword_youtube_in_chrome(self):
        r = self._call("YouTube - 某 channel", "chrome.exe", idle=0)
        self.assertEqual(r.activity, "视频")

    def test_title_keyword_genshin_in_title(self):
        r = self._call("原神", "unknown.exe", idle=0)
        self.assertEqual(r.activity, "游戏")

    # 3) 进程精确匹配命中
    def test_proc_code_exe_is_work(self):
        r = self._call("main.py - ai_screenr - Visual Studio Code", "code.exe", idle=0)
        self.assertEqual(r.activity, "工作")

    def test_proc_wechat_is_social(self):
        r = self._call("微信", "wechat.exe", idle=0)
        self.assertEqual(r.activity, "社交")

    def test_proc_chrome_no_title_keyword_is_browse(self):
        r = self._call("Google 搜索结果", "chrome.exe", idle=0)
        self.assertEqual(r.activity, "浏览")

    # 4) 大小写无关
    def test_proc_case_insensitive(self):
        r = self._call("", "CODE.EXE", idle=0)
        self.assertEqual(r.activity, "工作")

    # 5) 未命中 -> 其他
    def test_no_match_returns_other(self):
        r = self._call("某个无关键词的窗口", "totally_unknown_app.exe", idle=0)
        self.assertEqual(r.activity, "其他")

    # 6) 空进程空标题 -> 其他
    def test_empty_inputs(self):
        r = self._call("", "", idle=0)
        self.assertEqual(r.activity, "其他")
        self.assertEqual(r.app, "未知")


if __name__ == "__main__":
    unittest.main(verbosity=2)
