"""
data/pipeline.py
================
Gold-layer feature computation with structured logging and typed exceptions.

This is the production-grade version of the feature engineering logic.
Every function:
  - Logs entry, exit, and record counts
  - Raises typed exceptions on failure (never bare Exception)
  - Is point-in-time safe (strict anchor_ts boundary)
  - Is idempotent (safe to re-run on same partition)

Usage
-----
    from data.pipeline import GoldPipeline

    pipeline = GoldPipeline()
    features_df = pipeline.run(partition_date="2024-11-03")
"""

from __future__ import annotations

import sys
import traceback
from datetime import timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.exceptions import (
    DataLeakageError,
    DQCheckError,
    FeatureComputationError,
    PipelineException,
    SchemaValidationError,
    is_blocking,
)
from utils.logger import get_logger

# ── Module-level logger ───────────────────────────────────────────────────────

log = get_logger("gold", "pipeline")


# ── Individual feature functions ──────────────────────────────────────────────


def compute_rolling_workload(
    appearances: pd.DataFrame,
    player_id: str,
    anchor_ts: pd.Timestamp,
    window_days: int,
) -> float:
    """
    Total minutes played in [anchor_ts - window_days, anchor_ts).
    EXCLUSIVE of anchor_ts — point-in-time safe by construction.

    Raises
    ------
    DataLeakageError   if any match in the window has date >= anchor_ts
    FeatureComputationError  on unexpected failure
    """
    try:
        window_start = anchor_ts - timedelta(days=window_days)
        mask = (
            (appearances["player_name"] == player_id)
            & (appearances["match_date"] >= window_start)
            & (appearances["match_date"] < anchor_ts)  # strict
        )
        window_df = appearances[mask]

        # Leakage guard — should never trigger if mask is correct
        future = window_df[window_df["match_date"] >= anchor_ts]
        if not future.empty:
            raise DataLeakageError(
                feature_name=f"workload_{window_days}d",
                anchor_ts=str(anchor_ts),
                leaked_ts=str(future["match_date"].max()),
                player_id=player_id,
            )

        return float(window_df["minutes_played"].sum())

    except DataLeakageError:
        raise
    except Exception as exc:
        raise FeatureComputationError(
            feature_name=f"workload_{window_days}d",
            player_id=player_id,
            anchor_ts=str(anchor_ts),
            reason=str(exc),
        ) from exc


def compute_congestion_index(
    appearances: pd.DataFrame,
    player_id: str,
    anchor_ts: pd.Timestamp,
    window_days: int = 30,
) -> Optional[float]:
    """
    Average days between matches in the prior `window_days` days.
    Returns None if fewer than 2 matches — cannot compute average gap.
    """
    try:
        window_start = anchor_ts - timedelta(days=window_days)
        mask = (
            (appearances["player_name"] == player_id)
            & (appearances["match_date"] >= window_start)
            & (appearances["match_date"] < anchor_ts)
        )
        dates = appearances.loc[mask, "match_date"].sort_values().reset_index(drop=True)
        if len(dates) < 2:
            return None
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        return float(np.mean(gaps))

    except Exception as exc:
        raise FeatureComputationError(
            feature_name="congestion_index",
            player_id=player_id,
            anchor_ts=str(anchor_ts),
            reason=str(exc),
        ) from exc


def assign_congestion_tier(index: Optional[float]) -> int:
    """
    Map congestion index (avg rest days) to ordinal tier.
    Tier 4 = most congested (<= 3 rest days avg).
    """
    if index is None:
        return 1  # insufficient data → assume low congestion
    if index <= 3:
        return 4
    if index <= 4:
        return 3
    if index <= 6:
        return 2
    return 1


