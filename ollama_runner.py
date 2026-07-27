# ai_screenr/ollama_runner.py
"""确保 Ollama 在跑，并加载 minicpm-v 模型。

- 检查 /api/tags；无响应则 spawn `ollama serve`，等待健康检查通过
- 校验 {OLLAMA_MODEL} 已安装
"""
from __future__ import annotations

import subprocess
import time
import logging

import requests

import config

log = logging.getLogger(__name__)


def _is_healthy() -> bool:
    try:
        r = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=config.OLLAMA_HEALTH_TIMEOUT_SEC)
        return r.status_code == 200
    except Exception:
        return False


def _ensure_serve_started() -> bool:
    """spawn `ollama serve`（已运行则跳过）。返回是否在限定时间内健康。"""
    proc = subprocess.Popen(
        [config.OLLAMA_SERVE_BIN, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    log.info("ollama serve spawned pid=%s", proc.pid)
    deadline = time.time() + 30
    while time.time() < deadline:
        if _is_healthy():
            return True
        time.sleep(1)
    return False


def ensure_ollama_running() -> bool:
    """启动期调用。返回 Ollama 健康 & 模型可用；False 时调用方应提示用户。"""
    if not _is_healthy():
        log.info("Ollama 未在跑，尝试自启动 …")
        if not _ensure_serve_started():
            return False
    # 校验模型是否存在
    try:
        r = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=config.OLLAMA_HEALTH_TIMEOUT_SEC)
        names = [m.get("name", "") for m in r.json().get("models", [])]
        if config.OLLAMA_MODEL not in names:
            log.warning("模型 %s 未安装；已安装：%s", config.OLLAMA_MODEL, names)
            return False
        return True
    except Exception as e:
        log.warning("模型列表查询失败：%s", e)
        return False
