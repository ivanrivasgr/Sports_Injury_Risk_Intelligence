"""
utils/exceptions.py
===================
Typed exception hierarchy for the sports injury pipeline.

Every layer has its own exception class so that:
  - Error handling can be layer-specific (catch only what you expect)
  - Log messages automatically include layer context
  - CI tests can assert the correct exception type is raised
  - Downstream consumers know which layer failed without parsing strings

Hierarchy
---------
PipelineException                  ← base for all pipeline errors
  ├── DataContractError             ← source does not match expected schema
  ├── IngestionError                ← network / API / file read failure
  ├── BronzeWriteError              ← cannot write immutable raw record
  ├── EntityResolutionError         ← cannot resolve player_id / match_id
  ├── SchemaValidationError         ← Silver layer contract violation
  ├── DQCheckError                  ← data quality check failure (with severity)
  ├── TemporalAlignmentError        ← event timestamps are inconsistent
  ├── FeatureComputationError       ← Gold layer aggregation failure
  ├── DataLeakageError              ← future data detected in training window
  ├── FeatureStoreError             ← push/pull to feature store failed
  └── OODError                      ← inference on out-of-distribution input

Usage
-----
    from utils.exceptions import SchemaValidationError, DQCheckError

    if minutes < 0:
        raise SchemaValidationError(
            field="minutes_played",
            value=minutes,
            rule="minutes_played >= 0",
            layer="silver",
            source="appearances",
        )
"""

from __future__ import annotations

from typing import Any

# ── Base ──────────────────────────────────────────────────────────────────────


class PipelineException(Exception):
    """Base class for all pipeline exceptions."""

    def __init__(
        self,
        message: str,
        layer: str = "unknown",
        source: str = "unknown",
        context: dict | None = None,
    ):
        self.layer = layer
        self.source = source
        self.context = context or {}
        super().__init__(f"[{layer}/{source}] {message}")

    def to_dict(self) -> dict:
        return {
            "exception_type": type(self).__name__,
            "message": str(self),
            "layer": self.layer,
            "source": self.source,
            "context": self.context,
        }


# ── Ingestion layer ───────────────────────────────────────────────────────────


class DataContractError(PipelineException):
    """Source data does not match the registered data contract (schema)."""

    def __init__(self, source: str, expected_fields: list[str], received_fields: list[str], **kw):
        missing = set(expected_fields) - set(received_fields)
        extra = set(received_fields) - set(expected_fields)
        ctx = {"missing_fields": sorted(missing), "extra_fields": sorted(extra)}
        super().__init__(
            f"Data contract violation for source '{source}': "
            f"missing={sorted(missing)}, extra={sorted(extra)}",
            layer="ingestion",
            source=source,
            context=ctx,
        )


class IngestionError(PipelineException):
    """Network / API / file read failure during ingestion."""

    def __init__(self, source: str, reason: str, **kw):
        super().__init__(
            f"Ingestion failed for '{source}': {reason}",
            layer="ingestion",
            source=source,
            context={"reason": reason},
        )


# ── Bronze layer ──────────────────────────────────────────────────────────────


class BronzeWriteError(PipelineException):
    """Cannot write to the immutable Bronze store."""

    def __init__(self, partition: str, reason: str, **kw):
        super().__init__(
            f"Bronze write failed for partition '{partition}': {reason}",
            layer="bronze",
            source="writer",
            context={"partition": partition, "reason": reason},
        )


# ── Silver layer ──────────────────────────────────────────────────────────────


class EntityResolutionError(PipelineException):
    """Cannot resolve a canonical entity ID."""

    def __init__(self, entity_type: str, raw_value: Any, candidates: list | None = None, **kw):
        ctx = {
            "entity_type": entity_type,
            "raw_value": str(raw_value),
            "candidates": candidates or [],
        }
        super().__init__(
            f"Cannot resolve {entity_type} for value '{raw_value}'",
            layer="silver",
            source="entity_resolver",
            context=ctx,
        )


class SchemaValidationError(PipelineException):
    """A field value violates a Silver layer schema rule."""

    def __init__(
        self,
        field: str,
        value: Any,
        rule: str,
        layer: str = "silver",
        source: str = "validator",
        **kw,
    ):
        ctx = {"field": field, "value": str(value), "rule": rule}
        super().__init__(
            f"Schema violation: {field}={value!r} violates rule '{rule}'",
            layer=layer,
            source=source,
            context=ctx,
        )


# ── DQ layer ──────────────────────────────────────────────────────────────────


