"""NiceGUI 设置页「/settings」— Stitch Deep Dark Ops 风格。

保留：autostart.is_enabled/enable/disable 与 /settings/toggle 端点契约。
视觉：玻璃卡居中 + 青色光晕装饰 + Stitch 风霓虹滑块。
"""
from __future__ import annotations

from nicegui import ui, app
from fastapi import Query
from starlette.responses import JSONResponse

from ui import theme, autostart


@ui.page("/settings")
def settings_page():
    theme.inject()

    # ── 顶栏（与主页一致：品牌 + 回主页） ──
    with ui.element("div").classes("topbar"):
        ui.html(
            '<span class="brand"><span class="brand-mark">π</span>AI SCREENR</span>', sanitize=False)
        ui.html('<span class="caps" style="margin-right:10px">SETTINGS</span>', sanitize=False)
        ui.button(
            icon="arrow_back", on_click=lambda: ui.navigate.to("/")
        ).props("flat dense unelevated").classes("act-btn")

    # ── 背景装饰光晕 ──
    ui.html('<div class="glow-blob bg-glow-tl"></div>', sanitize=False)
    ui.html('<div class="glow-blob bg-glow-br"></div>', sanitize=False)

    # ── 主卡片居中 ──
    with ui.element("div").style(
        "position:relative;z-index:10;min-height:calc(100vh - 64px);"
        "display:flex;align-items:center;justify-content:center;padding:24px"
    ):
        with ui.element("div").classes("glass").style(
            "max-width:680px;width:100%;margin:auto"
        ):
            with ui.element("div").style(
                "display:flex;align-items:center;gap:12px;margin-bottom:28px"
            ):
                ui.html(
                    '<span class="material-symbols-outlined" '
                    'style="color:var(--primary);font-size:32px;text-shadow:0 0 12px currentColor">'
                    'tune</span>', sanitize=False)
                ui.html('<div class="h1">设置</div>', sanitize=False)
                ui.html(
                    '<div class="caps" style="margin-left:auto;color:var(--on-surface-variant)">'
                    'v1.0 · 离线</div>', sanitize=False)

            # 开机自启条目
            with ui.element("div").style(
                "display:flex;align-items:center;justify-content:space-between;"
                "padding:20px;border:1px solid rgba(60,73,76,0.4);"
                "border-radius:var(--r-md);background:rgba(9,15,17,0.5);"
                "border-top:1px solid rgba(138,235,255,0.18)"
            ):
                with ui.element("div").style("flex:1;padding-right:24px"):
                    with ui.element("div").style(
                        "display:flex;align-items:center;gap:10px;margin-bottom:6px"
                    ):
                        ui.html(
                            '<span class="material-symbols-outlined" '
                            'style="color:var(--on-surface-variant);font-size:18px">'
                            'power_settings_new</span>', sanitize=False)
                        ui.html('<div class="h3">开机自启动</div>', sanitize=False)
                    ui.html(
                        '<div class="data" style="color:var(--on-surface-variant);line-height:1.5">'
                        '系统启动时自动运行 AI SCREENR，确保持续的监控与活动记录。<br>'
                        '启动命令：pythonw main.py · 无窗口后台运行</div>', sanitize=False)
                # toggle — 保留 .switch / .track / .thumb 选择器供 theme.css 作用
                toggle = ui.html(
                    '<label class="switch"><input type="checkbox" '
                    f'{"checked" if autostart.is_enabled() else ""}>'
                    '<span class="track"></span><span class="thumb"></span></label>', sanitize=False)
                hint = ui.html('<div class="caps" style="margin-top:14px;color:var(--primary-dim);height:12px"></div>', sanitize=False)

            # 底部说明区
            ui.html(
                '<div style="margin-top:24px;padding:16px;border-top:1px solid rgba(60,73,76,0.3)">'
                '<div class="caps" style="margin-bottom:8px">关于</div>'
                '<div class="data" style="color:var(--on-surface-variant);line-height:1.6">'
                'AI SCREENR 是离线屏幕活动监控器，使用本地 Ollama 视觉模型 '
                '<span style="color:var(--primary)">minicpm-v4.6</span> '
                '每 20 秒分析屏幕一次，每 10 分钟聚合成活动段并生成日报。<br>'
                '全程不联网、不上传任何数据。</div>'
                '</div>', sanitize=False)

            # toggle change 监听（ui.html 不允许内联 <script>，走 add_body_html）
            ui.add_body_html(
                '''<script>
                document.addEventListener("DOMContentLoaded", function(){
                  const el = document.querySelector('.switch input');
                  if(el) el.addEventListener('change', function() {
                    fetch('/settings/toggle?enable=' + this.checked, {method:'POST'})
                      .then(r => r.json()).then(d => {
                          const h = document.querySelectorAll('.glass .caps')[1];
                          if(!h) return;
                          h.textContent = d.ok ? (this.checked ? '已开启' : '已关闭') : '操作失败';
                          h.style.color = d.ok ? '#8aebff' : '#ffb4ab';
                          setTimeout(()=>{h.textContent='';}, 2500);
                      });
                  });
                });
                </script>'''
            )


@app.post("/settings/toggle")
async def _toggle_handler(enable: bool = Query(...)):
    """开机自启 toggle 的 POST 端点。返回 JSON。"""
    ok = autostart.enable() if enable else autostart.disable()
    return JSONResponse({"ok": ok, "enabled": autostart.is_enabled()})
