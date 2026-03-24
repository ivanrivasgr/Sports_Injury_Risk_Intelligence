import streamlit as st
import streamlit.components.v1 as components

# ── Real Madrid palette ───────────────────────────────────────────────────────
# White #FFFFFF  Purple #4B0082 / #6B21A8  Gold #C9A84C  Light grey #F8F9FA

def render():
    st.markdown("<h2>03 · Architecture</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#6B7FA0; font-size:0.9rem; max-width:700px; margin-bottom:28px;'>
        A Medallion Architecture (Bronze → Silver → Gold) with a dedicated Feature Layer and
        ML Integration layer. Each layer has immutable state, versioning, and defined contracts.
    </p>
    """, unsafe_allow_html=True)

    # ── Architecture diagram — rendered via components.html to bypass sanitizer ─
    components.html("""
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&display=swap" rel="stylesheet">
    <style>body{margin:0;padding:0;background:transparent;}</style>
    <div style='background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px;
                padding:24px 20px; overflow-x:auto; font-family: IBM Plex Mono, monospace;'>

        <div style='font-size:0.65rem; letter-spacing:0.15em; color:#9BA8B8;
                    text-transform:uppercase; margin-bottom:18px;'>End-to-End Architecture</div>
        <table cellpadding='0' cellspacing='0' width='100%'>
        <tr>
            <td width='11%' valign='middle' align='center'>
                <div style='background:#F8F9FA; border:1px solid #E2E8F0; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#9BA8B8; text-transform:uppercase; margin-bottom:3px;'>Sources</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>APIs<br>Batch</div>
                </div>
            </td>
            <td width='3%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1.2rem; font-weight:700;'>→</span>
            </td>
            <td width='13%' valign='middle'>
                <div style='background:#F3F0FF; border:2px solid #6B21A8; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#6B21A8; text-transform:uppercase; margin-bottom:3px;'>Ingestion</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>Contracts<br>Tagging</div>
                </div>
            </td>
            <td width='3%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1.2rem; font-weight:700;'>→</span>
            </td>
            <td width='13%' valign='middle'>
                <div style='background:#FFF8F0; border:2px solid #C07830; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#C07830; text-transform:uppercase; margin-bottom:3px;'>🥉 Bronze</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>Immutable<br>Raw</div>
                </div>
            </td>
            <td width='3%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1.2rem; font-weight:700;'>→</span>
            </td>
            <td width='13%' valign='middle'>
                <div style='background:#F0F5FF; border:2px solid #2563A8; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#2563A8; text-transform:uppercase; margin-bottom:3px;'>🥈 Silver</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>Cleaned<br>Validated</div>
                </div>
            </td>
            <td width='3%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1.2rem; font-weight:700;'>→</span>
            </td>
            <td width='13%' valign='middle'>
                <div style='background:#F0FFF4; border:2px solid #2E7D32; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#2E7D32; text-transform:uppercase; margin-bottom:3px;'>📦 Enriched</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>Joins<br>Aligned</div>
                </div>
            </td>
            <td width='3%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1.2rem; font-weight:700;'>→</span>
            </td>
            <td width='13%' valign='middle'>
                <div style='background:#FFFDF0; border:2px solid #C9A84C; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#C9A84C; text-transform:uppercase; margin-bottom:3px;'>🥇 Gold</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>Features<br>Labels</div>
                </div>
            </td>
            <td width='3%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1.2rem; font-weight:700;'>→</span>
            </td>
            <td width='13%' valign='middle'>
                <div style='background:#FDF3FF; border:2px solid #6B21A8; border-radius:6px;
                            padding:10px 8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#6B21A8; text-transform:uppercase; margin-bottom:3px;'>🧠 Features</div>
                    <div style='color:#4A5568; font-size:0.7rem;'>PIT Safe<br>Versioned</div>
                </div>
            </td>
        </tr>
        </table>
        <table cellpadding='0' cellspacing='0' width='100%' style='margin-top:12px;'>
        <tr>
            <td width='65%'></td>
            <td width='2%' align='center' valign='middle'>
                <span style='color:#C9A84C; font-size:1rem;'>↓</span>
            </td>
            <td width='2%'></td>
            <td width='14%' valign='middle'>
                <div style='background:#F0FFFE; border:1px dashed #2E7D7A; border-radius:6px;
                            padding:8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#2E7D7A; text-transform:uppercase; margin-bottom:2px;'>Observability</div>
                    <div style='color:#4A5568; font-size:0.68rem;'>DQ · Drift · Alerts</div>
                </div>
            </td>
            <td width='3%'></td>
            <td width='14%' valign='middle'>
                <div style='background:#FDF3FF; border:1px dashed #6B21A8; border-radius:6px;
                            padding:8px; text-align:center;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.55rem;
                                color:#6B21A8; text-transform:uppercase; margin-bottom:2px;'>ML Layer</div>
                    <div style='color:#4A5568; font-size:0.68rem;'>Classifier · Survival</div>
                </div>
            </td>
        </tr>
        </table>
    </div>
    """, height=240, scrolling=False)

    # ── Layer details ─────────────────────────────────────────────────────────
    layers = [
        {
            "icon": "📥",
            "name": "Ingestion Layer",
            "color": "#6B21A8",
            "color_bg": "#F3F0FF",
            "responsibilities": [
                "API polling (league stats, weather, fixtures)",
                "Batch file ingestion (CSV, JSON, Parquet)",
                "Schema validation against registered data contracts",
                "Source tagging with `source_id`, `ingestion_ts`, `batch_id`",
                "Quarantine routing for contract violations",
            ],
            "tech": "Apache Airflow, Great Expectations, Kafka (event-driven), S3 landing zone",
        },
        {
            "icon": "🥉",
            "name": "Bronze Layer — Raw",
            "color": "#C07830",
            "color_bg": "#FFF8F0",
            "responsibilities": [
                "Immutable append-only storage — never overwrite",
                "Schema-on-read: preserve original structure",
                "Timestamped ingestion metadata on every record",
                "Source provenance tag on every partition",
                "No transformations — raw as received",
            ],
            "tech": "Delta Lake / Iceberg on S3, Parquet, partitioned by (source, date)",
        },
        {
            "icon": "🥈",
            "name": "Silver Layer — Clean",
            "color": "#2563A8",
            "color_bg": "#F0F5FF",
            "responsibilities": [
                "Schema enforcement via registered schemas (Avro/Protobuf)",
                "Entity resolution: `player_id`, `match_id`, `team_id` normalization",
                "Deduplication with deterministic merge keys",
                "Null handling with documented imputation strategy",
                "Data quality checks: completeness, range, referential integrity",
            ],
            "tech": "dbt Core + tests, PySpark, Great Expectations, schema registry",
        },
        {
            "icon": "📦",
            "name": "Enriched Layer",
            "color": "#2E7D32",
            "color_bg": "#F0FFF4",
            "responsibilities": [
                "Cross-source joins: appearances ↔ injuries ↔ fixtures ↔ weather",
                "Temporal alignment: all events pinned to `match_date` grain",
                "Derived columns: `days_since_last_match`, `competition_tier`",
                "Pre-computation of join-heavy aggregations",
                "No feature aggregations — reserved for Gold layer",
            ],
            "tech": "dbt, Spark, joined fact tables with surrogate keys",
        },
        {
            "icon": "🥇",
            "name": "Gold Layer — Features",
            "color": "#C9A84C",
            "color_bg": "#FFFDF0",
            "responsibilities": [
                "Rolling workload aggregations: 7 / 14 / 30-day windows",
                "Schedule congestion index computation",
                "Injury binary label engineering (with temporal lag)",
                "Exposure variable derivation (eligible minutes)",
                "Point-in-time correctness: no future data leakage",
            ],
            "tech": "dbt incremental models, window functions, feature versioning",
        },
        {
            "icon": "🧠",
            "name": "Feature Store",
            "color": "#6B21A8",
            "color_bg": "#FDF3FF",
            "responsibilities": [
                "Consistent feature definitions across training and inference",
                "Feature versioning: `feature_name:v1`, `feature_name:v2`",
                "Point-in-time join support for historical training",
                "Offline store (batch training) + Online store (inference)",
                "Reusable across multiple model experiments",
            ],
            "tech": "Feast, Tecton, or custom feature registry on Delta Lake",
        },
    ]

    st.markdown("<div class='section-header'>Layer specifications</div>",
                unsafe_allow_html=True)

    for layer in layers:
        with st.expander(f"{layer['icon']}  {layer['name']}"):
            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown("""
                <div style='font-family:IBM Plex Mono,monospace; font-size:0.72rem;
                            color:#6B21A8; letter-spacing:0.1em; margin-bottom:10px;'>
                    RESPONSIBILITIES
                </div>
                """, unsafe_allow_html=True)
                for r in layer["responsibilities"]:
                    st.markdown(f"""
                    <div style='padding:5px 0; border-bottom:1px solid #F0F4F8;'>
                        <span style='color:#C9A84C; font-size:0.9rem;'>▸</span>
                        <span style='color:#4A5568; font-size:0.83rem; margin-left:8px;'>{r}</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style='background:{layer["color_bg"]}; border:1px solid {layer["color"]};
                            border-radius:6px; padding:16px;'>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.65rem;
                                color:#9BA8B8; text-transform:uppercase; letter-spacing:0.1em;
                                margin-bottom:8px;'>Technology stack</div>
                    <div style='color:#4A5568; font-size:0.82rem; line-height:1.6;'>
                        {layer["tech"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
