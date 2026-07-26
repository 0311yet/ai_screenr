# 离线屏幕活动监控
离线、本地运行、不联网。每 20s 用 Ollama `minicpm-v` 视觉模型分析一帧屏幕，每 10 分钟聚合成一段活动记录，生成每日活动报告（游戏/工作/视频/社交/浏览/空闲 占比）。Windows 桌面应用形态（PySide6 托盘 + 主界面）。

## 主信号 & 辅信号
- 主：VLM，每 20s 强制推理一次（上一帧没跑完则跳过本帧，不排队）。
- 辅：Win32 接口（前台窗口标题、进程名、键鼠空闲时间、锁屏判断）。
  - 作用 1：当 VLM 失败/超时时，用进程名/标题走规则表兜底一条，不留空窗。
  - 作用 2：作为 VLM prompt 上下文（"当前前台窗口标题：XXX"）。
  - 作用 3：空闲检测与锁屏期间停 VLM。

## 颗粒度
- 20s 一条瞬时事件 → events 表（source=vlm/fallback、skipped 标记等）
- 10min 一段聚合 → segments 表（主标签 + breakdown 占比 + top_apps）
- 每日一报告 → reports 表 + `reports/YYYY-MM-DD.md`

## 空闲检测
- 键鼠空闲（`GetLastInputInfo`）超过阈值 → 标"空闲"label，但 VLM 继续跑（可能是阅读/视频）。
- 锁屏 / 显示器关闭 → 停 VLM，标段为"系统空闲"。

## Ollama 自启动
程序启动时检测 Ollama 进程，未运行则拉起 `ollama serve`；校验 `minicpm-v` 已安装，否则 UI 报错。

## 状态
核心链路已实装并验收（离线端到端跑通）：
- `capture/windows.py`：前台窗口/进程/空闲秒（ctypes GetLastInputInfo + GetTickCount64，避开 49.7 天回绕）/ 锁屏（OpenInputDesktop desktop名==Winlogon）
- `capture/screen.py`：1080P 截图直送（默认不缩），JPEG q85
- `classify/vlm.py`：调 Ollama minicpm-v4.6，用 `format` schema 强制 JSON，~3.3s/次
- `classify/fallback.py`：进程/标题规则表兼底
- `classify/merge.py`：VLM 主、fallback 兼底、锁屏直接空闲
- `storage/db.py`：SQLite schema + WAL，events/segments/reports
- `aggregator/segment.py`：10min 段聚合（主标签 + breakdown + top_apps）
- `report/daily.py`：Markdown 日报
- `ollama_runner.py`：Ollama 检测/自启动/模型校验
- `engine.py`：纯 Python 后台线程循环（1Hz Win / 20s VLM / 10min 聚合）
- `ui/tray.py` + `ui/mainwindow.py`：PySide6 托盘 + 主界面（占比/时间线/事件明细）

待办（可选）：开机自启、屏灭检测（`screen_off` 目前恒 False）、日报自动跨日、多显示器支持。

## 依赖
见 `requirements.txt`（已钉版本）。

## 启动
```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python main.py
```
