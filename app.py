"""
app.py - Streamlit frontend for Lab Report Intelligence Agent.

Multi-page SaaS-style app with top navigation bar, dark/light theme toggle,
Home / Analyze / About pages routed via session state.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import re as _re

import streamlit as st
import plotly.graph_objects as go

from ai_summary import generate_health_guidance, generate_summary
from analyzer import AnalysisReport, AnalyzedTest, Severity, Status, analyze
from parser import EmptyPDFError, PDFExtractionError, extract_text_from_pdf, parse_lab_values

# ──────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Lab Report Intelligence Agent",
    page_icon="🧬",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────
# Session-state defaults
# ──────────────────────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True


def _nav_to(page: str) -> None:
    st.session_state.page = page


# ──────────────────────────────────────────────────────────────────────
# Theme variables
# ──────────────────────────────────────────────────────────────────────

def _theme():
    """Return a dict of CSS variables for the active theme."""
    if st.session_state.dark_mode:
        return dict(
            bg="linear-gradient(170deg, #0f172a 0%, #1e1b4b 40%, #0f172a 100%)",
            text="#e2e8f0", text_muted="#94a3b8", text_dim="#64748b",
            card_bg="rgba(255,255,255,0.05)", card_border="rgba(255,255,255,0.08)",
            card_hover_shadow="rgba(0,0,0,0.25)",
            navbar_bg="rgba(15,23,42,0.85)", navbar_border="rgba(255,255,255,0.06)",
            accent="#818cf8", accent2="#38bdf8", accent_glow="rgba(129,140,248,0.15)",
            heading_fill="linear-gradient(135deg,#818cf8,#a78bfa,#38bdf8,#22d3ee)",
            score_track="rgba(255,255,255,0.06)", score_num="#fff",
            table_even="rgba(255,255,255,0.015)", table_hover="rgba(129,140,248,0.06)",
            table_border="rgba(255,255,255,0.04)", table_th_bg="rgba(255,255,255,0.02)",
            banner_good_bg="rgba(34,197,94,0.12)", banner_good_c="#4ade80", banner_good_b="rgba(34,197,94,0.25)",
            banner_mod_bg="rgba(245,158,11,0.12)", banner_mod_c="#fbbf24", banner_mod_b="rgba(245,158,11,0.25)",
            banner_risk_bg="rgba(239,68,68,0.12)", banner_risk_c="#f87171", banner_risk_b="rgba(239,68,68,0.25)",
            disc_bg="rgba(245,158,11,0.08)", disc_border="rgba(245,158,11,0.15)", disc_c="#fcd34d",
            summary_heading="#c4b5fd",
            upload_dash="rgba(129,140,248,0.3)", upload_dash_hover="rgba(129,140,248,0.7)",
            footer_c="#475569",
        )
    return dict(
        bg="linear-gradient(170deg, #f8fafc 0%, #eef2ff 40%, #f8fafc 100%)",
        text="#1e293b", text_muted="#64748b", text_dim="#94a3b8",
        card_bg="rgba(255,255,255,0.75)", card_border="rgba(0,0,0,0.08)",
        card_hover_shadow="rgba(0,0,0,0.1)",
        navbar_bg="rgba(255,255,255,0.88)", navbar_border="rgba(0,0,0,0.08)",
        accent="#6366f1", accent2="#0ea5e9", accent_glow="rgba(99,102,241,0.12)",
        heading_fill="linear-gradient(135deg,#6366f1,#8b5cf6,#0ea5e9,#06b6d4)",
        score_track="rgba(0,0,0,0.06)", score_num="#1e293b",
        table_even="rgba(0,0,0,0.02)", table_hover="rgba(99,102,241,0.06)",
        table_border="rgba(0,0,0,0.06)", table_th_bg="rgba(0,0,0,0.03)",
        banner_good_bg="rgba(34,197,94,0.1)", banner_good_c="#16a34a", banner_good_b="rgba(34,197,94,0.2)",
        banner_mod_bg="rgba(245,158,11,0.1)", banner_mod_c="#d97706", banner_mod_b="rgba(245,158,11,0.2)",
        banner_risk_bg="rgba(239,68,68,0.1)", banner_risk_c="#dc2626", banner_risk_b="rgba(239,68,68,0.2)",
        disc_bg="rgba(245,158,11,0.06)", disc_border="rgba(245,158,11,0.12)", disc_c="#92400e",
        summary_heading="#6366f1",
        upload_dash="rgba(99,102,241,0.25)", upload_dash_hover="rgba(99,102,241,0.6)",
        footer_c="#94a3b8",
    )


# ──────────────────────────────────────────────────────────────────────
# CSS (theme-aware)
# ──────────────────────────────────────────────────────────────────────

def _build_css() -> str:
    t = _theme()
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ===== GLOBAL ===== */
html {{ scroll-behavior: smooth; }}
html, body, [class*="st-"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}}
.block-container {{ padding-top: 4.5rem; padding-bottom: 3rem; max-width: 1150px; }}
.stApp {{ background: {t['bg']}; }}
.stApp, .stApp p, .stApp li, .stApp span {{ color: {t['text']}; }}

/* ===== HIDE SIDEBAR ===== */
[data-testid="stSidebar"],[data-testid="collapsedControl"],button[kind="header"] {{ display:none !important; }}

/* ===== NAVBAR ===== */

/* ===== HERO (Home) ===== */
.hero {{ text-align:center; padding:5rem 1rem 2rem; }}
.hero h1 {{
    font-size:3.4rem; font-weight:900; letter-spacing:-1.5px; line-height:1.12;
    background:{t['heading_fill']};
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:0.8rem;
}}
.hero .tagline {{ color:{t['text_muted']}; font-size:1.25rem; font-weight:400; margin:0 auto 1.2rem; max-width:620px; }}
.hero .desc {{ color:{t['text_dim']}; font-size:1rem; max-width:560px; margin:0 auto 2.2rem; line-height:1.7; }}
.hero-divider {{
    width:120px; height:3px; margin:0 auto 2rem; border-radius:3px;
    background:linear-gradient(90deg,transparent,{t['accent']},{t['accent2']},transparent);
    box-shadow: 0 0 8px {t['accent']}50, 0 0 20px {t['accent']}25, 0 0 40px {t['accent2']}15;
    animation:pulse-line 3s ease-in-out infinite;
}}
@keyframes pulse-line {{ 0%,100%{{opacity:.6;width:90px;box-shadow:0 0 6px {t['accent']}35}} 50%{{opacity:1;width:140px;box-shadow:0 0 14px {t['accent']}60,0 0 30px {t['accent2']}25}} }}
.cta-btn {{
    display:inline-block; padding:0.85rem 2.6rem; border-radius:14px; font-weight:700; font-size:1rem;
    color:#fff; background:linear-gradient(135deg,{t['accent']},{t['accent2']}); text-decoration:none;
    box-shadow:0 4px 20px {t['accent_glow']}; transition:all 0.35s cubic-bezier(.22,1,.36,1);
    border:none; cursor:pointer;
}}
.cta-btn:hover {{
    transform:translateY(-3px) scale(1.04);
    box-shadow: 0 12px 40px {t['accent_glow']}, 0 0 20px {t['accent']}40, 0 0 40px {t['accent2']}25;
}}

/* ===== FEATURE CARDS (Home) ===== */
.feat-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1.4rem; margin-top:2.5rem; }}
.feat-card {{
    background:{t['card_bg']}; border:1px solid {t['card_border']}; border-radius:18px;
    padding:1.8rem 1.5rem; text-align:center;
    transition:all 0.4s cubic-bezier(.22,1,.36,1);
    backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
}}
.feat-card:hover {{
    transform:translateY(-4px);
    box-shadow: 0 10px 30px {t['card_hover_shadow']}, 0 0 15px {t['accent']}18, 0 0 30px {t['accent2']}10;
    border-color: {t['accent']}30;
}}
.feat-card .f-icon {{ font-size:2.2rem; margin-bottom:0.6rem; }}
.feat-card .f-title {{ font-weight:700; font-size:1rem; margin-bottom:0.3rem; color:{t['text']}; }}
.feat-card .f-desc {{ font-size:0.85rem; color:{t['text_muted']}; line-height:1.55; }}

/* ===== STATUS BANNER ===== */
.status-banner {{
    max-width:700px; margin:1.2rem auto; padding:0.75rem 1.4rem; border-radius:14px;
    text-align:center; font-weight:600; font-size:0.95rem;
    backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); border:1px solid {t['card_border']};
}}
.banner-good {{ background:{t['banner_good_bg']}; color:{t['banner_good_c']}; border-color:{t['banner_good_b']}; }}
.banner-moderate {{ background:{t['banner_mod_bg']}; color:{t['banner_mod_c']}; border-color:{t['banner_mod_b']}; }}
.banner-risk {{ background:{t['banner_risk_bg']}; color:{t['banner_risk_c']}; border-color:{t['banner_risk_b']}; }}

/* ===== UPLOAD AREA ===== */
.upload-zone {{
    max-width:620px; margin:0 auto; background:{t['card_bg']};
    border:2px dashed {t['upload_dash']}; border-radius:20px; padding:2.5rem 2rem;
    text-align:center; transition:all 0.3s ease; backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
}}
.upload-zone:hover {{ border-color:{t['upload_dash_hover']}; box-shadow:0 0 30px {t['accent_glow']}, 0 0 20px {t['accent']}20, 0 0 40px {t['accent2']}12; }}
.upload-zone .upload-icon {{ font-size:3.2rem; margin-bottom:0.5rem; }}
.upload-zone p {{ color:{t['text_muted']}; font-size:1rem; margin:0.3rem 0 0; }}

/* ===== GLASS / METRIC / SCORE ===== */
.glass-card {{
    background:{t['card_bg']}; backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
    border:1px solid {t['card_border']}; border-radius:20px; padding:1.6rem 1.8rem;
    box-shadow:0 8px 32px {t['card_hover_shadow']}; transition:transform 0.2s,box-shadow 0.2s;
}}
.glass-card:hover {{ transform:translateY(-3px); box-shadow:0 12px 40px {t['card_hover_shadow']}; }}
.score-wrap {{ display:flex; flex-direction:column; align-items:center; gap:0.4rem; }}
.score-circle {{ position:relative; width:150px; height:150px; }}
.score-circle svg {{ transform:rotate(-90deg); width:150px; height:150px; }}
.score-circle .track {{ fill:none; stroke:{t['score_track']}; stroke-width:10; }}
.score-circle .fill {{
    fill:none; stroke-width:10; stroke-linecap:round;
    transition:stroke-dashoffset 1.5s cubic-bezier(.4,0,.2,1);
    filter: drop-shadow(0 0 8px {t['accent']}65) drop-shadow(0 0 16px {t['accent2']}35) drop-shadow(0 0 28px {t['accent']}15);
    animation: ringGlow 3s ease-in-out infinite;
}}
@keyframes ringGlow {{
    0%,100% {{ filter: drop-shadow(0 0 6px {t['accent']}55) drop-shadow(0 0 12px {t['accent2']}25); }}
    50%     {{ filter: drop-shadow(0 0 10px {t['accent']}75) drop-shadow(0 0 20px {t['accent2']}40) drop-shadow(0 0 36px {t['accent']}18); }}
}}
.score-number {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:2.6rem; font-weight:900; color:{t['score_num']}; }}
.score-tag {{ font-size:0.82rem; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; color:{t['text_muted']}; }}
.m-card {{
    background:{t['card_bg']}; backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
    border:1px solid {t['card_border']}; border-radius:18px; padding:1.6rem 1rem; text-align:center;
    transition:all 0.4s cubic-bezier(.22,1,.36,1);
}}
.m-card:hover {{
    transform:translateY(-6px) scale(1.04);
    box-shadow: 0 15px 45px {t['card_hover_shadow']}, 0 0 12px {t['accent']}20, 0 0 25px {t['accent2']}12;
    border-color: {t['accent']}25;
}}
.m-card .m-icon {{ font-size:1.8rem; margin-bottom:0.3rem; }}
.m-card .m-val {{ font-size:2.4rem; font-weight:900; margin:0.2rem 0; line-height:1; }}
.m-card .m-lbl {{ font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:{t['text_muted']}; }}

/* ===== TABLE ===== */
.tbl-wrap {{
    overflow-x:auto; border-radius:16px; border:1px solid {t['card_border']};
    background:{t['card_bg']}; backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
}}
.tbl-wrap table {{ width:100%; border-collapse:collapse; }}
.tbl-wrap th {{
    text-align:left; padding:0.9rem 1.1rem; font-weight:700; font-size:0.78rem;
    color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.8px;
    border-bottom:1px solid {t['table_border']}; background:{t['table_th_bg']};
}}
.tbl-wrap td {{ text-align:left; padding:0.8rem 1.1rem; font-size:0.95rem; color:{t['text']}; border-bottom:1px solid {t['table_border']}; }}
.tbl-wrap tr:nth-child(even) td {{ background:{t['table_even']}; }}
.tbl-wrap tr:hover td {{ background:{t['table_hover']}; }}
.tbl-wrap tr:last-child td {{ border-bottom:none; }}

/* ===== BADGES ===== */
.badge {{ display:inline-block; padding:0.3rem 0.85rem; border-radius:9999px; font-size:0.72rem; font-weight:800; color:#fff; letter-spacing:0.6px; text-transform:uppercase; }}
.badge-normal {{ background:linear-gradient(135deg,#22c55e,#16a34a); box-shadow:0 2px 8px rgba(34,197,94,0.3); }}
/* High severity tiers */
.badge-high-mild     {{ background:linear-gradient(135deg,#f87171,#ef4444); box-shadow:0 2px 8px rgba(248,113,113,0.3); }}
.badge-high-moderate {{ background:linear-gradient(135deg,#ef4444,#dc2626); box-shadow:0 2px 8px rgba(239,68,68,0.4); }}
.badge-high-critical {{ background:linear-gradient(135deg,#dc2626,#991b1b); box-shadow:0 2px 10px rgba(220,38,38,0.5); }}
/* Low severity tiers */
.badge-low-mild     {{ background:linear-gradient(135deg,#fbbf24,#f59e0b); box-shadow:0 2px 8px rgba(251,191,36,0.3); }}
.badge-low-moderate {{ background:linear-gradient(135deg,#f59e0b,#d97706); box-shadow:0 2px 8px rgba(245,158,11,0.4); }}
.badge-low-critical {{ background:linear-gradient(135deg,#d97706,#92400e); box-shadow:0 2px 10px rgba(217,119,6,0.5); }}
/* Severity label next to badge */
.sev-label {{ font-size:0.68rem; font-weight:600; opacity:0.8; margin-left:0.15rem; }}

/* ===== TABLE ROW SEVERITY TINTS ===== */
.row-high-mild td     {{ background:rgba(248,113,113,0.05) !important; }}
.row-high-moderate td {{ background:rgba(239,68,68,0.09) !important; }}
.row-high-critical td {{ background:rgba(220,38,38,0.14) !important; }}
.row-low-mild td      {{ background:rgba(251,191,36,0.05) !important; }}
.row-low-moderate td  {{ background:rgba(245,158,11,0.09) !important; }}
.row-low-critical td  {{ background:rgba(217,119,6,0.14) !important; }}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {{ gap:0.4rem; background:{t['card_bg']}; border-radius:14px; padding:0.35rem; border:1px solid {t['card_border']}; }}
.stTabs [data-baseweb="tab"] {{ border-radius:10px; padding:0.6rem 1.3rem; font-weight:600; font-size:0.88rem; color:{t['text_muted']}; transition:all 0.2s; }}
.stTabs [data-baseweb="tab"]:hover {{ color:{t['text']}; background:{t['accent_glow']}; }}
.stTabs [aria-selected="true"] {{ background:{t['accent_glow']} !important; color:{t['accent']} !important; box-shadow:0 0 12px {t['accent_glow']}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:transparent !important; }}

/* ===== GUIDANCE / SUMMARY CARDS ===== */
.guidance-card, .summary-card {{
    background:{t['card_bg']}; backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
    border:1px solid {t['card_border']}; border-radius:18px; padding:1.8rem 2rem; line-height:1.75;
}}
.guidance-card h2, .summary-card h2, .summary-card h3 {{ color:{t['summary_heading']}; }}
.guidance-card h2 {{ font-size:1.25rem; font-weight:700; margin-top:1.8rem; margin-bottom:0.6rem; padding-bottom:0.4rem; border-bottom:1px solid {t['card_border']}; }}
.guidance-card h2:first-child {{ margin-top:0; }}
.guidance-card ul {{ padding-left:1.2rem; }} .guidance-card li {{ margin-bottom:0.3rem; }}
.guidance-card strong, .summary-card strong {{ color:{t['text']}; }}

/* ===== FOOTER ===== */
.footer-divider {{
    height:1px; margin:2.5rem 0 1.5rem;
    background:linear-gradient(90deg, transparent, {t['accent']}40, {t['accent2']}40, transparent);
    box-shadow: 0 0 6px {t['accent']}15, 0 0 12px {t['accent2']}08;
}}
.disclaimer-box {{
    background:{t['disc_bg']}; border:1px solid {t['disc_border']}; border-left:4px solid #f59e0b;
    border-radius:12px; padding:1rem 1.4rem; font-size:0.88rem; color:{t['disc_c']}; line-height:1.7;
}}
.footer-text {{ text-align:center; color:{t['footer_c']}; font-size:0.78rem; margin-top:1rem; letter-spacing:0.3px; }}

/* ===== ABOUT PAGE ===== */
.about-section {{ max-width:820px; margin:0 auto; }}
.about-section h2 {{ font-size:1.8rem; font-weight:800; background:{t['heading_fill']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.5rem; }}
.about-section h3 {{ font-size:1.15rem; font-weight:700; color:{t['accent']}; margin-top:2rem; margin-bottom:0.6rem; }}
.about-section p, .about-section li {{ color:{t['text_muted']}; line-height:1.7; }}
.tech-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1rem; margin-top:1rem; }}
.tech-chip {{
    background:{t['card_bg']}; border:1px solid {t['card_border']}; border-radius:14px;
    padding:1.1rem 1rem; text-align:center; font-weight:600; font-size:0.92rem; color:{t['text']};
    transition:all 0.35s cubic-bezier(.22,1,.36,1); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
}}
.tech-chip:hover {{ transform:translateY(-3px); box-shadow:0 8px 24px {t['card_hover_shadow']}, 0 0 10px {t['accent']}15; border-color:{t['accent']}25; }}
.tech-chip .t-icon {{ font-size:1.6rem; margin-bottom:0.35rem; }}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {{ background:{t['card_bg']}; border-radius:14px; padding:0.5rem; border:1px solid {t['card_border']}; }}
[data-testid="stFileUploader"] label {{ color:{t['text_muted']} !important; font-weight:600; }}
[data-testid="stFileUploadDropzone"],[data-testid="stFileUploader"] section {{
    min-height:120px !important; position:relative; z-index:10; pointer-events:auto !important;
    border:2px dashed {t['upload_dash']} !important; border-radius:14px !important;
    background:{t['accent_glow']} !important; transition:border-color 0.25s,background 0.25s;
}}
[data-testid="stFileUploadDropzone"]:hover,[data-testid="stFileUploader"] section:hover {{
    border-color:{t['upload_dash_hover']} !important;
}}
[data-testid="stFileUploadDropzone"] *,[data-testid="stFileUploader"] section * {{ pointer-events:auto !important; }}
[data-testid="stFileUploadDropzone"] input[type="file"],[data-testid="stFileUploader"] input[type="file"] {{
    position:absolute !important; top:0 !important; left:0 !important;
    width:100% !important; height:100% !important; opacity:0 !important; cursor:pointer !important; z-index:20 !important;
}}
[data-testid="stExpander"] {{ background:{t['card_bg']}; border:1px solid {t['card_border']}; border-radius:14px; }}

/* ===== ENTRANCE ANIMATIONS (enhanced) ===== */
@keyframes fadeInUp {{
    0%   {{ opacity:0; transform:translateY(32px) scale(0.97); filter:blur(4px); }}
    60%  {{ opacity:0.85; transform:translateY(-3px) scale(1.005); filter:blur(0); }}
    100% {{ opacity:1; transform:translateY(0) scale(1); filter:blur(0); }}
}}
@keyframes fadeInDown {{
    0%   {{ opacity:0; transform:translateY(-24px) scale(0.97); filter:blur(3px); }}
    60%  {{ opacity:0.9; transform:translateY(2px) scale(1.003); filter:blur(0); }}
    100% {{ opacity:1; transform:translateY(0) scale(1); filter:blur(0); }}
}}
@keyframes fadeIn {{
    0%   {{ opacity:0; filter:blur(2px); }}
    100% {{ opacity:1; filter:blur(0); }}
}}
@keyframes scaleIn {{
    0%   {{ opacity:0; transform:scale(0.7) rotate(-2deg); }}
    60%  {{ opacity:1; transform:scale(1.04) rotate(0.5deg); }}
    100% {{ opacity:1; transform:scale(1) rotate(0); }}
}}
@keyframes slideInLeft {{
    0%   {{ opacity:0; transform:translateX(-36px) skewX(2deg); }}
    60%  {{ opacity:0.9; transform:translateX(3px) skewX(-0.5deg); }}
    100% {{ opacity:1; transform:translateX(0) skewX(0); }}
}}
@keyframes slideInRight {{
    0%   {{ opacity:0; transform:translateX(36px) skewX(-2deg); }}
    60%  {{ opacity:0.9; transform:translateX(-3px) skewX(0.5deg); }}
    100% {{ opacity:1; transform:translateX(0) skewX(0); }}
}}
@keyframes popIn {{
    0%   {{ opacity:0; transform:scale(0.5) rotate(-3deg); }}
    50%  {{ opacity:1; transform:scale(1.08) rotate(1deg); }}
    70%  {{ transform:scale(0.97) rotate(-0.5deg); }}
    100% {{ opacity:1; transform:scale(1) rotate(0); }}
}}
@keyframes bounceIn {{
    0%   {{ opacity:0; transform:scale(0.3); }}
    40%  {{ opacity:1; transform:scale(1.12); }}
    60%  {{ transform:scale(0.94); }}
    80%  {{ transform:scale(1.03); }}
    100% {{ transform:scale(1); }}
}}
@keyframes elasticIn {{
    0%   {{ opacity:0; transform:scale(0) rotateZ(-12deg); }}
    55%  {{ opacity:1; transform:scale(1.08) rotateZ(3deg); }}
    70%  {{ transform:scale(0.96) rotateZ(-1.5deg); }}
    85%  {{ transform:scale(1.02) rotateZ(0.5deg); }}
    100% {{ transform:scale(1) rotateZ(0); }}
}}
@keyframes slideReveal {{
    0%   {{ opacity:0; clip-path:inset(0 100% 0 0); transform:translateX(-12px); }}
    100% {{ opacity:1; clip-path:inset(0 0 0 0); transform:translateX(0); }}
}}
@keyframes flipIn {{
    0%   {{ opacity:0; transform:perspective(600px) rotateY(-60deg) scale(0.85); }}
    60%  {{ opacity:1; transform:perspective(600px) rotateY(8deg) scale(1.02); }}
    100% {{ opacity:1; transform:perspective(600px) rotateY(0) scale(1); }}
}}
@keyframes shimmer {{
    0%   {{ background-position:-200% 0; }}
    100% {{ background-position:200% 0; }}
}}
@keyframes float {{
    0%,100% {{ transform:translateY(0) rotate(0); }}
    25%     {{ transform:translateY(-5px) rotate(1deg); }}
    75%     {{ transform:translateY(-3px) rotate(-0.5deg); }}
    50%     {{ transform:translateY(-8px) rotate(-1deg); }}
}}
@keyframes pulse {{
    0%,100% {{ transform:scale(1); opacity:1; }}
    50%     {{ transform:scale(1.06); opacity:0.85; }}
}}
@keyframes glowPulse {{
    0%,100% {{ box-shadow:0 0 8px rgba(129,140,248,0.15); }}
    50%     {{ box-shadow:0 0 24px rgba(129,140,248,0.35), 0 0 48px rgba(56,189,248,0.12); }}
}}
@keyframes borderGlow {{
    0%,100% {{ border-color:{t['card_border']}; }}
    50%     {{ border-color:{t['accent']}60; }}
}}
@keyframes gentleSway {{
    0%,100% {{ transform:rotate(0); }}
    25%     {{ transform:rotate(1.5deg); }}
    75%     {{ transform:rotate(-1.5deg); }}
}}
@keyframes typewriter {{
    from {{ width:0; }}
    to   {{ width:100%; }}
}}
@keyframes drawLine {{
    from {{ stroke-dashoffset:377; }}
    to   {{ stroke-dashoffset:0; }}
}}

/* —————— NAVBAR —————— */
.navbar-row [data-testid="stHorizontalBlock"] {{
    animation: fadeInDown 0.6s cubic-bezier(.22,1,.36,1) both;
}}
.nav-brand-cell {{
    animation: slideInLeft 0.7s cubic-bezier(.22,1,.36,1) both;
}}

/* —————— HERO —————— */
.hero {{
    animation: fadeInUp 0.8s cubic-bezier(.22,1,.36,1) both;
}}
.hero h1 {{
    animation: fadeInUp 0.9s cubic-bezier(.22,1,.36,1) 0.08s both;
}}
.hero .tagline {{
    animation: fadeInUp 0.85s cubic-bezier(.22,1,.36,1) 0.2s both;
}}
.hero .desc {{
    animation: fadeInUp 0.85s cubic-bezier(.22,1,.36,1) 0.32s both;
}}
.hero-divider {{
    animation: scaleIn 0.7s cubic-bezier(.22,1,.36,1) 0.42s both;
}}

/* —————— CTA —————— */
.cta-btn {{
    animation: bounceIn 0.8s cubic-bezier(.22,1,.36,1) 0.5s both;
}}
.cta-btn:hover {{
    animation: pulse 1.2s ease-in-out infinite;
}}

/* —————— FEATURE CARDS (staggered flip) —————— */
.feat-grid {{
    animation: fadeIn 0.5s ease both;
}}
.feat-card:nth-child(1) {{ animation: flipIn 0.7s cubic-bezier(.22,1,.36,1) 0.1s both; }}
.feat-card:nth-child(2) {{ animation: flipIn 0.7s cubic-bezier(.22,1,.36,1) 0.22s both; }}
.feat-card:nth-child(3) {{ animation: flipIn 0.7s cubic-bezier(.22,1,.36,1) 0.34s both; }}
.feat-card:nth-child(4) {{ animation: flipIn 0.7s cubic-bezier(.22,1,.36,1) 0.46s both; }}
.feat-card {{ transition: transform 0.35s cubic-bezier(.22,1,.36,1), box-shadow 0.35s ease; }}
.feat-card:hover {{ transform: translateY(-6px) scale(1.03); }}

/* —————— UPLOAD —————— */
.upload-zone {{
    animation: scaleIn 0.7s cubic-bezier(.22,1,.36,1) 0.15s both;
}}
.upload-zone:hover {{
    animation: glowPulse 2s ease-in-out infinite;
}}
[data-testid="stFileUploader"] {{
    animation: fadeInUp 0.6s cubic-bezier(.22,1,.36,1) 0.1s both;
}}

/* —————— STATUS BANNER —————— */
.status-banner {{
    animation: slideReveal 0.7s cubic-bezier(.22,1,.36,1) 0.1s both;
}}
.banner-good  {{ animation: slideReveal 0.7s cubic-bezier(.22,1,.36,1) 0.1s both, borderGlow 3s ease-in-out 1.5s infinite; }}
.banner-moderate {{ animation: slideReveal 0.7s cubic-bezier(.22,1,.36,1) 0.1s both; }}
.banner-risk   {{ animation: slideReveal 0.7s cubic-bezier(.22,1,.36,1) 0.1s both, pulse 2s ease 2s infinite; }}

/* —————— SCORE RING —————— */
.score-wrap {{
    animation: bounceIn 0.9s cubic-bezier(.22,1,.36,1) 0.15s both;
}}
.score-circle svg .fill {{
    animation: drawLine 1.8s cubic-bezier(.22,1,.36,1) 0.4s both;
}}
.score-number {{
    animation: popIn 0.6s cubic-bezier(.22,1,.36,1) 1.2s both;
}}
.score-tag {{
    animation: fadeIn 0.5s ease 1.4s both;
}}

/* —————— METRIC CARDS (elastic stagger) —————— */
.m-card {{
    animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) both;
}}
.section-title + div [data-testid="stHorizontalBlock"] > div:nth-child(1) .m-card {{ animation-delay: 0.15s; }}
.section-title + div [data-testid="stHorizontalBlock"] > div:nth-child(2) .m-card {{ animation-delay: 0.28s; }}
.section-title + div [data-testid="stHorizontalBlock"] > div:nth-child(3) .m-card {{ animation-delay: 0.41s; }}
.section-title + div [data-testid="stHorizontalBlock"] > div:nth-child(4) .m-card {{ animation-delay: 0.54s; }}
.m-card:hover {{
    animation: glowPulse 2s ease-in-out infinite;
}}

/* —————— RESULTS TABLE (row cascade) —————— */
.tbl-wrap {{
    animation: fadeInUp 0.7s cubic-bezier(.22,1,.36,1) 0.1s both;
}}
.tbl-wrap tr {{
    animation: fadeInUp 0.4s cubic-bezier(.22,1,.36,1) both;
}}
.tbl-wrap tbody tr:nth-child(1)  {{ animation-delay: 0.12s; }}
.tbl-wrap tbody tr:nth-child(2)  {{ animation-delay: 0.16s; }}
.tbl-wrap tbody tr:nth-child(3)  {{ animation-delay: 0.20s; }}
.tbl-wrap tbody tr:nth-child(4)  {{ animation-delay: 0.24s; }}
.tbl-wrap tbody tr:nth-child(5)  {{ animation-delay: 0.28s; }}
.tbl-wrap tbody tr:nth-child(6)  {{ animation-delay: 0.32s; }}
.tbl-wrap tbody tr:nth-child(7)  {{ animation-delay: 0.36s; }}
.tbl-wrap tbody tr:nth-child(8)  {{ animation-delay: 0.40s; }}
.tbl-wrap tbody tr:nth-child(9)  {{ animation-delay: 0.44s; }}
.tbl-wrap tbody tr:nth-child(10) {{ animation-delay: 0.48s; }}
.tbl-wrap tbody tr:nth-child(n+11) {{ animation-delay: 0.52s; }}

/* —————— GLASS CARDS —————— */
.glass-card {{
    animation: fadeInUp 0.65s cubic-bezier(.22,1,.36,1) 0.1s both;
}}

/* —————— SUMMARY & GUIDANCE —————— */
.summary-card {{
    animation: flipIn 0.7s cubic-bezier(.22,1,.36,1) 0.1s both;
}}
.guidance-card {{
    animation: flipIn 0.7s cubic-bezier(.22,1,.36,1) 0.1s both;
}}

/* —————— TABS —————— */
.stTabs {{
    animation: fadeIn 0.5s cubic-bezier(.22,1,.36,1) 0.15s both;
}}
.stTabs [data-baseweb="tab"] {{
    transition: all 0.3s cubic-bezier(.22,1,.36,1);
}}
.stTabs [data-baseweb="tab"]:hover {{
    transform: translateY(-1px);
}}

/* —————— ABOUT PAGE —————— */
.about-section {{
    animation: fadeInUp 0.8s cubic-bezier(.22,1,.36,1) 0.1s both;
}}
.about-section h2 {{
    animation: slideReveal 0.8s cubic-bezier(.22,1,.36,1) 0.15s both;
}}
.about-section h3 {{
    animation: slideInLeft 0.6s cubic-bezier(.22,1,.36,1) 0.1s both;
}}

/* —————— TECH CHIPS (staggered bounce) —————— */
.tech-grid {{
    animation: fadeIn 0.4s ease both;
}}
.tech-chip:nth-child(1) {{ animation: bounceIn 0.5s cubic-bezier(.22,1,.36,1) 0.08s both; }}
.tech-chip:nth-child(2) {{ animation: bounceIn 0.5s cubic-bezier(.22,1,.36,1) 0.16s both; }}
.tech-chip:nth-child(3) {{ animation: bounceIn 0.5s cubic-bezier(.22,1,.36,1) 0.24s both; }}
.tech-chip:nth-child(4) {{ animation: bounceIn 0.5s cubic-bezier(.22,1,.36,1) 0.32s both; }}
.tech-chip:nth-child(5) {{ animation: bounceIn 0.5s cubic-bezier(.22,1,.36,1) 0.40s both; }}

/* —————— DISCLAIMER / FOOTER —————— */
.disclaimer-box {{
    animation: fadeInUp 0.5s ease 0.3s both;
}}
.footer-text {{
    animation: fadeIn 0.6s ease 0.45s both;
}}

/* —————— FLOATING ICONS (staggered perpetual) —————— */
.feat-card .f-icon {{ animation: float 3.5s ease-in-out infinite; }}
.feat-card:nth-child(2) .f-icon {{ animation-delay: 0.5s; }}
.feat-card:nth-child(3) .f-icon {{ animation-delay: 1s; }}
.feat-card:nth-child(4) .f-icon {{ animation-delay: 1.5s; }}
.m-card .m-icon {{ animation: float 3s ease-in-out infinite; }}
.tech-chip .t-icon {{ animation: gentleSway 4s ease-in-out infinite; }}
.tech-chip:nth-child(2) .t-icon {{ animation-delay: 0.6s; }}
.tech-chip:nth-child(3) .t-icon {{ animation-delay: 1.2s; }}

/* —————— SECTION TITLE —————— */
.section-title {{
    animation: slideReveal 0.6s cubic-bezier(.22,1,.36,1) both;
}}

/* —————— BADGES (perpetual subtle pulse) —————— */
.badge {{
    transition: transform 0.2s ease;
}}
.badge:hover {{ transform: scale(1.12); }}
.badge-high-critical {{ animation: pulse 2.5s ease-in-out 2s infinite; }}

/* ===== RISK CARDS GRID ===== */
.risk-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1rem; margin-top: 1rem;
}}
.risk-card {{
    background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 16px;
    padding: 1.2rem; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    transition: all 0.4s cubic-bezier(.22,1,.36,1);
}}
.risk-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 12px 36px {t['card_hover_shadow']}, 0 0 12px {t['accent']}15;
    border-color: {t['accent']}25;
}}
.risk-card .rc-header {{
    display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem;
}}
.risk-card .rc-icon {{
    font-size: 1.5rem;
}}
.risk-card .rc-title {{
    font-size: 0.95rem; font-weight: 700; color: {t['text']};
}}
.risk-card .rc-tests {{
    font-size: 0.78rem; color: {t['text_muted']}; line-height: 1.5; margin-top: 0.4rem;
}}
.risk-badge {{
    display: inline-block; padding: 0.15rem 0.55rem; border-radius: 8px;
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
}}
.risk-low {{
    background: rgba(34,197,94,0.12); color: #4ade80;
}}
.risk-moderate {{
    background: rgba(245,158,11,0.12); color: #fbbf24;
}}
.risk-high {{
    background: rgba(239,68,68,0.12); color: #f87171;
}}
.risk-normal {{
    background: rgba(148,163,184,0.12); color: {t['text_muted']};
}}
/* Risk card animations (elastic cascade) */
.risk-card:nth-child(1)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.05s both; }}
.risk-card:nth-child(2)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.14s both; }}
.risk-card:nth-child(3)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.23s both; }}
.risk-card:nth-child(4)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.32s both; }}
.risk-card:nth-child(5)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.41s both; }}
.risk-card:nth-child(6)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.50s both; }}
.risk-card:nth-child(7)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.59s both; }}
.risk-card:nth-child(8)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.68s both; }}
.risk-card:nth-child(9)  {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.77s both; }}
.risk-card:nth-child(10) {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.86s both; }}
.risk-card .rc-icon {{ animation: float 3s ease-in-out 1s infinite; }}
.risk-badge {{ animation: popIn 0.5s ease 0.6s both; }}
.risk-card:hover {{ animation: glowPulse 2s ease-in-out infinite; }}

/* ===== VISUAL INSIGHTS ===== */
.insight-title {{
    font-size: 1.15rem; font-weight: 700; color: {t['text']};
    margin-bottom: 0.3rem;
    animation: slideReveal 0.6s cubic-bezier(.22,1,.36,1) 0.1s both;
}}
.insight-subtitle {{
    font-size: 0.78rem; color: {t['text_muted']}; margin-bottom: 0.6rem;
    animation: fadeIn 0.5s ease 0.25s both;
}}
/* Plotly chart containers */
[data-testid="stPlotlyChart"] {{
    animation: scaleIn 0.8s cubic-bezier(.22,1,.36,1) 0.2s both;
    border-radius: 16px;
    overflow: hidden;
}}

/* ===== STATS BAR ===== */
.stats-bar {{
    display: flex; align-items: center; justify-content: center; gap: 3rem;
    padding: 1.6rem 2rem; margin: 2rem auto; max-width: 800px;
    background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 20px;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 4px 24px {t['card_hover_shadow']}, 0 0 14px {t['accent']}12, 0 0 28px {t['accent2']}06;
}}
.stats-bar:hover {{
    box-shadow: 0 4px 24px {t['card_hover_shadow']}, 0 0 20px {t['accent']}18, 0 0 40px {t['accent2']}10;
}}
.stats-bar .stat-item {{ text-align: center; }}
.stats-bar .stat-val {{
    font-size: 2rem; font-weight: 900;
    background: {t['heading_fill']}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.stats-bar .stat-lbl {{ font-size: 0.78rem; font-weight: 600; color: {t['text_muted']}; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.15rem; }}

/* ===== HOW IT WORKS (Steps) ===== */
.steps-container {{ max-width: 900px; margin: 0 auto; }}
.steps-row {{ display: flex; align-items: stretch; gap: 1.2rem; margin-top: 1.5rem; }}
.step-card {{
    flex: 1; position: relative; background: {t['card_bg']}; border: 1px solid {t['card_border']};
    border-radius: 18px; padding: 2rem 1.4rem 1.6rem; text-align: center;
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    transition: all 0.4s cubic-bezier(.22,1,.36,1);
}}
.step-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 12px 36px {t['card_hover_shadow']}, 0 0 12px {t['accent']}18;
    border-color: {t['accent']}30;
}}
.step-num {{
    position: absolute; top: -16px; left: 50%; transform: translateX(-50%);
    width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.85rem; color: #fff;
    background: linear-gradient(135deg, {t['accent']}, {t['accent2']});
    box-shadow: 0 3px 12px {t['accent_glow']}, 0 0 10px {t['accent']}40;
}}
.step-icon {{ font-size: 2.2rem; margin: 0.5rem 0 0.6rem; }}
.step-title {{ font-weight: 700; font-size: 1rem; color: {t['text']}; margin-bottom: 0.3rem; }}
.step-desc {{ font-size: 0.84rem; color: {t['text_muted']}; line-height: 1.55; }}
.step-arrow {{ display: flex; align-items: center; justify-content: center; font-size: 1.6rem; color: {t['accent']}; min-width: 30px; opacity: 0.5; }}

/* ===== TRUST BADGES ===== */
.trust-row {{ display: flex; align-items: center; justify-content: center; gap: 2rem; flex-wrap: wrap; margin: 1.5rem auto; }}
.trust-badge {{
    display: flex; align-items: center; gap: 0.45rem;
    padding: 0.55rem 1.1rem; border-radius: 999px;
    background: {t['card_bg']}; border: 1px solid {t['card_border']};
    font-size: 0.82rem; font-weight: 600; color: {t['text_muted']};
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    transition: all 0.35s cubic-bezier(.22,1,.36,1);
}}
.trust-badge:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px {t['accent_glow']}, 0 0 10px {t['accent']}12;
    border-color: {t['accent']}25;
}}
.trust-badge .t-emoji {{ font-size: 1rem; }}

/* ===== TESTIMONIALS ===== */
.testimonial-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; margin-top: 1.5rem; }}
.testimonial-card {{
    background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 18px;
    padding: 1.6rem 1.4rem; position: relative;
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    transition: all 0.4s cubic-bezier(.22,1,.36,1);
}}
.testimonial-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 12px 36px {t['card_hover_shadow']}, 0 0 10px {t['accent']}15;
    border-color: {t['accent']}20;
}}
.testimonial-card .quote {{ font-size: 2rem; line-height: 1; color: {t['accent']}; opacity: 0.3; position: absolute; top: 0.8rem; left: 1rem; }}
.testimonial-card .t-text {{ font-style: italic; color: {t['text_muted']}; font-size: 0.9rem; line-height: 1.6; margin-top: 0.5rem; }}
.testimonial-card .t-author {{ display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem; }}
.testimonial-card .t-avatar {{
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, {t['accent']}, {t['accent2']});
    display: flex; align-items: center; justify-content: center; font-size: 1rem;
}}
.testimonial-card .t-name {{ font-weight: 700; font-size: 0.85rem; color: {t['text']}; }}
.testimonial-card .t-role {{ font-size: 0.75rem; color: {t['text_dim']}; }}

/* ===== GLOW DIVIDER (neon) ===== */
.glow-divider {{
    height: 2px; max-width: 500px; margin: 2.5rem auto;
    background: linear-gradient(90deg, transparent 0%, {t['accent']}80 20%, {t['accent']} 40%, {t['accent2']} 60%, {t['accent2']}80 80%, transparent 100%);
    border-radius: 2px;
    box-shadow: 0 0 8px {t['accent']}55, 0 0 20px {t['accent']}30, 0 0 45px {t['accent2']}18, 0 0 80px {t['accent']}08;
    animation: neonBreath 4s ease-in-out infinite;
}}
@keyframes neonBreath {{
    0%,100% {{ opacity:0.55; box-shadow: 0 0 8px {t['accent']}45, 0 0 20px {t['accent']}22, 0 0 45px {t['accent2']}12; }}
    50%     {{ opacity:0.9; box-shadow: 0 0 12px {t['accent']}70, 0 0 30px {t['accent']}40, 0 0 60px {t['accent2']}25, 0 0 100px {t['accent']}10; }}
}}

/* ===== SECTION HEADING (centered) ===== */
.section-heading {{ text-align: center; margin-bottom: 0.3rem; }}
.section-heading h2 {{
    font-size: 1.6rem; font-weight: 800;
    background: {t['heading_fill']};
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block;
}}
.section-heading p {{ color: {t['text_muted']}; font-size: 0.95rem; margin-top: 0.3rem; }}

/* ===== GRADIENT BORDER CARD ===== */
.glow-border-card {{
    position: relative; border-radius: 20px; padding: 2px;
    background: linear-gradient(135deg, {t['accent']}, {t['accent2']}, {t['accent']});
    background-size: 200% 200%;
    animation: gradientShift 4s ease-in-out infinite;
}}
.glow-border-card .inner {{
    background: {t['bg']}; border-radius: 18px; padding: 2rem 1.8rem;
}}
@keyframes gradientShift {{
    0%,100% {{ background-position: 0% 50%; }}
    50%     {{ background-position: 100% 50%; }}
}}

/* ===== CONTRIBUTOR / TEAM CARDS ===== */
.team-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.2rem; margin-top: 1rem; }}
.team-card {{
    background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 18px;
    padding: 1.5rem 1rem; text-align: center;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    transition: all 0.4s cubic-bezier(.22,1,.36,1);
}}
.team-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 12px 36px {t['card_hover_shadow']}, 0 0 10px {t['accent']}15;
    border-color: {t['accent']}20;
}}
.team-card .tm-avatar {{
    width: 56px; height: 56px; border-radius: 50%; margin: 0 auto 0.7rem;
    background: linear-gradient(135deg, {t['accent']}, {t['accent2']});
    display: flex; align-items: center; justify-content: center; font-size: 1.6rem;
}}
.team-card .tm-name {{ font-weight: 700; font-size: 0.95rem; color: {t['text']}; }}
.team-card .tm-role {{ font-size: 0.78rem; color: {t['text_muted']}; margin-top: 0.15rem; }}

/* ===== PIPELINE FLOW ===== */
.pipeline-flow {{
    display: flex; align-items: center; justify-content: center; gap: 0.3rem;
    flex-wrap: wrap; margin: 1.5rem auto; max-width: 900px;
}}
.pipe-node {{
    display: flex; align-items: center; gap: 0.4rem;
    padding: 0.5rem 1rem; border-radius: 12px;
    background: {t['card_bg']}; border: 1px solid {t['card_border']};
    font-size: 0.85rem; font-weight: 600; color: {t['text']};
    white-space: nowrap;
}}
.pipe-node .p-icon {{ font-size: 1.1rem; }}
.pipe-arrow {{ font-size: 1.2rem; color: {t['accent']}; opacity: 0.5; }}

/* ===== TIP CALLOUT ===== */
.tip-callout {{
    display: flex; align-items: flex-start; gap: 0.8rem;
    background: {t['accent_glow']}; border: 1px solid {t['card_border']};
    border-left: 4px solid {t['accent']}; border-radius: 14px;
    padding: 1.1rem 1.4rem; margin: 1.5rem auto; max-width: 700px;
}}
.tip-callout .tip-icon {{ font-size: 1.4rem; flex-shrink: 0; }}
.tip-callout .tip-text {{ font-size: 0.9rem; color: {t['text_muted']}; line-height: 1.6; }}
.tip-callout .tip-text b {{ color: {t['text']}; }}

/* ===== ANIMATED COUNTER ===== */
.counter-row {{ display: flex; align-items: center; justify-content: center; gap: 3.5rem; margin: 2rem auto; flex-wrap: wrap; }}
.counter-item {{ text-align: center; }}
.counter-item .c-icon {{ font-size: 1.8rem; margin-bottom: 0.3rem; }}
.counter-item .c-val {{
    font-size: 2.2rem; font-weight: 900;
    background: {t['heading_fill']}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.counter-item .c-lbl {{ font-size: 0.75rem; font-weight: 600; color: {t['text_muted']}; text-transform: uppercase; letter-spacing: 1px; }}

/* ===== COMPONENT animations (enhanced) ===== */
.stats-bar {{ animation: fadeInUp 0.7s cubic-bezier(.22,1,.36,1) 0.4s both; }}
.stats-bar:hover {{ animation: glowPulse 2.5s ease-in-out infinite; }}
.stats-bar .stat-item:nth-child(1) {{ animation: bounceIn 0.6s ease 0.55s both; }}
.stats-bar .stat-item:nth-child(2) {{ animation: bounceIn 0.6s ease 0.68s both; }}
.stats-bar .stat-item:nth-child(3) {{ animation: bounceIn 0.6s ease 0.81s both; }}
.stats-bar .stat-item:nth-child(4) {{ animation: bounceIn 0.6s ease 0.94s both; }}

.steps-row {{ animation: fadeIn 0.5s ease 0.25s both; }}
.step-card:nth-child(1) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.15s both; }}
.step-card:nth-child(2) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.30s both; }}
.step-card:nth-child(3) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.45s both; }}
.step-card:nth-child(4) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.60s both; }}
.step-card:nth-child(5) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.75s both; }}
.step-card:nth-child(6) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.90s both; }}
.step-card:nth-child(7) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 1.05s both; }}
.step-icon {{ animation: float 3s ease-in-out 1.2s infinite; }}
.step-card:hover .step-icon {{ animation: pulse 0.8s ease-in-out 1; }}
.step-arrow {{ animation: fadeIn 0.3s ease 0.8s both; }}

.trust-badge:nth-child(1) {{ animation: bounceIn 0.5s ease 0.5s both; }}
.trust-badge:nth-child(2) {{ animation: bounceIn 0.5s ease 0.62s both; }}
.trust-badge:nth-child(3) {{ animation: bounceIn 0.5s ease 0.74s both; }}
.trust-badge:nth-child(4) {{ animation: bounceIn 0.5s ease 0.86s both; }}
.trust-badge:hover {{ animation: pulse 0.6s ease-in-out 1; }}

.testimonial-card:nth-child(1) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.15s both; }}
.testimonial-card:nth-child(2) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.30s both; }}
.testimonial-card:nth-child(3) {{ animation: flipIn 0.65s cubic-bezier(.22,1,.36,1) 0.45s both; }}
.testimonial-card .quote {{ animation: popIn 0.5s ease 0.6s both; }}
.testimonial-card .t-avatar {{ animation: bounceIn 0.5s ease 0.5s both; }}

.glow-divider {{ animation: scaleIn 0.7s ease 0.4s both; }}
.glow-border-card {{ animation: fadeInUp 0.7s cubic-bezier(.22,1,.36,1) 0.15s both; }}
.section-heading {{ animation: fadeInUp 0.6s cubic-bezier(.22,1,.36,1) 0.1s both; }}
.section-heading h2 {{ animation: slideReveal 0.8s cubic-bezier(.22,1,.36,1) 0.2s both; }}

.pipeline-flow {{ animation: fadeIn 0.5s ease 0.15s both; }}
.pipe-node:nth-child(1)  {{ animation: bounceIn 0.5s ease 0.1s both; }}
.pipe-node:nth-child(2)  {{ animation: bounceIn 0.5s ease 0.18s both; }}
.pipe-node:nth-child(3)  {{ animation: bounceIn 0.5s ease 0.26s both; }}
.pipe-node:nth-child(4)  {{ animation: bounceIn 0.5s ease 0.34s both; }}
.pipe-node:nth-child(5)  {{ animation: bounceIn 0.5s ease 0.42s both; }}
.pipe-node:nth-child(6)  {{ animation: bounceIn 0.5s ease 0.50s both; }}
.pipe-node:nth-child(7)  {{ animation: bounceIn 0.5s ease 0.58s both; }}
.pipe-node:nth-child(8)  {{ animation: bounceIn 0.5s ease 0.66s both; }}
.pipe-node:nth-child(9)  {{ animation: bounceIn 0.5s ease 0.74s both; }}
.pipe-arrow {{ animation: fadeIn 0.3s ease 0.5s both; }}
.pipe-node .p-icon {{ animation: gentleSway 3s ease-in-out 1s infinite; }}

.tip-callout {{ animation: slideInLeft 0.65s cubic-bezier(.22,1,.36,1) 0.25s both; }}
.tip-callout .tip-icon {{ animation: float 2.5s ease-in-out 0.8s infinite; }}

.team-card:nth-child(1) {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.08s both; }}
.team-card:nth-child(2) {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.20s both; }}
.team-card:nth-child(3) {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.32s both; }}
.team-card:nth-child(4) {{ animation: elasticIn 0.7s cubic-bezier(.22,1,.36,1) 0.44s both; }}
.team-card .tm-avatar {{ animation: bounceIn 0.5s ease 0.5s both; }}
.team-card:hover .tm-avatar {{ animation: pulse 0.8s ease-in-out 1; }}

.counter-row {{ animation: fadeInUp 0.6s cubic-bezier(.22,1,.36,1) 0.25s both; }}
.counter-item:nth-child(1) {{ animation: bounceIn 0.6s ease 0.35s both; }}
.counter-item:nth-child(2) {{ animation: bounceIn 0.6s ease 0.48s both; }}
.counter-item:nth-child(3) {{ animation: bounceIn 0.6s ease 0.61s both; }}
.counter-item:nth-child(4) {{ animation: bounceIn 0.6s ease 0.74s both; }}
.counter-item .c-icon {{ animation: float 3s ease-in-out 1s infinite; }}

/* ===== NEON BADGE GLOW ===== */
.badge-high-mild     {{ box-shadow:0 2px 8px rgba(248,113,113,0.3), 0 0 12px rgba(248,113,113,0.15); }}
.badge-high-moderate {{ box-shadow:0 2px 8px rgba(239,68,68,0.4), 0 0 14px rgba(239,68,68,0.22), 0 0 26px rgba(239,68,68,0.1); }}
.badge-high-critical {{ box-shadow:0 2px 8px rgba(220,38,38,0.45), 0 0 16px rgba(220,38,38,0.3), 0 0 32px rgba(220,38,38,0.12); }}
.badge-low-mild      {{ box-shadow:0 2px 8px rgba(251,191,36,0.3), 0 0 12px rgba(251,191,36,0.15); }}
.badge-low-moderate  {{ box-shadow:0 2px 8px rgba(245,158,11,0.4), 0 0 14px rgba(245,158,11,0.22), 0 0 26px rgba(245,158,11,0.1); }}
.badge-low-critical  {{ box-shadow:0 2px 8px rgba(217,119,6,0.45), 0 0 16px rgba(217,119,6,0.3), 0 0 32px rgba(217,119,6,0.12); }}
.badge-normal {{ box-shadow:0 2px 8px rgba(34,197,94,0.35), 0 0 14px rgba(34,197,94,0.2), 0 0 28px rgba(34,197,94,0.08); }}

/* ===== NEON TAB GLOW ===== */
.stTabs [aria-selected="true"] {{
    box-shadow: 0 0 12px {t['accent_glow']}, 0 0 22px {t['accent']}18, 0 0 36px {t['accent2']}08 !important;
}}

/* ===== NEON UPLOAD ZONE ===== */
.upload-zone:hover {{
    box-shadow: 0 0 20px {t['accent']}20, 0 0 40px {t['accent2']}12;
}}

/* ===== NEON PIPE NODES ===== */
.pipe-node {{
    transition: all 0.3s ease;
}}
.pipe-node:hover {{
    box-shadow: 0 4px 16px {t['card_hover_shadow']}, 0 0 10px {t['accent']}15;
    border-color: {t['accent']}25;
    transform: translateY(-2px);
}}

/* ===== HELPERS ===== */
.spacer-xs {{ margin-top:0.5rem; }} .spacer-sm {{ margin-top:1rem; }}
.spacer-md {{ margin-top:1.8rem; }} .spacer-lg {{ margin-top:2.8rem; }}
.section-title {{ font-size:0.78rem; font-weight:700; color:{t['text_dim']}; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:1rem; }}

</style>
"""


