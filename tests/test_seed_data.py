"""
tests/test_seed_data.py
=======================
Validates the seed dataset schema, value ranges, and integrity constraints.

These tests run on every CI push (no network required — seed data is bundled).
They catch regressions introduced by changes to data/seed_data.py.

Run locally:
    pytest tests/test_seed_data.py -v
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.seed_data import get_appearances_df, get_injuries_df, get_weather_df

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def injuries():
    return get_injuries_df()


@pytest.fixture(scope="module")
def appearances():
    return get_appearances_df()


@pytest.fixture(scope="module")
def weather():
    return get_weather_df()


# ── injuries table ────────────────────────────────────────────────────────────


class TestInjuriesSchema:

    def test_required_columns_present(self, injuries):
        required = [
            "player_name",
            "season",
            "injury_type",
            "date_start",
            "date_end",
            "days_missed",
            "last_match_venue",
            "competition",
            "position",
            "is_muscular",
            "age_at_injury",
        ]
        for col in required:
            assert col in injuries.columns, f"Missing column: {col}"

    def test_no_null_player_name(self, injuries):
        nulls = injuries["player_name"].isna().sum()
        assert nulls == 0, f"Found {nulls} null player_name values"

    def test_no_null_date_start(self, injuries):
        nulls = injuries["date_start"].isna().sum()
        assert nulls == 0, f"Found {nulls} null date_start values"

    def test_date_types(self, injuries):
        assert pd.api.types.is_datetime64_any_dtype(
            injuries["date_start"]
        ), "date_start must be datetime"
        assert pd.api.types.is_datetime64_any_dtype(
            injuries["date_end"]
        ), "date_end must be datetime"

    def test_season_format(self, injuries):
        """Season must follow YYYY-YY format."""
        bad = injuries[~injuries["season"].str.match(r"^\d{4}-\d{2}$")]
        assert len(bad) == 0, f"Invalid season format: {bad['season'].unique()}"

    def test_is_muscular_binary(self, injuries):
        assert injuries["is_muscular"].isin([0, 1]).all(), "is_muscular must be 0 or 1"

    def test_days_missed_non_negative(self, injuries):
        neg = (injuries["days_missed"] < 0).sum()
        assert neg == 0, f"Found {neg} negative days_missed values"

    def test_days_missed_upper_bound(self, injuries):
        """No injury should last more than 2 seasons (730 days)."""
        extreme = (injuries["days_missed"] > 730).sum()
        assert extreme == 0, f"Found {extreme} injuries > 730 days"

    def test_venue_values(self, injuries):
        valid_venues = {"Bernabéu", "Away"}
        bad = set(injuries["last_match_venue"].unique()) - valid_venues
        assert not bad, f"Unknown venue values: {bad}"

    def test_date_end_after_date_start(self, injuries):
        """date_end must be >= date_start (or date_end may be null)."""
        valid = injuries.dropna(subset=["date_end"])
        bad = valid[valid["date_end"] < valid["date_start"]]
        assert len(bad) == 0, f"Found {len(bad)} records where date_end < date_start"

    def test_age_at_injury_reasonable(self, injuries):
        """Professional footballers are between 15 and 45."""
        bad = injuries[(injuries["age_at_injury"] < 15) | (injuries["age_at_injury"] > 45)]
        assert (
            len(bad) == 0
        ), f"Found {len(bad)} records with unreasonable age: {bad[['player_name','age_at_injury']]}"

    def test_minimum_record_count(self, injuries):
        """Dataset must have at least 50 records (sanity check)."""
        assert len(injuries) >= 50, f"Too few injury records: {len(injuries)} (expected >= 50)"

    def test_minimum_seasons(self, injuries):
        assert (
            injuries["season"].nunique() >= 4
        ), f"Expected >= 4 seasons, got {injuries['season'].nunique()}"

    def test_minimum_players(self, injuries):
        assert (
            injuries["player_name"].nunique() >= 10
        ), f"Expected >= 10 players, got {injuries['player_name'].nunique()}"

    def test_position_values(self, injuries):
        valid_positions = {"GK", "CB", "RB", "LB", "CM", "AM", "RW", "LW", "ST", "UNK"}
        bad = set(injuries["position"].unique()) - valid_positions
        assert not bad, f"Unknown position codes: {bad}"

    def test_muscular_injury_rate_plausible(self, injuries):
        """Muscular injuries should be 50–90% of all injuries (documented literature range)."""
        rate = injuries["is_muscular"].mean()
        assert (
            0.50 <= rate <= 0.90
        ), f"Muscular injury rate {rate:.1%} outside expected range [50%, 90%]"


# ── appearances table ─────────────────────────────────────────────────────────


class TestAppearancesSchema:

    def test_required_columns(self, appearances):
        required = ["player_name", "match_date", "minutes_played", "venue", "competition"]
        for col in required:
            assert col in appearances.columns, f"Missing column: {col}"

    def test_minutes_played_range(self, appearances):
        bad = appearances[
            (appearances["minutes_played"] < 0) | (appearances["minutes_played"] > 120)
        ]
        assert len(bad) == 0, f"Found {len(bad)} records with minutes_played outside [0, 120]"

    def test_venue_values(self, appearances):
        valid = {"Bernabéu", "Away"}
        bad = set(appearances["venue"].unique()) - valid
        assert not bad, f"Unknown venue values: {bad}"

    def test_no_null_player_name(self, appearances):
        assert appearances["player_name"].isna().sum() == 0


# ── weather table ─────────────────────────────────────────────────────────────


class TestWeatherSchema:

    def test_required_columns(self, weather):
        required = ["date", "temp_max_c", "temp_min_c", "precipitation_mm", "wind_kph"]
        for col in required:
            assert col in weather.columns, f"Missing column: {col}"

    def test_temperature_range(self, weather):
        bad_max = weather[weather["temp_max_c"] > 50]
        bad_min = weather[weather["temp_min_c"] < -20]
        assert len(bad_max) == 0, f"temp_max_c > 50°C in {len(bad_max)} records"
        assert len(bad_min) == 0, f"temp_min_c < -20°C in {len(bad_min)} records"

    def test_temp_max_gte_min(self, weather):
        bad = weather[weather["temp_max_c"] < weather["temp_min_c"]]
        assert len(bad) == 0, f"Found {len(bad)} records where temp_max < temp_min"

    def test_precipitation_non_negative(self, weather):
        neg = (weather["precipitation_mm"] < 0).sum()
        assert neg == 0, f"Found {neg} negative precipitation values"

    def test_wind_non_negative(self, weather):
        neg = (weather["wind_kph"] < 0).sum()
        assert neg == 0, f"Found {neg} negative wind_kph values"
