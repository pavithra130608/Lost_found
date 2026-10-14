import streamlit as st
import os
from datetime import date

from ai.item_match import find_item_matches
from ai.storage import add_item, load_items, save_items, update_item_status
from ai.image_match import (
    find_image_matches,
    save_uploaded_image
)
from ai.smart_match import (
    get_smart_match_explanation,
    render_smart_match_html,
    render_smart_match_summary_html,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Lost & Found",
    page_icon="🔎",
    layout="wide"
)


# =========================================================
# FILE PATHS
# =========================================================

LOST_FILE = "data/lost_items.json"
FOUND_FILE = "data/found_items.json"


# =========================================================
# MATCHING FUNCTIONS
# =========================================================

def get_matches_for_lost(lost_item, found_items):
    """Return credible, unclaimed found reports for one lost item."""

    return find_item_matches(lost_item, found_items)[0]


def count_all_matches(lost_items, found_items):
    """Count all possible matches."""

    count = 0

    for lost in lost_items:

        matches = get_matches_for_lost(
            lost,
            found_items
        )

        count += len(matches)

    return count


# =========================================================
# CUSTOM CSS
# =========================================================
st.html(
    """<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ============================================
   DESIGN TOKENS — CLEAN MODERN LIGHT THEME
============================================ */
:root {
    --bg-primary:   #f8fafc;
    --bg-secondary: #ffffff;
    --bg-card:      #ffffff;
    --bg-glass:     rgba(255, 255, 255, 0.9);
    --border:       #e2e8f0;
    --border-hover: #cbd5e1;

    --accent-primary:      #2563eb;
    --accent-primary-hover:#1d4ed8;
    --accent-sky:          #0284c7;
    --accent-amber:        #d97706;
    --accent-emerald:      #059669;
    --accent-purple:       #7c3aed;

    --text-primary:  #0f172a;
    --text-secondary:#475569;
    --text-muted:    #64748b;

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 22px;

    --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
    --shadow-md: 0 4px 14px -1px rgba(15, 23, 42, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.04);
    --shadow-lg: 0 12px 28px -4px rgba(15, 23, 42, 0.1), 0 4px 10px -2px rgba(15, 23, 42, 0.04);
    --shadow-glow-blue: 0 4px 18px rgba(37, 99, 235, 0.18);
}

/* ============================================
   BASE / RESET
============================================ */
html, body, .stApp,
[data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary);
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

[data-testid="stAppViewContainer"] .main .block-container {
    max-width: 1340px;
    padding: 1.5rem 2.5rem 4rem;
}

/* ============================================
   SIDEBAR — CLEAN MINIMALIST WHITE
============================================ */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 2px 0 16px rgba(15, 23, 42, 0.03);
}

/* Sidebar logo/title */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] [data-testid="stHeading"] h1 {
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    font-size: 1.35rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.02em;
    margin-bottom: 0 !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 0.77rem !important;
    line-height: 1.55;
}

[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 0.75rem 0;
}

/* Sidebar nav menu buttons */
[data-testid="stSidebar"] [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 0.35rem !important;
    width: 100% !important;
}

/* Base style for all navigation items */
[data-testid="stSidebar"] [role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    box-sizing: border-box !important;
    border-radius: var(--radius-md) !important;
    padding: 0.65rem 0.95rem !important;
    margin: 0 !important;
    background: #ffffff !important;
    border: 1px solid #f1f5f9 !important;
    color: #475569 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: all 180ms ease !important;
    cursor: pointer !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02) !important;
}

/* Hover state */
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: #f8fafc !important;
    border-color: #cbd5e1 !important;
    color: #0f172a !important;
    transform: translateX(3px) !important;
}

/* Hide the circular radio dot */
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
    display: none !important;
}

/* Selected nav item */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked),
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
    border-left: 4px solid #2563eb !important;
    color: #1d4ed8 !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1) !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] p {
    color: #1d4ed8 !important;
    font-weight: 600 !important;
}

/* ============================================
   TYPOGRAPHY
============================================ */
h1, h2, h3, h4, h5 {
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
}

[data-testid="stHeading"] h1 {
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    line-height: 1.2 !important;
}

[data-testid="stHeading"] h2 {
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

[data-testid="stHeading"] h3 {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

p, li {
    color: var(--text-secondary);
    line-height: 1.65;
    font-size: 0.93rem;
}

/* ============================================
   HERO BANNER
============================================ */
.home-hero {
    background: linear-gradient(135deg, #ffffff 0%, #eff6ff 60%, #e0f2fe 100%);
    border: 1px solid #dbeafe;
    border-radius: var(--radius-xl);
    padding: 2.5rem 2.8rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-md), var(--shadow-glow-blue);
}

.home-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(37, 99, 235, 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.home-hero::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(2, 132, 199, 0.07) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.main-title {
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    color: #0f172a;
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

.eyebrow {
    font-family: 'Inter', sans-serif;
    color: #2563eb;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
    position: relative;
    z-index: 1;
}

.subtitle {
    color: #475569;
    font-size: 1rem;
    margin: 0;
    position: relative;
    z-index: 1;
}

/* ============================================
   ACTION CARDS
============================================ */
.action-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    min-height: 148px;
    margin-bottom: 0.7rem;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: transform 200ms ease, border-color 200ms ease, box-shadow 200ms ease;
}

.action-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #f59e0b, #d97706);
    border-radius: 4px 0 0 4px;
}

.action-card.found::before {
    background: linear-gradient(180deg, #10b981, #059669);
}

.action-card:hover {
    transform: translateY(-2px);
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
}

.action-card h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-primary) !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    margin: 0 0 0.5rem !important;
    -webkit-text-fill-color: var(--text-primary) !important;
}

.action-card p {
    color: var(--text-secondary);
    line-height: 1.55;
    margin: 0;
    font-size: 0.88rem;
}

/* ============================================
   SECTION TITLES
============================================ */
.section-title {
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    color: var(--text-primary);
    font-size: 1.4rem;
    font-weight: 700;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ============================================
   METRICS
============================================ */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1.1rem 1.3rem !important;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm) !important;
    transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}

[data-testid="stMetric"]::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #2563eb, #38bdf8);
    border-radius: 3px 3px 0 0;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md) !important;
    border-color: #cbd5e1 !important;
}

[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
    -webkit-text-fill-color: var(--text-primary) !important;
}

/* ============================================
   CONTAINERS / CARDS
============================================ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: border-color 200ms ease, box-shadow 200ms ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #93c5fd !important;
    box-shadow: var(--shadow-md) !important;
}

/* ============================================
   FORMS & INPUTS
============================================ */
[data-testid="stForm"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.6rem 1.8rem !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Inputs */
input, textarea {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    transition: border-color 180ms ease, box-shadow 180ms ease !important;
}

input:focus, textarea:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    outline: none !important;
}

input::placeholder, textarea::placeholder {
    color: var(--text-muted) !important;
}

/* Select / dropdown */
[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

[data-baseweb="select"] svg {
    fill: var(--text-secondary) !important;
}

/* Labels */
[data-testid="stForm"] label,
label[data-testid] {
    color: #334155 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

/* File uploader */
[data-testid="stFileUploader"] section {
    background: #f8fafc !important;
    border: 1px dashed #cbd5e1 !important;
    border-radius: var(--radius-md) !important;
    transition: background 180ms ease, border-color 180ms ease;
}

[data-testid="stFileUploader"] section:hover {
    background: #f1f5f9 !important;
    border-color: #94a3b8 !important;
}

/* ============================================
   BUTTONS
============================================ */
.stButton > button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stFileUploader"] button {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: var(--radius-sm) !important;
    color: #1e293b !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    min-height: 2.7rem !important;
    letter-spacing: 0.01em;
    box-shadow: var(--shadow-sm) !important;
    transition: all 180ms ease !important;
}

.stButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stFileUploader"] button:hover {
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
    transform: translateY(-1px) !important;
}

/* Primary buttons */
[data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border-color: transparent !important;
    color: #ffffff !important;
    box-shadow: 0 2px 10px rgba(37, 99, 235, 0.28) !important;
    font-weight: 700 !important;
}

[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.38) !important;
    transform: translateY(-1px) !important;
    color: #ffffff !important;
}

/* ============================================
   EXPANDERS
============================================ */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--text-primary) !important;
}

/* ============================================
   ALERTS / INFO BOXES
============================================ */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    font-size: 0.88rem !important;
}

[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
    background: #eff6ff !important;
    border-color: #bfdbfe !important;
    color: #1e40af !important;
}

[data-testid="stAlert"][data-baseweb="notification"][kind="success"] {
    background: #ecfdf5 !important;
    border-color: #a7f3d0 !important;
    color: #065f46 !important;
}

[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
    background: #fffbeb !important;
    border-color: #fde68a !important;
    color: #92400e !important;
}

[data-testid="stAlert"][data-baseweb="notification"][kind="error"] {
    background: #fef2f2 !important;
    border-color: #fecaca !important;
    color: #991b1b !important;
}

/* ============================================
   DIVIDERS
============================================ */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ============================================
   LINKS
============================================ */
[data-testid="stMarkdownContainer"] a {
    color: var(--accent-primary) !important;
    text-decoration: none !important;
}

[data-testid="stMarkdownContainer"] a:hover {
    color: var(--accent-primary-hover) !important;
    text-decoration: underline !important;
}

/* ============================================
   SCROLLBAR
============================================ */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #f1f5f9;
}
::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}

/* ============================================
   STATUS BADGES
============================================ */
.status-lost {
    padding: 4px 12px;
    border-radius: 99px;
    background: #fef3c7;
    border: 1px solid #fde68a;
    color: #b45309;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-block;
}

.status-found {
    padding: 4px 12px;
    border-radius: 99px;
    background: #d1fae5;
    border: 1px solid #a7f3d0;
    color: #065f46;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-block;
}

.status-claimed {
    padding: 4px 12px;
    border-radius: 99px;
    background: #ede9fe;
    border: 1px solid #ddd6fe;
    color: #6b21a8;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-block;
}

/* ============================================
   CAPTIONS / SMALL TEXT
============================================ */
[data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
}

/* ============================================
   IMAGE
============================================ */
[data-testid="stImage"] img {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
}

/* ============================================
   SELECTBOX / DROPDOWN
============================================ */
[data-baseweb="popover"] ul {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-md) !important;
}

[data-baseweb="popover"] li {
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
}

[data-baseweb="popover"] li:hover {
    background: #f1f5f9 !important;
    color: var(--accent-primary) !important;
}

/* ============================================
   ACTIVITY FEED & MATCH CARDS
============================================ */
.activity-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow-sm);
    transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.activity-card:hover {
    transform: translateY(-2px);
    border-color: #93c5fd;
    box-shadow: var(--shadow-md);
}

.activity-left {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.activity-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: #0f172a;
}

.activity-meta {
    font-size: 0.8rem;
    color: #475569;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.2rem;
}

.activity-date {
    font-size: 0.82rem;
    color: #64748b;
    font-weight: 500;
}

.meta-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.55rem;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 0.78rem;
    color: #475569;
}

.score-badge {
    padding: 0.35rem 0.75rem;
    border-radius: 99px;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: -0.01em;
    display: inline-block;
}
.score-high {
    background: #d1fae5;
    border: 1px solid #a7f3d0;
    color: #065f46;
}
.score-med {
    background: #fef3c7;
    border: 1px solid #fde68a;
    color: #b45309;
}
.score-low {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    color: #64748b;
}
</style>"""
)


