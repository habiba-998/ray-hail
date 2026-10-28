"""CSS for the SATRA identity (tokens in src/brand.py): deep green, satellite navy and teal on warm off-white.
Red / amber / grey are used ONLY for status, always with text + icon.

Selectors target Streamlit's stable data-testid attributes, keyed containers (.st-key-*) and our own classes only.
"""
from __future__ import annotations

import streamlit as st

from ..brand import PALETTE

P = PALETTE
GREEN = P["green"]       # primary actions
GREEN_DARK = P["navy"]   # headings, wordmark
TEAL = P["teal"]         # accents, observation
GREEN_LIGHT = "#EAF2EE"  # soft backgrounds
LINE = P["line"]         # borders
INK = P["ink"]           # text
MUTED = P["muted"]       # secondary text
# status: (accent, background, text) – always shown together with a label and an icon
STATUS = {"HIGH": (P["red"], "#FBEDEC", "#9B3434"), "MODERATE": (P["amber"], "#FCF3E2", "#7A5410"),
          "HEALTHY": (P["ok"], "#E9F4EE", "#1F5E3E"), "NO_DATA": (P["gray"], "#F0F2F3", "#4A555B"),
          "NO_CROP": ("#A9B2B6", "#F4F5F6", P["muted"])}

_status_css = "\n".join(
    f".kpi.{k} {{ border-top-color:{c}; }} .kpi.{k} .n {{ color:{tx}; }}\n"
    f".pill.{k} {{ background:{bg}; color:{tx}; border:1px solid {c}; }}"
    for k, (c, bg, tx) in STATUS.items()
)

BASE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Sans:wght@500;700&display=swap');
html, body, [class*="css"], button, input, textarea, select {{
  font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif; color:{INK}; }}
[data-testid="stMainBlockContainer"].block-container {{ padding-top: 3.2rem !important; max-width: 1120px; }}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:{P["paper"]}; }}

/* ---------- type scale (one place) ----------
   brand 2.75rem · page question 1.5rem · section 1.1rem · body 1rem · nav .95rem · labels / chips .85rem · captions .8rem */
:root {{ --fs-brand:2.75rem; --fs-brand-latin:1.1rem; --fs-q:1.5rem; --fs-h2:1.1rem; --fs-body:1rem; --fs-nav:.95rem;
  --fs-small:.85rem; --fs-xs:.78rem; --radius:12px; }}

/* ---------- header: row 1 = brand + farm picker, row 2 = data status ---------- */
.st-key-header {{ background:#fff; border:1px solid {LINE}; border-top:3px solid {TEAL}; border-radius:14px;
  padding:16px 20px 22px 20px; gap:.25rem; }}
.brand {{ display:flex; align-items:center; gap:16px; min-width:0; }}
.brand img {{ width:84px; height:84px; flex:0 0 84px; display:block; }}
.brand-text {{ min-width:0; }}
.brand-name {{ font-size:var(--fs-brand); font-weight:700; color:{GREEN}; line-height:1.05; margin:0;
  display:flex; align-items:baseline; flex-wrap:wrap; gap:4px 14px; }}
.brand-latin {{ font-family:'IBM Plex Sans', 'Segoe UI', sans-serif; font-size:var(--fs-brand-latin); font-weight:700;
  letter-spacing:.3em; color:{GREEN_DARK}; }}
.brand-sub {{ color:{MUTED}; font-size:var(--fs-body); margin-top:6px; line-height:1.4; }}
.st-key-header [data-testid="stSelectbox"] label p {{ font-size:var(--fs-xs); font-weight:600; color:{MUTED}; }}
.statusbar {{ display:flex; flex-wrap:wrap; align-items:center; gap:10px 28px; margin:14px 0 0 0; padding-top:12px;
  border-top:1px solid {LINE}; }}
.statusbar .fact {{ display:flex; flex-direction:column; gap:1px; }}
.statusbar .fact .lbl {{ font-size:var(--fs-xs); color:{MUTED}; }}
.statusbar .fact .val {{ font-size:.95rem; font-weight:600; color:{INK}; }}
.chip {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:4px 12px; font-weight:600;
  font-size:var(--fs-small); line-height:1.4; white-space:nowrap; }}
