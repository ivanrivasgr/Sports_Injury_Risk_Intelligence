import streamlit as st


def render():
    st.markdown("""
    <div style='margin-bottom: 32px;'>
        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.65rem;
                    letter-spacing: 0.18em; color: #94A3B8; text-transform: uppercase;'>
            Production-Grade · Data Engineering · ML Architecture
        </div>
        <h1 style='font-size: 2.4rem; font-weight: 700; line-height: 1.1;
                   color: #0D1B2A; margin: 8px 0;'>
            Injury Risk Intelligence<br>
            <span style='color: #6B21A8;'>System Design Blueprint</span>
        </h1>
        <p style='color: #475569; font-size: 1rem; max-width: 620px; line-height: 1.6;'>
            A rigorous data architecture for evaluating injury risk in professional football —
            from raw ingestion to ML-ready feature stores.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Data Sources", "8", "classified by quality"),
        ("Pipeline Layers", "5", "Bronze → Gold"),
        ("Core Tables", "6", "defined grain"),
        ("Feature Groups", "12", "point-in-time safe"),
    ]
    for col, (label, val, sub) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <h4>{label}</h4>
                <div class='value'>{val}</div>
                <div class='sub'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown("<div class='section-header'>What this project demonstrates</div>",
                    unsafe_allow_html=True)

        items = [
            ("🏗️", "Production-Level Thinking",
             "Layered Medallion architecture (Bronze/Silver/Gold) with immutable raw storage, versioned datasets, and full lineage."),
            ("🔒", "Engineering Rigor",
             "Data contracts, entity resolution, schema enforcement, idempotent pipelines, and partitioned incremental loads."),
            ("📐", "ML Readiness",
             "Point-in-time correct features, a dedicated feature store, and separation between training and inference paths."),
            ("🔍", "Trustworthy Pipelines",
             "Observability layer with data quality checks, drift detection, and pipeline health monitoring."),
        ]
        for icon, title, desc in items:
            st.markdown(f"""
            <div class='pipe-step'>
                <div style='display: flex; align-items: flex-start; gap: 12px;'>
                    <div style='font-size: 1.4rem; margin-top: 2px;'>{icon}</div>
                    <div>
                        <div style='color: #0F172A; font-weight: 600; font-size: 0.9rem;
                                    margin-bottom: 4px;'>{title}</div>
                        <div class='layer-desc'>{desc}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.markdown("<div class='section-header'>Positioning statement</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div style='background: linear-gradient(160deg, #F0F4FF 0%, #EFF6FF 100%);
                    border: 1px solid #BFDBFE; border-radius: 8px; padding: 24px;'>
            <div style='font-family: IBM Plex Mono, monospace; font-size: 1.1rem;
                        color: #1E3A5F; line-height: 1.7; font-style: italic;'>
                "This is not an analysis<br>of outcomes.<br><br>
                This is the <span style='color: #6B21A8;'>system required</span><br>
                to make reliable<br>analysis possible."
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>System scope</div>",
                    unsafe_allow_html=True)

        scope_items = [
            ("✅", "Association analysis"),
            ("✅", "Feature engineering"),
            ("✅", "Pipeline orchestration"),
            ("✅", "Data quality monitoring"),
            ("❌", "Causal inference claims"),
            ("❌", "Live production data"),
        ]
        for icon, label in scope_items:
            color = "#16A34A" if icon == "✅" else "#DC2626"
            st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 10px;
                        padding: 6px 0; border-bottom: 1px solid #E2E8F0;'>
                <span style='color: {color}; font-size: 1rem;'>{icon}</span>
                <span style='color: #334155; font-size: 0.85rem;
                             font-family: IBM Plex Mono, monospace;'>{label}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px;
                padding: 18px 24px; display: flex; gap: 16px; align-items: flex-start;'>
        <div style='color: #1D4ED8; font-size: 1.2rem;'>ℹ️</div>
        <div>
            <div style='color: #1D4ED8; font-family: IBM Plex Mono, monospace;
                        font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
                        margin-bottom: 4px;'>Navigation guide</div>
            <div style='color: #334155; font-size: 0.85rem; line-height: 1.6;'>
                Use the sidebar to explore each layer of the architecture.
                Start with <strong>01 · Problem Framing</strong> to understand the design constraints,
                then follow the layers from Data Sources through to the ML integration.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
