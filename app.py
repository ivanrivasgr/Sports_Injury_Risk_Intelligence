import streamlit as st
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

st.set_page_config(
    page_title="Sports Injury Risk — Data Architecture",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Real Madrid theme: White · Purple · Gold ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Backgrounds */
.stApp { background: #F8F9FA; }
.block-container {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 2rem 2.5rem !important;
    margin-top: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    max-width: 1100px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}
section[data-testid="stSidebar"] * { color: #1A2B3C !important; }
section[data-testid="stSidebar"] .stRadio label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.04em !important;
    padding: 3px 0 !important;
}

/* Typography */
h1 { color: #0D1B2A !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
h2 { color: #0D1B2A !important; font-weight: 600 !important; }
h3 { color: #4B0082 !important; font-weight: 600 !important; }
p, li { color: #4A5568; line-height: 1.65; }
hr  { border-color: #E2E8F0 !important; }

/* Section header — gold underline accent */
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6B21A8;
    border-bottom: 2px solid #C9A84C;
    padding-bottom: 6px;
    margin-bottom: 16px;
}

/* Metric cards — gold top border */
.metric-card {
    background: #FAFAFA;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #C9A84C;
    border-radius: 6px;
    padding: 16px 18px;
    margin-bottom: 10px;
}
.metric-card h4 {
    color: #6B21A8;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0 0 6px 0;
}
.metric-card .value { color: #0D1B2A; font-size: 1.9rem; font-weight: 700; line-height: 1; }
.metric-card .sub { color: #9BA8B8; font-size: 0.72rem; margin-top: 4px; font-family: 'IBM Plex Mono', monospace; }

/* Badges */
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.06em; font-weight: 600; text-transform: uppercase;
}
.badge-real    { background: #F0FFF4; color: #2E7D32; border: 1px solid #A5D6A7; }
.badge-proxy   { background: #FFF8F0; color: #C07830; border: 1px solid #F5CFA0; }
.badge-partial { background: #F3F0FF; color: #6B21A8; border: 1px solid #D8B4FE; }

/* Warn / info boxes */
.warn-box {
    background: #FFFBEB; border-left: 3px solid #C9A84C;
    padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 12px 0;
}
.warn-box p { color: #7A5C1E; font-size: 0.83rem; margin: 0; }

.info-box {
    background: #F3F0FF; border-left: 3px solid #6B21A8;
    padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 12px 0;
}
.info-box p { color: #4B0082; font-size: 0.83rem; margin: 0; }

/* Pipeline step */
.pipe-step {
    background: #FAFAFA; border: 1px solid #E2E8F0;
    border-left: 3px solid #C9A84C;
    border-radius: 0 6px 6px 0; padding: 14px 18px; margin-bottom: 8px;
}
.pipe-step .layer-name {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.1em; text-transform: uppercase; color: #6B21A8; margin-bottom: 5px;
}
.pipe-step .layer-desc { color: #4A5568; font-size: 0.83rem; line-height: 1.5; }

/* Code */
code {
    background: #F3F0FF !important; color: #4B0082 !important;
    border: 1px solid #D8B4FE !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important; padding: 2px 6px !important; border-radius: 3px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #FAFAFA !important; color: #1A2B3C !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
    border: 1px solid #E2E8F0 !important; border-radius: 6px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.72rem !important;
}
.stTabs [aria-selected="true"] { color: #6B21A8 !important; border-bottom-color: #C9A84C !important; }

/* DataFrame — border only, let Streamlit handle internal theme */
.stDataFrame { border: 1px solid #E2E8F0 !important; border-radius: 6px !important; }

/* Selectbox dropdown — light background */
.stSelectbox > div { border-color: #E2E8F0 !important; border-radius: 6px !important; }
[data-baseweb="popover"] [role="option"] { background: #FFFFFF !important; color: #0F172A !important; }
[data-baseweb="popover"] [role="option"]:hover { background: #F1F5F9 !important; }
[data-baseweb="popover"] [aria-selected="true"] { background: #EFF6FF !important; }
[data-baseweb="menu"] { background: #FFFFFF !important; }
[data-baseweb="menu"] li { color: #0F172A !important; background: #FFFFFF !important; }

/* Expanders — visible border and spacing to distinguish items */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    background: #F8FAFC !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #F1F5F9 !important;
}
[data-testid="stExpander"][open] summary {
    border-bottom: 1px solid #E2E8F0 !important;
    background: #EFF6FF !important;
}

/* Multiselect tags — purple */
.stMultiSelect span[data-baseweb="tag"] {
    background: #F3F0FF !important; color: #4B0082 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:6px 0 18px 0; border-bottom:1px solid #E2E8F0; margin-bottom:14px;'>
        <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                    letter-spacing:0.18em; color:#9BA8B8; text-transform:uppercase;
                    margin-bottom:6px;'>PORTFOLIO PROJECT</div>
        <div style='font-size:1.05rem; font-weight:700; color:#0D1B2A; line-height:1.25;'>
            Sports Injury Risk<br>
            <span style='color:#6B21A8;'>Risk Intelligence</span>
        </div>
        <div style='font-family:IBM Plex Mono,monospace; font-size:0.58rem;
                    color:#9BA8B8; margin-top:8px;'>
            v1.0.0 · production-grade
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        [
            "00 · Overview",
            "01 · Problem Framing",
            "02 · Data Sources",
            "03 · Architecture",
            "04 · Data Model",
            "05 · Feature Engineering",
            "06 · Pipeline DAG",
            "07 · Observability",
            "08 · ML Layer",
            "09 · Limitations",
            "📊 Real Data Dashboard",
            "🔬 CI/CD & Debug",
        ],
        label_visibility="collapsed",
    )

    st.markdown("""
    <div style='margin-top:18px; padding-top:14px; border-top:1px solid #E2E8F0;
                font-family:IBM Plex Mono,monospace; font-size:0.58rem;
                color:#9BA8B8; line-height:1.6;'>
        ⚠️ Association analysis only.<br>NOT causal inference.
    </div>
    """, unsafe_allow_html=True)

# ── Routing ───────────────────────────────────────────────────────────────────
if page == "00 · Overview":
    from views import p00_overview; p00_overview.render()
elif page == "01 · Problem Framing":
    from views import p01_framing; p01_framing.render()
elif page == "02 · Data Sources":
    from views import p02_sources; p02_sources.render()
elif page == "03 · Architecture":
    from views import p03_architecture; p03_architecture.render()
elif page == "04 · Data Model":
    from views import p04_datamodel; p04_datamodel.render()
elif page == "05 · Feature Engineering":
    from views import p05_features; p05_features.render()
elif page == "06 · Pipeline DAG":
    from views import p06_dag; p06_dag.render()
elif page == "07 · Observability":
    from views import p07_observability; p07_observability.render()
elif page == "08 · ML Layer":
    from views import p08_ml; p08_ml.render()
elif page == "09 · Limitations":
    from views import p09_limitations; p09_limitations.render()
elif page == "📊 Real Data Dashboard":
    from views import p10_dashboard; p10_dashboard.render()
elif page == "🔬 CI/CD & Debug":
    from views import p11_cicd; p11_cicd.render()