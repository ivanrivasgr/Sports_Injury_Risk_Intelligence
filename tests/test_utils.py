"""
tests/test_utils.py
===================
Tests for utils/logger.py and utils/exceptions.py.

Validates that:
  - Exceptions carry correct metadata
  - is_blocking() correctly classifies severity
  - Logger writes valid JSONL records
  - Logger never crashes the pipeline (even on write failure)

Run locally:
    pytest tests/test_utils.py -v
"""

import json
import sys
import unittest.mock as mock
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.exceptions import (
    BronzeWriteError,
    DataContractError,
    DataLeakageError,
    DQCheckError,
    EntityResolutionError,
    FeatureComputationError,
    FeatureStoreError,
    IngestionError,
    OODError,
    PipelineException,
    SchemaValidationError,
    TemporalAlignmentError,
    is_blocking,
)
from utils.logger import JSONL_PATH, PipelineLogger, clear_logs, get_logger, read_log_records

# ── Exception tests ───────────────────────────────────────────────────────────


class TestPipelineException:

    def test_base_exception_defaults(self):
        exc = PipelineException("something went wrong")
        assert exc.layer == "unknown"
        assert exc.source == "unknown"
        assert exc.context == {}
        assert "unknown/unknown" in str(exc)

    def test_base_exception_custom_context(self):
        exc = PipelineException("msg", layer="gold", source="engine", context={"k": "v"})
        assert exc.layer == "gold"
        assert exc.source == "engine"
        assert exc.context == {"k": "v"}

    def test_to_dict_contains_all_fields(self):
        exc = PipelineException("test", layer="silver", source="validator")
        d = exc.to_dict()
        assert d["exception_type"] == "PipelineException"
        assert d["layer"] == "silver"
        assert d["source"] == "validator"
        assert "message" in d
        assert "context" in d

    def test_is_subclass_of_exception(self):
        exc = PipelineException("base")
        assert isinstance(exc, Exception)


