"""ai_screenr 离线单测包。

测点（与原占位规划一致）：
  test_merge    : VLM 抛异常 -> 走 fallback；锁屏/屏灭 -> 标空闲不调 VLM
  test_segment   : 混合 events -> 主标签与 breakdown / skip top_apps 正确
  test_fallback  : 规则表覆盖常见程序命中、空闲/标题关键词优先级

运行：
  .venv/Scripts/python -m unittest discover tests -v
"""
