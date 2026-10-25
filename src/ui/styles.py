"""CSS. Identity: calm agricultural green on white. Red / amber are used ONLY for status, always with text + icon.

Selectors target Streamlit's stable data-testid attributes, keyed containers (.st-key-*) and our own classes only.
"""
from __future__ import annotations

import streamlit as st

GREEN = "#2F7D4E"        # primary
GREEN_DARK = "#1E5B38"   # headings, important elements
GREEN_LIGHT = "#EEF6F0"  # soft backgrounds
LINE = "#DDE5DF"         # borders
INK = "#1F2D27"          # text
MUTED = "#5E6E66"        # secondary text
STATUS = {"HIGH": ("#D64541", "#FDECEB", "#A12F2B"), "MODERATE": ("#E3A008", "#FFF6DD", "#7A5600"),
          "HEALTHY": ("#2E9E5B", "#EAF6EF", "#1E5B38"), "NO_DATA": ("#5B6770", "#F1F3F4", "#3F4A52"),
          "NO_CROP": ("#9AA3A8", "#F4F5F6", "#5E6E66")}

_status_css = "\n".join(
    f".kpi.{k} {{ border-top-color:{c}; }} .kpi.{k} .n {{ color:{tx}; }}\n"
    f".pill.{k} {{ background:{bg}; color:{tx}; border:1px solid {c}; }}"
    for k, (c, bg, tx) in STATUS.items()
)

BASE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
html, body, [class*="css"], button, input, textarea, select {{
  font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif; color:{INK}; }}
[data-testid="stMainBlockContainer"].block-container {{ padding-top: 3.2rem !important; max-width: 1120px; }}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:#FAFBFA; }}

