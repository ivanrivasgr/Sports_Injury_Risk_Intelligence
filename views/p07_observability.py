import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render():
    st.markdown("<h2>07 · Observability</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #64748B; font-size: 0.9rem; max-width: 700px; margin-bottom: 28px;'>
        Production systems fail silently. Observability detects data quality degradation,
        pipeline failures, and distribution drift before they corrupt downstream models.
    </p>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 DQ Checks",
        "🔄 Pipeline Health",
        "📊 Drift Detection",
        "🚨 Alert Rules",
    ])

    with tab1:
        st.markdown("<div class='section-header'>Data quality check suite</div>",
                    unsafe_allow_html=True)

        np.random.seed(7)
        checks = [
            ("appearances", "completeness", "minutes_played NOT NULL", "CRITICAL", 0.9999, 0.9998),
            ("appearances", "range", "0 ≤ minutes_played ≤ 120", "HIGH", 0.9995, 1.0000),
            ("appearances", "uniqueness", "UNIQUE(player_id, match_id)", "CRITICAL", 1.0000, 1.0000),
            ("matches", "completeness", "kickoff_datetime NOT NULL", "CRITICAL", 1.0000, 1.0000),
            ("matches", "referential", "home_team_id IN teams", "HIGH", 0.9990, 0.9987),
            ("injuries", "completeness", "player_id NOT NULL", "CRITICAL", 1.0000, 0.9991),
            ("injuries", "temporal", "report_date ≥ match kickoff", "HIGH", 0.9940, 0.9956),
            ("injuries", "range", "days_missed BETWEEN 0 AND 365", "MEDIUM", 0.9885, 0.9901),
            ("env_conditions", "completeness", "temperature_c NOT NULL", "MEDIUM", 0.9720, 0.9710),
            ("env_conditions", "range", "-15 ≤ temperature_c ≤ 50", "MEDIUM", 0.9999, 1.0000),
            ("gold_features", "range", "workload_14d ≥ 0", "HIGH", 1.0000, 1.0000),
            ("gold_features", "range", "congestion_tier BETWEEN 1 AND 4", "HIGH", 1.0000, 1.0000),
        ]

        df = pd.DataFrame(checks, columns=[
            "Table", "Check Type", "Rule", "Severity",
            "Pass Rate D-1", "Pass Rate D-0"
        ])

        def severity_style(val):
            colors = {"CRITICAL": "#DC2626", "HIGH": "#D97706", "MEDIUM": "#1D4ED8"}
            c = colors.get(val, "#64748B")
            return f"color: {c}; font-weight: 600;"

        def pass_rate_style(val):
            if val >= 0.999:
                return "color: #16A34A;"
            elif val >= 0.990:
                return "color: #D97706;"
            else:
                return "color: #DC2626;"

        styled = df.style\
            .applymap(severity_style, subset=["Severity"])\
            .applymap(pass_rate_style, subset=["Pass Rate D-1", "Pass Rate D-0"])\
            .format({"Pass Rate D-1": "{:.4f}", "Pass Rate D-0": "{:.4f}"})

        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown("""
        <div class='info-box' style='margin-top: 12px;'>
            <p>CRITICAL checks block downstream tasks. HIGH checks trigger alerts but allow continuation.
            MEDIUM checks are logged and reviewed weekly.</p>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='section-header'>Simulated pipeline run history</div>",
                    unsafe_allow_html=True)

        np.random.seed(42)
        days = pd.date_range(end=pd.Timestamp.today(), periods=30, freq="D")
        statuses = np.random.choice(["success", "success", "success", "warning", "failed"],
                                     30, p=[0.82, 0.07, 0.03, 0.06, 0.02])

        runs = pd.DataFrame({
            "Date": days,
            "Status": statuses,
            "Duration (min)": np.random.normal(18, 3.5, 30).clip(10, 35).round(1),
            "Records Processed": (np.random.normal(12400, 800, 30)).astype(int),
            "Warnings": np.where(statuses == "warning", np.random.randint(1, 4, 30), 0),
        })

        col1, col2, col3, col4 = st.columns(4)
        total = len(runs)
        success = (runs["Status"] == "success").sum()
        warning = (runs["Status"] == "warning").sum()
        failed  = (runs["Status"] == "failed").sum()

        with col1:
            st.markdown(f"""<div class='metric-card'><h4>Success Rate</h4>
            <div class='value' style='color: #16A34A;'>{success/total*100:.0f}%</div>
            <div class='sub'>{success}/{total} runs</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class='metric-card'><h4>Warnings</h4>
            <div class='value' style='color: #D97706;'>{warning}</div>
            <div class='sub'>last 30 days</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class='metric-card'><h4>Failures</h4>
            <div class='value' style='color: #DC2626;'>{failed}</div>
            <div class='sub'>last 30 days</div></div>""", unsafe_allow_html=True)
        with col4:
            avg_dur = runs["Duration (min)"].mean()
            st.markdown(f"""<div class='metric-card'><h4>Avg Duration</h4>
            <div class='value'>{avg_dur:.1f}</div>
            <div class='sub'>minutes / run</div></div>""", unsafe_allow_html=True)

        # Run timeline chart
        status_colors = {"success": "#16A34A", "warning": "#D97706", "failed": "#DC2626"}
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=runs["Date"],
            y=runs["Duration (min)"],
            marker_color=[status_colors[s] for s in runs["Status"]],
            name="Run duration",
            hovertemplate="Date: %{x}<br>Duration: %{y}m<extra></extra>",
        ))
        fig.update_layout(
            template="plotly_white", paper_bgcolor="#F8FAFC",
            plot_bgcolor="#F1F5F9", height=220,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="#E2E8F0",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),
            yaxis=dict(gridcolor="#E2E8F0", title="Minutes",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),
            font_family="IBM Plex Mono", font_color="#0F172A",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("<div class='section-header'>Feature distribution drift monitoring</div>",
                    unsafe_allow_html=True)

        st.markdown("""
        <p style='color: #475569; font-size: 0.83rem; margin-bottom: 16px;'>
            Population Stability Index (PSI) measures how much a feature distribution has shifted
            between a reference window (training period) and the current production window.
            PSI > 0.25 triggers an alert.
        </p>
        """, unsafe_allow_html=True)

        np.random.seed(99)
        n_weeks = 12
        weeks = [f"W-{n_weeks - i}" for i in range(n_weeks)]
        features_drift = {
            "workload_14d":     np.clip(np.random.normal(0.04, 0.02, n_weeks), 0.001, 0.3),
            "congestion_index": np.clip(np.random.normal(0.08, 0.04, n_weeks), 0.001, 0.3),
            "days_since_last":  np.clip(np.random.normal(0.03, 0.015, n_weeks), 0.001, 0.3),
            "temperature_c":    np.clip(np.cumsum(np.random.normal(0.01, 0.03, n_weeks)) + 0.03, 0.001, 0.35),
        }
        features_drift["temperature_c"][-1] = 0.28  # inject spike

        fig = go.Figure()
        palette = ["#1D4ED8", "#D97706", "#16A34A", "#DC2626"]
        for (feat, vals), color in zip(features_drift.items(), palette):
            fig.add_trace(go.Scatter(
                x=weeks, y=vals, mode="lines+markers",
                name=feat, line=dict(color=color, width=1.5),
                marker=dict(size=5),
            ))
        fig.add_hline(y=0.1, line=dict(color="#D97706", dash="dot", width=1),
                      annotation_text="warn (PSI=0.1)", annotation_font_color="#D97706")
        fig.add_hline(y=0.25, line=dict(color="#DC2626", dash="dot", width=1),
                      annotation_text="alert (PSI=0.25)", annotation_font_color="#DC2626")
        fig.update_layout(
            template="plotly_white", paper_bgcolor="#F8FAFC",
            plot_bgcolor="#F1F5F9", height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="#E2E8F0",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),
            yaxis=dict(gridcolor="#E2E8F0", title="PSI",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),
            font_family="IBM Plex Mono", font_color="#0F172A",
            legend=dict(bgcolor="#FFFFFF", bordercolor="#E2E8F0", borderwidth=1, font=dict(color="#0F172A", size=11)),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption("Synthetic data. temperature_c spike at W-0 illustrates seasonal distribution shift detection.")

    with tab4:
        st.markdown("<div class='section-header'>Alert rule registry</div>",
                    unsafe_allow_html=True)

        alerts = [
            ("PIPELINE_FAILURE", "CRITICAL", "Pipeline run fails 2 consecutive times",
             "PagerDuty + Slack #alerts", "Immediate"),
            ("DQ_CRITICAL_FAIL", "CRITICAL", "Any CRITICAL DQ check fails",
             "PagerDuty + Slack #data-quality", "Immediate"),
            ("DQ_HIGH_FAIL", "HIGH", "Any HIGH DQ check pass rate < 0.990",
             "Slack #data-quality", "15 min"),
            ("DRIFT_ALERT", "HIGH", "Any feature PSI > 0.25",
             "Slack #ml-monitoring", "Daily summary"),
            ("INGESTION_LATE", "MEDIUM", "Source not received within SLA window",
             "Slack #pipeline-health", "30 min"),
            ("RECORD_COUNT_DROP", "HIGH", "Daily record count drops >30% vs 7d avg",
             "Slack #data-quality", "1 hour"),
            ("SCHEMA_CHANGE", "CRITICAL", "Unexpected schema change detected in source",
             "PagerDuty + Email", "Immediate"),
        ]

        for name, sev, condition, channel, latency in alerts:
            color_map = {"CRITICAL": "#DC2626", "HIGH": "#D97706", "MEDIUM": "#2563EB"}
            bg_map    = {"CRITICAL": "#FEF2F2", "HIGH": "#FFFBEB", "MEDIUM": "#EFF6FF"}
            st.markdown(f"""
            <div class='pipe-step'>
                <div style='width:100%; align-items: center;'>
                    <div>
                        <span style='background: {bg_map[sev]}; color: {color_map[sev]};
                                     font-family: IBM Plex Mono, monospace; font-size: 0.62rem;
                                     padding: 2px 8px; border-radius: 3px;
                                     border: 1px solid {color_map[sev]}40;'>{sev}</span>
                        <div style='color: #0F172A; font-size: 0.85rem; font-weight: 600;
                                    margin-top: 5px;'>{name}</div>
                    </div>
                    <div style='color: #475569; font-size: 0.8rem;'>{condition}</div>
                    <div style='color: #64748B; font-family: IBM Plex Mono, monospace;
                                font-size: 0.75rem;'>{channel}</div>
                    <div style='color: #6B21A8; font-family: IBM Plex Mono, monospace;
                                font-size: 0.75rem;'>{latency}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