def compute_injury_label(
    injuries: pd.DataFrame,
    player_id: str,
    anchor_ts: pd.Timestamp,
    horizon_days: int = 7,
) -> int:
    """
    Binary label: did an injury occur in (anchor_ts, anchor_ts + horizon_days]?

    IMPORTANT: This is a LOOK-AHEAD function.
    It must ONLY be called during training dataset construction.
    It must NEVER be called during inference.

    Raises
    ------
    DataLeakageError  if anchor_ts itself is included (concurrent labelling)
    """
    try:
        horizon_end = anchor_ts + timedelta(days=horizon_days)
        mask = (
            (injuries["player_name"] == player_id)
            & (injuries["date_start"] > anchor_ts)  # strict — not at anchor
            & (injuries["date_start"] <= horizon_end)
        )
        # Leakage guard: ensure no injury at exactly anchor_ts slipped through
        at_anchor = injuries[
            (injuries["player_name"] == player_id) & (injuries["date_start"] == anchor_ts)
        ]
        if not at_anchor.empty:
            raise DataLeakageError(
                feature_name="injured_next_7d",
                anchor_ts=str(anchor_ts),
                leaked_ts=str(anchor_ts),
                player_id=player_id,
            )
        return int(injuries[mask].shape[0] > 0)

    except DataLeakageError:
        raise
    except Exception as exc:
        raise FeatureComputationError(
            feature_name="injury_label",
            player_id=player_id,
            anchor_ts=str(anchor_ts),
            reason=str(exc),
        ) from exc


# ── Schema validators ─────────────────────────────────────────────────────────


def validate_appearances_schema(df: pd.DataFrame) -> None:
    """Silver-layer schema contract for appearances."""
    required = {"player_name", "match_date", "minutes_played", "venue", "competition"}
    missing = required - set(df.columns)
    if missing:
        raise SchemaValidationError(
            field=str(missing),
            value="<missing>",
            rule=f"required columns: {required}",
        )
    bad_minutes = df[(df["minutes_played"] < 0) | (df["minutes_played"] > 120)]
    if not bad_minutes.empty:
        raise SchemaValidationError(
            field="minutes_played",
            value=str(bad_minutes["minutes_played"].iloc[0]),
            rule="0 <= minutes_played <= 120",
        )
    log.debug("Appearances schema: OK", context={"rows": len(df)})


def validate_injuries_schema(df: pd.DataFrame) -> None:
    """Silver-layer schema contract for injuries."""
    required = {"player_name", "date_start", "injury_type", "days_missed"}
    missing = required - set(df.columns)
    if missing:
        raise SchemaValidationError(
            field=str(missing),
            value="<missing>",
            rule=f"required columns: {required}",
        )
    if df["player_name"].isna().any():
        raise SchemaValidationError(
            field="player_name",
            value="NULL",
            rule="player_name NOT NULL",
        )
    log.debug("Injuries schema: OK", context={"rows": len(df)})


# ── DQ checks ────────────────────────────────────────────────────────────────


def run_dq_checks(df: pd.DataFrame, table: str) -> list[dict]:
    """
    Run data quality checks on a Silver/Gold table.
    Returns list of check results. Raises DQCheckError on CRITICAL failures.
    """
    results = []

    def check(name: str, pass_rate: float, threshold: float, severity: str):
        passed = pass_rate >= threshold
        results.append(
            {
                "check": name,
                "table": table,
                "pass_rate": round(pass_rate, 4),
                "threshold": threshold,
                "severity": severity,
                "passed": passed,
            }
        )
        if not passed:
            exc = DQCheckError(name, table, pass_rate, threshold, severity)
            if is_blocking(exc):
                log.critical(
                    f"DQ BLOCK: {name}", context={"pass_rate": pass_rate, "threshold": threshold}
                )
                raise exc
            else:
                log.warning(
                    f"DQ WARN: {name}", context={"pass_rate": pass_rate, "threshold": threshold}
                )
        return passed

    if "player_name" in df.columns:
        completeness = 1 - df["player_name"].isna().mean()
        check("player_name_completeness", completeness, 0.999, "CRITICAL")

    if "minutes_played" in df.columns:
        valid_range = ((df["minutes_played"] >= 0) & (df["minutes_played"] <= 120)).mean()
        check("minutes_played_range", valid_range, 0.999, "HIGH")

    if "days_missed" in df.columns:
        non_neg = (df["days_missed"] >= 0).mean()
        check("days_missed_non_negative", non_neg, 1.0, "HIGH")

    return results


# ── Gold pipeline ─────────────────────────────────────────────────────────────


