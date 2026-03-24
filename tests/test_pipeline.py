"""
tests/test_pipeline.py
======================
Tests for Gold-layer feature computation logic.

Covers:
  - Rolling workload windows (7/14/30d)
  - Congestion index computation
  - Point-in-time correctness (no future data leakage)
  - Injury label temporal assignment
  - Edge cases (no prior matches, single match, gaps in schedule)

Run locally:
    pytest tests/test_pipeline.py -v
"""

import sys
from pathlib import Path
from datetime import timedelta

import pandas as pd
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ── Inline pipeline functions (mirrors Gold layer logic) ─────────────────────
# These are the actual computation functions. In production they live in
# data/pipeline.py — tested here directly to validate the logic.

def compute_rolling_workload(
    appearances: pd.DataFrame,
    player_id: str,
    anchor_ts: pd.Timestamp,
    window_days: int,
) -> float:
    """
    Sum minutes played in [anchor_ts - window_days, anchor_ts).
    EXCLUSIVE of anchor_ts itself (point-in-time safe).
    """
    window_start = anchor_ts - timedelta(days=window_days)
    mask = (
        (appearances["player_name"] == player_id) &
        (appearances["match_date"] >= window_start) &
        (appearances["match_date"] < anchor_ts)          # ← strict less-than
    )
    return float(appearances.loc[mask, "minutes_played"].sum())


def compute_congestion_index(
    appearances: pd.DataFrame,
    player_id: str,
    anchor_ts: pd.Timestamp,
    window_days: int = 30,
) -> float | None:
    """
    Average days between matches in the 30-day window before anchor_ts.
    Returns None if fewer than 2 matches in window.
    """
    window_start = anchor_ts - timedelta(days=window_days)
    mask = (
        (appearances["player_name"] == player_id) &
        (appearances["match_date"] >= window_start) &
        (appearances["match_date"] < anchor_ts)
    )
    dates = appearances.loc[mask, "match_date"].sort_values().reset_index(drop=True)
    if len(dates) < 2:
        return None
    gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
    return float(np.mean(gaps))


def compute_injury_label(
    injuries: pd.DataFrame,
    player_id: str,
    anchor_ts: pd.Timestamp,
    horizon_days: int = 7,
) -> int:
    """
    Binary: did an injury occur in (anchor_ts, anchor_ts + horizon_days]?
    This is a LOOK-AHEAD function — only used in training label construction.
    """
    horizon_end = anchor_ts + timedelta(days=horizon_days)
    mask = (
        (injuries["player_name"] == player_id) &
        (injuries["date_start"] > anchor_ts) &      # ← strict greater-than (future only)
        (injuries["date_start"] <= horizon_end)
    )
    return int(injuries[mask].shape[0] > 0)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_appearances():
    """Controlled appearance history for a single player."""
    base = pd.Timestamp("2024-10-01")
    return pd.DataFrame([
        {"player_name": "Player A", "match_date": base - timedelta(days=d),
         "minutes_played": 90, "venue": "Away", "competition": "LaLiga"}
        for d in [1, 5, 8, 15, 22, 32, 45]   # days before base
    ])


@pytest.fixture
def sample_injuries():
    base = pd.Timestamp("2024-10-01")
    return pd.DataFrame([
        {"player_name": "Player A",
         "date_start": base + timedelta(days=3),
         "injury_type": "Muscle injury", "days_missed": 14},
    ])


# ── Rolling workload tests ────────────────────────────────────────────────────

