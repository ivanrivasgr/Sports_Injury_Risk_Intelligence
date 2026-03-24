import streamlit as st
import plotly.graph_objects as go
import numpy as np


def render():
    st.markdown("<h2>06 · Pipeline DAG</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #64748B; font-size: 0.9rem; max-width: 700px; margin-bottom: 28px;'>
        DAG-based orchestration with explicit task dependencies, incremental refresh strategy,
        idempotent jobs, and partitioned processing by date.
    </p>
    """, unsafe_allow_html=True)

    # DAG visualization — usar rectángulos via shapes + annotations para texto legible
    tasks = {
        "ingest_appearances":   (0.5,  5.5, "Ingest\nApps",      "#1E40AF", "DS-02"),
        "ingest_injuries":      (0.5,  4.0, "Ingest\nInjuries",  "#9F1239", "DS-01"),
        "ingest_fixtures":      (0.5,  2.5, "Ingest\nFixtures",  "#1E40AF", "DS-03"),
        "ingest_weather":       (0.5,  1.0, "Ingest\nWeather",   "#065F46", "DS-06"),
        "validate_appearances": (2.2,  5.5, "Validate\nContract","#1D4ED8", ""),
        "validate_injuries":    (2.2,  4.0, "Validate\nContract","#BE123C", ""),
        "validate_fixtures":    (2.2,  2.5, "Validate\nContract","#1D4ED8", ""),
        "validate_weather":     (2.2,  1.0, "Validate\nContract","#047857", ""),
        "bronze_write":         (3.9,  3.25,"Bronze\nWrite",     "#92400E", ""),
        "silver_players":       (5.4,  5.0, "Silver\nPlayers",   "#1E3A5F", ""),
        "silver_matches":       (5.4,  3.5, "Silver\nMatches",   "#1E3A5F", ""),
        "silver_injuries":      (5.4,  2.0, "Silver\nInjuries",  "#7F1D1D", ""),
        "enrich_player_match":  (7.0,  3.75,"Enriched\nPly×Mch", "#064E3B", ""),
        "gold_features":        (8.5,  3.75,"Gold\nFeatures",    "#78350F", ""),
        "feature_store_push":   (10.0, 3.75,"Feature\nStore",    "#4C1D95", ""),
        "dq_monitor":           (8.5,  2.0, "DQ\nMonitor",       "#0F3460", ""),
    }

    edges = [
        ("ingest_appearances",  "validate_appearances"),
        ("ingest_injuries",     "validate_injuries"),
        ("ingest_fixtures",     "validate_fixtures"),
        ("ingest_weather",      "validate_weather"),
        ("validate_appearances","bronze_write"),
        ("validate_injuries",   "bronze_write"),
        ("validate_fixtures",   "bronze_write"),
        ("validate_weather",    "bronze_write"),
        ("bronze_write",        "silver_players"),
        ("bronze_write",        "silver_matches"),
        ("bronze_write",        "silver_injuries"),
        ("silver_players",      "enrich_player_match"),
        ("silver_matches",      "enrich_player_match"),
        ("silver_injuries",     "enrich_player_match"),
        ("enrich_player_match", "gold_features"),
        ("gold_features",       "feature_store_push"),
        ("gold_features",       "dq_monitor"),
    ]

    W = 0.75  # half-width of node box
    H = 0.42  # half-height of node box

    fig = go.Figure()

    # Draw edges (before nodes so they appear behind)
    for src, dst in edges:
        x0, y0 = tasks[src][:2]
        x1, y1 = tasks[dst][:2]
        fig.add_trace(go.Scatter(
            x=[x0 + W, x1 - W],
            y=[y0, y1],
            mode="lines",
            line=dict(color="#64748B", width=1.5),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Draw nodes as filled rectangles via shapes, text via annotations
    shapes = []
    annotations = []
    # Invisible scatter just for hover
    for name, (x, y, label, color, tag) in tasks.items():
        shapes.append(dict(
            type="rect",
            x0=x - W, x1=x + W,
            y0=y - H, y1=y + H,
            fillcolor=color,
            line=dict(color="#1E293B", width=1.5),
            layer="above",
        ))
        display = label + (f"\n[{tag}]" if tag else "")
        lines = display.split("\n")
        if len(lines) == 3:
            # 3 lines: shift up slightly
            annotations.append(dict(x=x, y=y+0.10, text=lines[0],
                font=dict(family="IBM Plex Mono", size=9, color="#FFFFFF"),
                showarrow=False, xanchor="center"))
            annotations.append(dict(x=x, y=y-0.05, text=lines[1],
                font=dict(family="IBM Plex Mono", size=9, color="#FFFFFF"),
                showarrow=False, xanchor="center"))
            annotations.append(dict(x=x, y=y-0.20, text=lines[2],
                font=dict(family="IBM Plex Mono", size=8, color="#E2E8F0"),
                showarrow=False, xanchor="center"))
        else:
            for i, line in enumerate(lines):
                offset = 0.13 if len(lines)==2 else 0
                annotations.append(dict(
                    x=x, y=y + offset - i*0.26,
                    text=line,
                    font=dict(family="IBM Plex Mono", size=9, color="#FFFFFF"),
                    showarrow=False, xanchor="center",
                ))

        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(size=1, color="rgba(0,0,0,0)"),
            hovertemplate=f"<b>{name}</b><extra></extra>",
            showlegend=False,
        ))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#F8FAFC",
        plot_bgcolor="#EEF2F7",
        height=460,
        margin=dict(t=10, b=10, l=10, r=20),
        xaxis=dict(visible=False, range=[-0.2, 11.2]),
        yaxis=dict(visible=False, range=[0.3, 6.5]),
        shapes=shapes,
        annotations=annotations,
        dragmode="pan",
    )

    st.plotly_chart(fig, use_container_width=True)


    # Task details
    st.markdown("<div class='section-header'>Task specifications</div>",
                unsafe_allow_html=True)

    task_specs = [
        {
            "group": "Ingestion Tasks",
            "tasks": [
                ("ingest_appearances", "Daily @ 06:00 UTC", "Incremental", "api_appearances_conn",
                 "Fetch latest match appearances from league API"),
                ("ingest_injuries", "Event-triggered + daily fallback", "Incremental",
                 "injury_tracker_conn", "Scrape injury reports; de-dup by (player_id, report_date)"),
                ("ingest_fixtures", "Weekly + rescheduling trigger", "Incremental",
                 "fixtures_api_conn", "Sync upcoming and completed fixture records"),
                ("ingest_weather", "Post-match (2h after kickoff)", "Incremental",
                 "weather_api_conn", "Retrieve historical weather for completed matches"),
            ]
        },
        {
            "group": "Transform Tasks",
            "tasks": [
                ("bronze_write", "After all validate_* succeed", "Append-only",
                 "S3 Delta write", "Immutable append to partitioned bronze table"),
                ("silver_players", "After bronze_write", "Merge (SCD Type 2)",
                 "dbt run", "Entity resolution + schema enforcement"),
                ("silver_matches", "After bronze_write", "Upsert on match_id",
                 "dbt run", "Normalize matches, resolve team IDs"),
                ("silver_injuries", "After bronze_write", "Upsert on injury_id",
                 "dbt run", "Standardize injury types, compute days_missed"),
                ("enrich_player_match", "After all silver_*", "Incremental by date",
                 "dbt run", "Cross-source join, temporal alignment"),
                ("gold_features", "After enrich_player_match", "Incremental by date",
                 "dbt run", "Rolling windows, congestion, feature aggregation"),
            ]
        },
        {
            "group": "Output Tasks",
            "tasks": [
                ("feature_store_push", "After gold_features", "Batch push",
                 "Feature Store SDK", "Materialize features to offline + online store"),
                ("dq_monitor", "After gold_features", "Each run",
                 "Great Expectations", "Run DQ suite; alert on failures"),
            ]
        },
    ]

    for group in task_specs:
        st.markdown(f"""
        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.7rem; color: #6B21A8;
                    letter-spacing: 0.1em; text-transform: uppercase;
                    margin: 16px 0 8px 0;'>{group['group']}</div>
        """, unsafe_allow_html=True)

        for task_name, schedule, refresh, conn, desc in group["tasks"]:
            st.markdown(f"""
            <div class='pipe-step'>
                <div style='width:100%;'>
                    <div>
                        <code style='font-size: 0.75rem !important;'>{task_name}</code>
                        <div style='color: #475569; font-size: 0.8rem; margin-top: 5px;'>{desc}</div>
                    </div>
                    <div>
                        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.6rem;
                                    color: #94A3B8; text-transform: uppercase; margin-bottom: 2px;'>Schedule</div>
                        <div style='color: #334155; font-size: 0.78rem;'>{schedule}</div>
                    </div>
                    <div>
                        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.6rem;
                                    color: #94A3B8; text-transform: uppercase; margin-bottom: 2px;'>Refresh</div>
                        <div style='color: #334155; font-size: 0.78rem;'>{refresh}</div>
                    </div>
                    <div>
                        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.6rem;
                                    color: #94A3B8; text-transform: uppercase; margin-bottom: 2px;'>Connection</div>
                        <div style='color: #334155; font-size: 0.78rem;'>{conn}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class='info-box'>
        <p><strong>Idempotency guarantee:</strong> All tasks use deterministic merge keys.
        Re-running any task for the same date partition produces identical output.
        Retry-safe execution is enforced at the orchestration layer via Airflow's task state machine.</p>
    </div>
    """, unsafe_allow_html=True)