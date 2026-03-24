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
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.exceptions import (
    DataContractError, SchemaValidationError, DQCheckError,
    DataLeakageError, FeatureComputationError, EntityResolutionError,
    OODError, IngestionError, BronzeWriteError, is_blocking,
)
from utils.logger import get_logger, read_log_records, clear_logs, JSONL_PATH


# ── Exception tests ───────────────────────────────────────────────────────────

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

    def test_schema_validation_error(self):
        exc = SchemaValidationError("minutes_played", -5, "minutes_played >= 0")
        assert exc.context["field"] == "minutes_played"
        assert exc.context["value"] == "-5"
        assert exc.context["rule"] == "minutes_played >= 0"
        assert exc.layer == "silver"

    def test_dq_check_critical_blocks_pipeline(self):
        exc = DQCheckError("uniqueness_check", "appearances", 0.998, 0.999, "CRITICAL")
        assert exc.blocks_pipeline is True
        assert is_blocking(exc) is True

    def test_dq_check_high_does_not_block(self):
        exc = DQCheckError("range_check", "appearances", 0.991, 0.999, "HIGH")
        assert exc.blocks_pipeline is False
        assert is_blocking(exc) is False

    def test_dq_check_medium_does_not_block(self):
        exc = DQCheckError("completeness_check", "weather", 0.97, 0.99, "MEDIUM")
        assert exc.blocks_pipeline is False
        assert is_blocking(exc) is False

    def test_data_leakage_always_blocks(self):
        exc = DataLeakageError("workload_14d", "2024-11-03", "2024-11-10", "player-abc")
        assert is_blocking(exc) is True

    def test_bronze_write_always_blocks(self):
        exc = BronzeWriteError("2024-11-03", "Disk full")
        assert is_blocking(exc) is True

    def test_ood_error_has_flag(self):
        exc = OODError("player-xyz", "No training history")
        assert exc.ood_flag is True
        assert is_blocking(exc) is False   # OOD warns but doesn't block

    def test_to_dict_contains_all_fields(self):
        exc = SchemaValidationError("minutes_played", -5, "minutes_played >= 0")
        d = exc.to_dict()
        assert "exception_type" in d
        assert "message" in d
        assert "layer" in d
        assert "source" in d
        assert "context" in d

    def test_exception_message_includes_layer_source(self):
        exc = EntityResolutionError("player_id", "Vinicius Jr.")
        msg = str(exc)
        assert "silver" in msg
        assert "entity_resolver" in msg

    def test_ingestion_error(self):
        exc = IngestionError("transfermarkt", "Connection timeout after 20s")
        assert exc.layer == "ingestion"
        assert "Connection timeout" in str(exc)

    def test_feature_computation_error(self):
        exc = FeatureComputationError(
            "workload_14d", "player-abc", "2024-11-03", "Division by zero"
        )
        assert exc.layer == "gold"
        assert exc.context["feature"] == "workload_14d"


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

    def test_jsonl_records_are_valid_json(self):
        log = get_logger("bronze", "writer")
        log.info("Record 1")
        log.warning("Record 2")
        log.error("Record 3")
        lines = JSONL_PATH.read_text().strip().splitlines()
        for line in lines:
            parsed = json.loads(line)   # raises if invalid
            assert "ts" in parsed
            assert "level" in parsed
            assert "message" in parsed

    def test_context_is_dict(self):
        log = get_logger("gold", "engine")
        log.info("Computed feature", context={"feature": "workload_14d", "value": 270.0})
        records = read_log_records(5)
        assert isinstance(records[-1]["context"], dict)

    def test_multiple_layers_separate_records(self):
        clear_logs()
        get_logger("bronze", "writer").info("Bronze write")
        get_logger("silver", "validator").warning("Schema warn")
        get_logger("gold", "engine").error("Feature error")
        records = read_log_records(10)
        layers = [r["layer"] for r in records]
        assert "bronze" in layers
        assert "silver" in layers
        assert "gold"   in layers

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
