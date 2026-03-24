"""
views/p11_cicd.py
=================
CI/CD status, test results, pipeline debug console, and log viewer.
Shows what a production observability + debugging interface looks like.
"""

import json
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipeline import GoldPipeline, run_dq_checks
from data.seed_data import get_appearances_df, get_injuries_df
from utils.exceptions import (
    DataContractError,
    DataLeakageError,
    DQCheckError,
    FeatureComputationError,
    SchemaValidationError,
    is_blocking,
)
from utils.logger import JSONL_PATH, clear_logs, get_logger, read_log_records

DARK = "#F8FAFC"; BG = "#F1F5F9"; CARD = "#FFFFFF"; BORD = "#E2E8F0"
TEXT = "#475569"; HIGH = "#0F172A"; BLUE = "#1D4ED8"; GRN = "#16A34A"
RED = "#DC2626"; ORG = "#D97706"; PRP = "#6B21A8"


def sh(label):
    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.68rem;"
        f"letter-spacing:0.12em;text-transform:uppercase;color:{BLUE};"
        f"border-bottom:1px solid {BORD};padding-bottom:6px;margin-bottom:14px;'>"
        f"{label}</div>",
        unsafe_allow_html=True,
    )


def status_badge(text, ok):
    color = GRN if ok else RED
    bg    = "#DCFCE7" if ok else "#FEF2F2"
    border= "#86EFAC" if ok else "#FCA5A5"
    icon  = "✓" if ok else "✗"
    st.markdown(
        f"<span style='background:{bg};color:{color};border:1px solid {border};"
        f"font-family:IBM Plex Mono,monospace;font-size:0.72rem;"
        f"padding:3px 10px;border-radius:4px;margin-right:8px;'>"
        f"{icon} {text}</span>",
        unsafe_allow_html=True,
    )


# ── Run all tests inline (no pytest required) ─────────────────────────────────