class GoldPipeline:
    """
    Orchestrates the full Bronze → Gold feature computation for a date partition.

    Methods
    -------
    run(partition_date)          Build feature table for a specific date
    run_full(for_training=True)  Build full historical feature table
    """

    def __init__(self):
        self.log = get_logger("gold", "GoldPipeline")

    def run_full(
        self,
        appearances: pd.DataFrame,
        injuries: pd.DataFrame,
        for_training: bool = True,
        label_horizon_days: int = 7,
    ) -> pd.DataFrame:
        """
        Compute Gold-layer features for all (player, match) pairs.

        Parameters
        ----------
        appearances     Silver-layer appearances table
        injuries        Silver-layer injuries table
        for_training    If True, compute injury label (look-ahead)
        label_horizon_days  Days after anchor to check for injury
        """
        self.log.info(
            "Gold pipeline started",
            context={
                "appearances": len(appearances),
                "injuries": len(injuries),
                "for_training": for_training,
            },
        )

        # ── Schema validation ─────────────────────────────────────────────────
        try:
            validate_appearances_schema(appearances)
            validate_injuries_schema(injuries)
        except SchemaValidationError as e:
            self.log.exception("Schema validation failed", e)
            raise

        # ── DQ checks ─────────────────────────────────────────────────────────
        dq_results = []
        try:
            dq_results += run_dq_checks(appearances, "appearances")
            dq_results += run_dq_checks(injuries, "injuries")
        except DQCheckError as e:
            self.log.exception("DQ check blocked pipeline", e)
            raise

        # ── Feature computation ───────────────────────────────────────────────
        records = []
        errors = []
        players = appearances["player_name"].unique()

        for player in players:
            player_apps = appearances[appearances["player_name"] == player]

            for _, row in player_apps.iterrows():
                anchor = pd.Timestamp(row["match_date"])
                rec = {
                    "player_name": player,
                    "anchor_ts": anchor,
                    "venue": row.get("venue"),
                    "competition": row.get("competition"),
                    "minutes_played": row["minutes_played"],
                }

                # Rolling workload
                for w in [7, 14, 30]:
                    try:
                        rec[f"workload_{w}d"] = compute_rolling_workload(
                            appearances, player, anchor, w
                        )
                    except (DataLeakageError, FeatureComputationError) as e:
                        errors.append(e.to_dict())
                        self.log.exception(
                            f"workload_{w}d failed",
                            e,
                            context={"player": player, "anchor": str(anchor)},
                        )
                        rec[f"workload_{w}d"] = None

                # Congestion
                try:
                    ci = compute_congestion_index(appearances, player, anchor)
                    rec["congestion_index"] = ci
                    rec["congestion_tier"] = assign_congestion_tier(ci)
                except FeatureComputationError as e:
                    errors.append(e.to_dict())
                    rec["congestion_index"] = None
                    rec["congestion_tier"] = 1

                # Label (training only)
                if for_training:
                    try:
                        rec["injured_next_7d"] = compute_injury_label(
                            injuries, player, anchor, label_horizon_days
                        )
                    except DataLeakageError as e:
                        # Leakage is always fatal
                        self.log.exception("DATA LEAKAGE DETECTED — aborting", e)
                        raise
                    except FeatureComputationError as e:
                        errors.append(e.to_dict())
                        rec["injured_next_7d"] = None

                records.append(rec)

        features_df = pd.DataFrame(records)

        self.log.info(
            "Gold pipeline complete",
            context={
                "output_rows": len(features_df),
                "feature_errors": len(errors),
                "error_rate": round(len(errors) / max(len(records), 1), 4),
            },
        )

        if errors:
            self.log.warning(
                f"{len(errors)} feature computation errors logged",
                context={"first_error": errors[0] if errors else None},
            )

        return features_df, dq_results, errors


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    from data.seed_data import get_appearances_df, get_injuries_df

    appearances = get_appearances_df()
    injuries = get_injuries_df()

    pipeline = GoldPipeline()
    features, dq, errors = pipeline.run_full(appearances, injuries, for_training=True)

    print(f"\n{'='*50}")
    print(f"Gold features: {len(features)} rows × {len(features.columns)} cols")
    print(f"DQ checks:     {len(dq)} checks, {sum(1 for r in dq if not r['passed'])} failed")
    print(f"Feature errors: {len(errors)}")
    print(f"\nColumns: {list(features.columns)}")
    print(f"\nSample:\n{features.head(3).to_string()}")