class TestExceptions:

    def test_data_contract_error_fields(self):
        exc = DataContractError(
            "transfermarkt",
            expected_fields=["player_id", "injury_type", "date_start"],
            received_fields=["player_id", "injury_type"],
        )
        assert exc.layer == "ingestion"
        assert "date_start" in exc.context["missing_fields"]
        assert len(exc.context["extra_fields"]) == 0

    def test_data_contract_error_extra_fields(self):
        exc = DataContractError(
            "fbref",
            expected_fields=["player_id"],
            received_fields=["player_id", "extra_col"],
        )
        assert "extra_col" in exc.context["extra_fields"]
        assert len(exc.context["missing_fields"]) == 0

    def test_schema_validation_error(self):
        exc = SchemaValidationError("minutes_played", -5, "minutes_played >= 0")
        assert exc.context["field"] == "minutes_played"
        assert exc.context["value"] == "-5"
        assert exc.context["rule"] == "minutes_played >= 0"
        assert exc.layer == "silver"

    def test_schema_validation_error_custom_layer(self):
        exc = SchemaValidationError("age", 200, "age <= 100", layer="gold", source="custom")
        assert exc.layer == "gold"
        assert exc.source == "custom"

    def test_dq_check_critical_blocks_pipeline(self):
        exc = DQCheckError("uniqueness_check", "appearances", 0.998, 0.999, "CRITICAL")
        assert exc.blocks_pipeline is True
        assert is_blocking(exc) is True
        assert exc.severity == "CRITICAL"

    def test_dq_check_high_does_not_block(self):
        exc = DQCheckError("range_check", "appearances", 0.991, 0.999, "HIGH")
        assert exc.blocks_pipeline is False
        assert is_blocking(exc) is False

    def test_dq_check_medium_does_not_block(self):
        exc = DQCheckError("completeness_check", "weather", 0.97, 0.99, "MEDIUM")
        assert exc.blocks_pipeline is False
        assert is_blocking(exc) is False

    def test_dq_check_invalid_severity_defaults_to_high(self):
        exc = DQCheckError("some_check", "table", 0.5, 0.9, "INVALID_SEVERITY")
        assert exc.severity == "HIGH"
        assert exc.blocks_pipeline is False

    def test_dq_check_context_fields(self):
        exc = DQCheckError("null_check", "injuries", 0.95, 0.99, "HIGH")
        assert exc.context["check_name"] == "null_check"
        assert exc.context["table"] == "injuries"
        assert "pass_rate" in exc.context
        assert "threshold" in exc.context

    def test_data_leakage_always_blocks(self):
        exc = DataLeakageError("workload_14d", "2024-11-03", "2024-11-10", "player-abc")
        assert is_blocking(exc) is True
        assert exc.context["feature"] == "workload_14d"
        assert exc.context["player_id"] == "player-abc"

    def test_data_leakage_no_player(self):
        exc = DataLeakageError("workload_7d", "2024-11-03", "2024-11-10")
        assert is_blocking(exc) is True
        assert exc.context["player_id"] is None

    def test_bronze_write_always_blocks(self):
        exc = BronzeWriteError("2024-11-03", "Disk full")
        assert is_blocking(exc) is True
        assert exc.layer == "bronze"
        assert exc.context["partition"] == "2024-11-03"
        assert exc.context["reason"] == "Disk full"

    def test_ood_error_has_flag(self):
        exc = OODError("player-xyz", "No training history")
        assert exc.ood_flag is True
        assert is_blocking(exc) is False

    def test_ood_error_with_distance_metric(self):
        exc = OODError("player-abc", "Too far from centroid", distance_metric=3.7)
        assert exc.context["distance_metric"] == 3.7
        assert exc.ood_flag is True

    def test_entity_resolution_error(self):
        exc = EntityResolutionError("player_id", "Vinicius Jr.", candidates=["Vinicius Jr"])
        assert exc.layer == "silver"
        assert exc.source == "entity_resolver"
        assert exc.context["entity_type"] == "player_id"
        assert exc.context["candidates"] == ["Vinicius Jr"]

    def test_entity_resolution_no_candidates(self):
        exc = EntityResolutionError("match_id", "unknown-match")
        assert exc.context["candidates"] == []

    def test_ingestion_error(self):
        exc = IngestionError("transfermarkt", "Connection timeout after 20s")
        assert exc.layer == "ingestion"
        assert "Connection timeout" in str(exc)
        assert exc.context["reason"] == "Connection timeout after 20s"

    def test_feature_computation_error(self):
        exc = FeatureComputationError(
            "workload_14d", "player-abc", "2024-11-03", "Division by zero"
        )
        assert exc.layer == "gold"
        assert exc.context["feature"] == "workload_14d"
        assert exc.context["player_id"] == "player-abc"
        assert exc.context["reason"] == "Division by zero"

    def test_temporal_alignment_error(self):
        exc = TemporalAlignmentError("player-1", "match", "2024-11-10", "2024-11-03")
        assert exc.layer == "enriched"
        assert exc.source == "temporal_aligner"
        assert exc.context["event_type"] == "match"

    def test_feature_store_error(self):
        exc = FeatureStoreError("push", "workload_features", "Timeout")
        assert exc.layer == "feature_store"
        assert exc.context["operation"] == "push"
        assert exc.context["feature_view"] == "workload_features"
        assert exc.context["reason"] == "Timeout"

    def test_exception_message_includes_layer_source(self):
        exc = EntityResolutionError("player_id", "Vinicius Jr.")
        msg = str(exc)
        assert "silver" in msg
        assert "entity_resolver" in msg

    def test_is_blocking_non_pipeline_exception(self):
        """is_blocking should return False for non-DQCheckError PipelineExceptions."""
        exc = IngestionError("source", "timeout")
        assert is_blocking(exc) is False

    def test_schema_validation_to_dict(self):
        exc = SchemaValidationError("minutes_played", -5, "minutes_played >= 0")
        d = exc.to_dict()
        assert "exception_type" in d
        assert "message" in d
        assert "layer" in d
        assert "source" in d
        assert "context" in d


# ── Logger tests ──────────────────────────────────────────────────────────────


