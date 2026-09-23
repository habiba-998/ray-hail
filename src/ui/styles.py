"""CSS for both modes. Farmer components use large type, big touch targets and text + icon (never colour alone)."""
from __future__ import annotations

import streamlit as st

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Tajawal:wght@500;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', 'Tajawal', 'Segoe UI', sans-serif; }
[data-testid="stMainBlockContainer"].block-container { padding-top: 4.2rem !important; max-width: 1280px; }

/* ---------- top bar ---------- */
.topbar { display:flex; align-items:center; gap:14px; }
.topbar img { height:54px; }
.topbar h1 { margin:0; font-size:1.9rem; font-weight:800; color:#0B2530; line-height:1.1; }
.topbar h1 .ar { font-family:'Tajawal',sans-serif; color:#0F766E; }
.topbar .sub { color:#3E5560; font-size:1rem; margin-top:2px; }
.databadge { border-radius:12px; padding:9px 14px; font-weight:600; font-size:.95rem; margin:8px 0 6px 0; }
.databadge.real { background:#E4F6EC; border:1px solid #2E9E5B; color:#155C35; }
.databadge.demo { background:#FFF4D6; border:2px solid #F2B01E; color:#6B4A00; }

/* ---------- big touch targets ---------- */
div.stButton > button { min-height:56px; font-size:1.05rem; font-weight:600; border-radius:14px; }
[data-testid="stButtonGroup"] button { min-height:46px; font-size:1rem; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div { min-height:48px; font-size:1.02rem; }

/* ---------- farmer cards ---------- */
.section-title { font-size:1.05rem; font-weight:800; color:#3E5560; letter-spacing:.4px; margin:14px 0 6px 0; text-transform:uppercase; }
.status-card { display:flex; align-items:center; gap:18px; border-radius:18px; padding:20px 22px; border:2px solid; }
.status-card .icon { flex:0 0 64px; height:64px; border-radius:50%; display:flex; align-items:center; justify-content:center;
                     font-size:2rem; color:#fff; font-weight:800; }
.status-card h2 { margin:0; font-size:1.9rem; font-weight:800; color:#0B2530; line-height:1.2; }
.status-card .sub { color:#3E5560; font-size:1rem; margin-top:4px; }
.prio-card { border-radius:16px; padding:16px 18px; background:#fff; border:1px solid #E3E8EA; border-left:10px solid; }
.prio-card .zone { font-size:1.6rem; font-weight:800; color:#0B2530; }
.prio-card .lbl { font-size:1.15rem; font-weight:700; margin-top:2px; }
.prio-card .act { font-size:1.08rem; color:#0B2530; margin-top:8px; }
.prio-card .note { font-size:.9rem; color:#5B6770; margin-top:8px; }
.pill { display:inline-block; border-radius:999px; padding:4px 12px; font-weight:700; font-size:.95rem; color:#fff; }
.chips { font-size:1rem; color:#3E5560; margin:10px 0 2px 0; }
.soft { background:#fff; border:1px solid #E3E8EA; border-radius:16px; padding:14px 16px; }
.soft h4 { margin:0 0 6px 0; font-size:1.1rem; color:#0B2530; }
.soft p { margin:0; font-size:1.02rem; color:#28414B; }
.note-card { background:#F1F6FB; border:1px solid #BCD3EA; border-radius:14px; padding:12px 14px; font-size:1rem; color:#1F3A52; }
.sig { background:#fff; border:1px solid #E3E8EA; border-radius:14px; padding:12px 14px; height:100%; border-top:6px solid; }
.sig .t { font-size:.9rem; color:#5B6770; font-weight:700; text-transform:uppercase; letter-spacing:.3px; }
.sig .v { font-size:1.12rem; font-weight:700; color:#0B2530; margin-top:4px; }
.legend-big { display:flex; flex-wrap:wrap; gap:8px 16px; font-size:1rem; margin:6px 0; }
.legend-big span.sw { display:inline-block; width:18px; height:18px; border-radius:4px; vertical-align:-3px; margin-inline-end:6px; }
.checklist li { font-size:1.05rem; margin-bottom:4px; }

/* ---------- technical mode (kept from the original dashboard) ---------- */
.card { background:#fff; border:1px solid #E3E8EA; border-radius:14px; padding:14px 16px; height:100%;
        box-shadow: 0 1px 2px rgba(11,37,48,.04);}
.card .lbl { color:#5B6770; font-size:.78rem; text-transform:uppercase; letter-spacing:.6px;}
.card .val { font-size:1.6rem; font-weight:800; color:#0B2530; line-height:1.2;}
.card .sub { color:#5B6770; font-size:.82rem;}
.zonecard { border-radius:14px; padding:16px 18px; color:#fff; margin-bottom:10px;}
.zonecard h3 { margin:0 0 4px 0; color:#fff;}
.rtl { direction: rtl; text-align:right; font-family:'Tajawal',sans-serif; font-size:1.05rem;}
.legend { background:#fff; border:1px solid #E3E8EA; border-radius:10px; padding:10px 12px; font-size:.85rem; margin-bottom:10px;}
.legend .lg-item { display:flex; align-items:center; gap:8px; margin-top:4px;}
.legend .lg-item span { width:14px; height:14px; border-radius:3px; display:inline-block;}
.legend .lg-bar { height:12px; border-radius:6px; margin-top:6px;}
.legend .lg-ticks { display:flex; justify-content:space-between; color:#5B6770; font-size:.75rem;}
.flow { display:flex; align-items:stretch; gap:6px; flex-wrap:wrap; margin:6px 0 14px 0; }
.flow .fs { flex:1 1 120px; background:#fff; border:1px solid #E3E8EA; border-top:4px solid #0F766E; border-radius:12px; padding:10px 12px; }
.flow .fs.ml { border-top-color:#D64541; background:#FFF7F6; }
.flow .fs b { display:block; font-size:.9rem; color:#0B2530; }
.flow .fs small { color:#5B6770; font-size:.8rem; line-height:1.35; display:block; margin-top:4px; }
.flow .fa { align-self:center; font-size:1.1rem; color:#0F766E; }
.badge { display:inline-block; border-radius:999px; padding:2px 10px; font-size:.75rem; font-weight:700; letter-spacing:.4px; }
.badge.on { background:#E4F6EC; color:#155C35; border:1px solid #2E9E5B; }
.badge.off { background:#F3F6F7; color:#5B6770; border:1px solid #9AA3A8; }
.caveat { background:#F3F6F7; border-left:4px solid #0F766E; border-radius:8px; padding:10px 14px; font-size:.88rem; color:#28414B;}
.footer { color:#5B6770; font-size:.8rem; text-align:center; margin-top:28px;}

/* ---------- phones ---------- */
@media (max-width: 640px) {
  .topbar h1 { font-size:1.5rem; } .topbar img { height:42px; }
  .status-card { padding:16px; gap:12px; } .status-card h2 { font-size:1.45rem; }
  .status-card .icon { flex-basis:52px; height:52px; font-size:1.6rem; }
  .prio-card .zone { font-size:1.35rem; }
  .flow .fa { display:none; }
}
</style>
"""

RTL_CSS = """
<style>
/* Arabic: right-to-left text in the farmer views (layout of maps/charts is unchanged) */
[data-testid="stMain"] .stMarkdown, [data-testid="stMain"] .stCaption, .status-card, .prio-card, .soft, .note-card, .sig,
[data-testid="stMain"] [data-testid="stExpander"] summary, .legend-big, .databadge, .topbar .sub {
  direction: rtl; text-align: right; font-family: 'Tajawal', 'Segoe UI', sans-serif; }
div.stButton > button p { font-family: 'Tajawal', 'Segoe UI', sans-serif; font-size:1.1rem; }
</style>
"""


def inject(rtl: bool) -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    if rtl:
        st.markdown(RTL_CSS, unsafe_allow_html=True)
