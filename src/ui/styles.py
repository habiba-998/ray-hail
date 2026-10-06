"""CSS. Identity: calm agricultural GREEN + WHITE. Red / yellow are used ONLY for status, always with text + icon."""
from __future__ import annotations

import streamlit as st

GREEN = "#2F7D4E"        # primary
GREEN_DARK = "#1E5B38"   # important elements, headings
GREEN_LIGHT = "#EEF6F0"  # soft backgrounds
LINE = "#DDE9E0"         # borders
INK = "#1F2D27"          # text
MUTED = "#5E6E66"        # secondary text

BASE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;700&family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif; color:{INK}; }}
[data-testid="stMainBlockContainer"].block-container {{ padding-top: 4.2rem !important; max-width: 1180px; }}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:#FFFFFF; }}

/* ---------- top bar ---------- */
.topbar {{ display:flex; align-items:center; gap:14px; }}
.topbar img {{ height:52px; }}
.topbar h1 {{ margin:0; font-size:1.85rem; font-weight:800; color:{GREEN_DARK}; line-height:1.1; }}
.topbar h1 .ar {{ font-family:'IBM Plex Sans Arabic',sans-serif; color:{GREEN}; }}
.topbar .sub {{ color:{MUTED}; font-size:1rem; margin-top:3px; }}
.databadge {{ border-radius:12px; padding:8px 14px; font-weight:500; font-size:.92rem; margin:8px 0 4px 0; }}
.databadge.real {{ background:{GREEN_LIGHT}; border:1px solid {LINE}; color:{GREEN_DARK}; }}
.databadge.demo {{ background:#FFF6DD; border:2px solid #E8B21E; color:#6B4A00; font-weight:700; }}

/* ---------- controls: large touch targets ---------- */
div.stButton > button {{ min-height:54px; font-size:1.05rem; font-weight:600; border-radius:14px; }}
div.stButton > button[kind="primary"] {{ background:{GREEN}; border-color:{GREEN}; }}
div.stButton > button[kind="primary"]:hover {{ background:{GREEN_DARK}; border-color:{GREEN_DARK}; }}
[data-testid="stButtonGroup"] button {{ min-height:46px; font-size:1rem; }}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{ min-height:48px; font-size:1.02rem; }}
[data-testid="stFileUploaderDropzone"] {{ min-height:120px; border:2px dashed {GREEN}; background:{GREEN_LIGHT}; border-radius:16px; }}
[data-testid="stCheckbox"] label p {{ font-size:1.05rem; }}

/* ---------- farmer cards ---------- */
.q {{ font-size:1.5rem; font-weight:700; color:{GREEN_DARK}; margin:6px 0 10px 0; }}
.section-title {{ font-size:1.12rem; font-weight:700; color:{GREEN_DARK}; margin:18px 0 8px 0; }}
.muted {{ color:{MUTED}; font-size:.95rem; }}
.card {{ background:#fff; border:1px solid {LINE}; border-radius:16px; padding:16px 18px; }}
.card.soft {{ background:{GREEN_LIGHT}; }}
.status-hero {{ display:flex; align-items:center; gap:16px; border-radius:18px; padding:18px 20px; border:1px solid {LINE}; background:#fff; }}
.status-hero .dot {{ flex:0 0 58px; height:58px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.7rem; color:#fff; font-weight:800; }}
.status-hero h2 {{ margin:0; font-size:1.6rem; font-weight:700; color:{INK}; line-height:1.25; }}
.status-hero .sub {{ color:{MUTED}; font-size:.98rem; margin-top:2px; }}
.tiles {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; margin-top:10px; }}
.tile {{ border:1px solid {LINE}; border-radius:14px; padding:12px 10px; text-align:center; background:#fff; }}
.tile .n {{ font-size:1.9rem; font-weight:800; line-height:1.1; }}
.tile .l {{ font-size:.95rem; color:{MUTED}; }}
.zone-card {{ border-radius:16px; padding:16px 18px; background:#fff; border:1px solid {LINE}; border-inline-start:10px solid; }}
.zone-card .z {{ font-size:1.5rem; font-weight:800; color:{INK}; }}
.zone-card .s {{ font-size:1.1rem; font-weight:700; margin-top:2px; }}
.zone-card .d {{ font-size:1.02rem; color:{INK}; margin-top:8px; }}
.zone-card .n {{ font-size:.88rem; color:{MUTED}; margin-top:8px; }}
.pill {{ display:inline-block; border-radius:999px; padding:3px 12px; font-weight:700; font-size:.92rem; }}
.cause {{ display:flex; align-items:center; gap:12px; padding:10px 12px; border:1px solid {LINE}; border-radius:12px; margin-bottom:6px; background:#fff; }}
.cause .ic {{ font-size:1.5rem; flex:0 0 32px; text-align:center; }}
.cause .nm {{ flex:1; font-size:1.05rem; font-weight:600; }}
.lvl {{ border-radius:999px; padding:3px 10px; font-size:.85rem; font-weight:700; white-space:nowrap; }}
.lvl.strong {{ background:#FDE7E6; color:#A12F2B; }}
.lvl.moderate {{ background:#FFF3D6; color:#7A5600; }}
.lvl.weak {{ background:{GREEN_LIGHT}; color:{GREEN_DARK}; }}
.lvl.none {{ background:#F2F4F3; color:{MUTED}; font-weight:500; }}
.note-card {{ background:#F4F8FC; border:1px solid #CFDDEB; border-radius:14px; padding:12px 14px; font-size:1rem; color:#1F3A52; }}
.legend-big {{ display:flex; flex-wrap:wrap; gap:8px 16px; font-size:1rem; margin:6px 0; }}
.legend-big span.sw {{ display:inline-block; width:16px; height:16px; border-radius:4px; vertical-align:-3px; margin-inline-end:6px; }}
.checklist li {{ font-size:1.05rem; margin-bottom:5px; }}
.status-line {{ font-size:1.25rem; font-weight:600; margin:6px 0; }}
.side-brand {{ display:flex; align-items:center; gap:8px; font-size:1.5rem; font-weight:700; color:{GREEN_DARK}; margin-bottom:12px; }}
.side-brand img {{ height:36px; }}
[data-testid="stSidebar"] {{ background:{GREEN_LIGHT}; }}
[data-testid="stSidebar"] [data-testid="stRadio"] label p {{ font-size:1.08rem; }}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{ padding:6px 0; }}
.step {{ font-size:1.05rem; font-weight:700; color:{GREEN}; margin:14px 0 6px 0; }}

/* ---------- technical mode (kept from the original dashboard) ---------- */
.card .lbl {{ color:{MUTED}; font-size:.78rem; text-transform:uppercase; letter-spacing:.6px;}}
.card .val {{ font-size:1.6rem; font-weight:800; color:{INK}; line-height:1.2;}}
.card .sub {{ color:{MUTED}; font-size:.82rem;}}
.zonecard {{ border-radius:14px; padding:16px 18px; color:#fff; margin-bottom:10px;}}
.zonecard h3 {{ margin:0 0 4px 0; color:#fff;}}
.rtl {{ direction: rtl; text-align:right; font-family:'IBM Plex Sans Arabic',sans-serif; font-size:1.05rem;}}
.legend {{ background:#fff; border:1px solid {LINE}; border-radius:10px; padding:10px 12px; font-size:.85rem; margin-bottom:10px;}}
.legend .lg-item {{ display:flex; align-items:center; gap:8px; margin-top:4px;}}
.legend .lg-item span {{ width:14px; height:14px; border-radius:3px; display:inline-block;}}
.legend .lg-bar {{ height:12px; border-radius:6px; margin-top:6px;}}
.legend .lg-ticks {{ display:flex; justify-content:space-between; color:{MUTED}; font-size:.75rem;}}
.flow {{ display:flex; align-items:stretch; gap:6px; flex-wrap:wrap; margin:6px 0 14px 0; }}
.flow .fs {{ flex:1 1 120px; background:#fff; border:1px solid {LINE}; border-top:4px solid {GREEN}; border-radius:12px; padding:10px 12px; }}
.flow .fs.ml {{ border-top-color:#D64541; background:#FFF7F6; }}
.flow .fs b {{ display:block; font-size:.9rem; color:{INK}; }}
.flow .fs small {{ color:{MUTED}; font-size:.8rem; line-height:1.35; display:block; margin-top:4px; }}
.flow .fa {{ align-self:center; font-size:1.1rem; color:{GREEN}; }}
.badge {{ display:inline-block; border-radius:999px; padding:2px 10px; font-size:.75rem; font-weight:700; letter-spacing:.4px; }}
.badge.on {{ background:{GREEN_LIGHT}; color:{GREEN_DARK}; border:1px solid {GREEN}; }}
.badge.off {{ background:#F3F6F7; color:{MUTED}; border:1px solid #9AA3A8; }}
.caveat {{ background:#F3F6F4; border-inline-start:4px solid {GREEN}; border-radius:8px; padding:10px 14px; font-size:.88rem; color:#28414B;}}
.footer {{ color:{MUTED}; font-size:.8rem; text-align:center; margin-top:28px;}}

/* ---------- phones ---------- */
@media (max-width: 640px) {{
  .topbar h1 {{ font-size:1.45rem; }} .topbar img {{ height:40px; }}
  .status-hero {{ padding:14px; gap:12px; }} .status-hero h2 {{ font-size:1.3rem; }}
  .status-hero .dot {{ flex-basis:48px; height:48px; font-size:1.4rem; }}
  .tile .n {{ font-size:1.5rem; }} .q {{ font-size:1.25rem; }}
  .flow .fa {{ display:none; }}
}}
</style>
"""

RTL_CSS = """
<style>
/* Arabic: right-to-left text in the farmer views (maps/charts keep their own layout) */
[data-testid="stMain"] .stMarkdown, [data-testid="stMain"] .stCaption, [data-testid="stMain"] [data-testid="stExpander"] summary,
[data-testid="stMain"] [data-testid="stCheckbox"], [data-testid="stMain"] [data-testid="stRadio"], [data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] [data-testid="stRadio"], [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
.status-hero, .zone-card, .card, .note-card, .cause, .legend-big, .databadge, .topbar .sub, .tiles {
  direction: rtl; text-align: right; font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif; }
div.stButton > button p { font-family: 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif; font-size:1.08rem; }
</style>
"""


def inject(rtl: bool) -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    if rtl:
        st.markdown(RTL_CSS, unsafe_allow_html=True)