# =========================================================
# SIDEBAR
# =========================================================

NAV_PAGES = [
    "Home",
    "Report Lost",
    "Report Found",
    "Possible Matches",
    "Image Search",
    "Reports"
]

if "nav_page" not in st.session_state or st.session_state.nav_page not in NAV_PAGES:
    st.session_state.nav_page = "Home"

st.sidebar.title("🔎 AI Lost & Found")

st.sidebar.caption(
    "Find what you've lost. Return what you've found."
)

st.sidebar.divider()

NAV_ICONS = {
    "Home": "🏠  Home",
    "Report Lost": "📢  Report Lost",
    "Report Found": "📦  Report Found",
    "Possible Matches": "🎯  Possible Matches",
    "Image Search": "🖼️  Image Search",
    "Reports": "📊  Reports"
}

def on_nav_change():
    st.session_state.nav_page = st.session_state.sidebar_nav_selection

page = st.sidebar.radio(
    "Navigation",
    NAV_PAGES,
    index=NAV_PAGES.index(st.session_state.nav_page),
    format_func=lambda x: NAV_ICONS.get(x, x),
    key="sidebar_nav_selection",
    on_change=on_nav_change
)

st.sidebar.caption(
    "Match ratings rank candidates; they are not proof of ownership."
)

st.sidebar.divider()

