# ai_screenr/ui/theme.py
"""设计系统（Stitch "Sentinel Intelligence" 转译）。

把 Tailwind config + <style> token 全部翻译成静态 CSS / JSON。
所有页面 import 共用，避免 NiceGUI 引 Tailwind CDN 依赖外网。
"""
from __future__ import annotations

# ── 设计色板（取自 DESIGN.md） ─────────────────────
CANVAS = "#020617"
SURFACE = "#0b1326"
SURFACE_CONTAINER_LOW = "#131b2e"
SURFACE_CONTAINER = "#171f33"
SURFACE_CONTAINER_HIGH = "#222a3d"
SURFACE_CONTAINER_HIGHEST = "#2d3449"
ON_SURFACE = "#dae2fd"
ON_SURFACE_VARIANT = "#bbc9cd"
OUTLINE_VARIANT = "#3c494c"
PRIMARY = "#8aebff"          # 电青
PRIMARY_DIM = "#22d3ee"
ON_PRIMARY = "#00363e"
SECONDARY = "#b7c8e1"
TERTIARY = "#ffd785"         # 警告琥珀
ERROR = "#ffb4ab"

# 活动类目配色（保留 7 类）
ACT_COLOR = {
    "工作": "#22c55e",      # 绿
    "学习": "#3b82f6",      # 蓝
    "游戏": "#a855f7",      # 紫
    "视频": "#ec4899",      # 粉红
    "社交": "#f59e0b",      # 橙
    "浏览": "#64748b",      # 灰蓝
    "空闲": "#475569",      # 中灰
    "其他": "#52525b",      # 暗灰
    "—":   "#1e293b",
}

# Material Symbols 图标映射（按活动）
ACT_ICON = {
    "工作": "code",
    "学习": "menu_book",
    "游戏": "sports_esports",
    "视频": "play_circle",
    "社交": "forum",
    "浏览": "language",
    "空闲": "bedtime",
    "其他": "apps",
    "—":   "horizontal_rule",
}

# ── 字体 ──────────────────────────────────────
# Geist（正文/UI）+ JetBrains Mono（数据/HUD）。
# 通过 Google Fonts CDN 一次性引入（轻量、监控页面只在用户主动看时打开）。
_FONTS_LINK = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Geist:wght@400;500;600;700&'
    'family=JetBrains+Mono:wght@400;500;600&'
    'family=Material+Symbols+Outlined:wght@FILL@100..700,0..1&display=swap" rel="stylesheet">'
)