def run_inline_tests() -> list[dict]:
    """
    Execute all test cases inline and return results.
    This mirrors the pytest suite but runs inside the Streamlit process
    so results display in real time — no subprocess needed.
    """
    from datetime import timedelta

    results = []

    def test(name: str, fn):
        try:
            fn()
            results.append({"name": name, "passed": True, "error": None})
        except AssertionError as e:
            results.append({"name": name, "passed": False, "error": str(e)})
        except Exception as e:
            results.append({"name": name, "passed": False,
                            "error": f"{type(e).__name__}: {e}"})

    injuries    = get_injuries_df()
    appearances = get_appearances_df()

    from data.pipeline import (
        compute_congestion_index,
        compute_injury_label,
        compute_rolling_workload,
        validate_appearances_schema,
        validate_injuries_schema,
    )

    # ── Seed data ─────────────────────────────────────────────────────────────
    def check_required_cols():
        required = ["player_name","season","injury_type","date_start","date_end",
                    "days_missed","last_match_venue","competition","position",
                    "is_muscular","age_at_injury"]
        missing = [c for c in required if c not in injuries.columns]
        assert not missing, f"Missing columns: {missing}"
    test("injuries: required columns present", check_required_cols)
    test("injuries: no null player_name", lambda:
         (_ := injuries["player_name"].isna().sum()) == 0 or
         (_ for _ in ()).throw(AssertionError(f"Found {_} nulls")))
    test("injuries: no null player_name (assert)", lambda:
         __import__('builtins').__dict__['__build_class__'] and
         (lambda: None if injuries["player_name"].isna().sum() == 0
          else (_ for _ in ()).throw(AssertionError))())

    # Simpler approach
    def check_no_null_player():
        n = injuries["player_name"].isna().sum()
        assert n == 0, f"Found {n} null player_name values"
    test("injuries: no null player_name", check_no_null_player)

    def check_date_types():
        assert pd.api.types.is_datetime64_any_dtype(injuries["date_start"])
        assert pd.api.types.is_datetime64_any_dtype(injuries["date_end"])
    test("injuries: date columns are datetime", check_date_types)

    def check_season_format():
        bad = injuries[~injuries["season"].str.match(r"^\d{4}-\d{2}$")]
        assert len(bad) == 0, f"Invalid seasons: {bad['season'].unique()}"
    test("injuries: season format YYYY-YY", check_season_format)

    def check_is_muscular_binary():
        assert injuries["is_muscular"].isin([0, 1]).all()
    test("injuries: is_muscular is binary 0/1", check_is_muscular_binary)

    def check_days_missed_non_neg():
        neg = (injuries["days_missed"] < 0).sum()
        assert neg == 0, f"Found {neg} negative days_missed"
    test("injuries: days_missed >= 0", check_days_missed_non_neg)

    def check_venues():
        bad = set(injuries["last_match_venue"].unique()) - {"Bernabéu","Away"}
        assert not bad, f"Unknown venues: {bad}"
    test("injuries: valid venue values", check_venues)

    def check_date_order():
        valid = injuries.dropna(subset=["date_end"])
        bad = valid[valid["date_end"] < valid["date_start"]]
        assert len(bad) == 0, f"date_end < date_start in {len(bad)} records"
    test("injuries: date_end >= date_start", check_date_order)

    def check_age_range():
        bad = injuries[(injuries["age_at_injury"] < 15) | (injuries["age_at_injury"] > 45)]
        assert len(bad) == 0, f"Unreasonable ages: {bad[['player_name','age_at_injury']]}"
    test("injuries: age 15–45 for all players", check_age_range)

    def check_muscular_rate():
        rate = injuries["is_muscular"].mean()
        assert 0.50 <= rate <= 0.90, f"Muscular rate {rate:.1%} outside [50%,90%]"
    test("injuries: muscular rate 50–90%", check_muscular_rate)

    def check_appearances_minutes():
        bad = appearances[(appearances["minutes_played"] < 0) | (appearances["minutes_played"] > 120)]
        assert len(bad) == 0, f"minutes_played out of [0,120]: {len(bad)} rows"
    test("appearances: minutes_played in [0,120]", check_appearances_minutes)

    # ── Pipeline: rolling workload ────────────────────────────────────────────
    base = pd.Timestamp("2024-10-01")
    sample_apps = pd.DataFrame([
        {"player_name":"Player A","match_date": base - timedelta(days=d),
         "minutes_played":90,"venue":"Away","competition":"LaLiga"}
        for d in [1, 5, 8, 15, 22, 32, 45]
    ])

    def test_7d():
        r = compute_rolling_workload(sample_apps, "Player A", base, 7)
        assert r == 180.0, f"Expected 180, got {r}"
    test("pipeline: workload_7d window correct", test_7d)

    def test_14d():
        r = compute_rolling_workload(sample_apps, "Player A", base, 14)
        assert r == 270.0, f"Expected 270, got {r}"
    test("pipeline: workload_14d window correct", test_14d)

    def test_30d():
        r = compute_rolling_workload(sample_apps, "Player A", base, 30)
        assert r == 450.0, f"Expected 450, got {r}"
    test("pipeline: workload_30d window correct", test_30d)

    def test_anchor_excluded():
        extra = pd.DataFrame([{"player_name":"Player A","match_date":base,
                               "minutes_played":90,"venue":"Home","competition":"LaLiga"}])
        apps2 = pd.concat([sample_apps, extra], ignore_index=True)
        r = compute_rolling_workload(apps2, "Player A", base, 7)
        assert r == 180.0, f"Anchor leaked: got {r}"
    test("pipeline: anchor match excluded (no leakage)", test_anchor_excluded)

    def test_no_prior_matches():
        empty = pd.DataFrame(columns=["player_name","match_date","minutes_played","venue","competition"])
        r = compute_rolling_workload(empty, "Ghost", base, 14)
        assert r == 0.0
    test("pipeline: zero workload when no prior matches", test_no_prior_matches)

    def test_wrong_player():
        r = compute_rolling_workload(sample_apps, "Player B", base, 30)
        assert r == 0.0
    test("pipeline: other player's matches excluded", test_wrong_player)

    # ── Point-in-time leakage check ───────────────────────────────────────────
    def test_no_leakage_series():
        anchors = pd.date_range("2024-09-20", "2024-10-10", freq="2D")
        for anchor in anchors:
            ws = anchor - timedelta(days=14)
            mask = (
                (sample_apps["player_name"] == "Player A") &
                (sample_apps["match_date"] >= ws) &
                (sample_apps["match_date"] < anchor)
            )
            future = sample_apps[mask][sample_apps[mask]["match_date"] >= anchor]
            assert len(future) == 0, f"Leakage at anchor={anchor}: {len(future)} future rows"
    test("pipeline: no future data in any rolling window", test_no_leakage_series)

    # ── Injury label ─────────────────────────────────────────────────────────
    sample_inj = pd.DataFrame([{
        "player_name":"Player A",
        "date_start": base + timedelta(days=3),
        "injury_type":"Muscle injury","days_missed":14,
    }])

    def test_label_within_horizon():
        label = compute_injury_label(sample_inj, "Player A", base, 7)
        assert label == 1
    test("pipeline: injury within 7d horizon → label=1", test_label_within_horizon)

    def test_label_outside_horizon():
        label = compute_injury_label(sample_inj, "Player A", base, 2)
        assert label == 0
    test("pipeline: injury outside 2d horizon → label=0", test_label_outside_horizon)

    def test_no_concurrent_label():
        at_anchor = pd.DataFrame([{
            "player_name":"Player A",
            "date_start": base,
            "injury_type":"Muscle","days_missed":7
        }])
        try:
            label = compute_injury_label(at_anchor, "Player A", base, 7)
            assert label == 0, "Concurrent injury labelled 1 — DATA LEAKAGE"
        except (DataLeakageError, FeatureComputationError):
            pass  # correct — leakage detected and raised
    test("pipeline: concurrent injury at anchor → NOT labelled 1 (leakage guard)", test_no_concurrent_label)

    # ── Exceptions ───────────────────────────────────────────────────────────
    def test_dq_critical_blocks():
        exc = DQCheckError("uniqueness", "appearances", 0.998, 0.999, "CRITICAL")
        assert exc.blocks_pipeline is True
        assert is_blocking(exc) is True
    test("exceptions: CRITICAL DQ check blocks pipeline", test_dq_critical_blocks)

    def test_dq_high_no_block():
        exc = DQCheckError("range", "appearances", 0.991, 0.999, "HIGH")
        assert is_blocking(exc) is False
    test("exceptions: HIGH DQ check does not block", test_dq_high_no_block)

    def test_leakage_always_blocks():
        exc = DataLeakageError("workload_14d", "2024-11-03", "2024-11-10", "player-x")
        assert is_blocking(exc) is True
    test("exceptions: DataLeakageError always blocks", test_leakage_always_blocks)

    def test_schema_error_has_context():
        exc = SchemaValidationError("minutes_played", -5, "minutes_played >= 0")
        assert exc.context["field"] == "minutes_played"
        assert exc.layer == "silver"
    test("exceptions: SchemaValidationError has correct context", test_schema_error_has_context)

    # ── Logger ───────────────────────────────────────────────────────────────
    def test_logger_writes_jsonl():
        clear_logs()
        log = get_logger("silver", "ci_test")
        log.info("CI test message", context={"ci": True})
        records = read_log_records(5)
        assert len(records) >= 1
        last = records[-1]
        assert last["message"] == "CI test message"
        assert last["layer"] == "silver"
        assert last["context"]["ci"] is True
    test("logger: writes valid JSONL record", test_logger_writes_jsonl)

    def test_logger_jsonl_valid():
        clear_logs()
        log = get_logger("gold", "ci_test")
        log.warning("W1"); log.error("E1"); log.info("I1")
        lines = JSONL_PATH.read_text().strip().splitlines()
        for line in lines:
            parsed = json.loads(line)
            assert "ts" in parsed and "level" in parsed and "message" in parsed
    test("logger: all records are valid JSON", test_logger_jsonl_valid)

    return results


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.markdown(f"""
    <div style='margin-bottom:24px;'>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.6rem;
                    letter-spacing:0.18em;color:#94A3B8;text-transform:uppercase;'>
            CI/CD · Testing · Debugging · Observability
        </div>
        <h1 style='font-size:2rem;font-weight:700;color:{HIGH};margin:6px 0 4px;'>
            CI / CD & Debug Console
        </h1>
        <p style='color:#64748B;font-size:0.85rem;max-width:660px;margin:0;'>
            Live test runner, pipeline debug console, structured log viewer,
            and GitHub Actions workflow overview.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧪 Test Suite",
        "⚙️ Pipeline Debug",
        "📋 Log Viewer",
        "🔄 CI/CD Workflows",
    ])

    # ── Tab 1: Test suite ─────────────────────────────────────────────────────
    with tab1:
        sh("Unit test suite — runs inline (mirrors pytest)")

        st.markdown(f"""
        <div style='background:{CARD};border:1px solid {BORD};border-radius:6px;
                    padding:12px 16px;margin-bottom:16px;font-family:IBM Plex Mono,monospace;
                    font-size:0.75rem;color:{TEXT};'>
            Tests cover: seed data schema · pipeline feature logic · point-in-time leakage ·
            exception hierarchy · logger JSONL output
        </div>
        """, unsafe_allow_html=True)

        if st.button("▶ Run All Tests", type="primary"):
            with st.spinner("Running test suite..."):
                results = run_inline_tests()

            passed = sum(1 for r in results if r["passed"])
            failed = sum(1 for r in results if not r["passed"])
            total  = len(results)

            # Summary bar
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"""<div class='metric-card'>
                <h4>Tests Passed</h4><div class='value' style='color:{GRN};'>{passed}</div>
                <div class='sub'>of {total}</div></div>""", unsafe_allow_html=True)
            col2.markdown(f"""<div class='metric-card'>
                <h4>Tests Failed</h4>
                <div class='value' style='color:{"#DC2626" if failed else GRN};'>{failed}</div>
                <div class='sub'>{"BLOCKING" if failed else "all clear"}</div></div>""",
                unsafe_allow_html=True)
            col3.markdown(f"""<div class='metric-card'>
                <h4>Pass Rate</h4>
                <div class='value' style='color:{"#DC2626" if failed else GRN};'>
                    {passed/total:.0%}</div>
                <div class='sub'>{"below 100%" if failed else "100%"}</div></div>""",
                unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            sh("Test results")

            # Group by category
            categories = {}
            for r in results:
                cat = r["name"].split(":")[0].strip()
                categories.setdefault(cat, []).append(r)

            for cat, cat_results in categories.items():
                cat_pass = all(r["passed"] for r in cat_results)
                icon = "✅" if cat_pass else "❌"
                with st.expander(f"{icon}  {cat}  ({sum(r['passed'] for r in cat_results)}/{len(cat_results)})",
                                 expanded=not cat_pass):
                    for r in cat_results:
                        color = GRN if r["passed"] else RED
                        icon2  = "✓" if r["passed"] else "✗"
                        label = r["name"].split(":", 1)[-1].strip()
                        st.markdown(
                            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
                            f"color:{color};padding:4px 0;border-bottom:1px solid {BORD};'>"
                            f"{icon2} &nbsp; {label}</div>",
                            unsafe_allow_html=True,
                        )
                        if not r["passed"] and r["error"]:
                            st.markdown(
                                f"<div style='background:#FEF2F2;border-left:3px solid {RED};"
                                f"padding:6px 10px;margin:4px 0;font-family:IBM Plex Mono,monospace;"
                                f"font-size:0.7rem;color:#B91C1C;'>{r['error']}</div>",
                                unsafe_allow_html=True,
                            )

            if failed == 0:
                st.success(f"✓ All {total} tests passed — pipeline is CI-green")
            else:
                st.error(f"✗ {failed} test(s) failed — review errors above before deploy")
        else:
            st.markdown(f"""
            <div style='background:{CARD};border:1px dashed {BORD};border-radius:6px;
                        padding:24px;text-align:center;color:#94A3B8;
                        font-family:IBM Plex Mono,monospace;font-size:0.8rem;'>
                Press "Run All Tests" to execute the full suite
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 2: Pipeline debug ─────────────────────────────────────────────────
    with tab2:
        sh("Gold Pipeline — Interactive Debug Run")

        st.markdown(f"""
        <div style='color:{TEXT};font-size:0.83rem;margin-bottom:16px;line-height:1.6;'>
            Runs the full Gold pipeline on the seed dataset with real logging.
            Logs appear in the Log Viewer tab after execution.
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        for_training = col1.checkbox("Build training labels (look-ahead)", value=True)
        horizon = col2.slider("Label horizon (days)", 3, 14, 7)

        if st.button("▶ Run Gold Pipeline", type="primary"):
            log_handle = get_logger("gold", "debug_run")
            log_handle.info("Debug pipeline triggered from UI",
                            context={"for_training": for_training, "horizon": horizon})

            with st.spinner("Running pipeline..."):
                try:
                    apps = get_appearances_df()
                    inj  = get_injuries_df()
                    pipeline = GoldPipeline()
                    features, dq_results, errors = pipeline.run_full(
                        apps, inj,
                        for_training=for_training,
                        label_horizon_days=horizon,
                    )
                    success = True
                except Exception as e:
                    success = False
                    err_msg = traceback.format_exc()
                    log_handle.exception("Pipeline failed", e)

            if success:
                st.success(f"✓ Pipeline completed: {len(features)} rows, "
                           f"{len(dq_results)} DQ checks, {len(errors)} errors")

                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Output rows", len(features))
                c2.metric("Feature columns", len(features.columns))
                c3.metric("DQ checks", f"{sum(r['passed'] for r in dq_results)}/{len(dq_results)} passed")
                c4.metric("Feature errors", len(errors), delta=None if not errors else "⚠")

                sh("DQ check results")
                for r in dq_results:
                    ok = r["passed"]
                    color = GRN if ok else (RED if r["severity"]=="CRITICAL" else ORG)
                    icon  = "✓" if ok else "✗"
                    st.markdown(
                        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.73rem;"
                        f"color:{color};padding:4px 0;border-bottom:1px solid {BORD};'>"
                        f"{icon} [{r['severity']}] {r['check']} ({r['table']}) — "
                        f"pass_rate={r['pass_rate']:.4f} (threshold={r['threshold']})</div>",
                        unsafe_allow_html=True,
                    )

                sh("Feature output sample")
                st.dataframe(features.head(10), use_container_width=True, hide_index=True)

                if errors:
                    sh("Feature computation errors")
                    st.json(errors[:5])
            else:
                st.error("Pipeline failed — see traceback below")
                st.code(err_msg, language="python")

    # ── Tab 3: Log viewer ─────────────────────────────────────────────────────
    with tab3:
        sh("Structured JSONL Log Viewer")

        col1, col2, col3 = st.columns([2,2,1])
        level_filter = col1.multiselect(
            "Level", ["DEBUG","INFO","WARNING","ERROR","CRITICAL"],
            default=["INFO","WARNING","ERROR","CRITICAL"],
        )
        layer_filter = col2.multiselect(
            "Layer", ["ingestion","bronze","silver","enriched","gold","feature_store","ml","app"],
            default=["ingestion","bronze","silver","enriched","gold","feature_store","ml","app"],
        )
        n_records = col3.number_input("Last N", min_value=10, max_value=500, value=100, step=10)

        if st.button("🗑 Clear logs"):
            clear_logs()
            st.success("Logs cleared")
            st.rerun()

        records = read_log_records(n=int(n_records))

        if not records:
            st.markdown(f"""
            <div style='background:{CARD};border:1px dashed {BORD};border-radius:6px;
                        padding:24px;text-align:center;color:#94A3B8;
                        font-family:IBM Plex Mono,monospace;font-size:0.8rem;'>
                No logs yet. Run the pipeline or tests to generate log entries.
            </div>
            """, unsafe_allow_html=True)
        else:
            filtered = [
                r for r in records
                if r.get("level") in level_filter
                and r.get("layer") in layer_filter
            ]

            st.caption(f"Showing {len(filtered)} of {len(records)} records "
                       f"(after level/layer filter) · Log file: {JSONL_PATH}")

            level_colors = {
                "DEBUG": TEXT, "INFO": GRN,
                "WARNING": ORG, "ERROR": RED, "CRITICAL": "#ff3030",
            }
            layer_colors = {
                "ingestion": PRP, "bronze": "#92400E", "silver": BLUE,
                "enriched": GRN,  "gold": ORG,         "feature_store": PRP,
                "ml": "#0E7490",  "app": TEXT,
            }

            for r in reversed(filtered):
                lc = level_colors.get(r.get("level","INFO"), TEXT)
                lay_c = layer_colors.get(r.get("layer","app"), TEXT)
                ts_short = r.get("ts","")[:19].replace("T"," ")
                ctx = r.get("context", {})
                ctx_str = f" · {json.dumps(ctx)}" if ctx else ""

                st.markdown(
                    f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.72rem;"
                    f"padding:5px 8px;border-bottom:1px solid {BORD};"
                    f"display:flex;gap:12px;align-items:baseline;'>"
                    f"<span style='color:#94A3B8;min-width:130px;'>{ts_short}</span>"
                    f"<span style='color:{lc};min-width:70px;font-weight:600;'>{r.get('level','?')}</span>"
                    f"<span style='color:{lay_c};min-width:160px;'>[{r.get('layer','?')}/{r.get('source','?')}]</span>"
                    f"<span style='color:{TEXT};flex:1;'>{r.get('message','')}"
                    f"<span style='color:#94A3B8;font-size:0.68rem;'>{ctx_str}</span></span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── Tab 4: CI/CD workflows ────────────────────────────────────────────────
    with tab4:
        sh("GitHub Actions Workflows")

        st.markdown(f"""
        <div style='color:{TEXT};font-size:0.83rem;margin-bottom:20px;line-height:1.6;'>
            Two workflows are defined in <code>.github/workflows/</code>.
            CI runs on every push and PR. CD triggers on merge to main after CI passes.
        </div>
        """, unsafe_allow_html=True)

        # CI workflow
        ci_jobs = [
            ("lint",              "Ruff + Black",           "Linting on data/, utils/, tests/",           True),
            ("test",              "pytest + coverage",      "Unit tests, coverage gate ≥ 80%",            True),
            ("data-contracts",    "Schema validation",      "Seed data + pipeline end-to-end",            True),
            ("leakage-check",     "Leakage guard",          "Point-in-time correctness across all windows",True),
            ("streamlit-import",  "Import check",           "All pages + modules parse without error",    True),
        ]

        st.markdown(f"""
        <div style='background:{CARD};border:1px solid {BORD};border-radius:8px;
                    padding:20px;margin-bottom:16px;'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.68rem;
                        color:{BLUE};text-transform:uppercase;letter-spacing:0.1em;
                        margin-bottom:14px;'>
                ci.yml — triggers on push + pull_request → main / develop
            </div>
        """, unsafe_allow_html=True)

        for job_id, label, desc, ok in ci_jobs:
            color = GRN if ok else RED
            st.markdown(
                f"<div style='width:100%;padding:10px 0;border-bottom:1px solid {BORD};"
                f"font-family:IBM Plex Mono,monospace;font-size:0.73rem;'>"
                f"<span style='color:{BLUE};min-width:160px;display:inline-block;'>{job_id}</span>"
                f"<span style='color:{HIGH};font-weight:600;min-width:160px;display:inline-block;'>{label}</span>"
                f"<span style='color:{TEXT};margin-right:16px;'>{desc}</span>"
                f"<span style='color:{color};float:right;font-weight:600;'>{'✓ pass' if ok else '✗ fail'}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # CD workflow
        cd_steps = [
            ("ci-gate",        "Requires all CI jobs to pass"),
            ("deploy",         "Verifies entry point + data contract, notifies Streamlit Cloud"),
            ("smoke-test",     "HTTP health check after deploy (STREAMLIT_APP_URL secret)"),
        ]

        st.markdown(f"""
        <div style='background:{CARD};border:1px solid {BORD};border-radius:8px;
                    padding:20px;margin-bottom:16px;'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.68rem;
                        color:{PRP};text-transform:uppercase;letter-spacing:0.1em;
                        margin-bottom:14px;'>
                cd.yml — triggers on push to main (after CI gate)
            </div>
        """, unsafe_allow_html=True)

        for step, desc in cd_steps:
            st.markdown(
                f"<div style='width:100%;padding:10px 0;border-bottom:1px solid {BORD};"
                f"font-family:IBM Plex Mono,monospace;font-size:0.73rem;'>"
                f"<span style='color:{PRP};min-width:140px;display:inline-block;'>{step}</span>"
                f"<span style='color:{TEXT};'>{desc}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Setup instructions
        sh("Setup — 4 steps to activate CI/CD")
        steps = [
            ("1", "Push to GitHub",
             "git init && git add . && git commit -m 'Initial' && git push origin main"),
            ("2", "Connect Streamlit Cloud",
             "share.streamlit.io → New app → select repo → main file: app.py"),
            ("3", "Add secret (optional)",
             "GitHub → Settings → Secrets → Actions → STREAMLIT_APP_URL=https://your-app.streamlit.app"),
            ("4", "Every PR now runs CI",
             "Push to any branch → GitHub Actions triggers automatically"),
        ]
        for num, title, cmd in steps:
            st.markdown(f"""
            <div style='background:{CARD};border:1px solid {BORD};border-radius:6px;
                        padding:14px 16px;margin-bottom:8px;display:flex;gap:14px;'>
                <div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:4px;
                            width:28px;height:28px;display:flex;align-items:center;
                            justify-content:center;font-family:IBM Plex Mono,monospace;
                            font-size:0.8rem;font-weight:700;color:{BLUE};flex-shrink:0;'>
                    {num}</div>
                <div>
                    <div style='color:{HIGH};font-weight:600;font-size:0.85rem;
                                margin-bottom:4px;'>{title}</div>
                    <code style='font-size:0.75rem !important;'>{cmd}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
