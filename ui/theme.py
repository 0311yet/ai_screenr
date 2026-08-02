"""ai_screenr 设计系统 — Stitch "Sentinel Console / Deep Dark Ops" 风格。

由 Google Stitch 生成的 design system 落地：
- 配色取 Material You 命名（primary/secondary/tertiary + surface-* five-tier）
- 双字体：Inter（结构/标题）+ JetBrains Mono（数据/标签），Material Symbols 图标
- Glassmorphism + CRT scanline 纹理 + 1px 边 + neon 内发光
所有页面共用，避免 NiceGUI 引 Tailwind CDN 依赖外网。
"""
from __future__ import annotations

# ── Stitch Design Tokens ──────────────────────
# 背景与表面（五层 container）
CANVAS = "#0e1416"               # 纯深底
SURFACE = "#0e1416"
SURFACE_DIM = "#0e1416"
SURFACE_BRIGHT = "#343a3c"
SURFACE_LOWEST = "#090f11"
SURFACE_LOW = "#161d1e"
SURFACE_CONTAINER = "#1a2122"
SURFACE_HIGH = "#242b2d"
SURFACE_HIGHEST = "#2f3638"
SURFACE_VARIANT = "#2f3638"

# 文本与边线
ON_SURFACE = "#dde4e5"
ON_SURFACE_VARIANT = "#bbc9cd"
ON_BACKGROUND = "#dde4e5"
OUTLINE = "#859397"
OUTLINE_VARIANT = "#3c494c"
INVERSE_SURFACE = "#dde4e5"
INVERSE_ON_SURFACE = "#2b3233"

# 主色与辅色（霓虹青/蓝绿/琥珀）
PRIMARY = "#8aebff"              # 霓虹青 - 主交互/活跃
PRIMARY_DIM = "#2fd9f4"          # primary-fixed-dim
PRIMARY_CONTAINER = "#22d3ee"
ON_PRIMARY = "#00363e"
ON_PRIMARY_CONTAINER = "#005763"
PRIMARY_FIXED = "#a2eeff"
SECONDARY = "#44e2cd"
SECONDARY_DIM = "#3cddc7"
SECONDARY_CONTAINER = "#03c6b2"
ON_SECONDARY = "#003731"
ON_SECONDARY_CONTAINER = "#004d44"
TERTIARY = "#ffd6a3"
TERTIARY_DIM = "#ffb957"
TERTIARY_CONTAINER = "#ffb13b"
ON_TERTIARY = "#462b00"
ERROR = "#ffb4ab"
ON_ERROR = "#690005"
ERROR_CONTAINER = "#93000a"

# 圆角 / spacing
RADIUS_SM = "4px"
RADIUS = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"
RADIUS_FULL = "9999px"
SP_UNIT = "4px"
SP_SM = "8px"
SP_MD = "16px"
SP_LG = "24px"
SP_XL = "48px"
GUTTER = "16px"
MARGIN_SAFE = "24px"

# 活动类目配色（8 类，含学习）— 取 Material 风高饱和色，作小指示用
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

# ── 字体引入（一次性给页面 head） ─────────────
_FONTS_LINK = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Inter:wght@400;500;600;700&'
    'family=JetBrains+Mono:wght@400;500;600&'
    'family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" rel="stylesheet">'
)