# ── 主样式表 ──────────────────────────────────
_CSS = f"""
:root {{
  --canvas:{CANVAS}; --surface:{SURFACE};
  --surface-low:{SURFACE_CONTAINER_LOW}; --surface:{SURFACE_CONTAINER};
  --surface-high:{SURFACE_CONTAINER_HIGH}; --surface-highest:{SURFACE_CONTAINER_HIGHEST};
  --on-surface:{ON_SURFACE}; --on-surface-variant:{ON_SURFACE_VARIANT};
  --outline-variant:{OUTLINE_VARIANT}; --primary:{PRIMARY}; --primary-dim:{PRIMARY_DIM};
  --secondary:{SECONDARY}; --tertiary:{TERTIARY}; --error:{ERROR};
  --radius:4px; --radius-md:6px; --radius-lg:8px; --radius-xl:16px;
}}
* {{ box-sizing:border-box; }}
html,body {{
  background:{CANVAS}; color:{ON_SURFACE}; margin:0; min-height:100vh; width:100%;
  font-family:'Geist','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
}}
/* 清掉 NiceGUI / Quasar 默认布局偏干由自己的 CSS 主导 */
.nicegui-content, .q-page, .q-layout, .q-page-container {{
  background:transparent !important; color:{ON_SURFACE} !important;
  padding:0 !important; display:block !important; width:100% !important;
  max-width:none !important; min-height:100vh !important;
}}
/* glass 卡与顶栏宽度展开 */
.glass, .topbar {{ width:100%; }}
.mono {{ font-family:'JetBrains Mono','Cascadia Code',monospace; }}
/* Glass 面板：半透明 + 模糊 + 顶部青色高光 */
.glass {{
  background:rgba(15,23,42,0.8);
  -webkit-backdrop-filter:blur(12px); backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.05);
  border-top:1px solid rgba(138,235,255,0.18);
  border-radius:var(--radius-lg);
  box-shadow:0 8px 24px rgba(0,0,0,0.4);
  padding:24px;
}}
.glass-tight {{ padding:20px; }}
.h1 {{
  font-family:'Geist'; font-weight:700; font-size:28px; line-height:1.15;
  letter-spacing:-0.01em; margin:0;
}}
.h2 {{ font-family:'Geist'; font-weight:600; font-size:22px; line-height:1.2; margin:0; }}
.h3 {{ font-family:'Geist'; font-weight:600; font-size:18px; margin:0; }}
.tiny {{ font-size:11px; color:{ON_SURFACE_VARIANT}; letter-spacing:0.04em; }}
.data {{ font-family:'JetBrains Mono'; font-size:13px; line-height:1.4; }}
.caps {{
  font-family:'JetBrains Mono'; font-weight:500; font-size:11px;
  letter-spacing:0.06em; text-transform:uppercase; color:{ON_SURFACE_VARIANT};
}}
.bold-mono {{ font-family:'JetBrains Mono'; font-weight:600; }}
/* 顶栏 */
.topbar {{
  position:sticky; top:0; z-index:30; padding:16px 24px;
  background:rgba(11,19,38,0.7);
  -webkit-backdrop-filter:blur(16px); backdrop-filter:blur(16px);
  border-bottom:1px solid rgba(60,73,76,0.4);
  box-shadow:0 0 20px rgba(34,211,238,0.06);
  display:flex; align-items:center; justify-content:flex-end; gap:8px;
}}
.brand {{
  font-family:'Geist'; font-weight:700; letter-spacing:-0.01em;
  text-transform:uppercase; color:{PRIMARY}; flex:1;
  font-size:24px; line-height:1;
}}
.brand .brand-mark {{ font-family:'JetBrains Mono'; color:{PRIMARY_DIM}; margin-right:6px; }}
.topbar .act-btn {{
  background:transparent; border:none; color:{ON_SURFACE_VARIANT};
  cursor:pointer; padding:6px 8px; border-radius:var(--radius);
  transition:color .2s, background .2s;
}}
.topbar .act-btn:hover {{ color:{PRIMARY}; }}
.material-symbols-outlined {{
  font-family:'Material Symbols Outlined'; font-weight:400; font-style:normal;
  font-size:22px; line-height:1; vertical-align:middle;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  -webkit-font-feature-settings:'liga'; font-feature-settings:'liga';
}}
/* 24h 时间轴 */
.timeline-wrap {{ display:flex; align-items:flex-end; gap:2px; height:96px;
  background:rgba(23,31,51,0.5); padding:6px; border-radius:var(--radius); }}
.seg {{ flex:1 1 0; min-width:0; border-radius:3px;
  transition:transform .15s, filter .15s; cursor:pointer; }}
.seg:hover {{ transform:scaleY(1.4); filter:brightness(1.2); }}
.seg.active {{ transform:scaleY(1.6); filter:brightness(1.4);
  outline:1px solid {PRIMARY}; outline-offset:2px; }}
.seg-empty {{ height:10%; background:{SURFACE_CONTAINER_HIGHEST}; }}
.timeline-axis {{ display:flex; justify-content:space-between; margin-top:6px;
  font-family:'JetBrains Mono'; font-size:11px; color:{ON_SURFACE_VARIANT}; }}
/* 当前活动旋转环 */
.orbit {{
  position:relative; width:144px; height:144px; border-radius:50%;
  background:rgba(34,211,238,0.08); display:grid; place-items:center; margin:0 auto;
}}
.orbit .ring {{
  position:absolute; inset:0; border-radius:50%;
  border:3px solid var(--orbit-c, {PRIMARY}); border-top-color:transparent;
  animation:spin 3s linear infinite;
}}
.orbit .core {{ font-size:42px; color:var(--orbit-c, {PRIMARY}); }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
/* conic 环图 */
.conic-donut {{ width:180px; height:180px; margin:auto; position:relative;
  border-radius:50%;
  box-shadow:0 0 30px rgba(34,211,238,0.05); }}
.conic-donut .hole {{ position:absolute; inset:18%; border-radius:50%;
  background:{SURFACE}; display:grid; place-items:center; text-align:center; }}
.conic-donut .hole .big {{ font-family:'Geist'; font-weight:700; font-size:26px;
  color:{PRIMARY}; line-height:1.1; }}
.conic-donut .hole .sub {{ font-family:'JetBrains Mono'; font-size:11px;
  color:{ON_SURFACE_VARIANT}; letter-spacing:0.05em; }}
.mix-row {{ display:flex; justify-content:space-between;
  font-family:'JetBrains Mono'; font-size:13px; padding:4px 0; }}
.mix-row .swatch {{ display:inline-block; width:10px; height:10px;
  border-radius:2px; margin-right:8px; vertical-align:middle; }}
/* 24h 强度柱图 */
.bars {{ display:flex; align-items:flex-end; gap:4px; height:172px;
  background:linear-gradient(to bottom, transparent 0, transparent 50%,
  rgba(0,0,0,0.12) 50%, rgba(0,0,0,0.12) 100%);
  background-size:100% 4px; background-repeat:repeat; padding:0 4px; }}
.bar {{ flex:1 1 0; min-width:0; background:{SURFACE_CONTAINER_HIGHEST};
  border-radius:2px 2px 0 0; position:relative; transition:background .15s; }}
.bar:hover {{ background:{PRIMARY_DIM}; }}
.bar .cap {{ position:absolute; top:0; left:0; right:0; height:3px;
  background:rgba(255,255,255,0.25); border-radius:2px 2px 0 0; }}
.bar-col {{ display:flex; flex-direction:column; align-items:center; gap:6px; flex:1; }}
.bar-col .lab {{ font-family:'JetBrains Mono'; font-size:10px;
  color:{ON_SURFACE_VARIANT}; opacity:0.6; }}
/* 活动日志表格 */
.log-table {{ width:100%; border-collapse:collapse; }}
.log-table th {{ text-align:left; font-family:'JetBrains Mono'; font-size:11px;
  letter-spacing:0.06em; text-transform:uppercase; color:{ON_SURFACE_VARIANT};
  border-bottom:1px solid rgba(60,73,76,0.4); padding:8px 10px 10px; }}
.log-table td {{ font-family:'JetBrains Mono'; font-size:13px;
  padding:10px; border-bottom:1px solid rgba(60,73,76,0.18); }}
.log-table tr:hover td {{ background:rgba(45,52,73,0.25); }}
.ev-icon {{ font-size:16px !important; vertical-align:-3px; margin-right:6px; }}
.live-dot {{ display:inline-block; width:6px; height:6px; border-radius:50%;
  background:{PRIMARY}; margin-right:6px; animation:pulse 1.4s ease-in-out infinite; }}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.35}} }}
.chip {{ display:inline-flex; align-items:center; gap:4px; padding:3px 8px;
  border:1px solid rgba(34,211,238,0.35); background:rgba(34,211,238,0.08);
  border-radius:var(--radius); font-family:'JetBrains Mono'; font-size:11px;
  color:{PRIMARY}; letter-spacing:0.04em; }}
/* QCard 走默认，复写：背景透明 + 不带 NiceGUI 默认边 */
.nicegui-card {{ background:transparent !important; border:none !important;
  box-shadow:none !important; }}
/* 设置页装饰光晕 */
.glow-blob {{ position:absolute; border-radius:50%; filter:blur(120px);
  pointer-events:none; }}
.bg-glow-tl {{ top:-10%; left:-10%; width:40vw; height:40vh;
  background:rgba(138,235,255,0.06); }}
.bg-glow-br {{ bottom:-10%; right:-10%; width:30vw; height:30vh;
  background:rgba(183,200,225,0.05); }}
/* 段详情 drawer */
.seg-detail {{ position:fixed; top:88px; right:24px; width:340px;
  background:rgba(15,23,42,0.92); -webkit-backdrop-filter:blur(16px); backdrop-filter:blur(16px);
  border:1px solid rgba(138,235,255,0.25); border-top:1px solid rgba(138,235,255,0.4);
  border-radius:var(--radius-lg); box-shadow:0 8px 32px rgba(0,0,0,0.5),
  0 0 24px rgba(34,211,238,0.08); padding:20px 20px 16px; z-index:50;
  font-family:'Geist'; }}
.seg-detail-close {{ position:absolute; top:10px; right:10px; width:28px; height:28px;
  background:transparent; border:none; color:{ON_SURFACE_VARIANT}; font-size:20px;
  cursor:pointer; border-radius:var(--radius); transition:color .2s, background .2s; }}
.seg-detail-close:hover {{ color:{PRIMARY}; background:rgba(138,235,255,0.1); }}
.seg-detail-head {{ display:flex; align-items:flex-start; gap:12px; margin-bottom:14px; }}
.seg-detail-icon {{ font-size:36px; color:{PRIMARY}; }}
.seg-detail-range {{ font-family:'JetBrains Mono'; font-size:11px; color:{ON_SURFACE_VARIANT};
  letter-spacing:0.05em; margin-bottom:2px; }}
.seg-detail-main {{ font-family:'Geist'; font-weight:700; font-size:22px; color:{PRIMARY};
  line-height:1.1; }}
.seg-detail-summary {{ font-family:'Geist'; font-size:13px; color:{ON_SURFACE};
  line-height:1.5; background:rgba(34,211,238,0.06); border-left:2px solid {PRIMARY_DIM};
  padding:8px 10px; border-radius:0 var(--radius) var(--radius) 0; margin-bottom:14px; }}
.seg-detail-section-title {{ font-family:'JetBrains Mono'; font-size:11px; color:{ON_SURFACE_VARIANT};
  letter-spacing:0.06em; text-transform:uppercase; margin:10px 0 6px; }}
.seg-detail-list {{ display:flex; flex-direction:column; gap:2px; }}
.seg-detail-row {{ display:flex; align-items:center; justify-content:space-between;
  font-family:'JetBrains Mono'; font-size:13px; color:{ON_SURFACE}; padding:4px 0; }}
.seg-detail-row span:first-child {{ display:flex; align-items:center; gap:8px; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap; }}
.seg-detail-row span:last-child {{ color:{ON_SURFACE_VARIANT}; flex-shrink:0; margin-left:8px; }}
.seg-detail-swatch {{ display:inline-block; width:8px; height:8px; border-radius:2px; flex-shrink:0; }}
.seg-detail-empty {{ padding:4px 0; opacity:0.5; }}
.seg-detail-stats {{ margin-top:12px; }}
/* 日报 modal */
.report-modal {{ position:fixed; inset:0; z-index:100; display:flex; align-items:center;
  justify-content:center; }}
.report-modal-backdrop {{ position:absolute; inset:0; background:rgba(2,6,23,0.65);
  -webkit-backdrop-filter:blur(4px); backdrop-filter:blur(4px); }}
.report-modal-card {{ position:relative; width:min(680px,92vw); max-height:84vh; display:flex;
  flex-direction:column; background:rgba(13,21,40,0.96);
  -webkit-backdrop-filter:blur(18px); backdrop-filter:blur(18px);
  border:1px solid rgba(138,235,255,0.22); border-top:1px solid rgba(138,235,255,0.4);
  border-radius:var(--radius-lg); box-shadow:0 16px 48px rgba(0,0,0,0.55),
  0 0 32px rgba(34,211,238,0.08); }}
.report-modal-head {{ display:flex; align-items:flex-start; justify-content:space-between;
  gap:12px; padding:18px 20px 12px; border-bottom:1px solid rgba(255,255,255,0.06); }}
.report-modal-title {{ font-family:'Geist'; font-weight:700; font-size:20px; color:{PRIMARY};
  display:flex; align-items:center; gap:8px; }}
.report-modal-title .material-symbols-outlined {{ font-size:24px; }}
.report-modal-sub {{ margin-top:3px; }}
.report-modal-actions {{ display:flex; align-items:center; gap:8px; }}
.report-date-select {{ background:rgba(255,255,255,0.05); border:1px solid {OUTLINE_VARIANT};
  color:{ON_SURFACE}; font-family:'JetBrains Mono'; font-size:12px; padding:5px 8px;
  border-radius:var(--radius); outline:none; cursor:pointer; }}
.report-date-select option {{ background:#0d1528; }}
.report-dl-btn {{ display:flex; align-items:center; justify-content:center; width:30px; height:30px;
  color:{ON_SURFACE_VARIANT}; border-radius:var(--radius); text-decoration:none;
  transition:color .2s, background .2s; }}
.report-dl-btn:hover {{ color:{PRIMARY}; background:rgba(138,235,255,0.1); }}
.report-dl-btn .material-symbols-outlined {{ font-size:20px; }}
.report-modal-close {{ width:30px; height:30px; background:transparent; border:none;
  color:{ON_SURFACE_VARIANT}; font-size:22px; cursor:pointer; border-radius:var(--radius);
  transition:color .2s, background .2s; }}
.report-modal-close:hover {{ color:{PRIMARY}; background:rgba(138,235,255,0.1); }}
.report-body {{ padding:16px 22px 22px; overflow-y:auto; font-family:'Geist'; color:{ON_SURFACE}; }}
.rp-h1 {{ font-size:18px; font-weight:700; margin:4px 0 12px; color:{PRIMARY}; }}
.rp-h2 {{ font-family:'JetBrains Mono'; font-size:12px; letter-spacing:0.06em;
  text-transform:uppercase; color:{ON_SURFACE_VARIANT}; margin:14px 0 6px; }}
.rp-li {{ font-family:'JetBrains Mono'; font-size:13px; padding:3px 0; line-height:1.5;
  border-left:2px solid rgba(138,235,255,0.15); padding-left:10px; margin:2px 0; }}
.rp-li b {{ color:{PRIMARY}; font-weight:600; }}
.rp-p {{ font-family:'JetBrains Mono'; font-size:13px; color:{ON_SURFACE_VARIANT};
  padding:6px 0 2px; }}
.rp-p b {{ color:{ON_SURFACE}; }}
/* toggle 开关 */
.switch {{ position:relative; display:inline-block; width:48px; height:26px; vertical-align:middle; }}
.switch input {{ opacity:0; width:0; height:0; }}
.switch .track {{ position:absolute; inset:0; background:{SURFACE_CONTAINER_HIGH};
  border-radius:9999px; border:2px solid {OUTLINE_VARIANT}; transition:.25s; }}
.switch .thumb {{ position:absolute; top:1px; left:1px; width:22px; height:22px;
  background:{SURFACE}; border-radius:50%; box-shadow:0 1px 3px rgba(0,0,0,.4);
  transition:.25s; }}
.switch input:checked + .track {{ background:{PRIMARY}; border-color:{PRIMARY}; }}
.switch input:checked + .track + .thumb {{ transform:translateX(22px); }}
/* 通用按钮 */
.btn {{
  background:{PRIMARY}; color:{ON_PRIMARY}; border:none; cursor:pointer;
  padding:8px 16px; border-radius:var(--radius); font-family:'JetBrains Mono';
  font-weight:500; font-size:12px; letter-spacing:0.05em;
  text-transform:uppercase; transition:transform .1s, background .2s;
}}
.btn:hover {{ background:rgba(138,235,255,0.85); }}
.btn:active {{ transform:scale(.96); }}
.btn-ghost {{ background:transparent; color:{ON_SURFACE_VARIANT};
  border:1px solid {SURFACE_CONTAINER_HIGHEST}; }}
.btn-ghost:hover {{ color:{PRIMARY}; border-color:rgba(138,235,255,0.4);
  background:rgba(138,235,255,0.06); }}
/* 4 列栅格 */
.grid-12 {{ display:grid; grid-template-columns:repeat(12, 1fr); gap:24px; }}
.col {{ grid-column:span 1; }}
.span-4 {{ grid-column:span 4; }}
.span-5 {{ grid-column:span 5; }}
.span-6 {{ grid-column:span 6; }}
.span-7 {{ grid-column:span 7; }}
.span-8 {{ grid-column:span 8; }}
.span-12 {{ grid-column:span 12; }}
.row {{ display:flex; align-items:center; gap:8px; }}
.row-end {{ display:flex; align-items:flex-end; gap:6px; }}
.cols-x {{ display:flex; align-items:flex-end; justify-content:space-between; }}
@media (max-width: 900px) {{
  .grid-12 {{ grid-template-columns:1fr; }}
  .span-4,.span-5,.span-6,.span-7,.span-8 {{ grid-column:span 1; }}
}}
"""

# ── 页面级注入（一次性给当前页加进 <head>） ──────────
def inject() -> None:
    from nicegui import ui
    ui.add_head_html(_FONTS_LINK)
    ui.add_head_html(f"<style>{_CSS}</style>")
