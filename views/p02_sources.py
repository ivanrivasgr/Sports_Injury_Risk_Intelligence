import streamlit as st
import pandas as pd


def render():
    st.markdown("<h2>02 · Data Sources</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #64748B; font-size: 0.9rem; max-width: 700px; margin-bottom: 28px;'>
        Every data source is classified by availability, reliability, and potential bias.
        No source is treated as ground truth without explicit documentation of its limitations.
    </p>
    """, unsafe_allow_html=True)

    sources = [
        {
            "id": "DS-01",
            "name": "Injury Reports",
            "category": "Injury",
            "type": "PARTIAL",
            "update": "Event-driven",
            "latency": "1-48h",
            "fields": "player_id, injury_type, match_id, return_date",
            "source": "Club communications, official league injury trackers",
            "limitations": "Significant under-reporting (~30-40% unreported). Injury type inconsistency across clubs. Return date often approximate.",
            "bias": "Selection bias: high-profile players more likely reported. Serious injuries over-represented.",
        },
        {
            "id": "DS-02",
            "name": "Match Appearances",
            "category": "Match",
            "type": "REAL",
            "update": "Post-match",
            "latency": "2-4h",
            "fields": "player_id, match_id, minutes_played, sub_on, sub_off, position",
            "source": "Official league APIs (e.g., StatsBomb, Opta, FBRef)",
            "limitations": "Historical depth varies by league. Position codes inconsistent across sources.",
            "bias": "Minimal for minutes played. Tactical position may differ from nominal.",
        },
        {
            "id": "DS-03",
            "name": "Fixture Calendar",
            "category": "Schedule",
            "type": "REAL",
            "update": "Weekly",
            "latency": "24h",
            "fields": "match_id, home_team, away_team, kickoff_datetime, competition",
            "source": "Official league fixture releases, football-data.co.uk",
            "limitations": "Rescheduled matches require re-ingestion. Cup fixtures often added late.",
            "bias": "None significant for schedule congestion analysis.",
        },
        {
            "id": "DS-04",
            "name": "Player Registry",
            "category": "Players",
            "type": "REAL",
            "update": "Transfer windows",
            "latency": "24-72h",
            "fields": "player_id, name, dob, nationality, position, height, weight, team_id",
            "source": "Transfermarkt API, official club rosters",
            "limitations": "Physical attributes (height/weight) not always current. Historical team history may have gaps.",
            "bias": "Lower-league players have sparser profiles.",
        },
        {
            "id": "DS-05",
            "name": "Pitch Conditions",
            "category": "Environmental",
            "type": "PROXY",
            "update": "Seasonal / match-day",
            "latency": "Variable",
            "fields": "stadium_id, surface_type, hybrid_flag, drainage_score, last_inspection",
            "source": "Stadium technical sheets, UEFA/FIFA pitch reports (partnership required)",
            "limitations": "No standardized public dataset. Requires stadium-level partnership. Inspection frequency inconsistent.",
            "bias": "Large stadiums better documented. Championship/League One under-represented.",
        },
        {
            "id": "DS-06",
            "name": "Weather at Kickoff",
            "category": "Environmental",
            "type": "PROXY",
            "update": "Match-day",
            "latency": "1h (historical)",
            "fields": "match_id, temperature_c, humidity_pct, precipitation_mm, wind_kph",
            "source": "Open-Meteo historical API, Visual Crossing",
            "limitations": "Stadium microclimate differs from nearest weather station. Indoor/covered stadiums not adjustable.",
            "bias": "Northern Europe over-represented in training data. Extreme conditions rare.",
        },
        {
            "id": "DS-07",
            "name": "Team Season Load",
            "category": "Match",
            "type": "PARTIAL",
            "update": "Weekly",
            "latency": "24h",
            "fields": "team_id, season, competition, match_count_ytd, cup_matches",
            "source": "Derived from DS-02 + DS-03",
            "limitations": "Fully derived — inherits all limitations of parent sources.",
            "bias": "Clubs in multiple competitions appear more congested; clubs relegated mid-season show structural breaks.",
        },
        {
            "id": "DS-08",
            "name": "GPS / Tracking Data",
            "category": "Workload",
            "type": "PROXY",
            "update": "Post-match",
            "latency": "4-8h",
            "fields": "player_id, match_id, distance_km, hsr_distance, sprint_count, peak_speed",
            "source": "Club proprietary STATSports / Catapult (not publicly available)",
            "limitations": "Not publicly available. Research-grade only. Requires NDA-level partnership.",
            "bias": "Elite clubs only. Consistency of device calibration varies.",
        },
    ]

    type_colors = {
        "REAL":    ("badge-real",    "Real"),
        "PROXY":   ("badge-proxy",   "Proxy"),
        "PARTIAL": ("badge-partial", "Partial"),
    }

    # Summary row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class='metric-card'><h4>Real Sources</h4>
        <div class='value'>3</div><div class='sub'>high confidence</div></div>""",
                    unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class='metric-card'><h4>Proxy Sources</h4>
        <div class='value'>3</div><div class='sub'>require validation</div></div>""",
                    unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class='metric-card'><h4>Partial Sources</h4>
        <div class='value'>2</div><div class='sub'>known gaps</div></div>""",
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Legend
    st.markdown("""
    <div style='margin-bottom: 20px;'>
        <span class='badge badge-real'>● Real — primary source, high confidence</span>
        <span class='badge badge-proxy'>● Proxy — indirect signal, validate before use</span>
        <span class='badge badge-partial'>● Partial — known gaps, bias-adjusted</span>
    </div>
    """, unsafe_allow_html=True)

    for src in sources:
        badge_class, badge_label = type_colors[src["type"]]
        with st.expander(f"  {src['id']} · {src['name']}  —  {src['category']}"):
            col_l, col_r = st.columns([3, 2])

            with col_l:
                st.markdown(f"""
                <span class='badge {badge_class}'>{badge_label}</span>
                <br><br>
                <div style='font-family: IBM Plex Mono, monospace; font-size: 0.75rem;
                            color: #6B21A8; margin-bottom: 4px;'>Fields</div>
                <code>{src['fields']}</code>
                <br><br>
                <div style='font-family: IBM Plex Mono, monospace; font-size: 0.75rem;
                            color: #6B21A8; margin-bottom: 4px;'>Source</div>
                <div style='color: #475569; font-size: 0.83rem;'>{src['source']}</div>
                """, unsafe_allow_html=True)

            with col_r:
                st.markdown(f"""
                <div style='width:100%;margin-bottom:16px;'>
                    <div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 5px;
                                padding: 10px;'>
                        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                    color: #64748B; text-transform: uppercase;
                                    letter-spacing: 0.1em;'>Update cycle</div>
                        <div style='color: #334155; font-size: 0.82rem;
                                    margin-top: 3px;'>{src['update']}</div>
                    </div>
                    <div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 5px;
                                padding: 10px;'>
                        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                    color: #64748B; text-transform: uppercase;
                                    letter-spacing: 0.1em;'>Latency</div>
                        <div style='color: #334155; font-size: 0.82rem;
                                    margin-top: 3px;'>{src['latency']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style='background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 5px;
                            padding: 10px; margin-bottom: 8px;'>
                    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                color: #92400E; text-transform: uppercase; letter-spacing: 0.1em;
                                margin-bottom: 4px;'>Limitations</div>
                    <div style='color: #78350F; font-size: 0.78rem; line-height: 1.5;'>{src['limitations']}</div>
                </div>
                <div style='background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 5px;
                            padding: 10px;'>
                    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                color: #D97706; text-transform: uppercase; letter-spacing: 0.1em;
                                margin-bottom: 4px;'>Bias risk</div>
                    <div style='color: #92400E; font-size: 0.78rem; line-height: 1.5;'>{src['bias']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class='warn-box'>
        <p><strong>Data Contract principle:</strong> Every source must have a defined schema,
        validation rules, and SLA before it enters the pipeline.
        Sources without a data contract are staged in quarantine, not ingested.</p>
    </div>
    """, unsafe_allow_html=True)