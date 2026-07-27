# ai_screenr/ui/settings_page.py
"""NiceGUI 设置页「/settings」。

设计：单张玻璃卡居中 + 背景青色/slate 光晕。节点：开机自启 toggle。
"""
from __future__ import annotations

from nicegui import ui, app
from fastapi import Query
from starlette.responses import JSONResponse

from ui import theme, autostart


@ui.page("/settings")
def settings_page():
    theme.inject()

    # 顶栏：与主页一致，标题 + 返回主页按钮
    with ui.element("div").classes("topbar"):
        ui.html(
            '<span class="brand"><span class="brand-mark">π</span>AI SCREENR</span>'
        )
        ui.html('<span class="caps" style="margin-right:10px">SETTINGS</span>')
        ui.button(
            icon="arrow_back", on_click=lambda: ui.navigate.to("/")
        ).props("flat dense unelevated").classes("act-btn")

    # ── 背景装饰光晕 ──
    ui.html('<div class="glow-blob bg-glow-tl"></div>')
    ui.html('<div class="glow-blob bg-glow-br"></div>')

    # ── 主卡片 ──
    with ui.element("div").style(
        "position:relative;z-index:10;min-height:calc(100vh - 72px);"
        "display:flex;align-items:center;justify-content:center;padding:24px"
    ):
        with ui.element("div").classes("glass").style(
            "max-width:640px;width:100%;margin:auto"
        ):
            with ui.element("div").style(
                "display:flex;align-items:center;gap:10px;margin-bottom:24px"
            ):
                ui.html(
                    '<span class="material-symbols-outlined" '
                    'style="color:var(--primary);font-size:28px">tune</span>'
                )
                ui.html('<div class="h1">设置</div>')

            # 开机自启
            with ui.element("div").style(
                "display:flex;align-items:center;justify-content:space-between;"
                "padding:16px;border:1px solid rgba(60,73,76,0.3);"
                "border-radius:8px;background:rgba(19,27,46,0.5)"
            ):
                with ui.element("div").style("flex:1;padding-right:24px"):
                    with ui.element("div").style(
                        "display:flex;align-items:center;gap:8px;margin-bottom:4px"
                    ):
                        ui.html(
                            '<span class="material-symbols-outlined" '
                            'style="color:var(--on-surface-variant);font-size:16px">'
                            'power_settings_new</span>'
                        )
                        ui.html(
                            '<div class="h3">开机自启动</div>'
                        )
                    ui.html(
                        '<div class="data" style="color:var(--on-surface-variant)">'
                        '系统启动时自动运行 AI SCREENR，确保持续的监控与活动记录。'
                        '</div>'
                    )
                # toggle
                toggle = ui.html(
                    '<label class="switch"><input type="checkbox" '
                    f'{"checked" if autostart.is_enabled() else ""}>'
                    '<span class="track"></span><span class="thumb"></span></label>'
                )
                hint = ui.html('<div class="caps" style="margin-top:10px"></div>')

            # toggle change listener — ui.html 不允许 <script>，用 ui.add_body_html
            ui.add_body_html(
                '''<script>
                document.addEventListener("DOMContentLoaded", function(){
                  const el = document.querySelector('.switch input');
                  if(el) el.addEventListener('change', function() {
                    fetch('/settings/toggle?enable=' + this.checked, {method:'POST'})
                      .then(r => r.json()).then(d => {
                          const h = document.querySelectorAll('.glass .caps')[0];
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
