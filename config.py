# ai_screenr 配置
"""所有可调参数集中在此。"""
from __future__ import annotations

# ---- 采样 ----
WIN_SAMPLE_INTERVAL_SEC = 1.0      # Win32 辅信号采集频率（1Hz）
VLM_INTERVAL_SEC = 20.0            # VLM 推理频率（20s 强制一次）
VLM_TIMEOUT_SEC = 18.0             # 单次 VLM 推理超时；超过则跳过该帧走兜底
VLM_SKIP_IF_RUNNING = True         # 上一帧没推完则跳过下一帧，不排队
SEGMENT_AGGREGATE_MIN = 10         # 段聚合周期（分钟）

# ---- 空闲检测 ----
IDLE_THRESHOLD_SEC = 5 * 60        # 超过此空闲秒数 -> "空闲"标签（仅键鼠静止，VLM 仍可跑）
LOCKED_SEGMENT_SKIP = True         # 锁屏/屏灭期间停 VLM 并标段为系统空闲

# ---- Ollama / VLM ----
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "minicpm-v4.6:latest"
OLLAMA_SERVE_BIN = "ollama"        # 自启动 ollama serve 所用的可执行名
OLLAMA_HEALTH_TIMEOUT_SEC = 5
OLLAMA_CHECK_INTERVAL_SEC = 60       # engine 每多久探一次 Ollama 是否在跑（仅在使用电脑时）
VLM_SCREEN_MAX_W = 1920            # 截图直送 1080P（3050 4G 跑 1.3B Q4 宽裕，不缩图保信息）
VLM_SCREEN_JPEG_Q = 85             # 送模前 JPEG 质量

# ---- 分类约束 ----
ACTIVITY_LABELS = ["工作", "游戏", "视频", "社交", "浏览", "空闲", "其他"]

# ---- 存储路径 ----
DB_PATH = "data/ai_screenr.db"     # SQLite 路径
REPORT_DIR = "reports"             # 日报 Markdown 输出目录
TIMELINE_RETENTION_DAYS = 30       # 历史清理阈值（保持n天）

# ---- UI ----
TRAY_ICON_PATH = "ui/resources/icon.png"

# ---- UI / 服务 ----
NICEGUI_HOST = "127.0.0.1"
NICEGUI_PORT = 8714     # 避开 8080 被本机服务占用