.chip.real {{ background:{GREEN_LIGHT}; color:{GREEN}; border:1px solid #BFD9C8; }}
.chip.demo {{ background:#FCF3E2; color:#7A5410; border:1px solid {P["amber"]}; }}
.chip.unavailable {{ background:#FBEDEC; color:#9B3434; border:1px solid {P["red"]}; }}
.databadge {{ border-radius:var(--radius); padding:10px 14px; font-weight:500; font-size:.95rem; margin:10px 0 4px 0; }}
.databadge.demo {{ background:#FCF3E2; border:1px solid {P["amber"]}; border-inline-start:6px solid {P["amber"]}; color:#5C3F00; font-weight:600; }}
.databadge.unavailable {{ background:#FBEDEC; border:1px solid {P["red"]}; border-inline-start:6px solid {P["red"]}; color:#7A1F1B; font-weight:700; }}

/* ---------- navigation (one row of segments under the header) ---------- */
.st-key-topnav {{ margin-top:.25rem; }}
.st-key-topnav [data-testid="stButtonGroup"] button {{ min-height:42px; font-size:var(--fs-nav); border-radius:10px; }}

/* ---------- controls: large touch targets ---------- */
div.stButton > button, div.stFormSubmitButton > button {{ min-height:50px; font-size:1.02rem; font-weight:600; border-radius:12px; }}
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {{ background:{GREEN}; border-color:{GREEN}; }}
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover {{ background:{GREEN_DARK}; border-color:{GREEN_DARK}; }}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{ min-height:44px; }}
[data-testid="stCheckbox"] label p {{ font-size:1.02rem; }}
[data-testid="stExpander"] details {{ border-radius:12px; border-color:{LINE}; background:#fff; }}

/* ---------- page typography ---------- */
.q {{ font-size:var(--fs-q); font-weight:700; color:{GREEN_DARK}; line-height:1.3; margin:18px 0 10px 0; }}
.section-title {{ font-size:var(--fs-h2); font-weight:700; color:{GREEN_DARK}; margin:22px 0 8px 0; padding-inline-start:10px;
  border-inline-start:4px solid {TEAL}; line-height:1.3; }}
.muted {{ color:{MUTED}; font-size:.94rem; }}

/* ---------- cards ---------- */
.card {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:14px 16px; }}
.card.soft {{ background:{GREEN_LIGHT}; border-color:#D3E6D9; }}
.note-card {{ background:#F4F7FB; border:1px solid #D6E1EC; border-radius:12px; padding:10px 14px; font-size:.97rem; color:#1F3A52; margin:6px 0; }}
.kpis {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin:4px 0 6px 0; }}
.kpi {{ background:#fff; border:1px solid {LINE}; border-top:5px solid; border-radius:12px; padding:12px 12px 10px 12px; }}
.kpi .n {{ font-size:2rem; font-weight:700; line-height:1.05; }}
.kpi .l {{ font-size:var(--fs-small); color:{INK}; margin-top:4px; line-height:1.35; }}
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
.ind-table {{ width:100%; border-collapse:separate; border-spacing:0; background:#fff; border:1px solid {LINE}; border-radius:12px; overflow:hidden; font-size:.95rem; }}
.ind-table th {{ background:#F4F7F5; color:{MUTED}; font-weight:600; padding:8px 10px; text-align:start; border-bottom:1px solid {LINE}; }}
.ind-table td {{ padding:8px 10px; border-bottom:1px solid #EEF2EF; }}
.ind-table tr:last-child td {{ border-bottom:0; }}
.flag {{ border-radius:999px; padding:1px 10px; font-weight:600; font-size:.85rem; white-space:nowrap; }}
.flag.yes {{ background:#FDECEB; color:#A12F2B; }} .flag.no {{ background:#EAF6EF; color:#1E5B38; }} .flag.na {{ background:#F1F3F4; color:{MUTED}; }}
.intro {{ font-size:var(--fs-body); color:{MUTED}; border-inline-start:3px solid {TEAL}; padding:2px 12px; margin:16px 0 2px 0;
  line-height:1.6; }}
.about-logo img {{ width:min(360px, 90%); display:block; margin:6px 0 12px 0; }}
.pipeline {{ display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:8px; margin:4px 0 10px 0; }}
.pipeline .step {{ background:#fff; border:1px solid {LINE}; border-top:4px solid {TEAL}; border-radius:12px; padding:10px; }}
.pipeline .step b {{ display:block; color:{GREEN_DARK}; font-size:1rem; }}
.pipeline .step small {{ display:block; color:{MUTED}; font-size:.85rem; line-height:1.4; margin-top:4px; }}
.pipeline .num {{ display:inline-block; width:22px; height:22px; border-radius:50%; background:{GREEN}; color:#fff; text-align:center;
  font-size:.8rem; line-height:22px; margin-bottom:4px; }}
.checklist {{ padding-inline-start:4px; list-style:none; }}
.checklist li {{ font-size:1.02rem; margin-bottom:6px; }}
.status-line {{ font-size:1.1rem; font-weight:600; margin:6px 0; }}
.footer {{ color:{MUTED}; font-size:.8rem; text-align:center; margin-top:32px; padding-top:12px; border-top:1px solid {LINE}; }}

/* ---------- phones ---------- */
@media (max-width: 720px) {{
  [data-testid="stMainBlockContainer"].block-container {{ padding-left:16px !important; padding-right:16px !important; }}
  .st-key-header {{ padding:14px 14px 20px 14px; }}
  .brand {{ gap:12px; }} .brand img {{ width:48px; height:48px; flex-basis:48px; }}
  :root {{ --fs-brand:1.9rem; --fs-brand-latin:.85rem; --fs-q:1.25rem; }}
  .brand-sub {{ font-size:.9rem; }}
  .statusbar {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:10px 16px; }}
  .statusbar .chip {{ grid-column:1 / -1; justify-self:start; }}
  .statusbar .fact:nth-of-type(3) {{ grid-column:1 / -1; }}  /* analysis period gets the full width */
  .kpis {{ grid-template-columns:repeat(2, minmax(0,1fr)); }}
  .pipeline {{ grid-template-columns:repeat(2, minmax(0,1fr)); }}
  .kpi .n {{ font-size:1.6rem; }}
  .zone-card .z {{ font-size:1.15rem; }}
  /* phones: one horizontally scrollable row of tabs instead of three wrapped rows */
  .st-key-topnav [data-testid="stButtonGroup"] [role="radiogroup"] {{ flex-wrap:nowrap; overflow-x:auto; scrollbar-width:none;
    -webkit-overflow-scrolling:touch; padding-bottom:2px; }}
  .st-key-topnav [data-testid="stButtonGroup"] [role="radiogroup"]::-webkit-scrollbar {{ display:none; }}
  .st-key-topnav [data-testid="stButtonGroup"] [role="radiogroup"] > button {{ flex:0 0 auto; white-space:nowrap; }}
  .ind-table {{ font-size:.86rem; }} .ind-table th, .ind-table td {{ padding:6px 6px; }}
}}
</style>
"""

RTL_CSS = """
<style>
/* Arabic: right-to-left text (maps and charts keep their own layout) */
[data-testid="stMain"] .stMarkdown, [data-testid="stMain"] .stCaption, [data-testid="stMain"] [data-testid="stExpander"] summary,
[data-testid="stMain"] [data-testid="stCheckbox"], [data-testid="stMain"] [data-testid="stRadio"], [data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stAlert"], [data-testid="stMain"] [data-testid="stForm"],
.zone-card, .card, .note-card, .cause, .legend-big, .databadge, .brand, .statusbar, .kpis, .intro, .pipeline, .brand-text {
  direction: rtl; text-align: right; }
.st-key-topnav [data-testid="stButtonGroup"], .st-key-header [data-testid="stHorizontalBlock"], .ind-table { direction: rtl; }
</style>
"""


def inject(rtl: bool) -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    if rtl:
        st.markdown(RTL_CSS, unsafe_allow_html=True)