class TestLogger:

    def setup_method(self):
        """Clear log file before each test."""
        clear_logs()

    def test_info_writes_jsonl_record(self):
        log = get_logger("silver", "test_source")
        log.info("Test message", context={"key": "value"})
        records = read_log_records(10)
        assert len(records) >= 1
        last = records[-1]
        assert last["message"] == "Test message"
        assert last["layer"] == "silver"
        assert last["source"] == "test_source"
        assert last["level"] == "INFO"
        assert last["context"]["key"] == "value"

    def test_debug_level_recorded(self):
        log = get_logger("bronze", "writer")
        log.debug("Debug message", context={"detail": "x"})
        records = read_log_records(5)
        last = records[-1]
        assert last["level"] == "DEBUG"
        assert last["message"] == "Debug message"

    def test_warning_level_recorded(self):
        log = get_logger("gold", "feature_engine")
        log.warning("High workload detected", context={"player": "Vinicius"})
        records = read_log_records(5)
        last = records[-1]
        assert last["level"] == "WARNING"

    def test_error_level_recorded(self):
        log = get_logger("ingestion", "transfermarkt")
        log.error("Schema violation", context={"field": "minutes_played"})
        records = read_log_records(5)
        last = records[-1]
        assert last["level"] == "ERROR"

    def test_critical_level_recorded(self):
        log = get_logger("gold", "leakage_guard")
        log.critical("Data leakage detected", context={"feature": "workload_14d"})
        records = read_log_records(5)
        last = records[-1]
        assert last["level"] == "CRITICAL"

    def test_exception_includes_traceback(self):
        log = get_logger("silver", "validator")
        try:
            raise ValueError("Simulated error")
        except ValueError as e:
            log.exception("Computation failed", e, context={"step": "workload"})
        records = read_log_records(5)
        last = records[-1]
        assert "traceback" in last["context"]
        assert "ValueError" in last["context"]["traceback"]
        assert "exception_type" in last["context"]
        assert last["context"]["exception_type"] == "ValueError"

    def test_exception_without_extra_context(self):
        log = get_logger("silver", "validator")
        try:
            raise RuntimeError("No context")
        except RuntimeError as e:
            log.exception("Failed", e)
        records = read_log_records(5)
        last = records[-1]
        assert "traceback" in last["context"]

    def test_jsonl_records_are_valid_json(self):
        log = get_logger("bronze", "writer")
        log.info("Record 1")
        log.warning("Record 2")
        log.error("Record 3")
        lines = JSONL_PATH.read_text().strip().splitlines()
        for line in lines:
            parsed = json.loads(line)
            assert "ts" in parsed
            assert "level" in parsed
            assert "message" in parsed

    def test_context_is_dict(self):
        log = get_logger("gold", "engine")
        log.info("Computed feature", context={"feature": "workload_14d", "value": 270.0})
        records = read_log_records(5)
        assert isinstance(records[-1]["context"], dict)

    def test_no_context_writes_empty_dict(self):
        log = get_logger("ml", "ood_detector")
        log.info("No context here")
        records = read_log_records(5)
        last = records[-1]
        assert last["context"] == {}

    def test_multiple_layers_separate_records(self):
        clear_logs()
        get_logger("bronze", "writer").info("Bronze write")
        get_logger("silver", "validator").warning("Schema warn")
        get_logger("gold", "engine").error("Feature error")
        records = read_log_records(10)
        layers = [r["layer"] for r in records]
        assert "bronze" in layers
        assert "silver" in layers
        assert "gold" in layers

    def test_read_log_records_respects_n(self):
        log = get_logger("silver", "bulk")
        for i in range(20):
            log.info(f"Record {i}")
        records = read_log_records(n=5)
        assert len(records) == 5

    def test_empty_log_returns_empty_list(self):
        clear_logs()
        records = read_log_records(10)
        assert records == []

    def test_get_logger_returns_pipeline_logger(self):
        log = get_logger("ml", "classifier")
        assert isinstance(log, PipelineLogger)
        assert log.layer == "ml"
        assert log.source == "classifier"

    def test_log_record_has_timestamp(self):
        log = get_logger("silver", "ts_test")
        log.info("timestamp test")
        records = read_log_records(5)
        last = records[-1]
        assert "ts" in last
        assert "T" in last["ts"]  # ISO format check

    def test_clear_logs_empties_file(self):
        log = get_logger("bronze", "writer")
        log.info("Before clear")
        clear_logs()
        records = read_log_records(10)
        assert records == []

    def test_logger_does_not_crash_on_bad_jsonl(self):
        """read_log_records should skip invalid lines gracefully."""
        JSONL_PATH.write_text('{"valid": true}\nNOT_JSON\n{"also": "valid"}\n')
        records = read_log_records(10)
        assert len(records) == 2

    def test_logger_survives_write_failure(self):
        """Logger must not crash the pipeline even if file write fails."""
        log = get_logger("silver", "resilient")
        with mock.patch("builtins.open", side_effect=OSError("disk full")):
            # Should NOT raise
            log.info("This should not crash")

    def test_all_layer_colors_exist(self):
        """Smoke test: loggers for all known layers initialize without error."""
        for layer in [
            "ingestion",
            "bronze",
            "silver",
            "enriched",
            "gold",
            "feature_store",
            "ml",
            "app",
        ]:
            log = get_logger(layer, "smoke")
            log.info(f"Layer {layer} ok")
        records = read_log_records(20)
        logged_layers = {r["layer"] for r in records}
        assert "ingestion" in logged_layers
        assert "gold" in logged_layers
