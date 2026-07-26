# 测试占位：填实现后补单测，离线运行不依赖真截屏/Ollama。
# 测点规划：
#   test_merge: 模拟 VLM 抛异常 -> 走 fallback；锁屏 -> 标空闲
#   test_segment: 30 条混合 events -> 主标签与 breakdown 正确
#   test_fallback: 规则表覆盖常见程序命中