# ──────────────────────────────────────────────────────────────────────
# Navbar renderer
# ──────────────────────────────────────────────────────────────────────

def _render_navbar() -> None:
    active = st.session_state.page
    dark = st.session_state.dark_mode
    t = _theme()

    # Inject navbar-specific CSS that targets the button row
    st.markdown(
        f"""
        <style>
        /* ── Navbar button overrides ── */
        .navbar-row [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            background: {t['navbar_bg']};
            backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
            border: 1px solid {t['navbar_border']};
            border-radius: 16px;
            padding: 0.45rem 1.2rem;
            box-shadow: 0 2px 16px rgba(0,0,0,0.08), 0 0 12px {t['accent']}08;
        }}
        /* Make every button in the navbar row uniform */
        .navbar-row .stButton > button {{
            white-space: nowrap !important;
            min-height: 38px !important;
            height: 38px !important;
            padding: 0 1.1rem !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            line-height: 1 !important;
            border-radius: 10px !important;
            letter-spacing: 0.2px !important;
            transition: all 0.2s ease !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        .navbar-row .stButton > button:hover {{
            transform: scale(1.03) !important;
        }}
        /* Active nav button (primary type) gets gradient */
        .navbar-row .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {t['accent']}, {t['accent2']}) !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 2px 12px {t['accent_glow']}, 0 0 18px {t['accent']}25 !important;
        }}
        /* Inactive nav buttons */
        .navbar-row .stButton > button[kind="secondary"] {{
            background: transparent !important;
            color: {t['text_muted']} !important;
            border: 1px solid {t['card_border']} !important;
        }}
        .navbar-row .stButton > button[kind="secondary"]:hover {{
            color: {t['text']} !important;
            background: {t['accent_glow']} !important;
        }}
        /* Brand text in first column */
        .nav-brand-cell {{
            display: flex; align-items: center; gap: 0.5rem;
            white-space: nowrap; padding: 0 0.3rem;
        }}
        .nav-brand-cell .dna {{ font-size: 1.4rem; }}
        .nav-brand-cell .brand-text {{
            font-weight: 800; font-size: 1.05rem;
            background: {t['heading_fill']}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Single row: brand + 4 nav buttons inside a styled container
    with st.container():
        st.markdown('<div class="navbar-row">', unsafe_allow_html=True)
        brand_col, c1, c2, c3, c4 = st.columns([3, 1, 1, 1, 1.2])

        with brand_col:
            st.markdown(
                '<div class="nav-brand-cell">'
                '<span class="dna">🧬</span>'
                '<span class="brand-text">Lab Report Intelligence Agent</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with c1:
            btn_type = "primary" if active == "Home" else "secondary"
            if st.button("🏠 Home", key="btn_home", type=btn_type, use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()
        with c2:
            btn_type = "primary" if active == "Analyze" else "secondary"
            if st.button("🔬 Analyze", key="btn_analyze", type=btn_type, use_container_width=True):
                st.session_state.page = "Analyze"
                st.rerun()
        with c3:
            btn_type = "primary" if active == "About" else "secondary"
            if st.button("ℹ️ About", key="btn_about", type=btn_type, use_container_width=True):
                st.session_state.page = "About"
                st.rerun()
        with c4:
            theme_label = "☀️ Light" if dark else "🌙 Dark"
            if st.button(theme_label, key="btn_toggle", use_container_width=True):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# Helpers (unchanged analysis rendering)
# ──────────────────────────────────────────────────────────────────────

def _score_color(score: int) -> str:
    if score >= 80:
        return "#22c55e"
    if score >= 60:
        return "#f59e0b"
    return "#ef4444"


def _status_badge(status: Status, severity: Severity = Severity.NORMAL) -> str:
    if status == Status.NORMAL:
        cls = "badge-normal"
        label = status.value
    else:
        sev_key = severity.value.lower()  # mild / moderate / critical
        base = "high" if status == Status.HIGH else "low"
        cls = f"badge-{base}-{sev_key}"
        label = f'{status.value} <span class="sev-label">({severity.value})</span>'
    return f'<span class="badge {cls}">{label}</span>'


def _render_score_svg(score: int) -> None:
    color = _score_color(score)
    c = 2 * 3.14159 * 60
    offset = c - (score / 100) * c
    st.markdown(
        f"""
        <div class="score-wrap">
            <div class="score-circle">
                <svg viewBox="0 0 140 140">
                    <circle class="track" cx="70" cy="70" r="60"/>
                    <circle class="fill" cx="70" cy="70" r="60"
                        stroke="{color}" stroke-dasharray="{c}" stroke-dashoffset="{offset}"/>
                </svg>
                <div class="score-number">{score}</div>
            </div>
            <div class="score-tag">Health Score</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_metric(icon: str, value, label: str, color: str = "#e2e8f0") -> None:
    st.markdown(
        f"""
        <div class="m-card">
            <div class="m-icon">{icon}</div>
            <div class="m-val" style="color:{color};">{value}</div>
            <div class="m-lbl">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_status_banner(score: int, abnormal: int) -> None:
    if score >= 80:
        cls, msg = "banner-good", "Overall Good - Your results look healthy. Keep it up!"
    elif score >= 60:
        cls = "banner-moderate"
        msg = f"Moderate Risk - {abnormal} value{'s' if abnormal != 1 else ''} need attention. See recommendations below."
    else:
        cls = "banner-risk"
        msg = f"High Risk - {abnormal} value{'s' if abnormal != 1 else ''} are outside normal range. Please consult a doctor."
    st.markdown(f'<div class="status-banner {cls}">{msg}</div>', unsafe_allow_html=True)


def _render_results_table(tests: list[AnalyzedTest]) -> None:
    if not tests:
        st.info("No recognized lab tests found in the report.")
        return
    sorted_tests = sorted(tests, key=lambda x: (x.status != Status.HIGH, x.status != Status.LOW))
    rows: list[str] = []
    for t in sorted_tests:
        badge = _status_badge(t.status, t.severity)
        nc = "#f87171" if t.status == Status.HIGH else "#fbbf24" if t.status == Status.LOW else "#cbd5e1"
        # Severity-based row tint class
        if t.status != Status.NORMAL:
            sev_key = t.severity.value.lower()
            base = "high" if t.status == Status.HIGH else "low"
            row_cls = f' class="row-{base}-{sev_key}"'
        else:
            row_cls = ""
        rows.append(
            f"<tr{row_cls}>"
            f'<td style="color:{nc};font-weight:600;">{t.canonical_name.title()}</td>'
            f"<td>{t.value} {t.unit}</td><td>{t.min_value} - {t.max_value} {t.unit}</td><td>{badge}</td></tr>"
        )
    st.markdown(
        '<div class="tbl-wrap"><table>'
        "<thead><tr><th>Test</th><th>Your Value</th><th>Normal Range</th><th>Status</th></tr></thead>"
        "<tbody>" + "\n".join(rows) + "</tbody></table></div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────
# Risk categorisation & Plotly charts
# ──────────────────────────────────────────────────────────────────────

_RISK_CATEGORIES: dict[str, dict] = {
    "Cardiovascular": {
        "icon": "❤️",
        "tests": {"total cholesterol", "ldl", "hdl", "triglycerides", "vldl"},
    },
    "Metabolic / Diabetes": {
        "icon": "🍬",
        "tests": {"fasting glucose", "random glucose", "hba1c", "pp glucose"},
    },
    "Kidney": {
        "icon": "🫘",
        "tests": {"creatinine", "bun", "urea", "uric acid", "egfr"},
    },
    "Liver": {
        "icon": "🫁",
        "tests": {"sgot", "sgpt", "alkaline phosphatase", "total bilirubin",
                  "direct bilirubin", "albumin", "globulin", "total protein",
                  "ag ratio", "ggt"},
    },
    "Thyroid": {
        "icon": "🦋",
        "tests": {"tsh", "t3", "t4", "free t3", "free t4"},
    },
    "Bone & Minerals": {
        "icon": "🦴",
        "tests": {"vitamin d", "calcium", "phosphorus", "magnesium"},
    },
    "Blood (CBC)": {
        "icon": "🩸",
        "tests": {"hemoglobin", "hematocrit", "rbc", "wbc", "platelets",
                  "mcv", "mch", "mchc", "rdw", "mpv"},
    },
    "Iron & Vitamins": {
        "icon": "💊",
        "tests": {"iron", "ferritin", "tibc", "vitamin b12", "folate"},
    },
    "Electrolytes": {
        "icon": "⚡",
        "tests": {"sodium", "potassium", "chloride"},
    },
    "Inflammation": {
        "icon": "🔥",
        "tests": {"esr", "crp"},
    },
}


def _categorize_risks(tests: list[AnalyzedTest]) -> list[dict]:
    """Return list of {category, icon, risk_level, abnormal, total, test_details}."""
    results = []
    for cat_name, cat_info in _RISK_CATEGORIES.items():
        matched = [t for t in tests if t.canonical_name in cat_info["tests"]]
        if not matched:
            continue
        abnormal = [t for t in matched if t.status != Status.NORMAL]
        ratio = len(abnormal) / len(matched) if matched else 0
        if ratio == 0:
            level = "normal"
        elif ratio < 0.4:
            level = "low"
        elif ratio < 0.7:
            level = "moderate"
        else:
            level = "high"
        details = []
        for t in matched:
            details.append({
                "name": t.canonical_name.title(),
                "value": t.value,
                "unit": t.unit,
                "status": t.status.value,
                "severity": t.severity.value,
            })
        results.append({
            "category": cat_name,
            "icon": cat_info["icon"],
            "risk_level": level,
            "abnormal": len(abnormal),
            "total": len(matched),
            "test_details": details,
        })
    # Sort: high risk first, then moderate, low, normal
    order = {"high": 0, "moderate": 1, "low": 2, "normal": 3}
    results.sort(key=lambda x: order.get(x["risk_level"], 4))
    return results


def _plotly_layout(title: str = "") -> dict:
    """Common transparent Plotly layout matching app theme."""
    dark = st.session_state.get("dark_mode", True)
    fg = "#e2e8f0" if dark else "#1e293b"
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=40, b=30),
        title=dict(text=title, font=dict(size=14, color=fg)) if title else None,
        font=dict(color=fg, size=11),
        legend=dict(font=dict(size=11, color=fg)),
    )


def _render_pie_chart(normal_count: int, abnormal_count: int) -> None:
    colors = ["#4ade80", "#f87171"]
    fig = go.Figure(go.Pie(
        labels=["Normal", "Abnormal"],
        values=[normal_count, abnormal_count],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.15)", width=1.5)),
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="%{label}: %{value} tests<extra></extra>",
    ))
    fig.update_layout(**_plotly_layout())
    fig.update_layout(height=280, showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_bar_chart(tests: list[AnalyzedTest]) -> None:
    abnormal = [t for t in tests if t.status != Status.NORMAL]
    if not abnormal:
        st.info("All values are within normal range — no bar chart needed.")
        return
    abnormal = sorted(abnormal, key=lambda x: abs(x.deviation_pct), reverse=True)[:12]
    names = [t.canonical_name.title() for t in abnormal]
    values = [t.value for t in abnormal]
    lows = [t.min_value for t in abnormal]
    highs = [t.max_value for t in abnormal]
    # Severity-graded bar colors
    _bar_sev = {
        (Status.HIGH, Severity.MILD): "#f87171",
        (Status.HIGH, Severity.MODERATE): "#ef4444",
        (Status.HIGH, Severity.CRITICAL): "#dc2626",
        (Status.LOW, Severity.MILD): "#fbbf24",
        (Status.LOW, Severity.MODERATE): "#f59e0b",
        (Status.LOW, Severity.CRITICAL): "#d97706",
    }
    bar_colors = [_bar_sev.get((t.status, t.severity), "#f87171") for t in abnormal]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=values, name="Your Value",
        marker_color=bar_colors, marker_line=dict(width=0),
        hovertemplate="%{x}: %{y}<extra>Your Value</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=names, y=lows, mode="markers+lines", name="Lower Bound",
        marker=dict(size=7, color="#38bdf8", symbol="triangle-down"),
        line=dict(dash="dot", color="#38bdf8", width=1.5),
        hovertemplate="%{x}: %{y}<extra>Lower Bound</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=names, y=highs, mode="markers+lines", name="Upper Bound",
        marker=dict(size=7, color="#a78bfa", symbol="triangle-up"),
        line=dict(dash="dot", color="#a78bfa", width=1.5),
        hovertemplate="%{x}: %{y}<extra>Upper Bound</extra>",
    ))
    fig.update_layout(**_plotly_layout())
    fig.update_layout(
        height=340, barmode="group",
        xaxis=dict(tickangle=-35),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_radar_chart(risk_data: list[dict]) -> None:
    if not risk_data:
        return
    categories = [r["category"] for r in risk_data]
    # Map risk level to a numeric score (0-100)
    level_score = {"normal": 10, "low": 40, "moderate": 70, "high": 95}
    scores = [level_score.get(r["risk_level"], 0) for r in risk_data]
    # Close the polygon
    categories_closed = categories + [categories[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure(go.Scatterpolar(
        r=scores_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(129,140,248,0.15)",
        line=dict(color="#818cf8", width=2),
        marker=dict(size=6, color="#818cf8"),
        hovertemplate="%{theta}: %{r}/100<extra></extra>",
    ))
    fig.update_layout(**_plotly_layout())
    fig.update_layout(
        height=340,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                            gridcolor="rgba(148,163,184,0.15)"),
            angularaxis=dict(gridcolor="rgba(148,163,184,0.15)"),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_risk_cards(risk_data: list[dict]) -> None:
    if not risk_data:
        return
    # Severity color map for per-test detail text
    _sev_colors = {
        "Critical": "#ef4444", "Moderate": "#f59e0b", "Mild": "#fbbf24", "Normal": "#94a3b8",
    }
    cards_html = '<div class="risk-grid">'
    for r in risk_data:
        badge_cls = f"risk-{r['risk_level']}"
        badge_text = r["risk_level"].upper()
        # Build detailed test list with severity labels
        test_parts = []
        for d in r["test_details"]:
            sev = d.get("severity", "Normal")
            if sev != "Normal":
                sc = _sev_colors.get(sev, "#94a3b8")
                test_parts.append(f'<span style="color:{sc};font-weight:600;">{d["name"]} ({sev})</span>')
            else:
                test_parts.append(d["name"])
        test_lines = ", ".join(test_parts)
        abn_txt = f"{r['abnormal']}/{r['total']} abnormal" if r["abnormal"] else f"All {r['total']} normal"
        # Pick a left-border accent color based on highest severity in category
        worst = "Normal"
        for d in r["test_details"]:
            s = d.get("severity", "Normal")
            if s == "Critical":
                worst = "Critical"; break
            if s == "Moderate" and worst != "Critical":
                worst = "Moderate"
            if s == "Mild" and worst == "Normal":
                worst = "Mild"
        border_color = _sev_colors.get(worst, "transparent")
        border_style = f' style="border-left:3px solid {border_color};"' if worst != "Normal" else ""
        cards_html += (
            f'<div class="risk-card"{border_style}>'
            f'<div class="rc-header">'
            f'<span class="rc-icon">{r["icon"]}</span>'
            f'<span class="rc-title">{r["category"]}</span>'
            f'<span class="risk-badge {badge_cls}">{badge_text}</span>'
            f'</div>'
            f'<div class="rc-tests">{abn_txt}<br/>{test_lines}</div>'
            f'</div>'
        )
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


def _md_to_safe(text: str) -> str:
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = _re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=_re.MULTILINE)
    text = _re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=_re.MULTILINE)
    lines = text.split('\n')
    result: list[str] = []
    in_list = False
    for line in lines:
        s = line.strip()
        if s.startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{s[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if s:
                result.append(s if s.startswith('<h') else f'<p>{s}</p>')
    if in_list:
        result.append('</ul>')
    return '\n'.join(result)


def _render_footer() -> None:
    st.markdown('<div class="footer-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="disclaimer-box">'
        "&#9888;&#65039; <b>Disclaimer:</b> This tool is for educational and informational purposes only. "
        "It is not a medical diagnosis. Always consult a qualified healthcare "
        "professional for medical advice, diagnoses, or treatment."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="footer-text">Lab Report Intelligence Agent &mdash; Health insights at your fingertips</p>'
        '<p class="footer-text" style="margin-top:0.3rem;">&copy; 2026 Code Crafters. All rights reserved.</p>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────
# PAGE: Home
# ──────────────────────────────────────────────────────────────────────

def _page_home() -> None:
    t = _theme()

    # ── HERO ──
    st.markdown(
        '<div class="hero">'
        "<h1>🧬 Lab Report<br>Intelligence Agent</h1>"
        '<p class="tagline">AI-powered lab report analysis with personalized health insights.</p>'
        '<p class="desc">Upload your lab report PDF and get an instant breakdown of your health metrics, '
        "compare values against medical benchmarks, and receive personalized food &amp; lifestyle recommendations "
        "&mdash; all in seconds.</p>"
        '<div class="hero-divider"></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── TRUST BADGES ──
    st.markdown(
        '<div class="trust-row">'
        '<div class="trust-badge"><span class="t-emoji">🔒</span> Secure & Private</div>'
        '<div class="trust-badge"><span class="t-emoji">⚡</span> Instant Results</div>'
        '<div class="trust-badge"><span class="t-emoji">🏥</span> Clinically Validated</div>'
        '<div class="trust-badge"><span class="t-emoji">🆓</span> 100% Free</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── CTA BUTTON ──
    _c1, c_btn, _c2 = st.columns([1, 1, 1])
    with c_btn:
        if st.button("🚀  Start Analysis", use_container_width=True, type="primary"):
            _nav_to("Analyze")
            st.rerun()

    # ── STATS BAR ──
    st.markdown(
        '<div class="stats-bar">'
        '<div class="stat-item"><div class="stat-val">50+</div><div class="stat-lbl">Lab Tests</div></div>'
        '<div class="stat-item"><div class="stat-val">3s</div><div class="stat-lbl">Avg Speed</div></div>'
        '<div class="stat-item"><div class="stat-val">100%</div><div class="stat-lbl">Rule-Based</div></div>'
        '<div class="stat-item"><div class="stat-val">24/7</div><div class="stat-lbl">Available</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── FEATURE CARDS ──
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-heading"><h2>Key Features</h2>'
        '<p>Everything you need to understand your lab results</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="feat-grid">'
        '<div class="feat-card"><div class="f-icon">📄</div><div class="f-title">PDF Parsing</div>'
        '<div class="f-desc">Extracts lab values from any standard text-based PDF lab report automatically.</div></div>'
        '<div class="feat-card"><div class="f-icon">📊</div><div class="f-title">Smart Analysis</div>'
        '<div class="f-desc">Compares every value against clinically validated reference ranges in real time.</div></div>'
        '<div class="feat-card"><div class="f-icon">🩺</div><div class="f-title">Health Summary</div>'
        '<div class="f-desc">Generates a clear, human-friendly explanation of your results with a health score.</div></div>'
        '<div class="feat-card"><div class="f-icon">🥗</div><div class="f-title">Diet & Lifestyle</div>'
        '<div class="f-desc">Personalized food recommendations and lifestyle tips to improve abnormal markers.</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── HOW IT WORKS ──
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-heading"><h2>How It Works</h2>'
        '<p>From PDF to actionable insights in 4 simple steps</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="steps-container"><div class="steps-row">'
        '<div class="step-card"><div class="step-num">1</div><div class="step-icon">📤</div>'
        '<div class="step-title">Upload PDF</div><div class="step-desc">Drop your lab report PDF into the Analyze page.</div></div>'
        '<div class="step-arrow">→</div>'
        '<div class="step-card"><div class="step-num">2</div><div class="step-icon">🔍</div>'
        '<div class="step-title">Extract Values</div><div class="step-desc">We parse test names, values, and units automatically.</div></div>'
        '<div class="step-arrow">→</div>'
        '<div class="step-card"><div class="step-num">3</div><div class="step-icon">⚖️</div>'
        '<div class="step-title">Compare Ranges</div><div class="step-desc">Each value is checked against medical reference ranges.</div></div>'
        '<div class="step-arrow">→</div>'
        '<div class="step-card"><div class="step-num">4</div><div class="step-icon">📋</div>'
        '<div class="step-title">Get Insights</div><div class="step-desc">Receive a health score, summary, and lifestyle advice.</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # ── TESTIMONIALS ──
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-heading"><h2>What Users Say</h2>'
        '<p>Trusted by students, patients, and health enthusiasts</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="testimonial-grid">'
        '<div class="testimonial-card"><div class="quote">&ldquo;</div>'
        '<div class="t-text">I finally understood my blood work results without Googling every test name. Super helpful!</div>'
        '<div class="t-author"><div class="t-avatar">👩‍🎓</div><div><div class="t-name">Priya S.</div>'
        '<div class="t-role">Medical Student</div></div></div></div>'
        '<div class="testimonial-card"><div class="quote">&ldquo;</div>'
        '<div class="t-text">The diet recommendations for my high cholesterol were spot-on. Clean UI too!</div>'
        '<div class="t-author"><div class="t-avatar">👨‍💼</div><div><div class="t-name">Rahul M.</div>'
        '<div class="t-role">Software Engineer</div></div></div></div>'
        '<div class="testimonial-card"><div class="quote">&ldquo;</div>'
        '<div class="t-text">Great hackathon project! The health score ring and animated cards look premium.</div>'
        '<div class="t-author"><div class="t-avatar">👨‍🏫</div><div><div class="t-name">Dr. Anand K.</div>'
        '<div class="t-role">Hackathon Judge</div></div></div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    _render_footer()


# ──────────────────────────────────────────────────────────────────────
# PAGE: Analyze
# ──────────────────────────────────────────────────────────────────────

def _page_analyze() -> None:
    t = _theme()
    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-heading"><h2>🔬 Upload &amp; Analyze</h2>'
        '<p>Drop your lab report PDF and get instant health insights</p></div>',
        unsafe_allow_html=True,
    )

    # ── PIPELINE FLOW ──
    st.markdown(
        '<div class="pipeline-flow">'
        '<div class="pipe-node"><span class="p-icon">📤</span> Upload</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">📝</span> Extract</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">🔍</span> Parse</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">⚖️</span> Analyze</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">📊</span> Report</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 3, 1])
    with col_c:
        uploaded = st.file_uploader(
            "Upload Lab Report (PDF)",
            type=["pdf"],
            help="Supports text-based PDF lab reports.",
        )

    if not uploaded:
        st.markdown(
            '<div class="upload-zone">'
            '<div class="upload-icon">📄</div>'
            "<p>Drop your PDF lab report above or click <b>Browse files</b> to get started.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        # ── TIP CALLOUT ──
        st.markdown(
            '<div class="tip-callout">'
            '<div class="tip-icon">💡</div>'
            '<div class="tip-text"><b>Pro Tip:</b> Make sure your lab report is a text-based PDF '
            '(not a scanned image). Reports from most hospitals and diagnostic labs work perfectly.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── SUPPORTED TESTS PREVIEW ──
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-heading"><h2>Supported Tests</h2>'
            '<p>We can analyze 50+ common lab parameters</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="trust-row">'
            '<div class="trust-badge"><span class="t-emoji">🩸</span> Hemoglobin</div>'
            '<div class="trust-badge"><span class="t-emoji">🔬</span> WBC / RBC</div>'
            '<div class="trust-badge"><span class="t-emoji">💉</span> Blood Sugar</div>'
            '<div class="trust-badge"><span class="t-emoji">🫀</span> Cholesterol</div>'
            '<div class="trust-badge"><span class="t-emoji">🦴</span> Calcium</div>'
            '<div class="trust-badge"><span class="t-emoji">🧪</span> Thyroid</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
        _render_footer()
        return

    # ── Pipeline ──
    with st.spinner("Extracting text from PDF..."):
        try:
            raw_text = extract_text_from_pdf(uploaded)
        except (EmptyPDFError, PDFExtractionError) as exc:
            st.error(f"{exc}")
            return

    with st.spinner("Parsing lab values..."):
        extracted = parse_lab_values(raw_text)

    if not extracted:
        st.warning("No lab test values could be parsed. Ensure it is a text-based report (not scanned).")
        _render_footer()
        return

    with st.spinner("Analyzing results..."):
        report = analyze(extracted)

    with st.spinner("Generating health summary..."):
        summary = generate_summary(report, api_key=None)

    with st.spinner("Generating health interpretation..."):
        health_guidance = generate_health_guidance(report, api_key=None)

    # ── Dashboard ──
    _render_dashboard(report, summary, health_guidance)
    _render_footer()


def _render_dashboard(report: AnalysisReport, summary, health_guidance: str) -> None:
    abnormal_count = sum(1 for t in report.matched if t.status != Status.NORMAL)
    normal_count = len(report.matched) - abnormal_count

    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    _render_status_banner(report.health_score, abnormal_count)

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
    with c1:
        _render_score_svg(report.health_score)
    with c2:
        _render_metric("🔬", len(report.matched), "Tests Matched", "#a5b4fc")
    with c3:
        _render_metric("✅", normal_count, "Normal", "#4ade80")
    with c4:
        _render_metric("⚠️", abnormal_count, "Abnormal", "#f87171")

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

    # ── Risk categorisation ──
    risk_data = _categorize_risks(report.matched)

    # ── Visual Insights ──
    st.markdown('<div class="section-title">📈 Visual Insights</div>', unsafe_allow_html=True)
    vi_pie, vi_bar = st.columns(2)
    with vi_pie:
        st.markdown('<div class="insight-title">Test Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="insight-subtitle">Normal vs Abnormal breakdown</div>', unsafe_allow_html=True)
        _render_pie_chart(normal_count, abnormal_count)
    with vi_bar:
        st.markdown('<div class="insight-title">Abnormal Values vs Bounds</div>', unsafe_allow_html=True)
        st.markdown('<div class="insight-subtitle">Your values compared to reference ranges</div>', unsafe_allow_html=True)
        _render_bar_chart(report.matched)

    if len(risk_data) >= 3:
        st.markdown('<div class="insight-title" style="margin-top:0.6rem;">Risk Radar</div>', unsafe_allow_html=True)
        st.markdown('<div class="insight-subtitle">Category-wise risk profile</div>', unsafe_allow_html=True)
        _render_radar_chart(risk_data)

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

    # ── Health Risk Overview ──
    st.markdown('<div class="section-title">🛡️ Health Risk Overview</div>', unsafe_allow_html=True)
    _render_risk_cards(risk_data)

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

    tab_results, tab_summary, tab_guidance = st.tabs([
        "📊  Detailed Results",
        "💡  Health Summary",
        "🧠  Food & Lifestyle Advice",
    ])

    with tab_results:
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        _render_results_table(report.matched)
        if report.unrecognized:
            st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
            with st.expander(f"Unrecognized tests ({len(report.unrecognized)})"):
                for u in report.unrecognized:
                    st.write(f"**{u.raw_name}**: {u.value}")

    with tab_summary:
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.caption("📐 Instant Analysis")
        s1, s2, s3 = st.tabs(["🩺 Overview", "🥗 Diet Suggestions", "🏃 Lifestyle"])
        with s1:
            st.markdown(f'<div class="summary-card">{_md_to_safe(summary.overview)}</div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="summary-card">{_md_to_safe(summary.diet_suggestions)}</div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="summary-card">{_md_to_safe(summary.lifestyle_recommendations)}</div>', unsafe_allow_html=True)

    with tab_guidance:
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="guidance-card">{_md_to_safe(health_guidance)}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# PAGE: About
# ──────────────────────────────────────────────────────────────────────

def _page_about() -> None:
    t = _theme()

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

    # ── HERO SECTION ──
    st.markdown(
        '<div class="about-section">'
        "<h2>🧬 Lab Report Intelligence Agent</h2>"
        '<p style="font-size:1.05rem;">A smart, AI-powered health-tech platform that transforms raw lab reports '
        "into actionable health insights in seconds.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── COUNTERS ──
    st.markdown(
        '<div class="counter-row">'
        '<div class="counter-item"><div class="c-icon">🧪</div><div class="c-val">50+</div><div class="c-lbl">Lab Tests</div></div>'
        '<div class="counter-item"><div class="c-icon">📄</div><div class="c-val">PDF</div><div class="c-lbl">Input Format</div></div>'
        '<div class="counter-item"><div class="c-icon">⚡</div><div class="c-val">&lt;5s</div><div class="c-lbl">Analysis Time</div></div>'
        '<div class="counter-item"><div class="c-icon">🎯</div><div class="c-val">100%</div><div class="c-lbl">Deterministic</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ── PROBLEM STATEMENT (gradient border card) ──
    st.markdown(
        '<div style="max-width:820px;margin:0 auto;">'
        '<div class="glow-border-card"><div class="inner">'
        '<div class="section-heading"><h2>🎯 Problem Statement</h2></div>'
        '<p style="color:' + t['text_muted'] + ';line-height:1.7;text-align:center;margin-top:0.8rem;">'
        '<b>#24 Healthcare</b> &mdash; Millions of patients receive lab reports filled with medical jargon and '
        "cryptic reference ranges. Most people don't understand what their values mean, leading to anxiety or "
        'missed early warning signs. <b>This tool bridges that gap.</b></p>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    # ── WHAT IT DOES ──
    st.markdown(
        '<div class="about-section">'
        "<h3>🔍 What It Does</h3>"
        "<ul>"
        "<li><b>Parses lab reports</b> &mdash; Automatically extracts test names, values, and units from PDF reports.</li>"
        "<li><b>Compares against medical benchmarks</b> &mdash; Each value is checked against clinically validated normal ranges.</li>"
        "<li><b>Generates human-friendly explanations</b> &mdash; Translates medical data into simple, easy-to-understand summaries.</li>"
        "<li><b>Provides food &amp; lifestyle advice</b> &mdash; Personalized dietary and lifestyle recommendations for every abnormal marker.</li>"
        "</ul>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ── ARCHITECTURE / PIPELINE ──
    st.markdown(
        '<div class="section-heading"><h2>⚙️ System Architecture</h2>'
        '<p>End-to-end processing pipeline</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pipeline-flow">'
        '<div class="pipe-node"><span class="p-icon">📄</span> PDF Input</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">🔤</span> pdfplumber</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">🧩</span> Regex Parser</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">📏</span> Range Lookup</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">📊</span> Analyzer</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">📝</span> Summary</div>'
        '<span class="pipe-arrow">→</span>'
        '<div class="pipe-node"><span class="p-icon">🖥️</span> Dashboard</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ── TECHNOLOGIES ──
    st.markdown(
        '<div class="section-heading"><h2>🛠️ Technologies Used</h2>'
        '<p>Built with modern, reliable tools</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tech-grid" style="max-width:820px;margin:0 auto;">'
        '<div class="tech-chip"><div class="t-icon">🐍</div>Python 3.9+</div>'
        '<div class="tech-chip"><div class="t-icon">📄</div>PDFPlumber</div>'
        '<div class="tech-chip"><div class="t-icon">🧠</div>Rule Engine</div>'
        '<div class="tech-chip"><div class="t-icon">📊</div>Custom Analyzer</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ── TEAM / CONTRIBUTORS ──
    st.markdown(
        '<div class="section-heading"><h2>👥 Team</h2>'
        '<p>Built with passion at a healthcare hackathon</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="team-grid" style="max-width:820px;margin:0 auto;">'
        '<div class="team-card"><div class="tm-avatar">👨‍💻</div>'
        '<div class="tm-name">Rohith G</div><div class="tm-role">Lead Developer</div></div>'
        '<div class="team-card"><div class="tm-avatar">🧬</div>'
        '<div class="tm-name">Lab Agent</div><div class="tm-role">AI Assistant</div></div>'
        '<div class="team-card"><div class="tm-avatar">🏥</div>'
        '<div class="tm-name">Open Source</div><div class="tm-role">Community</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    _render_footer()


# ──────────────────────────────────────────────────────────────────────
# Main entry
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Inject theme CSS
    st.markdown(_build_css(), unsafe_allow_html=True)

    # Render navbar
    _render_navbar()

    # Route pages
    page = st.session_state.page
    if page == "Analyze":
        _page_analyze()
    elif page == "About":
        _page_about()
    else:
        _page_home()


if __name__ == "__main__":
    main()
