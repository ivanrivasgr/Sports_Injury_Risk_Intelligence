import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render():
    st.markdown("<h2>04 · Data Model</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#6B7FA0; font-size:0.9rem; max-width:700px; margin-bottom:28px;'>
        Six core tables with explicitly defined grain, primary keys, and relationships.
        No ambiguity in aggregation or joins. Every join path is documented.
    </p>
    """, unsafe_allow_html=True)

    # ── ERD diagram — components.html bypasses Streamlit sanitizer ───────────
    components.html("""
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&display=swap" rel="stylesheet">
    <style>body{margin:0;padding:0;background:transparent;} * {box-sizing:border-box;}</style>
    <div style='background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px;
                padding:20px; font-family: IBM Plex Mono, monospace;'>

        <div style='font-family:IBM Plex Mono,monospace; font-size:0.65rem;
                    letter-spacing:0.15em; color:#9BA8B8; text-transform:uppercase;
                    margin-bottom:20px;'>Entity Relationship Diagram</div>

        <table width='100%' cellpadding='6' cellspacing='0'>
        <tr>
            <td width='33%' valign='top'>
                <div style='background:#F8F9FA; border:1px solid #E2E8F0; border-radius:6px; padding:14px;'>
                    <div style='font-family:IBM Plex Mono,monospace; color:#6B21A8; font-size:0.7rem;
                                font-weight:700; border-bottom:1px solid #E2E8F0; padding-bottom:6px; margin-bottom:8px;'>players</div>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; line-height:1.8;'>
                        <span style='color:#C9A84C;'>🔑 player_id</span><br>
                        <span style='color:#4A5568;'>name</span><br>
                        <span style='color:#4A5568;'>dob</span><br>
                        <span style='color:#4A5568;'>position</span><br>
                        <span style='color:#4A5568;'>nationality</span><br>
                        <span style='color:#9BA8B8; font-style:italic;'>grain: player</span>
                    </div>
                </div>
            </td>
            <td width='33%' valign='top' style='padding-left:8px;'>
                <div style='background:#F8F9FA; border:1px solid #E2E8F0; border-radius:6px; padding:14px;'>
                    <div style='font-family:IBM Plex Mono,monospace; color:#6B21A8; font-size:0.7rem;
                                font-weight:700; border-bottom:1px solid #E2E8F0; padding-bottom:6px; margin-bottom:8px;'>teams</div>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; line-height:1.8;'>
                        <span style='color:#C9A84C;'>🔑 team_id</span><br>
                        <span style='color:#4A5568;'>team_name</span><br>
                        <span style='color:#4A5568;'>league</span><br>
                        <span style='color:#4A5568;'>stadium_id</span><br>
                        <span style='color:#4A5568;'>country</span><br>
                        <span style='color:#9BA8B8; font-style:italic;'>grain: team</span>
                    </div>
                </div>
            </td>
            <td width='33%' valign='top' style='padding-left:8px;'>
                <div style='background:#F8F9FA; border:1px solid #E2E8F0; border-radius:6px; padding:14px;'>
                    <div style='font-family:IBM Plex Mono,monospace; color:#6B21A8; font-size:0.7rem;
                                font-weight:700; border-bottom:1px solid #E2E8F0; padding-bottom:6px; margin-bottom:8px;'>environmental_conditions</div>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; line-height:1.8;'>
                        <span style='color:#C9A84C;'>🔑 condition_id</span><br>
                        <span style='color:#2E7D32;'>🔗 match_id</span><br>
                        <span style='color:#4A5568;'>temperature_c</span><br>
                        <span style='color:#4A5568;'>humidity_pct</span><br>
                        <span style='color:#4A5568;'>surface_type</span><br>
                        <span style='color:#9BA8B8; font-style:italic;'>grain: match</span>
                    </div>
                </div>
            </td>
        </tr>
        <tr>
            <td width='33%' valign='top' style='padding-top:8px;'>
                <div style='background:#F3F0FF; border:2px solid #6B21A8; border-radius:6px; padding:14px;'>
                    <div style='font-family:IBM Plex Mono,monospace; color:#4B0082; font-size:0.7rem;
                                font-weight:700; border-bottom:1px solid #D8B4FE; padding-bottom:6px; margin-bottom:8px;'>matches ⭐ central</div>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; line-height:1.8;'>
                        <span style='color:#C9A84C;'>🔑 match_id</span><br>
                        <span style='color:#2E7D32;'>🔗 home_team_id</span><br>
                        <span style='color:#2E7D32;'>🔗 away_team_id</span><br>
                        <span style='color:#4A5568;'>kickoff_datetime</span><br>
                        <span style='color:#4A5568;'>competition</span><br>
                        <span style='color:#9BA8B8; font-style:italic;'>grain: match</span>
                    </div>
                </div>
            </td>
            <td width='33%' valign='top' style='padding-left:8px; padding-top:8px;'>
                <div style='background:#F8F9FA; border:1px solid #E2E8F0; border-radius:6px; padding:14px;'>
                    <div style='font-family:IBM Plex Mono,monospace; color:#6B21A8; font-size:0.7rem;
                                font-weight:700; border-bottom:1px solid #E2E8F0; padding-bottom:6px; margin-bottom:8px;'>appearances</div>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; line-height:1.8;'>
                        <span style='color:#C9A84C;'>🔑 appearance_id</span><br>
                        <span style='color:#2E7D32;'>🔗 player_id</span><br>
                        <span style='color:#2E7D32;'>🔗 match_id</span><br>
                        <span style='color:#4A5568;'>minutes_played</span><br>
                        <span style='color:#4A5568;'>position_played</span><br>
                        <span style='color:#9BA8B8; font-style:italic;'>grain: player × match</span>
                    </div>
                </div>
            </td>
            <td width='33%' valign='top' style='padding-left:8px; padding-top:8px;'>
                <div style='background:#FFF5F5; border:1px solid #FECACA; border-radius:6px; padding:14px;'>
                    <div style='font-family:IBM Plex Mono,monospace; color:#DC2626; font-size:0.7rem;
                                font-weight:700; border-bottom:1px solid #FECACA; padding-bottom:6px; margin-bottom:8px;'>injuries</div>
                    <div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; line-height:1.8;'>
                        <span style='color:#C9A84C;'>🔑 injury_id</span><br>
                        <span style='color:#2E7D32;'>🔗 player_id</span><br>
                        <span style='color:#2E7D32;'>🔗 match_id (last match)</span><br>
                        <span style='color:#4A5568;'>injury_type</span><br>
                        <span style='color:#4A5568;'>report_date</span><br>
                        <span style='color:#9BA8B8; font-style:italic;'>grain: injury event</span>
                    </div>
                </div>
            </td>
        </tr>
        </table>
        <p style='margin-top:16px; font-family:IBM Plex Mono,monospace; font-size:0.65rem;'>
            <span style='color:#C9A84C;'>🔑 Primary Key</span>
            &nbsp;&nbsp;&nbsp;
            <span style='color:#2E7D32;'>🔗 Foreign Key</span>
            &nbsp;&nbsp;&nbsp;
            <span style='color:#6B21A8; font-weight:700;'>⭐ Central fact table</span>
        </p>
    </div>
    """, height=420, scrolling=False)

    # ── Table specifications ──────────────────────────────────────────────────
    tables = {
        "players": {
            "grain": "One row per player",
            "pk": "player_id",
            "cols": [
                ("player_id", "VARCHAR(36)", "PK", "UUID — resolved across sources"),
                ("name", "VARCHAR", "", "Full name, normalized"),
                ("dob", "DATE", "", "Date of birth"),
                ("position", "VARCHAR(3)", "", "GK, CB, FB, CM, AM, FW"),
                ("nationality", "CHAR(3)", "", "ISO 3166-1 alpha-3"),
                ("height_cm", "SMALLINT", "", "May be NULL for historical players"),
                ("weight_kg", "SMALLINT", "", "May be NULL"),
                ("created_at", "TIMESTAMP", "", "Record creation timestamp"),
                ("updated_at", "TIMESTAMP", "", "Last update timestamp"),
            ],
            "notes": "Entity resolved from multiple sources. player_id is a canonical UUID mapped via fuzzy name + DOB matching.",
        },
        "matches": {
            "grain": "One row per match",
            "pk": "match_id",
            "cols": [
                ("match_id", "VARCHAR(36)", "PK", "UUID"),
                ("home_team_id", "VARCHAR(36)", "FK→teams", ""),
                ("away_team_id", "VARCHAR(36)", "FK→teams", ""),
                ("kickoff_datetime", "TIMESTAMP", "", "UTC timezone"),
                ("competition", "VARCHAR", "", "Standardized competition code"),
                ("season", "VARCHAR(9)", "", "e.g. 2023-24"),
                ("stadium_id", "VARCHAR(36)", "FK→stadiums", ""),
                ("home_score", "TINYINT", "", "NULL until completed"),
                ("away_score", "TINYINT", "", "NULL until completed"),
                ("status", "VARCHAR", "", "scheduled / completed / cancelled"),
            ],
            "notes": "Central fact table. All time-series analyses anchor to match_id and kickoff_datetime.",
        },
        "appearances": {
            "grain": "One row per player per match",
            "pk": "appearance_id",
            "cols": [
                ("appearance_id", "VARCHAR(36)", "PK", "UUID"),
                ("player_id", "VARCHAR(36)", "FK→players", ""),
                ("match_id", "VARCHAR(36)", "FK→matches", ""),
                ("team_id", "VARCHAR(36)", "FK→teams", ""),
                ("minutes_played", "SMALLINT", "", "0-120"),
                ("position_played", "VARCHAR(3)", "", "Actual position in match"),
                ("started", "BOOLEAN", "", "TRUE if in starting XI"),
                ("sub_on_minute", "TINYINT", "", "NULL if started or DNP"),
                ("sub_off_minute", "TINYINT", "", "NULL if played full game"),
            ],
            "notes": "Bridge table between players and matches. UNIQUE constraint on (player_id, match_id).",
        },
        "injuries": {
            "grain": "One row per injury event",
            "pk": "injury_id",
            "cols": [
                ("injury_id", "VARCHAR(36)", "PK", "UUID"),
                ("player_id", "VARCHAR(36)", "FK→players", ""),
                ("match_id", "VARCHAR(36)", "FK→matches", "Last match before report"),
                ("report_date", "DATE", "", "Date injury became public"),
                ("injury_type", "VARCHAR", "", "Standardized: hamstring, ACL, etc."),
                ("severity", "VARCHAR", "", "minor / moderate / severe"),
                ("return_date", "DATE", "", "May be NULL (unknown return)"),
                ("days_missed", "SMALLINT", "", "Derived from return_date - report_date"),
                ("source_reliability", "FLOAT", "", "0-1 confidence in report accuracy"),
            ],
            "notes": "Temporal assignment (match_id) is an approximation. Injury may have occurred during training.",
        },
        "teams": {
            "grain": "One row per team",
            "pk": "team_id",
            "cols": [
                ("team_id", "VARCHAR(36)", "PK", "UUID"),
                ("team_name", "VARCHAR", "", "Canonical name"),
                ("short_code", "CHAR(3)", "", "e.g. MCI, ARS"),
                ("league", "VARCHAR", "", "Standardized league code"),
                ("country", "CHAR(3)", "", "ISO 3166-1 alpha-3"),
                ("stadium_id", "VARCHAR(36)", "FK→stadiums", ""),
                ("active_from", "DATE", "", "Club founding or dataset start"),
            ],
            "notes": "Slowly changing dimension. Historical team changes tracked via active_from / active_to pattern.",
        },
        "environmental_conditions": {
            "grain": "One row per match",
            "pk": "condition_id",
            "cols": [
                ("condition_id", "VARCHAR(36)", "PK", "UUID"),
                ("match_id", "VARCHAR(36)", "FK→matches", "1:1 with matches"),
                ("temperature_c", "FLOAT", "", "At kickoff, degrees Celsius"),
                ("humidity_pct", "FLOAT", "", "0-100"),
                ("precipitation_mm", "FLOAT", "", "Rainfall in preceding 24h"),
                ("wind_kph", "FLOAT", "", "Average wind speed"),
                ("surface_type", "VARCHAR", "", "natural / hybrid / artificial"),
                ("pitch_hardness_proxy", "VARCHAR", "", "soft / firm / hard — proxy only"),
                ("data_source", "VARCHAR", "", "weather API identifier"),
            ],
            "notes": "Proxy data. Stadium microclimate not directly measurable. surface_type and hardness are coarse categorical proxies.",
        },
    }

    st.markdown("<div class='section-header'>Table specifications</div>",
                unsafe_allow_html=True)

    selected = st.selectbox(
        "Select table",
        list(tables.keys()),
        format_func=lambda x: f"📋 {x}",
    )

    t = tables[selected]
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h4>Grain</h4>
            <div style='color:#0D1B2A; font-size:0.9rem; font-weight:600; line-height:1.4;'>
                {t['grain']}
            </div>
        </div>
        <div class='metric-card'>
            <h4>Primary Key</h4>
            <div style='color:#C9A84C; font-family:IBM Plex Mono,monospace; font-size:0.85rem;'>
                {t['pk']}
            </div>
        </div>
        <div style='background:#F3F0FF; border:1px solid #D8B4FE; border-radius:6px; padding:14px;'>
            <div style='font-family:IBM Plex Mono,monospace; font-size:0.65rem;
                        color:#6B21A8; text-transform:uppercase; letter-spacing:0.1em;
                        margin-bottom:8px;'>Notes</div>
            <div style='color:#4A5568; font-size:0.8rem; line-height:1.6;'>{t['notes']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        df = pd.DataFrame(t["cols"], columns=["Column", "Type", "Constraint", "Notes"])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Column":     st.column_config.TextColumn("Column",     width="medium"),
                "Type":       st.column_config.TextColumn("Type",       width="small"),
                "Constraint": st.column_config.TextColumn("Constraint", width="small"),
                "Notes":      st.column_config.TextColumn("Notes",      width="large"),
            },
        )
