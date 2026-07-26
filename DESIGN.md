# ai_screenr 设计文档

离线屏幕活动监控器。本地运行、不联网，每 20s 用 Ollama 视觉模型分析一次屏幕，每 10 分钟聚合成一个时间段，生成每日活动报告（游戏/工作/视频等占比）。Windows 桌面应用形态。

## 硬约束

| 项 | 值 |
|----|----|
| OS | Windows 11 |
| GPU | RTX 3050 4GB |
| 视觉模型 | Ollama `minicpm-v4.6:latest`（1.3B Q4_K_M，本机已装已测，用 `format` schema 强制 JSON） |
| 主信号 | VLM（每 20s 强制一次） |
| 辅信号 | Win32 接口（前台窗口标题/进程名 + 空闲检测） |
| 产出颗粒度 | 10 分钟一段 |
| 空闲检测 | Win32 `GetLastInputInfo` |
| 形态 | 桌面应用（PySide6，托盘 + 主界面一起做） |
| 离线 | 全程离线，不上传任何数据 |

## 关键设计决策

1. **VLM 主力，Win 接口辅**：分类结论以 VLM 为准；VLM 失败/超时/无响应时，用 Win 接口的进程名+窗口标题走规则表兜底一条，保证不留空窗。
2. **20s 强制采样**：每隔 20s 必须触发一次 VLM 推理。若到达下一 20s 时上一帧仍在推理，**跳过这一帧**（记 skip 原因），不排队、不延迟累积。
3. **10 分钟统计聚合**：每 10 分钟把最近 30 条 20s 瞬时结论做占比聚合（多数标签为主，段内保留各分类占比明细），**不引入额外模型**。
4. **空闲检测分级**：
   - 空闲信号来自 `GetLastInputInfo`（无键鼠输入超过阈值）。
   - 仅键鼠静止但屏幕亮：VLM 继续跑（可能是阅读/视频这类被动观看，VLM 会如实判）。
   - 锁屏或显示器关闭：停 VLM，标"系统空闲"。
   - 用 `OpenInputDesktop`/`GetThreadDesktop` 判断是否锁屏，`GetLastInputInfo` 拿键鼠空闲秒数。
5. **Ollama 自启动**：程序启动时检测 Ollama 进程，未运行则自动拉起 `ollama serve`，并健康检查 `/api/tags`；拉起失败时 UI 提示用户。
6. **异步分离**：控制循环（1Hz Win 采集）与 VLM 推理走独立线程 + 队列，互不阻塞。

## 数据模型 (SQLite)

`events` — 20s 级瞬时事件

| 字段 | 说明 |
|------|------|
| ts | 时间戳 |
| activity | VLM/兜底结论：工作\|游戏\|视频\|社交\|浏览\|空闲\|其他 |
| app | 看出的程序名或网址 |
| detail | 一句话描述 |
| source | 来源标记：vlm / fallback |
| win_title | 当时前台窗口标题（辅信号） |
| proc_name | 当时前台进程名（辅信号） |
| idle_sec | 键鼠空闲秒数 |
| skipped | 是否被跳过的空采样（1=skip，0=正常） |
| note | skip 原因 / 其它备注 |

`segments` — 10 分钟聚合段

| 字段 | 说明 |
|------|------|
| since / until | 段起止时间 |
| main_activity | 段主标签 |
| breakdown | JSON，各分类占比明细 |
| top_apps | JSON，该段内出现过的 app 及占比 |
| vlm_count / skip_count / fallback_count | 该段统计 |

`reports` — 日报

| 字段 | 说明 |
|------|------|
| date | 日期 |
| total_active_sec | 当日活跃总秒数 |
| breakdown | JSON，全天各分类大占比 |
| timeline | JSON，144 段（或有效段）主标签序列 |
| created_at | 生成时间 |

## 模块划分

```
ai_screenr/
  main.py                # 入口：启动托盘 + 调度循环
  config.py              # 配置：采样间隔/模型名/阈值/数据库路径
  ollama_runner.py       # Ollama 检测/自启动/健康检查
  capture/
    windows.py           # win32：前台窗口标题+进程名+空闲检测+锁屏检测
    screen.py            # 截屏（缩到合适尺寸），返回 bytes
  classify/
    vlm.py               # 调 Ollama minicpm-v：截图→JSON结论
    fallback.py          # Win 规则表兜底
    merge.py             # 融合逻辑：VLM失败→fallback；正常→采VLM
  storage/
    db.py                # SQLite schema/写入/聚合查询
  aggregator/
    segment.py           # 10分钟段聚合：30条事件→一段
  report/
    daily.py             # 日报生成（Markdown）
  ui/
    tray.py              # 系统托盘
    mainwindow.py        # 主界面：今日时间线/占比/明细
    resources/           # 托盘图标等
  tests/                 # 离线单测：融合逻辑/聚合/兜底规则
  requirements.txt
  README.md
  DESIGN.md              # 本文件
```

## 调度循环（伪码）

```
主线程（控制循环，每秒一次）
  win = capture.windows.snapshot()          # 标题/进程/idle_sec/locked
  if win.locked or screen_off:
      mark_segment_gap("系统空闲")
      continue                                # 跳过这次及下一次VLM
  win_events.append(win)

VLM 触发线程（每20s定时）
  if vlm_running: skip_this_tick(); continue
  img = capture.screen.shot()
  push 推理任务入队

推理工作线程（消费队列）
  res = classify.vlm.classify(img, ctx=win)
  if res failed/timeout: res = classify.fallback.from_win(win)
  storage.db.insert_event(res)

聚合（每10min定时）
  seg = aggregator.segment.build(last_30_events)
  storage.db.insert_segment(seg)
  ui.refresh_today()
```

## VLM Prompt 模板（待定稿）

```
你在看用户电脑屏幕的截图。只回 JSON，不要多余文字：
{"activity":"工作|游戏|视频|社交|浏览|空闲|其他","app":"看出的程序或网址","detail":"一句话"}
```
当前窗口标题（辅信号）拼进 prompt 作为上下文。解析取首个 {...} 块。

## 先搭骨架的范围（本轮只做这个）

骨架已完成，核心链路已实装验收（详见 README 状态部分）。