class DQCheckError(PipelineException):
    """
    Data quality check failed.
    severity: 'CRITICAL' blocks downstream; 'HIGH' alerts; 'MEDIUM' logs.
    """

    SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM"}

    def __init__(
        self,
        check_name: str,
        table: str,
        pass_rate: float,
        threshold: float,
        severity: str = "HIGH",
        **kw,
    ):
        if severity not in self.SEVERITIES:
            severity = "HIGH"
        ctx = {
            "check_name": check_name,
            "table": table,
            "pass_rate": round(pass_rate, 6),
            "threshold": threshold,
            "severity": severity,
        }
        super().__init__(
            f"DQ check '{check_name}' on '{table}' failed: "
            f"pass_rate={pass_rate:.4f} < threshold={threshold} [{severity}]",
            layer="silver",
            source="dq_monitor",
            context=ctx,
        )
        self.severity = severity
        self.blocks_pipeline = severity == "CRITICAL"


# ── Enriched / Gold layer ─────────────────────────────────────────────────────


class TemporalAlignmentError(PipelineException):
    """Event timestamps are inconsistent or violate the temporal spine."""

    def __init__(self, player_id: str, event_type: str, event_ts: Any, anchor_ts: Any, **kw):
        ctx = {
            "player_id": player_id,
            "event_type": event_type,
            "event_ts": str(event_ts),
            "anchor_ts": str(anchor_ts),
        }
        super().__init__(
            f"Temporal misalignment for player {player_id}: "
            f"{event_type} at {event_ts} vs anchor {anchor_ts}",
            layer="enriched",
            source="temporal_aligner",
            context=ctx,
        )


class FeatureComputationError(PipelineException):
    """Gold layer feature aggregation produced an invalid result."""

    def __init__(self, feature_name: str, player_id: str, anchor_ts: Any, reason: str, **kw):
        ctx = {
            "feature": feature_name,
            "player_id": player_id,
            "anchor_ts": str(anchor_ts),
            "reason": reason,
        }
        super().__init__(
            f"Feature '{feature_name}' computation failed for "
            f"player {player_id} at {anchor_ts}: {reason}",
            layer="gold",
            source="feature_engine",
            context=ctx,
        )


class DataLeakageError(PipelineException):
    """
    Future data detected in a training feature window.
    This is a CRITICAL error — it must halt pipeline execution immediately.
    """

    def __init__(
        self, feature_name: str, anchor_ts: Any, leaked_ts: Any, player_id: str | None = None, **kw
    ):
        ctx = {
            "feature": feature_name,
            "anchor_ts": str(anchor_ts),
            "leaked_ts": str(leaked_ts),
            "player_id": player_id,
        }
        super().__init__(
            f"DATA LEAKAGE DETECTED: feature '{feature_name}' includes data "
            f"at {leaked_ts} which is after anchor {anchor_ts}",
            layer="gold",
            source="leakage_guard",
            context=ctx,
        )


# ── Feature Store ─────────────────────────────────────────────────────────────


class FeatureStoreError(PipelineException):
    """Feature store push or retrieval failed."""

    def __init__(self, operation: str, feature_view: str, reason: str, **kw):
        ctx = {"operation": operation, "feature_view": feature_view, "reason": reason}
        super().__init__(
            f"Feature store {operation} failed for '{feature_view}': {reason}",
            layer="feature_store",
            source="feature_store_client",
            context=ctx,
        )


# ── ML / Inference ────────────────────────────────────────────────────────────


class OODError(PipelineException):
    """Input to the model is out-of-distribution relative to training data."""

    def __init__(self, player_id: str, reason: str, distance_metric: float | None = None, **kw):
        ctx = {"player_id": player_id, "reason": reason, "distance_metric": distance_metric}
        super().__init__(
            f"OOD input detected for player {player_id}: {reason}",
            layer="ml",
            source="ood_detector",
            context=ctx,
        )
        self.ood_flag = True


# ── Utility ───────────────────────────────────────────────────────────────────


def is_blocking(exc: PipelineException) -> bool:
    """Returns True if this exception should halt downstream pipeline tasks."""
    if isinstance(exc, (DataLeakageError, BronzeWriteError)):
        return True
    if isinstance(exc, DQCheckError) and exc.blocks_pipeline:
        return True
    return False


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    exceptions = [
        DataContractError(
            "transfermarkt",
            ["player_id", "injury_type", "date_start"],
            ["player_id", "injury_type"],
        ),
        SchemaValidationError("minutes_played", -5, "minutes_played >= 0"),
        DQCheckError("uniqueness_check", "appearances", 0.9985, 0.999, "CRITICAL"),
        DataLeakageError("workload_14d", "2024-11-03", "2024-11-10", "player-abc"),
        OODError("player-xyz", "No historical appearances in training data"),
    ]
    for e in exceptions:
        print(
            f"  [{type(e).__name__}]  blocking={is_blocking(e) if isinstance(e, PipelineException) else 'N/A'}"
        )
        print(f"    {e}")