# ── 主样式表 ──────────────────────────────
_CSS = f"""
/* ===== Reset & 全局 ===== */
:root {{
  --canvas:{CANVAS}; --surface:{SURFACE};
  --surface-dim:{SURFACE_DIM}; --surface-bright:{SURFACE_BRIGHT};
  --surface-lowest:{SURFACE_LOWEST}; --surface-low:{SURFACE_LOW};
  --surface-container:{SURFACE_CONTAINER}; --surface-high:{SURFACE_HIGH};
  --surface-highest:{SURFACE_HIGHEST}; --surface-variant:{SURFACE_VARIANT};
  --on-surface:{ON_SURFACE}; --on-surface-variant:{ON_SURFACE_VARIANT};
  --outline:{OUTLINE}; --outline-variant:{OUTLINE_VARIANT};
  --inverse-surface:{INVERSE_SURFACE}; --inverse-on-surface:{INVERSE_ON_SURFACE};
  --primary:{PRIMARY}; --primary-dim:{PRIMARY_DIM}; --primary-container:{PRIMARY_CONTAINER};
  --on-primary:{ON_PRIMARY}; --on-primary-container:{ON_PRIMARY_CONTAINER}; --primary-fixed:{PRIMARY_FIXED};
  --secondary:{SECONDARY}; --secondary-dim:{SECONDARY_DIM}; --secondary-container:{SECONDARY_CONTAINER};
  --on-secondary:{ON_SECONDARY}; --on-secondary-container:{ON_SECONDARY_CONTAINER};
  --tertiary:{TERTIARY}; --tertiary-dim:{TERTIARY_DIM}; --tertiary-container:{TERTIARY_CONTAINER}; --on-tertiary:{ON_TERTIARY};
  --error:{ERROR}; --error-container:{ERROR_CONTAINER}; --on-error:{ON_ERROR};
  --r-sm:{RADIUS_SM}; --r:{RADIUS}; --r-md:{RADIUS_MD}; --r-lg:{RADIUS_LG}; --r-xl:{RADIUS_XL}; --r-full:{RADIUS_FULL};
  --sp-unit:{SP_UNIT}; --sp-sm:{SP_SM}; --sp-md:{SP_MD}; --sp-lg:{SP_LG}; --sp-xl:{SP_XL};
}}
* {{ box-sizing:border-box; }}
html, body {{
  margin:0; padding:0; min-height:100vh; width:100%;
  background:var(--canvas); color:var(--on-surface);
  font-family:'Inter','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  /* CRT 扫描线纹理：1px 横线，5% 白，错落叠在底色之上 */
  background-image:repeating-linear-gradient(
    to bottom, rgba(255,255,255,0.04) 0, rgba(255,255,255,0.04) 1px,
    transparent 1px, transparent 3px);
  background-attachment:fixed;
}}
/* 清掉 NiceGUI / Quasar 默认布局，让自定义 CSS 主导 */
.nicegui-content, .q-page, .q-layout, .q-page-container {{
  background:transparent !important; color:var(--on-surface) !important;
  padding:0 !important; display:block !important; width:100% !important;
  max-width:none !important; min-height:100vh !important;
}}
.glass, .topbar {{ width:100%; }}
.mono {{ font-family:'JetBrains Mono','Cascadia Code',monospace; }}

/* ===== Glassmorphism 卡片 ===== */
.glass {{
  position:relative;
  background:linear-gradient(180deg, rgba(26,33,34,0.78) 0%, rgba(16,20,22,0.78) 100%);
  -webkit-backdrop-filter:blur(14px); backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,0.06);
  border-top:1px solid rgba(138,235,255,0.22);
  border-radius:var(--r-lg);
  /* 用内发光替代重阴影：cyan 顶部高光 + 深底投影 */
  box-shadow:
    inset 0 1px 0 rgba(138,235,255,0.08),
    0 12px 32px rgba(0,0,0,0.55),
    0 0 24px rgba(34,211,238,0.04);
  padding:var(--sp-lg);
}}
.glass::before {{
  /* 玻璃卡内部扫描线（更淡），叠加在背景 */
  content:""; position:absolute; inset:0; border-radius:inherit;
  pointer-events:none; opacity:0.35;
  background-image:repeating-linear-gradient(
    to bottom, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 1px,
    transparent 1px, transparent 4px);
}}
.glass > * {{ position:relative; z-index:1; }}     /* 让内容浮在扫描线上 */
.glass-tight {{ padding:var(--sp-md); }}

/* ===== 文字层级（基于 Stitch typography） ===== */
.h1 {{ font-family:'Inter'; font-weight:700; font-size:32px; line-height:1.2;
       letter-spacing:-0.02em; margin:0; }}
.h2 {{ font-family:'Inter'; font-weight:600; font-size:24px; line-height:1.3; margin:0; }}
.h3 {{ font-family:'Inter'; font-weight:600; font-size:16px; line-height:1.4; margin:0; }}
.h4 {{ font-family:'Inter'; font-weight:600; font-size:13px; line-height:1.4; margin:0;
       color:var(--on-surface); letter-spacing:0.01em; }}
.tiny {{ font-size:11px; color:var(--on-surface-variant); letter-spacing:0.04em; }}
.data {{ font-family:'JetBrains Mono'; font-size:13px; line-height:1.5; letter-spacing:-0.01em; }}
.caps {{
  font-family:'JetBrains Mono'; font-weight:700; font-size:10px;
  letter-spacing:0.08em; text-transform:uppercase; color:var(--on-surface-variant);
}}
.bold-mono {{ font-family:'JetBrains Mono'; font-weight:600; }}

/* ===== Topbar ===== */
.topbar {{
  position:sticky; top:0; z-index:40;
  padding:14px var(--sp-lg);
  background:linear-gradient(180deg, rgba(14,20,22,0.92) 0%, rgba(14,20,22,0.78) 100%);
  -webkit-backdrop-filter:blur(18px); backdrop-filter:blur(18px);
  border-bottom:1px solid rgba(60,73,76,0.5);
  box-shadow:0 0 24px rgba(34,211,238,0.05);
  display:flex; align-items:center; justify-content:flex-end; gap:var(--sp-sm);
}}
.brand {{
  font-family:'Inter'; font-weight:700; font-size:22px;
  letter-spacing:-0.01em; text-transform:uppercase;
  color:var(--primary); flex:1; line-height:1;
  display:flex; align-items:center; gap:2px;
  text-shadow:0 0 12px rgba(138,235,255,0.35);
}}
.brand .brand-mark {{
  font-family:'JetBrains Mono'; color:var(--primary-dim);
  margin-right:8px; font-size:22px;
}}
.topbar .act-btn {{
  background:transparent; border:none; color:var(--on-surface-variant);
  cursor:pointer; padding:6px 8px; border-radius:var(--r-sm);
  transition:color .18s, background .18s, box-shadow .18s;
}}
.topbar .act-btn:hover {{ color:var(--primary); background:rgba(138,235,255,0.08); box-shadow:0 0 0 1px rgba(138,235,255,0.25); }}
.material-symbols-outlined {{
  font-family:'Material Symbols Outlined'; font-weight:400; font-style:normal;
  font-size:22px; line-height:1; vertical-align:middle;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  -webkit-font-feature-settings:'liga'; font-feature-settings:'liga';
}}

/* ===== 通用按钮 ===== */
.btn {{
  background:linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
  color:var(--on-primary); border:none; cursor:pointer;
  padding:8px 18px; border-radius:var(--r-md);
  font-family:'JetBrains Mono'; font-weight:600; font-size:11px;
  letter-spacing:0.08em; text-transform:uppercase;
  box-shadow:0 0 0 1px rgba(34,211,238,0.3), 0 0 14px rgba(34,211,238,0.18);
  transition:transform .1s, box-shadow .18s, filter .18s;
}}
.btn:hover {{ filter:brightness(1.08); box-shadow:0 0 0 1px rgba(34,211,238,0.5), 0 0 20px rgba(34,211,238,0.3); }}
.btn:active {{ transform:scale(.97); }}
.btn-ghost {{
  background:transparent; color:var(--on-surface-variant);
  border:1px solid var(--outline-variant);
  box-shadow:none;
}}
.btn-ghost:hover {{
  color:var(--primary); border-color:rgba(138,235,255,0.45);
  background:rgba(138,235,255,0.06);
  box-shadow:0 0 0 1px rgba(138,235,255,0.25), 0 0 14px rgba(34,211,238,0.12);
}}

/* ===== 24h 时间轴（144 段） ===== */
.timeline-wrap {{
  display:flex; align-items:flex-end; gap:2px; height:96px;
  background:rgba(9,15,17,0.5); padding:8px 8px 6px;
  border-radius:var(--r-md); border:1px solid rgba(60,73,76,0.3);
}}
.seg {{
  flex:1 1 0; min-width:0; border-radius:2px;
  transition:transform .15s, filter .15s, box-shadow .15s; cursor:pointer;
  position:relative;
}}
.seg:hover {{ transform:scaleY(1.35); filter:brightness(1.25); box-shadow:0 0 8px currentColor; }}
.seg.active {{
  transform:scaleY(1.55); filter:brightness(1.45);
  outline:1px solid var(--primary); outline-offset:2px;
  box-shadow:0 0 14px rgba(34,211,238,0.4);
}}
/* 有数据段顶部高光条（0..96px 按高度比例缩放，低于 12px 时仍可见） */
.seg-cap {{
  position:absolute; top:0; left:0; right:0; height:2px;
  background:rgba(255,255,255,0.4); border-radius:2px 2px 0 0;
}}
/* 空段：矮块、深底、无高光、不可点（退率达约 10%） */
.seg-empty {{ height:10%; background:var(--surface-highest); cursor:default; }}
.seg-empty:hover {{ transform:none; filter:none; box-shadow:none; cursor:default; }}
.seg-empty.seg.active {{ transform:none; outline:none; box-shadow:none; }}
.timeline-axis {{
  display:flex; justify-content:space-between; margin-top:var(--sp-sm);
  font-family:'JetBrains Mono'; font-size:10px; color:var(--on-surface-variant);
  opacity:0.7; letter-spacing:0.06em;
}}

/* ===== 当前活动旋转环 orbit ===== */
.orbit {{
  position:relative; width:148px; height:148px; border-radius:50%;
  background:radial-gradient(circle, rgba(34,211,238,0.10) 0%, rgba(14,20,22,0) 70%);
  display:grid; place-items:center; margin:0 auto;
}}
.orbit .ring {{
  position:absolute; inset:0; border-radius:50%;
  border:3px solid var(--orbit-c, var(--primary)); border-top-color:transparent;
  animation:spin 3s linear infinite;
  box-shadow:0 0 18px var(--orbit-c, rgba(34,211,238,0.5)), inset 0 0 12px var(--orbit-c, rgba(34,211,238,0.2));
}}
.orbit .core {{
  font-size:44px; color:var(--orbit-c, var(--primary));
  text-shadow:0 0 12px var(--orbit-c, rgba(34,211,238,0.6));
}}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}

/* ===== conic 环图（活动构成） ===== */
.conic-donut {{
  width:184px; height:184px; margin:auto; position:relative;
  border-radius:50%;
  box-shadow:0 0 32px rgba(34,211,238,0.06), inset 0 0 0 1px rgba(255,255,255,0.05);
}}
.conic-donut .hole {{
  position:absolute; inset:20%; border-radius:50%;
  background:radial-gradient(circle, var(--surface) 0%, var(--surface-low) 100%);
  display:grid; place-items:center; text-align:center;
  box-shadow:inset 0 0 12px rgba(0,0,0,0.5);
}}
.conic-donut .hole .big {{
  font-family:'Inter'; font-weight:700; font-size:26px;
  color:var(--primary); line-height:1.1; letter-spacing:-0.02em;
  text-shadow:0 0 10px rgba(138,235,255,0.3);
}}
.conic-donut .hole .sub {{
  font-family:'JetBrains Mono'; font-size:10px;
  color:var(--on-surface-variant); letter-spacing:0.08em; text-transform:uppercase;
}}
.mix-row {{
  display:flex; justify-content:space-between; align-items:center;
  font-family:'JetBrains Mono'; font-size:12px; padding:5px 0;
  border-bottom:1px solid rgba(255,255,255,0.04);
}}
.mix-row:last-child {{ border-bottom:none; }}
.mix-row .swatch {{
  display:inline-block; width:10px; height:10px; border-radius:2px;
  margin-right:10px; vertical-align:middle;
  box-shadow:0 0 6px currentColor;
}}

/* ===== 24h 强度柱图 ===== */
.bars {{
  display:flex; align-items:flex-end; gap:4px; height:184px;
  /* 扫描线节点感：每隔 4px 一道淡白线 */
  background:
    linear-gradient(to bottom, transparent 0, transparent 50%,
      rgba(255,255,255,0.05) 50%, rgba(255,255,255,0.05) 100%);
  background-size:100% 4px; background-repeat:repeat;
  padding:0 4px; border-radius:var(--r-md); border:1px solid rgba(60,73,76,0.25);
}}
.bar {{
  flex:1 1 0; min-width:0;
  background:linear-gradient(180deg, var(--primary-dim) 0%, var(--surface-highest) 100%);
  border-radius:2px 2px 0 0; position:relative;
  transition:filter .15s, box-shadow .15s;
}}
.bar:hover {{ filter:brightness(1.3); box-shadow:0 0 8px var(--primary-dim); }}
.bar .cap {{
  position:absolute; top:0; left:0; right:0; height:3px;
  background:var(--primary); border-radius:2px 2px 0 0;
  box-shadow:0 0 6px var(--primary);
}}

/* ===== 活动日志表 ===== */
.log-table {{
  width:100%; border-collapse:collapse; font-family:'JetBrains Mono';
}}
.log-table th {{
  text-align:left; font-family:'JetBrains Mono'; font-weight:700;
  font-size:10px; letter-spacing:0.08em; text-transform:uppercase;
  color:var(--on-surface-variant);
  border-bottom:1px solid rgba(60,73,76,0.5); padding:10px 12px 12px;
}}
.log-table td {{
  font-family:'JetBrains Mono'; font-size:12px; padding:9px 12px;
  border-bottom:1px solid rgba(255,255,255,0.04);
}}
.log-table tbody tr {{ transition:background .15s; }}
.log-table tbody tr:hover td {{ background:rgba(34,211,238,0.08); }}
.ev-icon {{ font-size:16px !important; vertical-align:-3px; margin-right:8px; }}

/* ===== 状态点 & chip ===== */
.live-dot {{
  display:inline-block; width:6px; height:6px; border-radius:50%;
  background:var(--primary); margin-right:6px;
  box-shadow:0 0 8px var(--primary);
  animation:pulse 1.6s ease-in-out infinite;
}}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.35; }} }}
.chip {{
  display:inline-flex; align-items:center; gap:4px; padding:3px 10px;
  border:1px solid rgba(34,211,238,0.4); background:rgba(34,211,238,0.08);
  border-radius:var(--r-full); font-family:'JetBrains Mono';
  font-weight:700; font-size:10px; letter-spacing:0.08em; text-transform:uppercase;
  color:var(--primary); box-shadow:0 0 10px rgba(34,211,238,0.12);
}}
/* QCard 复写 */
.nicegui-card {{ background:transparent !important; border:none !important; box-shadow:none !important; }}

/* ===== 设置页装饰光晕 ===== */
.glow-blob {{ position:absolute; border-radius:50%; filter:blur(120px); pointer-events:none; }}
.bg-glow-tl {{ top:-10%; left:-10%; width:40vw; height:40vh; background:rgba(138,235,255,0.08); }}
.bg-glow-br {{ bottom:-10%; right:-10%; width:30vw; height:30vh; background:rgba(68,226,205,0.06); }}

/* ===== toggle 开关（Stitch 风霓虹滑块） ===== */
.switch {{ position:relative; display:inline-block; width:52px; height:28px; vertical-align:middle; }}
.switch input {{ opacity:0; width:0; height:0; }}
.switch .track {{
  position:absolute; inset:0; background:var(--surface-high);
  border-radius:var(--r-full); border:1px solid var(--outline-variant);
  transition:.25s;
}}
.switch .thumb {{
  position:absolute; top:2px; left:2px; width:22px; height:22px;
  background:var(--surface-bright); border-radius:50%;
  box-shadow:0 1px 3px rgba(0,0,0,0.5); transition:.25s;
}}
.switch input:checked + .track {{
  background:linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
  border-color:var(--primary);
  box-shadow:0 0 12px rgba(34,211,238,0.4), inset 0 0 0 1px rgba(138,235,255,0.4);
}}
.switch input:checked + .track + .thumb {{ transform:translateX(24px); background:var(--on-primary); }}

/* ===== 12 列栅格 ===== */
.grid-12 {{ display:grid; grid-template-columns:repeat(12, 1fr); gap:var(--sp-lg); }}
.col {{ grid-column:span 1; }}
.span-3 {{ grid-column:span 3; }}
.span-4 {{ grid-column:span 4; }}
.span-5 {{ grid-column:span 5; }}
.span-6 {{ grid-column:span 6; }}
.span-7 {{ grid-column:span 7; }}
.span-8 {{ grid-column:span 8; }}
.span-9 {{ grid-column:span 9; }}
.span-12 {{ grid-column:span 12; }}
.row {{ display:flex; align-items:center; gap:var(--sp-sm); }}
.row-end {{ display:flex; align-items:flex-end; gap:6px; }}
.cols-x {{ display:flex; align-items:flex-end; justify-content:space-between; }}
@media (max-width: 980px) {{
  .grid-12 {{ grid-template-columns:1fr; }}
  .span-3,.span-4,.span-5,.span-6,.span-7,.span-8,.span-9 {{ grid-column:span 1; }}
}}

/* ===== 段详情 drawer（保留原选择器，仅 Stitch 化视觉） ===== */
.seg-detail {{
  position:fixed; top:88px; right:24px; width:340px;
  background:linear-gradient(180deg, rgba(26,33,34,0.95) 0%, rgba(14,20,22,0.95) 100%);
  -webkit-backdrop-filter:blur(18px); backdrop-filter:blur(18px);
  border:1px solid rgba(138,235,255,0.28);
  border-top:1px solid rgba(138,235,255,0.45);
  border-radius:var(--r-lg);
  box-shadow:0 12px 40px rgba(0,0,0,0.6), 0 0 30px rgba(34,211,238,0.1);
  padding:var(--sp-lg); z-index:60; font-family:'Inter';
}}
.seg-detail-close {{
  position:absolute; top:10px; right:10px; width:28px; height:28px;
  background:transparent; border:none; color:var(--on-surface-variant);
  font-size:20px; cursor:pointer; border-radius:var(--r-sm);
  transition:color .2s, background .2s;
}}
.seg-detail-close:hover {{ color:var(--primary); background:rgba(138,235,255,0.1); }}
.seg-detail-head {{ display:flex; align-items:flex-start; gap:12px; margin-bottom:14px; }}
.seg-detail-icon {{ font-size:36px; color:var(--primary); text-shadow:0 0 10px currentColor; }}
.seg-detail-range {{
  font-family:'JetBrains Mono'; font-size:11px; color:var(--on-surface-variant);
  letter-spacing:0.05em; margin-bottom:2px;
}}
.seg-detail-main {{
  font-family:'Inter'; font-weight:700; font-size:22px; color:var(--primary);
  line-height:1.1; text-shadow:0 0 10px currentColor;
}}
.seg-detail-summary {{
  font-family:'Inter'; font-size:13px; color:var(--on-surface); line-height:1.5;
  background:rgba(34,211,238,0.06); border-left:2px solid var(--primary-dim);
  padding:8px 12px; border-radius:0 var(--r-md) var(--r-md) 0; margin-bottom:14px;
}}
.seg-detail-section-title {{
  font-family:'JetBrains Mono'; font-weight:700; font-size:10px;
  color:var(--on-surface-variant); letter-spacing:0.08em; text-transform:uppercase;
  margin:10px 0 6px;
}}
.seg-detail-list {{ display:flex; flex-direction:column; gap:2px; }}
.seg-detail-row {{
  display:flex; align-items:center; justify-content:space-between;
  font-family:'JetBrains Mono'; font-size:13px; color:var(--on-surface); padding:4px 0;
}}
.seg-detail-row span:first-child {{
  display:flex; align-items:center; gap:8px; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap;
}}
.seg-detail-row span:last-child {{ color:var(--on-surface-variant); flex-shrink:0; margin-left:8px; }}
.seg-detail-swatch {{
  display:inline-block; width:8px; height:8px; border-radius:2px;
  flex-shrink:0; box-shadow:0 0 4px currentColor;
}}
.seg-detail-empty {{ padding:4px 0; opacity:0.5; }}
.seg-detail-stats {{ margin-top:12px; }}

/* ===== 日报 modal ===== */
.report-modal {{ position:fixed; inset:0; z-index:100; display:flex; align-items:center; justify-content:center; }}
.report-modal-backdrop {{
  position:absolute; inset:0; background:rgba(2,6,23,0.7);
  -webkit-backdrop-filter:blur(5px); backdrop-filter:blur(5px);
}}
.report-modal-card {{
  position:relative; width:min(720px,92vw); max-height:84vh; display:flex; flex-direction:column;
  background:linear-gradient(180deg, rgba(26,33,34,0.97) 0%, rgba(13,21,40,0.97) 100%);
  -webkit-backdrop-filter:blur(20px); backdrop-filter:blur(20px);
  border:1px solid rgba(138,235,255,0.25); border-top:1px solid rgba(138,235,255,0.4);
  border-radius:var(--r-lg);
  box-shadow:0 24px 64px rgba(0,0,0,0.65), 0 0 40px rgba(34,211,238,0.1);
}}
.report-modal-head {{
  display:flex; align-items:flex-start; justify-content:space-between; gap:12px;
  padding:18px 22px 14px; border-bottom:1px solid rgba(255,255,255,0.06);
}}
.report-modal-title {{
  font-family:'Inter'; font-weight:700; font-size:20px; color:var(--primary);
  display:flex; align-items:center; gap:8px;
  text-shadow:0 0 12px rgba(138,235,255,0.35);
}}
.report-modal-title .material-symbols-outlined {{ font-size:24px; }}
.report-modal-sub {{ margin-top:3px; }}
.report-modal-actions {{ display:flex; align-items:center; gap:8px; }}
.report-date-select {{
  background:rgba(255,255,255,0.05); border:1px solid var(--outline-variant);
  color:var(--on-surface); font-family:'JetBrains Mono'; font-size:12px;
  padding:6px 10px; border-radius:var(--r-sm); outline:none; cursor:pointer;
}}
.report-date-select option {{ background:#0d1528; }}
.report-dl-btn {{
  display:flex; align-items:center; justify-content:center;
  width:30px; height:30px; color:var(--on-surface-variant);
  border-radius:var(--r-sm); text-decoration:none;
  transition:color .2s, background .2s;
}}
.report-dl-btn:hover {{ color:var(--primary); background:rgba(138,235,255,0.1); }}
.report-dl-btn .material-symbols-outlined {{ font-size:20px; }}
.report-modal-close {{
  width:30px; height:30px; background:transparent; border:none;
  color:var(--on-surface-variant); font-size:22px; cursor:pointer;
  border-radius:var(--r-sm); transition:color .2s, background .2s;
}}
.report-modal-close:hover {{ color:var(--primary); background:rgba(138,235,255,0.1); }}
.report-body {{ padding:16px 24px 24px; overflow-y:auto; font-family:'Inter'; color:var(--on-surface); }}
.rp-h1 {{ font-size:20px; font-weight:700; margin:4px 0 12px; color:var(--primary); }}
.rp-h2 {{
  font-family:'JetBrains Mono'; font-weight:700; font-size:11px;
  letter-spacing:0.08em; text-transform:uppercase; color:var(--on-surface-variant);
  margin:14px 0 6px;
}}
.rp-li {{
  font-family:'JetBrains Mono'; font-size:13px; padding:4px 0 4px 12px;
  line-height:1.5; border-left:2px solid rgba(138,235,255,0.4); margin:2px 0;
}}
.rp-li b {{ color:var(--primary); font-weight:600; }}
.rp-p {{ font-family:'JetBrains Mono'; font-size:13px; color:var(--on-surface-variant); padding:6px 0 2px; }}
.rp-p b {{ color:var(--on-surface); }}
"""

# ── 页面级注入 ──────────────────────────────
def inject() -> None:
    """把字体 link + 全局 <style> 注入当前 NiceGUI 页面 head。"""
    from nicegui import ui
    ui.add_head_html(_FONTS_LINK)
    ui.add_head_html(f"<style>{_CSS}</style>")
