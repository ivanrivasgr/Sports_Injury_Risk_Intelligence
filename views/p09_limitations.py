import streamlit as st


def render():
    st.markdown("<h2>09 · Limitations</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #64748B; font-size: 0.9rem; max-width: 700px; margin-bottom: 28px;'>
        Intellectual honesty is a feature, not a weakness. Every limitation is documented
        explicitly so downstream consumers understand what the system can and cannot support.
    </p>
    """, unsafe_allow_html=True)

    # Primary disclaimer
    st.markdown("""
    <div style='background: linear-gradient(135deg, #F5F3FF 0%, #FEF3C7 100%);
                border: 2px solid #C9A84C; border-radius: 10px;
                padding: 28px 32px; margin-bottom: 28px; text-align: center;'>
        <div style='font-family: IBM Plex Mono, monospace; font-size: 1.1rem;
                    color: #4B0082; line-height: 1.7; letter-spacing: 0.04em;'>
            "This system supports <strong>association analysis</strong>.<br>
            It does <strong>not</strong> support causal inference."
        </div>
        <div style='color: #92400E; font-size: 0.78rem; margin-top: 12px;
                    font-family: IBM Plex Mono, monospace;'>
            All model outputs are conditional on stated assumptions and observed data availability.
        </div>
    </div>
    """, unsafe_allow_html=True)

    limitations = [
        {
            "id": "L-01",
            "category": "Data Completeness",
            "title": "Injury under-reporting",
            "severity": "HIGH",
            "description": (
                "An estimated 30-40% of muscle and soft-tissue injuries in professional football "
                "are never publicly reported. Minor injuries, training-ground incidents, and "
                "injuries masked by pain management are systematically absent from public datasets."
            ),
            "implication": (
                "The positive class (injured) in any training dataset is censored downward. "
                "Model sensitivity will be underestimated. Apparent 'risk' periods are "
                "conservative — true injury rates are likely higher."
            ),
            "mitigation": "source_reliability score on injury records; sensitivity analysis on label threshold.",
        },
        {
            "id": "L-02",
            "category": "Temporal Assignment",
            "title": "Match-injury association is approximate",
            "severity": "HIGH",
            "description": (
                "We cannot observe when exactly an injury occurred. Report date is assigned "
                "to the last match played before the report. Training injuries are entirely "
                "unobservable. The true event time is latent."
            ),
            "implication": (
                "Temporal features computed relative to the 'last match' may be measuring "
                "the wrong window. This introduces noise into the label-feature relationship."
            ),
            "mitigation": "Sensitivity tests with different temporal attribution windows (last 1, 2, 3 matches).",
        },
        {
            "id": "L-03",
            "category": "Proxy Variables",
            "title": "Pitch condition data is unavailable at scale",
            "severity": "HIGH",
            "description": (
                "No standardized, publicly accessible dataset exists for pitch hardness, "
                "drainage quality, or surface wear across professional leagues. "
                "We rely on surface_type (natural/hybrid/artificial) as a coarse proxy. "
                "This is a significant limitation for the specific problem of pitch-related injury."
            ),
            "implication": (
                "The core environmental variable of interest is unmeasured. "
                "Any association between surface_type and injury risk may be confounded "
                "by stadium type, team quality, match importance, and other factors."
            ),
            "mitigation": "Explicitly label surface features as PROXY. Document coefficient of variation in analyses.",
        },
        {
            "id": "L-04",
            "category": "Sampling Bias",
            "title": "Top-5 league over-representation",
            "severity": "MEDIUM",
            "description": (
                "Public datasets have significantly better coverage of Premier League, "
                "La Liga, Bundesliga, Serie A, and Ligue 1. Lower divisions, women's football, "
                "and non-European leagues are poorly covered or absent."
            ),
            "implication": (
                "Models trained on this data cannot be generalized to other contexts. "
                "Applying predictions to Championship or MLS players would be out-of-distribution."
            ),
            "mitigation": "Stratify all analyses by league tier. Evaluate separately per competition.",
        },
        {
            "id": "L-05",
            "category": "Confounding",
            "title": "Player quality and medical staff quality",
            "severity": "HIGH",
            "description": (
                "Elite players at elite clubs benefit from world-class medical and conditioning "
                "staff, advanced GPS load management, and proactive injury prevention. "
                "These are unobserved variables that correlate with both workload and injury rate."
            ),
            "implication": (
                "Naïve models may incorrectly assign low injury risk to high-workload elite players, "
                "because the protective effect of elite medical care is confounded with workload. "
                "This is a classic omitted variable bias scenario."
            ),
            "mitigation": "Include team-level fixed effects. Avoid cross-tier comparisons without adjustment.",
        },
        {
            "id": "L-06",
            "category": "Causal Inference",
            "title": "Association ≠ causation",
            "severity": "CRITICAL",
            "description": (
                "This entire system is designed for association analysis. "
                "Even with perfect data, a predictive model trained on observational data "
                "cannot establish causal effects without a valid identification strategy "
                "(RCT, instrumental variables, difference-in-differences, etc.)."
            ),
            "implication": (
                "No output from this system should be used to make decisions about "
                "pitch construction, scheduling policy, or individual player management "
                "without additional causal analysis and domain expert validation."
            ),
            "mitigation": "All communications must carry an explicit disclaimer. Model cards required for any external use.",
        },
    ]

    sev_colors = {
        "CRITICAL": "#DC2626",
        "HIGH": "#D97706",
        "MEDIUM": "#1D4ED8",
    }
    sev_bg = {
        "CRITICAL": "#FEF2F2",
        "HIGH": "#FFFBEB",
        "MEDIUM": "#EFF6FF",
    }
    sev_border = {
        "CRITICAL": "#FCA5A5",
        "HIGH": "#FCD34D",
        "MEDIUM": "#BFDBFE",
    }

    for lim in limitations:
        color  = sev_colors[lim["severity"]]
        bg     = sev_bg[lim["severity"]]
        border = sev_border[lim["severity"]]

        with st.expander(f"  {lim['id']} · {lim['title']}  [{lim['category']}]"):
            st.markdown(f"""
            <div style='background: {bg}; border: 1px solid {border}; border-radius: 6px;
                        padding: 6px 12px; margin-bottom: 14px; display: inline-block;'>
                <span style='color: {color}; font-family: IBM Plex Mono, monospace;
                             font-size: 0.68rem; letter-spacing: 0.1em; font-weight: 700;'>
                    {lim['severity']} severity
                </span>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style='background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 5px;
                            padding: 14px;'>
                    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                color: #64748B; text-transform: uppercase; margin-bottom: 6px;'>
                        Description</div>
                    <div style='color: #475569; font-size: 0.8rem; line-height: 1.6;'>
                        {lim['description']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style='background: {bg}; border: 1px solid {border}; border-radius: 5px;
                            padding: 14px;'>
                    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                color: {color}; text-transform: uppercase; margin-bottom: 6px;'>
                        Implication</div>
                    <div style='color: #334155; font-size: 0.8rem; line-height: 1.6;'>
                        {lim['implication']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 5px;
                            padding: 14px;'>
                    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                color: #16A34A; text-transform: uppercase; margin-bottom: 6px;'>
                        Mitigation</div>
                    <div style='color: #15803D; font-size: 0.8rem; line-height: 1.6;'>
                        {lim['mitigation']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px;
                padding: 24px 28px; margin-top: 8px;'>
        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.65rem;
                    color: #1D4ED8; letter-spacing: 0.12em; text-transform: uppercase;
                    margin-bottom: 14px;'>Final positioning</div>
        <div style='width:100%;'>
            <div>
                <div style='color: #16A34A; font-size: 0.85rem; font-weight: 600;
                            margin-bottom: 6px;'>This system CAN</div>
                <ul style='color: #5a9060; font-size: 0.8rem; line-height: 2; padding-left: 16px;'>
                    <li>Measure workload associations</li>
                    <li>Identify high-risk periods</li>
                    <li>Support hypothesis generation</li>
                    <li>Provide reproducible analysis</li>
                    <li>Track data quality over time</li>
                </ul>
            </div>
            <div>
                <div style='color: #DC2626; font-size: 0.85rem; font-weight: 600;
                            margin-bottom: 6px;'>This system CANNOT</div>
                <ul style='color: #905050; font-size: 0.8rem; line-height: 2; padding-left: 16px;'>
                    <li>Prove pitch X causes injuries</li>
                    <li>Provide individual risk verdicts</li>
                    <li>Replace medical expert judgment</li>
                    <li>Generalize beyond observed leagues</li>
                    <li>Account for unmeasured confounders</li>
                </ul>
            </div>
            <div>
                <div style='color: #D97706; font-size: 0.85rem; font-weight: 600;
                            margin-bottom: 6px;'>Required next steps</div>
                <ul style='color: #907040; font-size: 0.8rem; line-height: 2; padding-left: 16px;'>
                    <li>Partner with clubs for GPS data</li>
                    <li>Standardize pitch sensor data</li>
                    <li>Causal identification strategy</li>
                    <li>Expert review of feature logic</li>
                    <li>IRB / ethics review if applicable</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
