import streamlit as st


def render():
    st.markdown("<h2>01 · Problem Framing</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #94A3B8; font-size: 0.9rem; max-width: 700px; margin-bottom: 28px;'>
        Before a single byte is ingested, we define the structural question, the available observations,
        the assumptions we must make, and what the model outputs actually represent.
        This is the contract that governs every downstream decision.
    </p>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Structural Question",
        "👁️ Observed Data",
        "⚙️ Assumptions",
        "📤 Model Outputs",
    ])

    with tab1:
        st.markdown("<div class='section-header'>The question we are actually asking</div>",
                    unsafe_allow_html=True)

        st.markdown("""
        <div style='background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px;
                    padding: 28px 32px; margin-bottom: 20px;'>
            <div style='font-family: IBM Plex Mono, monospace; font-size: 0.68rem;
                        color: #94A3B8; letter-spacing: 0.12em; text-transform: uppercase;
                        margin-bottom: 10px;'>Primary question</div>
            <div style='font-size: 1.4rem; color: #0F172A; font-weight: 600; line-height: 1.4;'>
                "If we had to evaluate injury risk rigorously at scale,
                what data architecture would be required?"
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px;
                        padding: 20px; height: 180px;'>
                <div style='color: #16A34A; font-family: IBM Plex Mono, monospace;
                            font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase;
                            margin-bottom: 10px;'>✅ In scope</div>
                <ul style='color: #4a9060; font-size: 0.85rem; line-height: 1.8; margin: 0;
                           padding-left: 16px;'>
                    <li>Data system design</li>
                    <li>Feature architecture</li>
                    <li>Pipeline orchestration</li>
                    <li>Association measurement</li>
                    <li>Constraint-aware modeling</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style='background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px;
                        padding: 20px; height: 180px;'>
                <div style='color: #DC2626; font-family: IBM Plex Mono, monospace;
                            font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase;
                            margin-bottom: 10px;'>❌ Explicitly out of scope</div>
                <ul style='color: #905050; font-size: 0.85rem; line-height: 1.8; margin: 0;
                           padding-left: 16px;'>
                    <li>Causal claims ("pitch X causes injury")</li>
                    <li>Hot takes or media analysis</li>
                    <li>Conclusions without data</li>
                    <li>Individual player targeting</li>
                    <li>Real-time production deployment</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='section-header'>What we can actually observe</div>",
                    unsafe_allow_html=True)

        obs = [
            ("Match appearances", "Player was present in match, minutes played, substitution timestamp",
             "HIGH", "Official league APIs, transfermarkt"),
            ("Reported injuries", "Binary: injured / not injured, injury type, return date",
             "MEDIUM", "Club press conferences, official reports — under-reported"),
            ("Player workload", "Rolling minutes, match frequency",
             "HIGH", "Derived from appearances table"),
            ("Schedule congestion", "Days between matches, fixture count per window",
             "HIGH", "Fixture calendars — fully observable"),
            ("Pitch conditions", "Hardness proxy, drainage score, surface type",
             "LOW", "No standardized public source — requires partnership"),
            ("Weather at match", "Temperature, precipitation, humidity at kickoff",
             "MEDIUM", "Historical weather APIs — location-dependent"),
        ]

        for label, desc, confidence, source in obs:
            color_map = {"HIGH": "#16A34A", "MEDIUM": "#D97706", "LOW": "#DC2626"}
            bg_map = {"HIGH": "#ECFDF5", "MEDIUM": "#FFFBEB", "LOW": "#FEF2F2"}
            bc_map = {"HIGH": "#A7F3D0", "MEDIUM": "#FCD34D", "LOW": "#FCA5A5"}
            st.markdown(f"""
            <div style='background: {bg_map[confidence]}; border: 1px solid {bc_map[confidence]};
                        border-radius: 6px; padding: 14px 18px; margin-bottom: 8px;
                        display: flex; gap: 16px; align-items: flex-start;'>
                <div style='min-width: 60px; text-align: center;'>
                    <div style='color: {color_map[confidence]}; font-family: IBM Plex Mono, monospace;
                                font-size: 0.62rem; letter-spacing: 0.1em; font-weight: 700;'>{confidence}</div>
                    <div style='color: {color_map[confidence]}; font-size: 0.62rem;
                                opacity: 0.6;'>confidence</div>
                </div>
                <div>
                    <div style='color: #0F172A; font-weight: 600; font-size: 0.88rem;
                                margin-bottom: 3px;'>{label}</div>
                    <div style='color: #475569; font-size: 0.8rem; margin-bottom: 3px;'>{desc}</div>
                    <div style='font-family: IBM Plex Mono, monospace; color: #3a6080;
                                font-size: 0.72rem;'>Source: {source}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='section-header'>Explicit assumptions</div>",
                    unsafe_allow_html=True)

        assumptions = [
            ("A1", "Injury reporting completeness",
             "We assume ~60-70% of muscle injuries are publicly reported. Systemic under-reporting "
             "is treated as a known bias, not missing at random."),
            ("A2", "Temporal assignment",
             "We assume an injury 'occurred' in the last match played before the report date. "
             "This is an approximation — the true event time is unobserved."),
            ("A3", "Player homogeneity within position",
             "Players of the same position share similar baseline biomechanical risk profiles. "
             "This allows position-stratified analysis without individual biometric data."),
            ("A4", "Schedule as exogenous",
             "Fixture congestion is treated as largely exogenous to individual player injury risk "
             "for the purposes of feature construction."),
            ("A5", "Pitch proxies as valid signals",
             "In the absence of sensor data, pitch category (e.g., natural grass vs. hybrid) "
             "is used as a coarse proxy for surface hardness."),
        ]

        for code, title, desc in assumptions:
            st.markdown(f"""
            <div class='pipe-step'>
                <div style='display: flex; gap: 16px; align-items: flex-start;'>
                    <div style='background: #0a1e3a; border: 1px solid #1a3a5c; border-radius: 4px;
                                padding: 4px 10px; font-family: IBM Plex Mono, monospace;
                                color: #1D4ED8; font-size: 0.72rem; font-weight: 600;
                                white-space: nowrap; height: fit-content;'>{code}</div>
                    <div>
                        <div style='color: #0F172A; font-weight: 600; font-size: 0.88rem;
                                    margin-bottom: 5px;'>{title}</div>
                        <div style='color: #475569; font-size: 0.83rem; line-height: 1.6;'>{desc}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown("<div class='section-header'>What model outputs represent</div>",
                    unsafe_allow_html=True)

        st.markdown("""
        <div class='warn-box'>
            <p>⚠️ Model outputs are <strong>conditional association scores</strong>,
            not causal risk estimates. They reflect patterns in observed data under stated assumptions.</p>
        </div>
        """, unsafe_allow_html=True)

        outputs = [
            ("injury_risk_score", "float [0,1]",
             "Predicted probability of an injury event in the next match window, "
             "conditional on observed features. NOT a causal estimate."),
            ("workload_flag", "bool",
             "Binary flag indicating whether a player's rolling workload exceeds "
             "a configurable threshold percentile for their position cohort."),
            ("congestion_tier", "int [1-4]",
             "Ordinal severity of schedule congestion over rolling 30-day window. "
             "Tier 4 = fewer than 3 rest days per match on average."),
            ("feature_importance_vector", "array[float]",
             "Shapley-based feature attribution for model transparency. "
             "Used for auditing, not decision-making in isolation."),
        ]

        for name, dtype, desc in outputs:
            st.markdown(f"""
            <div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px;
                        padding: 16px 20px; margin-bottom: 8px;'>
                <div style='display: flex; gap: 12px; align-items: center; margin-bottom: 6px;'>
                    <code style='font-size: 0.82rem !important;'>{name}</code>
                    <span style='background: #EFF6FF; color: #1D4ED8; font-family: IBM Plex Mono, monospace;
                                 font-size: 0.65rem; padding: 2px 8px; border-radius: 3px;
                                 border: 1px solid #1a4a60;'>{dtype}</span>
                </div>
                <div style='color: #475569; font-size: 0.83rem; line-height: 1.5;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)