st.sidebar.caption(
    "Item type and report details are used to rank candidates."
)


# =========================================================
# HOME
# =========================================================

if page == "Home":

    lost_items = load_items(LOST_FILE)
    found_items = load_items(FOUND_FILE)

    active_found = [
        item
        for item in found_items
        if str(item.get("status", "Found")).strip().casefold() != "claimed"
    ]

    claimed_items = [
        item
        for item in found_items
        if str(item.get("status", "")).strip().casefold() == "claimed"
    ]

    total_matches = count_all_matches(
        lost_items,
        found_items
    )

    # =====================================================
    # HERO
    # =====================================================

    st.markdown(
        '<div class="home-hero">'
        '<div class="eyebrow">Campus item recovery</div>'
        '<div class="main-title">🔎 AI Lost &amp; Found</div>'
        '<div class="subtitle">Find what you\'ve lost. Return what you\'ve found.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # QUICK ACTIONS
    # =====================================================

    st.markdown(
        '<div class="section-title">What would you like to do?</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="action-card lost">
                <h3>📢 I Lost Something</h3>
                <p>
                    Report an item you lost and let the
                    system look for possible matches.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "📢 Report Lost Item",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.nav_page = "Report Lost"
            st.rerun()

    with col2:

        st.markdown(
            """
            <div class="action-card found">
                <h3>📦 I Found Something</h3>
                <p>
                    Report an item you found so its owner
                    can discover it.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "📦 Report Found Item",
            use_container_width=True
        ):
            st.session_state.nav_page = "Report Found"
            st.rerun()

    st.divider()

    # =====================================================
    # STATISTICS
    # =====================================================

    st.markdown(
        '<div class="section-title">📊 Current Activity</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📢 Lost",
            len(lost_items)
        )

    with col2:

        st.metric(
            "📦 Found",
            len(active_found)
        )

    with col3:

        st.metric(
            "🎯 Possible Matches",
            total_matches
        )

    with col4:

        st.metric(
            "✅ Claimed",
            len(claimed_items)
        )

    st.divider()

    # =====================================================
    # POSSIBLE MATCHES
    # =====================================================

    st.markdown(
        '<div class="section-title">🎯 Possible Matches</div>',
        unsafe_allow_html=True
    )

    all_matches = []

    for lost in lost_items:

        matches = get_matches_for_lost(
            lost,
            found_items
        )

        for match in matches:

            all_matches.append({
                "lost": lost,
                "match": match
            })

    all_matches.sort(
        key=lambda x: x["match"]["score"],
        reverse=True
    )

    if not all_matches:

        st.success(
            "No possible matches right now."
        )

        st.write(
            "When a matching found item is reported, "
            "it will appear here automatically."
        )

    else:

        st.write(
            "We found items that may correspond to "
            "reported lost items."
        )

        # Display only top 3 on dashboard
        for index, item_data in enumerate(
            all_matches[:3]
        ):

            lost = item_data["lost"]
            match = item_data["match"]
            found = match["found"]
            score = match["score"]
            score_cls = "score-high" if score >= 70 else ("score-med" if score >= 45 else "score-low")

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [2.5, 2.5, 1.3]
                )

                with col1:

                    st.markdown(
                        "#### 📢 Reported Lost"
                    )

                    st.markdown(
                        f"**{lost.get('item_type', 'Item')}**"
                    )

                    st.markdown(
                        f'<span class="meta-chip">📍 {lost.get("location", "Unknown")}</span> '
                        f'<span class="meta-chip">📅 {lost.get("date", "Unknown")}</span>',
                        unsafe_allow_html=True
                    )

                with col2:

                    st.markdown(
                        "#### 📦 Found Candidate"
                    )

                    st.markdown(
                        f"**{found.get('item_type', 'Item')}**"
                    )

                    st.markdown(
                        f'<span class="meta-chip">📍 {found.get("location", "Unknown")}</span> '
                        f'<span class="meta-chip">📅 {found.get("date", "Unknown")}</span>',
                        unsafe_allow_html=True
                    )

                with col3:

                    st.markdown(
                        f'<div style="text-align: right; margin-top: 0.5rem;">'
                        f'<span class="score-badge {score_cls}">🎯 {score:.0f}% Match</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    is_claimed = str(found.get("status", "")).strip().casefold() == "claimed"
                    status_badge = (
                        '<span class="status-claimed">CLAIMED</span>'
                        if is_claimed
                        else '<span class="status-found">AVAILABLE</span>'
                    )
                    st.markdown(
                        f'<div style="text-align: right; margin-top: 0.5rem;">{status_badge}</div>',
                        unsafe_allow_html=True
                    )

                explanation = get_smart_match_explanation(lost, found, match)
                st.caption(f"💡 **AI Match Analysis:** {explanation['summary']}")

    if len(all_matches) > 3:

        st.caption(
            f"{len(all_matches) - 3} more possible "
            "match(es) available."
        )

    st.divider()

    # =====================================================
    # RECENT ACTIVITY
    # =====================================================

    st.markdown(
        '<div class="section-title">🕒 Recent Activity</div>',
        unsafe_allow_html=True
    )

    recent_items = []

    for item in lost_items:

        recent_items.append({
            "type": "lost",
            "item": item
        })

    for item in found_items:

        recent_items.append({
            "type": "found",
            "item": item
        })

    # Sort by date where possible
    recent_items.sort(
        key=lambda x: x["item"].get("date", ""),
        reverse=True
    )

    if not recent_items:

        st.info(
            "No reports have been submitted yet."
        )

    else:

        for activity in recent_items[:6]:

            item = activity["item"]
            item_type = item.get("item_type", "Item")
            location = item.get("location") or "Campus"
            item_date = item.get("date") or "Recently"

            if activity["type"] == "lost":
                badge_html = '<span class="status-lost">📢 LOST</span>'
                reporter = item.get("name")
                desc_text = f"Reported by {reporter}" if reporter else "Reported lost"
            else:
                status = str(item.get("status", "Found")).strip().casefold()
                if status == "claimed":
                    badge_html = '<span class="status-claimed">✅ CLAIMED</span>'
                    desc_text = "Item returned to owner"
                else:
                    badge_html = '<span class="status-found">📦 FOUND</span>'
                    reporter = item.get("name")
                    desc_text = f"Reported by {reporter}" if reporter else "Reported found"

            card_html = (
                f'<div class="activity-card">'
                f'<div class="activity-left">'
                f'{badge_html}'
                f'<div>'
                f'<div class="activity-title">{item_type}</div>'
                f'<div class="activity-meta">'
                f'<span class="meta-chip">📍 {location}</span>'
                f'<span>{desc_text}</span>'
                f'</div>'
                f'</div>'
                f'</div>'
                f'<div class="activity-date">📅 {item_date}</div>'
                f'</div>'
            )
            st.html(card_html)


# =========================================================
# REPORT LOST
# =========================================================

elif page == "Report Lost":

    if "lost_form_version" not in st.session_state:
        st.session_state.lost_form_version = 0

    if st.session_state.get("lost_success_msg"):
        success_message = st.session_state.pop("lost_success_msg")
        st.success(f"✅ {success_message}")
        st.toast(success_message, icon="✅")

    lost_ver = st.session_state.lost_form_version

    st.title("📢 Report Lost Item")

    st.write(
        "Tell us about the item you lost."
    )

    st.divider()

    with st.form(f"lost_item_form_{lost_ver}"):

        col1, col2 = st.columns(2)

        with col1:

            item_type = st.selectbox(
                "Item Type",
                [
                    "Backpack",
                    "Wallet",
                    "Phone",
                    "Keys",
                    "ID Card",
                    "Laptop",
                    "Bottle",
                    "Book",
                    "Other"
                ],
                key=f"lost_item_type_{lost_ver}"
            )

            custom_item_type = st.text_input(
                "If you selected Other, what item is it?",
                placeholder="Type the item name",
                key=f"lost_custom_item_type_{lost_ver}"
            )

            color = st.text_input(
                "Color",
                placeholder="Example: Black",
                key=f"lost_color_{lost_ver}"
            )

            brand = st.text_input(
                "Brand",
                placeholder="Example: Nike",
                key=f"lost_brand_{lost_ver}"
            )

            location = st.selectbox(
                "Where did you lose it?",
                [
                    "Library",
                    "Canteen",
                    "Block A",
                    "Block B",
                    "Auditorium",
                    "Parking",
                    "Classroom",
                    "Other"
                ],
                key=f"lost_location_{lost_ver}"
            )

            custom_location = st.text_input(
                "If you selected Other, where was it lost?",
                placeholder="Type the location",
                key=f"lost_custom_location_{lost_ver}"
            )

        with col2:

            lost_date = st.date_input(
                "Date Lost",
                value=date.today(),
                key=f"lost_date_{lost_ver}"
            )

            name = st.text_input(
                "Your Name",
                placeholder="Enter your name",
                key=f"lost_name_{lost_ver}"
            )

            phone = st.text_input(
                "Phone Number",
                placeholder="Enter your phone number",
                key=f"lost_phone_{lost_ver}"
            )

            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                key=f"lost_email_{lost_ver}"
            )

            class_details = st.text_input(
                "Class Details",
                placeholder="Example: B.Sc Computer Science, Year 2",
                key=f"lost_class_details_{lost_ver}"
            )

            description = st.text_area(
                "Description",
                placeholder=(
                    "Describe the item in detail..."
                ),
                height=150,
                key=f"lost_description_{lost_ver}"
            )

            item_image = st.file_uploader(
                "Item Photo (optional)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"lost_item_photo_{lost_ver}"
            )

        submitted = st.form_submit_button(
            "📢 Submit Lost Report",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not phone.strip():

            st.warning(
                "Please enter your phone number."
            )

        elif not email.strip() or "@" not in email.strip():

            st.warning(
                "Please enter a valid email address."
            )

        elif item_type == "Other" and not custom_item_type.strip():

            st.warning(
                "Please type what kind of item you lost."
            )

        elif location == "Other" and not custom_location.strip():

            st.warning(
                "Please type where you lost the item."
            )

        elif not class_details.strip():

            st.warning(
                "Please enter your class details."
            )

        elif not description.strip():

            st.warning(
                "Please enter a description."
            )

        else:

            resolved_type = (
                custom_item_type.strip()
                if item_type == "Other"
                else item_type
            )
            resolved_location = (
                custom_location.strip()
                if location == "Other"
                else location
            )

            candidate_item = {
                "item_type": resolved_type,
                "color": color.strip(),
                "brand": brand.strip(),
                "location": resolved_location,
                "date": str(lost_date),
                "name": name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "class_details": class_details.strip(),
                "description": description.strip(),
                "status": "Lost"
            }

            image_save_failed = False
            image_path = ""
            if item_image is not None:
                try:
                    image_path = save_uploaded_image(item_image)
                except ValueError as error:
                    st.error(str(error))
                    image_save_failed = True
                except Exception as error:
                    st.error(f"Failed to process image: {error}")
                    image_save_failed = True

            if not image_save_failed:
                candidate_item["image_path"] = image_path
                try:
                    add_item(
                        LOST_FILE,
                        candidate_item
                    )
                except Exception as error:
                    st.error(f"Failed to save report: {error}")
                else:
                    st.session_state.lost_success_msg = "Lost item reported successfully!"
                    st.session_state.lost_form_version = lost_ver + 1
                    st.rerun()


# =========================================================
# REPORT FOUND
# =========================================================

elif page == "Report Found":

    if "found_form_version" not in st.session_state:
        st.session_state.found_form_version = 0

    if st.session_state.get("found_success_msg"):
        success_message = st.session_state.pop("found_success_msg")
        st.success(f"✅ {success_message}")
        st.toast(success_message, icon="✅")

    found_ver = st.session_state.found_form_version

    st.title("📦 Report Found Item")

    st.write(
        "Tell us about the item you found."
    )

    st.divider()

    with st.form(f"found_item_form_{found_ver}"):

        col1, col2 = st.columns(2)

        with col1:

            item_type = st.selectbox(
                "Item Type",
                [
                    "Backpack",
                    "Wallet",
                    "Phone",
                    "Keys",
                    "ID Card",
                    "Laptop",
                    "Bottle",
                    "Book",
                    "Other"
                ],
                key=f"found_item_type_{found_ver}"
            )

            custom_item_type = st.text_input(
                "If you selected Other, what item is it?",
                placeholder="Type the item name",
                key=f"found_custom_item_type_{found_ver}"
            )

            color = st.text_input(
                "Color",
                placeholder="Example: Black",
                key=f"found_color_{found_ver}"
            )

            brand = st.text_input(
                "Brand",
                placeholder="Example: Nike",
                key=f"found_brand_{found_ver}"
            )

            location = st.selectbox(
                "Where did you find it?",
                [
                    "Library",
                    "Canteen",
                    "Block A",
                    "Block B",
                    "Auditorium",
                    "Parking",
                    "Classroom",
                    "Other"
                ],
                key=f"found_location_{found_ver}"
            )

            custom_location = st.text_input(
                "If you selected Other, where was it found?",
                placeholder="Type the location",
                key=f"found_custom_location_{found_ver}"
            )

        with col2:

            found_date = st.date_input(
                "Date Found",
                value=date.today(),
                key=f"found_date_{found_ver}"
            )

            name = st.text_input(
                "Your Name",
                placeholder="Enter your name",
                key=f"found_name_{found_ver}"
            )

            phone = st.text_input(
                "Phone Number",
                placeholder="Enter your phone number",
                key=f"found_phone_{found_ver}"
            )

            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                key=f"found_email_{found_ver}"
            )

            class_details = st.text_input(
                "Class Details",
                placeholder="Example: B.Sc Computer Science, Year 2",
                key=f"found_class_details_{found_ver}"
            )

            description = st.text_area(
                "Description",
                placeholder=(
                    "Describe the item and where you found it..."
                ),
                height=150,
                key=f"found_description_{found_ver}"
            )

            item_image = st.file_uploader(
                "Item Photo (optional)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"found_item_photo_{found_ver}"
            )

        submitted = st.form_submit_button(
            "📦 Submit Found Report",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not phone.strip():

            st.warning(
                "Please enter your phone number."
            )

        elif not email.strip() or "@" not in email.strip():

            st.warning(
                "Please enter a valid email address."
            )

        elif item_type == "Other" and not custom_item_type.strip():

            st.warning(
                "Please type what kind of item you found."
            )

        elif location == "Other" and not custom_location.strip():

            st.warning(
                "Please type where you found the item."
            )

        elif not class_details.strip():

            st.warning(
                "Please enter your class details."
            )

        elif not description.strip():

            st.warning(
                "Please enter a description."
            )

        else:

            resolved_type = (
                custom_item_type.strip()
                if item_type == "Other"
                else item_type
            )
            resolved_location = (
                custom_location.strip()
                if location == "Other"
                else location
            )

            candidate_item = {
                "item_type": resolved_type,
                "color": color.strip(),
                "brand": brand.strip(),
                "location": resolved_location,
                "date": str(found_date),
                "name": name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "class_details": class_details.strip(),
                "description": description.strip(),
                "status": "Found"
            }

            image_save_failed = False
            image_path = ""
            if item_image is not None:
                try:
                    image_path = save_uploaded_image(item_image)
                except ValueError as error:
                    st.error(str(error))
                    image_save_failed = True
                except Exception as error:
                    st.error(f"Failed to process image: {error}")
                    image_save_failed = True

            if not image_save_failed:
                candidate_item["image_path"] = image_path
                try:
                    add_item(
                        FOUND_FILE,
                        candidate_item
                    )
                except Exception as error:
                    st.error(f"Failed to save report: {error}")
                else:
                    st.session_state.found_success_msg = "Found item reported successfully!"
                    st.session_state.found_form_version = found_ver + 1
                    st.rerun()


# =========================================================
# POSSIBLE MATCHES
# =========================================================

elif page == "Possible Matches":

    st.title("🎯 Possible Matches")

    st.caption(
        "Candidates require compatible item types and supporting identity details. "
        "A match rating ranks the criteria; it is not proof of ownership."
    )

    st.write(
        "Check items that may correspond to something "
        "you reported as lost."
    )

    st.divider()

    lost_items = load_items(LOST_FILE)
    found_items = load_items(FOUND_FILE)

    available_found_items = [
        item for item in found_items
        if str(item.get("status", "Found")).strip().casefold() != "claimed"
    ]

    if not lost_items:

        st.info(
            "No lost items have been reported yet."
        )

    elif not available_found_items:

        st.info(
            "There are no available found items yet."
        )

    else:

        # =================================================
        # SELECT LOST ITEM
        # =================================================

        lost_options = []

        for lost in lost_items:

            label = (
                f"ID {lost.get('id')} | "
                f"{lost.get('item_type', '')} | "
                f"{lost.get('color', '')} | "
                f"{lost.get('location', '')}"
            )

            lost_options.append(label)

        selected_lost = st.selectbox(
            "Select a lost item",
            lost_options
        )

        selected_index = lost_options.index(
            selected_lost
        )

        selected_lost_item = lost_items[
            selected_index
        ]

        # =================================================
        # SELECTED LOST ITEM
        # =================================================

        with st.container(border=True):

            st.markdown(
                "### 📢 Your Lost Item"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Type:** "
                    f"{selected_lost_item.get('item_type', '')}"
                )

                st.write(
                    f"**Color:** "
                    f"{selected_lost_item.get('color', '')}"
                )

                st.write(
                    f"**Brand:** "
                    f"{selected_lost_item.get('brand', '')}"
                )

            with col2:

                st.write(
                    f"**Location:** "
                    f"{selected_lost_item.get('location', '')}"
                )

                st.write(
                    f"**Date:** "
                    f"{selected_lost_item.get('date', '')}"
                )

                st.write(
                    f"**Description:** "
                    f"{selected_lost_item.get('description', '')}"
                )

        st.divider()

        # =================================================
        # FIND MATCHES
        # =================================================

        matches, rejected = find_item_matches(
            selected_lost_item,
            available_found_items
        )

        if not matches:

            st.warning(
                "No credible matches were found."
            )

            st.write(
                "Found reports with incompatible item types or no supporting "
                "identity details are not shown as candidates."
            )

        else:

            st.subheader(
                f"🔎 {len(matches)} Possible Match"
                + ("es" if len(matches) != 1 else "")
            )

            show_reporter_contact = st.checkbox(
                "Show found reporter contact details",
                value=False,
                key="show_found_reporter_contact",
            )

            for match_index, match in enumerate(matches):
                found = match["found"]
                explanation = get_smart_match_explanation(selected_lost_item, found, match)

                with st.container(border=True):
                    header_col, score_col = st.columns([3, 1])
                    with header_col:
                        st.subheader(f"📦 {found.get('item_type', 'Item')} Candidate (Report #{found.get('id', '')})")
                    with score_col:
                        st.metric("Match rating", f"{match['score']:.0f}/100")
                        st.success("Available")

                    # Smart Match Summary
                    st.markdown(
                        render_smart_match_summary_html(explanation),
                        unsafe_allow_html=True,
                    )

                    image_path = found.get("image_path")
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, width=220)

                    # Attribute Comparison Breakdown Table
                    st.markdown("#### 📋 Attribute Comparison")
                    st.markdown(render_smart_match_html(explanation), unsafe_allow_html=True)

                    # System matching criteria notes
                    with st.expander("📝 System Evaluation Notes", expanded=False):
                        for reason in match["reasons"]:
                            st.write(f"- {reason}")

                    if show_reporter_contact:
                        st.markdown("#### 👤 Reporter Contact")
                        st.write(f"**Reported by:** {found.get('name') or 'Not provided'}")
                        st.write(f"**Phone:** {found.get('phone') or 'Not provided'}")
                        st.write(f"**Email:** {found.get('email') or 'Not provided'}")

                    if st.button(
                        "Claim This Item",
                        key=f"claim_{found.get('id')}_{match_index}",
                        use_container_width=True,
                    ):
                        success = update_item_status(
                            FOUND_FILE,
                            found.get("id"),
                            "Claimed",
                        )
                        if success:
                            st.success("Item marked as claimed.")
                            st.rerun()
                        else:
                            st.error("Unable to update the item.")

        if rejected:
            with st.expander(f"Why {len(rejected)} other report(s) were rejected"):
                for entry in rejected:
                    found = entry["found"]
                    st.markdown(
                        f"**Report {found.get('id', 'unknown')}: "
                        f"{found.get('item_type', 'Item')}**"
                    )
                    for reason in entry["reasons"]:
                        st.write(f"- {reason}")


# =========================================================
# IMAGE SEARCH
# =========================================================

elif page == "Image Search":

    st.title("🖼️ Image Search")

    st.write(
        "Upload a photo to find visually similar reported items."
    )

    uploaded_image = st.file_uploader(
        "Photo to search for",
        type=["jpg", "jpeg", "png", "webp"],
        key="image_search_upload"
    )

    minimum_similarity = st.slider(
        "Minimum visual similarity",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
        format="%d%%"
    )

    if uploaded_image is not None:

        st.image(
            uploaded_image,
            caption="Search photo",
            width=280
        )

        if st.button("🔎 Search Reports", type="primary"):

            lost_matches = find_image_matches(
                uploaded_image.getvalue(),
                load_items(LOST_FILE)
            )

            found_candidates = [
                item
                for item in load_items(FOUND_FILE)
                if str(item.get("status", "Found")).strip().casefold() != "claimed"
            ]
            found_matches = find_image_matches(
                uploaded_image.getvalue(),
                found_candidates
            )

            lost_matches = [
                match
                for match in lost_matches
                if match["score"] >= minimum_similarity
            ]
            found_matches = [
                match
                for match in found_matches
                if match["score"] >= minimum_similarity
            ]

            if not lost_matches and not found_matches:

                st.info(
                    "No image matches met that similarity level. "
                    "Try lowering the minimum or upload a clearer photo."
                )

            else:

                for group_title, matches in (
                    ("Lost Report Matches", lost_matches),
                    ("Found Report Matches", found_matches)
                ):

                    st.subheader(
                        f"{group_title} ({len(matches)})"
                    )

                    if not matches:
                        st.info(
                            f"No {group_title.lower()} met that similarity level."
                        )
                        continue

                    for match in matches:

                        item = match["item"]

                        with st.container(border=True):

                            image_column, details_column = st.columns(
                                [1, 3]
                            )

                            with image_column:
                                image_path = item.get("image_path")
                                if image_path and os.path.exists(image_path):
                                    st.image(image_path, use_container_width=True)

                            with details_column:
                                st.markdown(
                                    f"### {item.get('item_type', 'Item')}"
                                )
                                st.write(
                                    f"**Visual similarity:** {match['score']}%"
                                )
                                st.write(
                                    f"**Report ID:** {item.get('id', '')}"
                                )
                                st.write(
                                    f"**Color:** {item.get('color') or 'Not specified'}"
                                )
                                st.write(
                                    f"**Brand:** {item.get('brand') or 'Not specified'}"
                                )
                                st.write(
                                    f"**Location:** {item.get('location', '')}"
                                )
                                st.write(
                                    f"**Date:** {item.get('date', '')}"
                                )
                                st.write(
                                    f"**Description:** {item.get('description', '')}"
                                )
                                st.write(
                                    f"**Reported by:** {item.get('name') or 'Not provided'}"
                                )
                                st.write(
                                    f"**Class:** {item.get('class_details') or 'Not provided'}"
                                )


# =========================================================
# REPORTS
# =========================================================

elif page == "Reports":

    st.title("📋 Reports")

    st.write(
        "View all lost and found reports in the system."
    )

    st.divider()

    lost_items = load_items(LOST_FILE)
    found_items = load_items(FOUND_FILE)

    # =====================================================
    # SUMMARY
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "📢 Lost Reports",
            len(lost_items)
        )

    with col2:

        st.metric(
            "📦 Found Reports",
            len(found_items)
        )

    with col3:

        claimed_count = sum(
            1
            for item in found_items
            if str(item.get("status", "")).strip().casefold() == "claimed"
        )

        st.metric(
            "✅ Claimed",
            claimed_count
        )

    st.divider()

    # =====================================================
    # LOST REPORTS
    # =====================================================

    st.subheader(f"📢 Lost Reports · {len(lost_items)}")

    if not lost_items:

        st.info(
            "No lost reports available."
        )

    else:

        for lost in lost_items:

            with st.expander(
                f"📢 {lost.get('item_type', 'Item')} · "
                f"{lost.get('location') or 'Location not provided'} · "
                f"{lost.get('date') or 'Date not provided'}",
                expanded=False,
            ):

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    image_path = lost.get("image_path")
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, width=220)

                    st.markdown("#### Item details")
                    detail_columns = st.columns(3)
                    lost_details = [
                        ("Report ID", lost.get("id", "")),
                        ("Color", lost.get("color") or "Not specified"),
                        ("Brand", lost.get("brand") or "Not specified"),
                        ("Location", lost.get("location") or "Not specified"),
                        ("Date", lost.get("date") or "Not specified"),
                        ("Reported by", lost.get("name") or "Not provided"),
                    ]
                    for detail_index, (label, value) in enumerate(lost_details):
                        with detail_columns[detail_index % len(detail_columns)]:
                            st.caption(label)
                            st.write(value)

                    st.markdown("#### Class details")
                    st.write(lost.get("class_details") or "Not provided")
                    st.markdown("#### Description")
                    st.write(lost.get("description") or "Not provided")

                with col2:

                    st.markdown(
                        "#### Status"
                    )

                    st.warning(
                        "📢 Lost"
                    )

                    matches = get_matches_for_lost(
                        lost,
                        found_items
                    )

                    if matches:

                        st.info(
                            f"🎯 {len(matches)} "
                            "possible match(es)"
                        )

                    else:

                        st.caption(
                            "No match yet"
                        )

    # =====================================================
    # FOUND REPORTS
    # =====================================================

    st.divider()

    st.subheader(f"📦 Found Reports · {len(found_items)}")

    if not found_items:

        st.info(
            "No found reports available."
        )

    else:

        for found in found_items:

            found_status = (
                "Claimed"
                if str(found.get("status", "Found")).strip().casefold() == "claimed"
                else "Available"
            )
            with st.expander(
                f"📦 {found.get('item_type', 'Item')} · "
                f"{found.get('location') or 'Location not provided'} · "
                f"{found.get('date') or 'Date not provided'} · {found_status}",
                expanded=False,
            ):

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    image_path = found.get("image_path")
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, width=220)

                    st.markdown("#### Item details")
                    detail_columns = st.columns(3)
                    found_details = [
                        ("Report ID", found.get("id", "")),
                        ("Color", found.get("color") or "Not specified"),
                        ("Brand", found.get("brand") or "Not specified"),
                        ("Location", found.get("location") or "Not specified"),
                        ("Date", found.get("date") or "Not specified"),
                        ("Reported by", found.get("name") or "Not provided"),
                    ]
                    for detail_index, (label, value) in enumerate(found_details):
                        with detail_columns[detail_index % len(detail_columns)]:
                            st.caption(label)
                            st.write(value)

                    st.markdown("#### Class details")
                    st.write(found.get("class_details") or "Not provided")
                    st.markdown("#### Description")
                    st.write(found.get("description") or "Not provided")

                with col2:

                    st.markdown(
                        "#### Status"
                    )

                    status = found.get(
                        "status",
                        "Found"
                    )

                    if str(status).strip().casefold() == "claimed":

                        st.success(
                            "✅ Claimed"
                        )

                    else:

                        st.info(
                            "📦 Found"
                        )

                        # Check whether this found item
                        # matches any lost item

                        possible_matches = sum(
                            1
                            for lost in lost_items
                            if any(
                                match["found"].get("id") == found.get("id")
                                for match in get_matches_for_lost(lost, [found])
                            )
                        )

                        if possible_matches:

                            st.info(
                                f"🎯 {possible_matches} "
                                "possible match(es)"
                            )

                        else:

                            st.caption(
                                "No match yet"
                            )