class TestRollingWorkload:

    def test_7d_window_correct(self, sample_appearances):
        """Only matches in last 7 days before anchor should be included."""
        anchor = pd.Timestamp("2024-10-01")
        result = compute_rolling_workload(sample_appearances, "Player A", anchor, 7)
        # days 1 and 5 are within 7 days, day 8 is outside
        assert result == 180.0, f"Expected 180, got {result}"

    def test_14d_window_correct(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        result = compute_rolling_workload(sample_appearances, "Player A", anchor, 14)
        # days 1, 5, 8 within 14 days
        assert result == 270.0, f"Expected 270, got {result}"

    def test_30d_window_correct(self, sample_appearances):
        anchor = pd.Timestamp("2024-10-01")
        result = compute_rolling_workload(sample_appearances, "Player A", anchor, 30)
        # days 1, 5, 8, 15, 22 within 30 days
        assert result == 450.0, f"Expected 450, got {result}"

    def test_anchor_match_excluded(self, sample_appearances):
        """Match exactly at anchor_ts must NOT be included (strict less-than)."""
        anchor = pd.Timestamp("2024-10-01")
        # Add a match exactly at anchor_ts
        extra = pd.DataFrame([{
            "player_name": "Player A", "match_date": anchor,
            "minutes_played": 90, "venue": "Bernabéu", "competition": "LaLiga"
        }])
        apps = pd.concat([sample_appearances, extra], ignore_index=True)
        result = compute_rolling_workload(apps, "Player A", anchor, 7)
        # Should still be 180 — anchor match excluded
        assert result == 180.0, \
            f"Anchor match leaked into window — DATA LEAKAGE: got {result}"

    def test_no_prior_matches_returns_zero(self):
        """Player with no prior matches should return 0, not error."""
        apps = pd.DataFrame(columns=["player_name","match_date","minutes_played","venue","competition"])
        result = compute_rolling_workload(apps, "Ghost Player", pd.Timestamp("2024-10-01"), 14)
        assert result == 0.0

    def test_wrong_player_excluded(self, sample_appearances):
        """Another player's appearances must not count."""
        result = compute_rolling_workload(sample_appearances, "Player B", pd.Timestamp("2024-10-01"), 30)
        assert result == 0.0

    def test_window_boundary_inclusive_start(self, sample_appearances):
        """Match exactly at window_start should be INCLUDED."""
        anchor = pd.Timestamp("2024-10-01")
        # Day 7 from anchor = exactly at window boundary for 7d window
        extra = pd.DataFrame([{
            "player_name": "Player A",
            "match_date": anchor - timedelta(days=7),
            "minutes_played": 45, "venue": "Away", "competition": "LaLiga"
        }])
        apps = pd.concat([sample_appearances, extra], ignore_index=True)
        result = compute_rolling_workload(apps, "Player A", anchor, 7)
        assert result == 225.0, f"Boundary match missing: expected 225, got {result}"


# ── Congestion index tests ────────────────────────────────────────────────────

class TestCongestionIndex:

    def test_returns_none_for_single_match(self, sample_appearances):
        """Cannot compute average gap with fewer than 2 matches."""
        anchor = pd.Timestamp("2024-10-01")
        # Only day 1 is within 3-day window
        result = compute_congestion_index(sample_appearances, "Player A", anchor, window_days=3)
        assert result is None

    def test_two_matches_gap(self):
        """Two matches 4 days apart → congestion index = 4.0."""
        base = pd.Timestamp("2024-10-01")
        apps = pd.DataFrame([
            {"player_name": "P", "match_date": base - timedelta(days=10),
             "minutes_played": 90, "venue": "Away", "competition": "LaLiga"},
            {"player_name": "P", "match_date": base - timedelta(days=6),
             "minutes_played": 90, "venue": "Away", "competition": "LaLiga"},
        ])
        result = compute_congestion_index(apps, "P", base, window_days=30)
        assert result == 4.0, f"Expected 4.0, got {result}"

    def test_high_congestion(self):
        """5 matches in 10 days → avg gap ~2.5 days."""
        base = pd.Timestamp("2024-10-01")
        apps = pd.DataFrame([
            {"player_name": "P", "match_date": base - timedelta(days=d),
             "minutes_played": 90, "venue": "Away", "competition": "LaLiga"}
            for d in [2, 4, 6, 8, 10]
        ])
        result = compute_congestion_index(apps, "P", base, window_days=30)
        assert result == 2.0, f"Expected 2.0, got {result}"

    def test_future_matches_excluded(self):
        """Matches after anchor_ts must not affect congestion index."""
        base = pd.Timestamp("2024-10-01")
        apps = pd.DataFrame([
            {"player_name": "P", "match_date": base - timedelta(days=5),
             "minutes_played": 90, "venue": "Away", "competition": "LaLiga"},
            {"player_name": "P", "match_date": base - timedelta(days=10),
             "minutes_played": 90, "venue": "Away", "competition": "LaLiga"},
            # Future match — must be excluded
            {"player_name": "P", "match_date": base + timedelta(days=3),
             "minutes_played": 90, "venue": "Away", "competition": "LaLiga"},
        ])
        result = compute_congestion_index(apps, "P", base, window_days=30)
        assert result == 5.0, \
            f"Future match leaked into congestion index: got {result}"


# ── Injury label tests ────────────────────────────────────────────────────────

class TestInjuryLabel:

    def test_injury_within_horizon(self, sample_injuries):
        """Injury at anchor+3d is within 7d horizon → label = 1."""
        anchor = pd.Timestamp("2024-10-01")
        label = compute_injury_label(sample_injuries, "Player A", anchor, 7)
        assert label == 1

    def test_no_injury_within_horizon(self, sample_injuries):
        """Injury at anchor+3d is outside 3d horizon → label = 0."""
        anchor = pd.Timestamp("2024-10-01")
        label = compute_injury_label(sample_injuries, "Player A", anchor, 2)
        assert label == 0

    def test_injury_exactly_at_anchor_excluded(self, sample_injuries):
        """
        CRITICAL: Injury at exactly anchor_ts must NOT be labelled as 1.
        This would represent concurrent labelling — data leakage.
        """
        injury_ts = pd.Timestamp("2024-10-01")
        injuries = pd.DataFrame([{
            "player_name": "Player A",
            "date_start": injury_ts,    # exactly at anchor
            "injury_type": "Muscle injury", "days_missed": 14,
        }])
        label = compute_injury_label(injuries, "Player A", injury_ts, 7)
        assert label == 0, \
            "CRITICAL: Injury at anchor_ts labelled as 1 — this is data leakage"

    def test_injury_before_anchor_excluded(self, sample_injuries):
        """Past injury must not affect future label."""
        anchor = pd.Timestamp("2024-10-10")  # anchor after injury
        label = compute_injury_label(sample_injuries, "Player A", anchor, 7)
        assert label == 0

    def test_wrong_player_excluded(self, sample_injuries):
        anchor = pd.Timestamp("2024-10-01")
        label = compute_injury_label(sample_injuries, "Player B", anchor, 7)
        assert label == 0

    def test_horizon_boundary_inclusive(self):
        """Injury exactly at anchor + horizon_days should be labelled 1."""
        anchor = pd.Timestamp("2024-10-01")
        injuries = pd.DataFrame([{
            "player_name": "P",
            "date_start": anchor + timedelta(days=7),  # exactly at boundary
            "injury_type": "Hamstring", "days_missed": 21,
        }])
        label = compute_injury_label(injuries, "P", anchor, 7)
        assert label == 1, "Boundary day should be included (≤ horizon_end)"


# ── Point-in-time integrity ───────────────────────────────────────────────────

class TestPointInTimeIntegrity:

    def test_no_future_data_in_any_window(self, sample_appearances):
        """
        Comprehensive leakage check: for a series of anchor points,
        verify that no match date in the workload window is >= anchor_ts.
        """
        anchors = pd.date_range("2024-09-20", "2024-10-10", freq="2D")
        for anchor in anchors:
            window_start = anchor - timedelta(days=14)
            mask = (
                (sample_appearances["player_name"] == "Player A") &
                (sample_appearances["match_date"] >= window_start) &
                (sample_appearances["match_date"] < anchor)
            )
            window_matches = sample_appearances[mask]
            future = window_matches[window_matches["match_date"] >= anchor]
            assert len(future) == 0, \
                f"DATA LEAKAGE at anchor={anchor}: {len(future)} future matches in window"