/* ---------- header ---------- */
.st-key-header {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:10px 16px 4px 16px; }}
.brand {{ display:flex; align-items:center; gap:12px; }}
.brand img {{ height:42px; }}
.brand h1 {{ margin:0; padding:0; font-size:1.6rem; font-weight:700; color:{GREEN_DARK}; line-height:1.1; }}
.brand .sub {{ color:{MUTED}; font-size:.92rem; margin-top:2px; }}
.statusbar {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px 14px; margin:10px 0 2px 0; font-size:.92rem; color:{MUTED}; }}
.chip {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:3px 12px; font-weight:600; font-size:.88rem; }}
.chip.real {{ background:{GREEN_LIGHT}; color:{GREEN_DARK}; border:1px solid #BFD9C8; }}
.chip.demo {{ background:#FFF6DD; color:#6B4A00; border:1px solid #E8B21E; }}
.chip.unavailable {{ background:#FDECEB; color:#7A1F1B; border:1px solid #D64541; }}
.databadge {{ border-radius:12px; padding:10px 14px; font-weight:500; font-size:.95rem; margin:10px 0 4px 0; }}
.databadge.demo {{ background:#FFF6DD; border:1px solid #E8B21E; border-inline-start:6px solid #E8B21E; color:#5C3F00; font-weight:600; }}
.databadge.unavailable {{ background:#FDECEB; border:1px solid #D64541; border-inline-start:6px solid #D64541; color:#7A1F1B; font-weight:700; }}

/* ---------- navigation (one row of segments under the header) ---------- */
.st-key-topnav [data-testid="stButtonGroup"] button {{ min-height:42px; font-size:.95rem; }}

/* ---------- controls: large touch targets ---------- */
div.stButton > button, div.stFormSubmitButton > button {{ min-height:50px; font-size:1.02rem; font-weight:600; border-radius:12px; }}
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {{ background:{GREEN}; border-color:{GREEN}; }}
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover {{ background:{GREEN_DARK}; border-color:{GREEN_DARK}; }}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{ min-height:44px; }}
[data-testid="stCheckbox"] label p {{ font-size:1.02rem; }}
[data-testid="stExpander"] details {{ border-radius:12px; border-color:{LINE}; background:#fff; }}

/* ---------- page typography ---------- */
.q {{ font-size:1.45rem; font-weight:700; color:{INK}; margin:14px 0 10px 0; }}
.section-title {{ font-size:1.05rem; font-weight:700; color:{GREEN_DARK}; margin:22px 0 8px 0; padding-inline-start:10px;
  border-inline-start:4px solid {GREEN}; line-height:1.3; }}
.muted {{ color:{MUTED}; font-size:.94rem; }}

/* ---------- cards ---------- */
.card {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:14px 16px; }}
.card.soft {{ background:{GREEN_LIGHT}; border-color:#D3E6D9; }}
.note-card {{ background:#F4F7FB; border:1px solid #D6E1EC; border-radius:12px; padding:10px 14px; font-size:.97rem; color:#1F3A52; margin:6px 0; }}
.kpis {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin:4px 0 6px 0; }}
.kpi {{ background:#fff; border:1px solid {LINE}; border-top:5px solid; border-radius:12px; padding:12px 12px 10px 12px; }}
.kpi .n {{ font-size:2rem; font-weight:700; line-height:1.05; }}
.kpi .l {{ font-size:.92rem; color:{INK}; margin-top:4px; line-height:1.35; }}
.meta {{ color:{MUTED}; font-size:.9rem; margin-top:6px; }}
.zone-card {{ border-radius:14px; padding:14px 16px; background:#fff; border:1px solid {LINE}; border-inline-start:8px solid; }}
.zone-card .top {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px 12px; }}
.zone-card .z {{ font-size:1.35rem; font-weight:700; color:{INK}; }}
.zone-card .s {{ font-size:1.08rem; font-weight:700; margin-top:4px; }}
.zone-card .d {{ font-size:1rem; color:{INK}; margin-top:8px; }}
.pill {{ display:inline-block; border-radius:999px; padding:2px 12px; font-weight:600; font-size:.9rem; }}
{_status_css}
.cause {{ display:flex; align-items:center; gap:12px; padding:10px 12px; border:1px solid {LINE}; border-radius:12px; margin-bottom:6px; background:#fff; }}
.cause .ic {{ font-size:1.4rem; flex:0 0 32px; text-align:center; }}
.cause .nm {{ flex:1; font-size:1.02rem; font-weight:600; }}
.lvl {{ border-radius:999px; padding:3px 10px; font-size:.85rem; font-weight:600; white-space:nowrap; }}
.lvl.strong {{ background:#FDECEB; color:#A12F2B; }}
.lvl.moderate {{ background:#FFF6DD; color:#7A5600; }}
.lvl.weak {{ background:{GREEN_LIGHT}; color:{GREEN_DARK}; }}
.lvl.none {{ background:#F2F4F3; color:{MUTED}; font-weight:500; }}
.legend-big {{ display:flex; flex-wrap:wrap; gap:6px 8px; margin:4px 0 8px 0; }}
.legend-big > span {{ display:inline-flex; align-items:center; gap:6px; background:#fff; border:1px solid {LINE}; border-radius:999px; padding:3px 10px; font-size:.9rem; }}
.legend-big span.sw {{ display:inline-block; width:12px; height:12px; border-radius:3px; }}
.checklist {{ padding-inline-start:4px; list-style:none; }}
.checklist li {{ font-size:1.02rem; margin-bottom:6px; }}
.status-line {{ font-size:1.1rem; font-weight:600; margin:6px 0; }}
.footer {{ color:{MUTED}; font-size:.8rem; text-align:center; margin-top:32px; padding-top:12px; border-top:1px solid {LINE}; }}

/* ---------- phones ---------- */
@media (max-width: 720px) {{
  [data-testid="stMainBlockContainer"].block-container {{ padding-left:16px !important; padding-right:16px !important; }}
  .brand h1 {{ font-size:1.35rem; }} .brand img {{ height:34px; }}
  .kpis {{ grid-template-columns:repeat(2, minmax(0,1fr)); }}
  .kpi .n {{ font-size:1.6rem; }} .q {{ font-size:1.2rem; }}
  .zone-card .z {{ font-size:1.15rem; }}
}}
</style>
"""

RTL_CSS = """
<style>
/* Arabic: right-to-left text (maps and charts keep their own layout) */
[data-testid="stMain"] .stMarkdown, [data-testid="stMain"] .stCaption, [data-testid="stMain"] [data-testid="stExpander"] summary,
[data-testid="stMain"] [data-testid="stCheckbox"], [data-testid="stMain"] [data-testid="stRadio"], [data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stAlert"], [data-testid="stMain"] [data-testid="stForm"],
.zone-card, .card, .note-card, .cause, .legend-big, .databadge, .brand, .statusbar, .kpis {
  direction: rtl; text-align: right; }
.st-key-topnav [data-testid="stButtonGroup"] { direction: rtl; }
</style>
"""


def inject(rtl: bool) -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    if rtl:
        st.markdown(RTL_CSS, unsafe_allow_html=True)
