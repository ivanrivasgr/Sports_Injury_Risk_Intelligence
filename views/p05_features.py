import streamlit as st
import pandas as pd
import numpy as np


def render():
    st.markdown("<h2>05 · Feature Engineering</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #64748B; font-size: 0.9rem; max-width: 700px; margin-bottom: 28px;'>
        All features are designed with point-in-time correctness as the primary constraint.
        No future data leaks into training windows. Features are separated into observed
        variables and derived aggregations.
    </p>
    """, unsafe_allow_html=True)

    # Pipeline walkthrough
    st.markdown("<div class='section-header'>Raw → Feature Pipeline walkthrough</div>",
                unsafe_allow_html=True)

    steps = [
        {
            "step": "01",
            "name": "Anchor point definition",
            "layer": "Gold",
            "desc": "Each training example is anchored to a (player_id, match_id) pair. "
                    "Features are computed using only data available at t < kickoff_datetime of that match.",
            "code": """-- Anchor table
SELECT
    a.player_id,
    a.match_id,
    m.kickoff_datetime AS anchor_ts,
    a.minutes_played,
    a.team_id
FROM appearances a
JOIN matches m USING (match_id)""",
        },
        {
            "step": "02",
            "name": "Rolling workload (7/14/30d)",
            "layer": "Gold",
            "desc": "Minutes played in the N days preceding anchor_ts. "
                    "Uses a window bounded by (anchor_ts - N days, anchor_ts exclusive).",
            "code": """-- Rolling 14-day workload
SELECT
    player_id,
    match_id,
    SUM(a2.minutes_played) AS workload_14d
FROM appearances a1
JOIN matches m1 USING (match_id)  -- anchor
JOIN appearances a2 USING (player_id)
JOIN matches m2 ON a2.match_id = m2.match_id
WHERE m2.kickoff_datetime >= m1.kickoff_datetime - INTERVAL '14 days'
  AND m2.kickoff_datetime <  m1.kickoff_datetime  -- point-in-time safe
GROUP BY 1, 2""",
        },
        {
            "step": "03",
            "name": "Schedule congestion index",
            "layer": "Gold",
            "desc": "Average days between matches in a rolling 30-day window. "
                    "Tier assignment: 4=<3 rest days avg, 3=3-4d, 2=4-6d, 1=>6d.",
            "code": """-- Days between matches (lag function)
SELECT
    player_id,
    match_id,
    kickoff_datetime,
    DATEDIFF('day',
        LAG(kickoff_datetime) OVER (
            PARTITION BY player_id
            ORDER BY kickoff_datetime
        ),
        kickoff_datetime
    ) AS days_since_last_match""",
        },
        {
            "step": "04",
            "name": "Injury label construction",
            "layer": "Gold",
            "desc": "Binary label: did an injury occur within 7 days after this match? "
                    "Temporal lag applied to avoid leakage. Label is assigned AFTER the anchor.",
            "code": """-- Injury label (look-ahead window, only for training)
SELECT
    a.player_id,
    a.match_id,
    CASE WHEN COUNT(i.injury_id) > 0 THEN 1 ELSE 0 END AS injured_next_7d
FROM appearances a
JOIN matches m USING (match_id)
LEFT JOIN injuries i ON
    i.player_id = a.player_id
    AND i.report_date BETWEEN m.kickoff_datetime::DATE
                          AND m.kickoff_datetime::DATE + 7
GROUP BY 1, 2""",
        },
        {
            "step": "05",
            "name": "Feature store registration",
            "layer": "Feature Store",
            "desc": "All features are versioned and stored with their computation timestamp. "
                    "Inference features reuse identical logic with real-time anchor.",
            "code": """# Feature registration (Feast-style)
player_workload_features = FeatureView(
    name="player_workload_v1",
    entities=["player_id"],
    ttl=timedelta(days=90),
    features=[
        Feature("workload_7d",  ValueType.FLOAT),
        Feature("workload_14d", ValueType.FLOAT),
        Feature("workload_30d", ValueType.FLOAT),
        Feature("congestion_tier", ValueType.INT32),
    ],
    online=True,
    batch_source=workload_source,
)""",
        },
    ]

    for s in steps:
        layer_color = {"Gold": "#92400E", "Feature Store": "#6B21A8"}.get(s["layer"], "#1D4ED8")
        layer_bg   = {"Gold": "#FEF3C7", "Feature Store": "#F3E8FF"}.get(s["layer"], "#EFF6FF")
        layer_bord = {"Gold": "#FCD34D", "Feature Store": "#C4B5FD"}.get(s["layer"], "#BFDBFE")
        st.markdown(f"<div style='height:1px;background:#E2E8F0;margin:4px 0 2px 0;'></div>", unsafe_allow_html=True)
        with st.expander(f"  Step {s['step']} — {s['name']}"):
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"""
                <span style='background: {layer_bg}; color: {layer_color}; font-family: IBM Plex Mono, monospace;
                             font-size: 0.65rem; padding: 2px 10px; border-radius: 3px;
                             border: 1px solid {layer_bord}; letter-spacing: 0.08em;'>
                    {s['layer']} Layer
                </span>
                <p style='color: #475569; font-size: 0.85rem; line-height: 1.6; margin-top: 12px;'>
                    {s['desc']}
                </p>
                """, unsafe_allow_html=True)
            with col2:
                st.code(s["code"], language="sql" if "SELECT" in s["code"] else "python")

    st.markdown("---")

    # Feature catalogue
    st.markdown("<div class='section-header'>Feature catalogue</div>",
                unsafe_allow_html=True)

    features = [
        # Observed
        ("minutes_played", "Observed", "FLOAT", "Exact minutes in anchor match", "appearances.minutes_played", "None"),
        ("position_played", "Observed", "VARCHAR", "Position in anchor match", "appearances.position_played", "None"),
        ("days_since_last_match", "Observed", "INT", "Calendar days since previous match", "LAG on appearances × matches", "None"),
        ("competition_tier", "Observed", "INT", "League tier (1=top, 4=lower)", "matches.competition + lookup", "None"),
        # Derived workload
        ("workload_7d", "Derived", "FLOAT", "Total minutes in prior 7 days", "SUM(minutes) rolling window", "Bounded by anchor_ts"),
        ("workload_14d", "Derived", "FLOAT", "Total minutes in prior 14 days", "SUM(minutes) rolling window", "Bounded by anchor_ts"),
        ("workload_30d", "Derived", "FLOAT", "Total minutes in prior 30 days", "SUM(minutes) rolling window", "Bounded by anchor_ts"),
        ("match_count_14d", "Derived", "INT", "Matches played in prior 14 days", "COUNT(match_id) rolling window", "Bounded by anchor_ts"),
        # Congestion
        ("congestion_index", "Derived", "FLOAT", "Avg rest days between matches (30d)", "Rolling avg of days_since_last_match", "Bounded by anchor_ts"),
        ("congestion_tier", "Derived", "INT", "Ordinal congestion severity (1-4)", "Binned from congestion_index", "Bounded by anchor_ts"),
        # Environmental
        ("temperature_c", "Observed", "FLOAT", "Temperature at kickoff", "environmental_conditions", "Proxy — nearest station"),
        ("surface_type_enc", "Derived", "INT", "Encoded surface type (0/1/2)", "OHE of surface_type", "Proxy variable"),
        # Label
        ("injured_next_7d", "Label", "BINARY", "Injury within 7 days post-match", "injuries look-ahead join", "Training only — not in inference"),
    ]

    type_map = {
        "Observed": ("badge-real", "Observed"),
        "Derived":  ("badge-proxy", "Derived"),
        "Label":    ("badge-partial", "Label"),
    }

    df = pd.DataFrame(features, columns=[
        "Feature Name", "Type", "DType", "Description", "Source Logic", "Leakage Guard"
    ])

    # Color-coded type column
    col_filter = st.multiselect(
        "Filter by type",
        ["Observed", "Derived", "Label"],
        default=["Observed", "Derived", "Label"],
    )

    filtered = df[df["Type"].isin(col_filter)]
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Feature Name": st.column_config.TextColumn(width="medium"),
            "Type": st.column_config.TextColumn(width="small"),
            "DType": st.column_config.TextColumn(width="small"),
            "Description": st.column_config.TextColumn(width="large"),
            "Source Logic": st.column_config.TextColumn(width="large"),
            "Leakage Guard": st.column_config.TextColumn(width="large"),
        },
    )

    st.markdown("""
    <div class='info-box' style='margin-top: 16px;'>
        <p><strong>Point-in-time correctness rule:</strong>
        Every feature window is bounded by <code>anchor_ts - N days</code> to
        <code>anchor_ts - 1 second</code>. The label window is only applied during
        training dataset construction and is never exposed during inference.</p>
    </div>
    """, unsafe_allow_html=True)

    # Synthetic feature distribution
    st.markdown("<br><div class='section-header'>Synthetic feature distributions (illustrative)</div>",
                unsafe_allow_html=True)

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    np.random.seed(42)
    n = 800
    injured = np.random.choice([0, 1], n, p=[0.88, 0.12])

    workload_14d = np.where(injured == 1,
                             np.random.normal(220, 35, n),
                             np.random.normal(175, 45, n))
    congestion = np.where(injured == 1,
                           np.random.normal(2.8, 0.7, n),
                           np.random.normal(3.8, 0.9, n))

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["workload_14d by injury label",
                                        "congestion_index by injury label"])

    for label, color, name in [(0, "#1D4ED8", "Not injured"), (1, "#DC2626", "Injured")]:
        mask = injured == label
        fig.add_trace(go.Histogram(
            x=workload_14d[mask], name=name, marker_color=color,
            opacity=0.7, nbinsx=30, legendgroup=name,
        ), row=1, col=1)
        fig.add_trace(go.Histogram(
            x=congestion[mask], name=name, marker_color=color,
            opacity=0.7, nbinsx=25, legendgroup=name, showlegend=False,
        ), row=1, col=2)

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#F8FAFC",
        plot_bgcolor="#F1F5F9",
        font_family="IBM Plex Mono",
        font_color="#0F172A",
        legend=dict(bgcolor="#FFFFFF", bordercolor="#E2E8F0", borderwidth=1,
                    font=dict(color="#0F172A", size=11)),
        barmode="overlay",
        height=320,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    fig.update_xaxes(gridcolor="#E2E8F0", showgrid=True,
        tickfont=dict(color="#334155", size=11), title_font=dict(color="#334155"))
    fig.update_yaxes(gridcolor="#E2E8F0", showgrid=True,
        tickfont=dict(color="#334155", size=11), title_font=dict(color="#334155"))

    st.plotly_chart(fig, use_container_width=True)
    st.caption("⚠️ Synthetic data for illustration only. Not derived from real injury datasets.")