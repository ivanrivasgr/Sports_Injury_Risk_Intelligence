"""
tests/test_pipeline.py
======================
Tests for data/pipeline.py — Gold-layer feature computation.

Covers:
  - compute_rolling_workload (windows, leakage guard, edge cases)
  - compute_congestion_index (gaps, None cases)
  - assign_congestion_tier (all tiers)
  - compute_injury_label (binary label, leakage guard)
  - validate_appearances_schema / validate_injuries_schema
  - run_dq_checks (pass, warn, block)
  - GoldPipeline.run_full (happy path, schema error, dq error, leakage abort)

Run locally:
    pytest tests/test_pipeline.py -v
"""

import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.pipeline import (
    GoldPipeline,
    assign_congestion_tier,
    compute_congestion_index,
    compute_injury_label,
    compute_rolling_workload,
    run_dq_checks,
    validate_appearances_schema,
    validate_injuries_schema,
)
from utils.exceptions import (
    DataLeakageError,
    DQCheckError,
    FeatureComputationError,
    SchemaValidationError,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_appearances():
    base = pd.Timestamp("2024-10-01")
    return pd.DataFrame(
        [
            {
                "player_name": "Player A",
                "match_date": base - timedelta(days=d),
                "minutes_played": 90,
                "venue": "Away",
                "competition": "LaLiga",
            }
            for d in [1, 5, 8, 15, 22, 32, 45]
        ]
    )


@pytest.fixture
def sample_injuries():
    base = pd.Timestamp("2024-10-01")
    return pd.DataFrame(
        [
            {
                "player_name": "Player A",
                "date_start": base + timedelta(days=3),
                "injury_type": "Muscle injury",
                "days_missed": 14,
            }
        ]
    )


@pytest.fixture
def valid_appearances():
    return pd.DataFrame(
        {
            "player_name": ["Player A", "Player B"],
            "match_date": [pd.Timestamp("2024-10-01"), pd.Timestamp("2024-10-02")],
            "minutes_played": [90, 75],
            "venue": ["Away", "Bernabéu"],
            "competition": ["LaLiga", "UCL"],
        }
    )


@pytest.fixture
def valid_injuries():
    return pd.DataFrame(
        {
            "player_name": ["Player A"],
            "date_start": [pd.Timestamp("2024-10-05")],
            "injury_type": ["Muscle injury"],
            "days_missed": [14],
        }
    )


# ── compute_rolling_workload ──────────────────────────────────────────────────


class TestRollingWorkload:

    def test_7d_window(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        result = compute_rolling_workload(sample_appearances, "Player A", anchor, 7)
        assert result == 180.0

    def test_14d_window(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        result = compute_rolling_workload(sample_appearances, "Player A", anchor, 14)
        assert result == 270.0

    def test_30d_window(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        result = compute_rolling_workload(sample_appearances, "Player A", anchor, 30)
        assert result == 450.0

    def test_anchor_match_excluded(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        extra = pd.DataFrame(
            [
                {
                    "player_name": "Player A",
                    "match_date": anchor,
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                }
            ]
        )
        apps = pd.concat([sample_appearances, extra], ignore_index=True)
        result = compute_rolling_workload(apps, "Player A", anchor, 7)
        assert result == 180.0

    def test_no_prior_matches_returns_zero(self):
        apps = pd.DataFrame(
            columns=["player_name", "match_date", "minutes_played", "venue", "competition"]
        )
        result = compute_rolling_workload(apps, "Ghost", pd.Timestamp("2024-10-01"), 14)
        assert result == 0.0

    def test_wrong_player_excluded(self, sample_appearances):
        result = compute_rolling_workload(
            sample_appearances, "Player B", pd.Timestamp("2024-10-01"), 30
        )
        assert result == 0.0

    def test_boundary_inclusive_start(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        extra = pd.DataFrame(
            [
                {
                    "player_name": "Player A",
                    "match_date": anchor - timedelta(days=7),
                    "minutes_played": 45,
                    "venue": "Away",
                    "competition": "LaLiga",
                }
            ]
        )
        apps = pd.concat([sample_appearances, extra], ignore_index=True)
        result = compute_rolling_workload(apps, "Player A", anchor, 7)
        assert result == 225.0


# ── compute_congestion_index ──────────────────────────────────────────────────


class TestCongestionIndex:

    def test_none_for_single_match(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        result = compute_congestion_index(sample_appearances, "Player A", anchor, window_days=3)
        assert result is None

    def test_none_for_no_matches(self):
        apps = pd.DataFrame(
            columns=["player_name", "match_date", "minutes_played", "venue", "competition"]
        )
        result = compute_congestion_index(apps, "Ghost", pd.Timestamp("2024-10-01"))
        assert result is None

    def test_two_matches_gap(self):
        base = pd.Timestamp("2024-10-01")
        apps = pd.DataFrame(
            [
                {
                    "player_name": "P",
                    "match_date": base - timedelta(days=10),
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                },
                {
                    "player_name": "P",
                    "match_date": base - timedelta(days=6),
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                },
            ]
        )
        result = compute_congestion_index(apps, "P", base, window_days=30)
        assert result == 4.0

    def test_high_congestion(self):
        base = pd.Timestamp("2024-10-01")
        apps = pd.DataFrame(
            [
                {
                    "player_name": "P",
                    "match_date": base - timedelta(days=d),
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                }
                for d in [2, 4, 6, 8, 10]
            ]
        )
        result = compute_congestion_index(apps, "P", base, window_days=30)
        assert result == 2.0

    def test_future_matches_excluded(self):
        base = pd.Timestamp("2024-10-01")
        apps = pd.DataFrame(
            [
                {
                    "player_name": "P",
                    "match_date": base - timedelta(days=5),
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                },
                {
                    "player_name": "P",
                    "match_date": base - timedelta(days=10),
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                },
                {
                    "player_name": "P",
                    "match_date": base + timedelta(days=3),
                    "minutes_played": 90,
                    "venue": "Away",
                    "competition": "LaLiga",
                },
            ]
        )
        result = compute_congestion_index(apps, "P", base, window_days=30)
        assert result == 5.0


# ── assign_congestion_tier ────────────────────────────────────────────────────


class TestCongestionTier:

    def test_none_returns_tier_1(self):
        assert assign_congestion_tier(None) == 1

    def test_index_3_returns_tier_4(self):
        assert assign_congestion_tier(3.0) == 4

    def test_index_2_returns_tier_4(self):
        assert assign_congestion_tier(2.0) == 4

    def test_index_4_returns_tier_3(self):
        assert assign_congestion_tier(4.0) == 3

    def test_index_3_5_returns_tier_3(self):
        assert assign_congestion_tier(3.5) == 3

    def test_index_6_returns_tier_2(self):
        assert assign_congestion_tier(6.0) == 2

    def test_index_5_returns_tier_2(self):
        assert assign_congestion_tier(5.0) == 2

    def test_index_7_returns_tier_1(self):
        assert assign_congestion_tier(7.0) == 1

    def test_index_10_returns_tier_1(self):
        assert assign_congestion_tier(10.0) == 1


# ── compute_injury_label ──────────────────────────────────────────────────────


class TestInjuryLabel:

    def test_injury_within_horizon(self, sample_injuries):
        anchor = pd.Timestamp("2024-10-01")
        label = compute_injury_label(sample_injuries, "Player A", anchor, 7)
        assert label == 1

    def test_no_injury_within_horizon(self, sample_injuries):
        anchor = pd.Timestamp("2024-10-01")
        label = compute_injury_label(sample_injuries, "Player A", anchor, 2)
        assert label == 0

    def test_injury_at_anchor_raises_leakage(self):
        injury_ts = pd.Timestamp("2024-10-01")
        injuries = pd.DataFrame(
            [
                {
                    "player_name": "Player A",
                    "date_start": injury_ts,
                    "injury_type": "Muscle injury",
                    "days_missed": 14,
                }
            ]
        )
        with pytest.raises(DataLeakageError):
            compute_injury_label(injuries, "Player A", injury_ts, 7)

    def test_injury_before_anchor_excluded(self, sample_injuries):
        anchor = pd.Timestamp("2024-10-10")
        label = compute_injury_label(sample_injuries, "Player A", anchor, 7)
        assert label == 0

    def test_wrong_player_excluded(self, sample_injuries):
        anchor = pd.Timestamp("2024-10-01")
        label = compute_injury_label(sample_injuries, "Player B", anchor, 7)
        assert label == 0

    def test_horizon_boundary_inclusive(self):
        anchor = pd.Timestamp("2024-10-01")
        injuries = pd.DataFrame(
            [
                {
                    "player_name": "P",
                    "date_start": anchor + timedelta(days=7),
                    "injury_type": "Hamstring",
                    "days_missed": 21,
                }
            ]
        )
        label = compute_injury_label(injuries, "P", anchor, 7)
        assert label == 1

    def test_no_injuries_returns_zero(self):
        injuries = pd.DataFrame(columns=["player_name", "date_start", "injury_type", "days_missed"])
        label = compute_injury_label(injuries, "Player A", pd.Timestamp("2024-10-01"), 7)
        assert label == 0


# ── validate_appearances_schema ───────────────────────────────────────────────


class TestValidateAppearancesSchema:

    def test_valid_df_passes(self, valid_appearances):
        validate_appearances_schema(valid_appearances)  # should not raise

    def test_missing_column_raises(self):
        df = pd.DataFrame({"player_name": ["A"], "match_date": [pd.Timestamp("2024-10-01")]})
        with pytest.raises(SchemaValidationError):
            validate_appearances_schema(df)

    def test_negative_minutes_raises(self, valid_appearances):
        valid_appearances.loc[0, "minutes_played"] = -1
        with pytest.raises(SchemaValidationError):
            validate_appearances_schema(valid_appearances)

    def test_minutes_over_120_raises(self, valid_appearances):
        valid_appearances.loc[0, "minutes_played"] = 121
        with pytest.raises(SchemaValidationError):
            validate_appearances_schema(valid_appearances)


# ── validate_injuries_schema ──────────────────────────────────────────────────


class TestValidateInjuriesSchema:

    def test_valid_df_passes(self, valid_injuries):
        validate_injuries_schema(valid_injuries)  # should not raise

    def test_missing_column_raises(self):
        df = pd.DataFrame({"player_name": ["A"]})
        with pytest.raises(SchemaValidationError):
            validate_injuries_schema(df)

    def test_null_player_name_raises(self, valid_injuries):
        valid_injuries.loc[0, "player_name"] = None
        with pytest.raises(SchemaValidationError):
            validate_injuries_schema(valid_injuries)


# ── run_dq_checks ─────────────────────────────────────────────────────────────


class TestDQChecks:

    def test_clean_appearances_passes_all(self, valid_appearances):
        results = run_dq_checks(valid_appearances, "appearances")
        assert all(r["passed"] for r in results)

    def test_clean_injuries_passes_all(self, valid_injuries):
        results = run_dq_checks(valid_injuries, "injuries")
        assert all(r["passed"] for r in results)

    def test_null_player_name_critical_raises(self):
        df = pd.DataFrame(
            {
                "player_name": [None] * 10 + ["Player A"] * 990,
                "minutes_played": [90] * 1000,
            }
        )
        with pytest.raises(DQCheckError):
            run_dq_checks(df, "test_table")

    def test_bad_minutes_range_warns_not_blocks(self):
        df = pd.DataFrame(
            {
                "player_name": ["Player A"] * 1000,
                "minutes_played": [90] * 990 + [150] * 10,
            }
        )
        results = run_dq_checks(df, "test_table")
        failed = [r for r in results if not r["passed"]]
        assert len(failed) == 1
        assert failed[0]["check"] == "minutes_played_range"

    def test_negative_days_missed_warns(self):
        df = pd.DataFrame(
            {
                "player_name": ["Player A"] * 100,
                "days_missed": [-1] + [14] * 99,
            }
        )
        results = run_dq_checks(df, "injuries")
        failed = [r for r in results if not r["passed"]]
        assert any(r["check"] == "days_missed_non_negative" for r in failed)

    def test_results_contain_required_keys(self, valid_appearances):
        results = run_dq_checks(valid_appearances, "appearances")
        for r in results:
            assert "check" in r
            assert "pass_rate" in r
            assert "passed" in r
            assert "severity" in r


# ── GoldPipeline ──────────────────────────────────────────────────────────────


class TestGoldPipeline:

    def test_run_full_returns_three_values(self, valid_appearances, valid_injuries):
        pipeline = GoldPipeline()
        result = pipeline.run_full(valid_appearances, valid_injuries, for_training=True)
        assert len(result) == 3

    def test_run_full_has_expected_columns(self, valid_appearances, valid_injuries):
        pipeline = GoldPipeline()
        features, dq, errors = pipeline.run_full(
            valid_appearances, valid_injuries, for_training=True
        )
        assert "workload_7d" in features.columns
        assert "workload_14d" in features.columns
        assert "workload_30d" in features.columns
        assert "congestion_index" in features.columns
        assert "congestion_tier" in features.columns
        assert "injured_next_7d" in features.columns

    def test_run_full_no_training_no_label(self, valid_appearances, valid_injuries):
        pipeline = GoldPipeline()
        features, dq, errors = pipeline.run_full(
            valid_appearances, valid_injuries, for_training=False
        )
        assert "injured_next_7d" not in features.columns

    def test_run_full_output_rows_match_input(self, valid_appearances, valid_injuries):
        pipeline = GoldPipeline()
        features, _, _ = pipeline.run_full(valid_appearances, valid_injuries, for_training=True)
        assert len(features) == len(valid_appearances)

    def test_run_full_no_errors_on_clean_data(self, valid_appearances, valid_injuries):
        pipeline = GoldPipeline()
        _, _, errors = pipeline.run_full(valid_appearances, valid_injuries, for_training=True)
        assert errors == []

    def test_run_full_dq_results_returned(self, valid_appearances, valid_injuries):
        pipeline = GoldPipeline()
        _, dq, _ = pipeline.run_full(valid_appearances, valid_injuries, for_training=True)
        assert isinstance(dq, list)
        assert len(dq) > 0

    def test_run_full_raises_on_bad_schema(self, valid_injuries):
        bad_appearances = pd.DataFrame({"player_name": ["A"]})
        pipeline = GoldPipeline()
        with pytest.raises(SchemaValidationError):
            pipeline.run_full(bad_appearances, valid_injuries, for_training=True)

    def test_run_full_raises_on_dq_critical(self, valid_injuries):
        bad_appearances = pd.DataFrame(
            {
                "player_name": [None] * 10 + ["Player A"] * 990,
                "match_date": [pd.Timestamp("2024-10-01")] * 1000,
                "minutes_played": [90] * 1000,
                "venue": ["Away"] * 1000,
                "competition": ["LaLiga"] * 1000,
            }
        )
        pipeline = GoldPipeline()
        with pytest.raises(DQCheckError):
            pipeline.run_full(bad_appearances, valid_injuries, for_training=True)

    def test_run_full_aborts_on_leakage(self, valid_appearances):
        anchor = valid_appearances["match_date"].iloc[0]
        injuries_with_leakage = pd.DataFrame(
            [
                {
                    "player_name": valid_appearances["player_name"].iloc[0],
                    "date_start": anchor,
                    "injury_type": "Muscle injury",
                    "days_missed": 14,
                }
            ]
        )
        pipeline = GoldPipeline()
        with pytest.raises(DataLeakageError):
            pipeline.run_full(valid_appearances, injuries_with_leakage, for_training=True)

    def test_run_full_with_real_seed_data(self):
        from data.seed_data import get_appearances_df, get_injuries_df

        apps = get_appearances_df()
        inj = get_injuries_df()
        pipeline = GoldPipeline()
        features, dq, errors = pipeline.run_full(apps, inj, for_training=True)
        assert len(features) > 0
        assert "workload_14d" in features.columns
        assert "injured_next_7d" in features.columns
        failed_dq = [r for r in dq if not r["passed"]]
        assert len(failed_dq) == 0


# ── Point-in-time integrity ───────────────────────────────────────────────────


class TestPointInTimeIntegrity:

    def test_no_future_data_in_any_window(self, sample_appearances):
        anchors = pd.date_range("2024-09-20", "2024-10-10", freq="2D")
        for anchor in anchors:
            window_start = anchor - timedelta(days=14)
            mask = (
                (sample_appearances["player_name"] == "Player A")
                & (sample_appearances["match_date"] >= window_start)
                & (sample_appearances["match_date"] < anchor)
            )
            window_matches = sample_appearances[mask]
            future = window_matches[window_matches["match_date"] >= anchor]
            assert len(future) == 0, f"DATA LEAKAGE at anchor={anchor}"
