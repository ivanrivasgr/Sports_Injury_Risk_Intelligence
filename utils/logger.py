"""
utils/logger.py
===============
Structured logger for the sports injury pipeline.

Every log entry carries:
  - timestamp (UTC)
  - layer      (ingestion / bronze / silver / enriched / gold / feature_store)
  - source     (which data source or task)
  - level      (DEBUG / INFO / WARNING / ERROR / CRITICAL)
  - message
  - context    (arbitrary dict — player_id, match_id, partition, etc.)

Writes to:
  - Console (colored, human-readable)
  - logs/pipeline.jsonl (newline-delimited JSON, machine-readable)

Usage
-----
    from utils.logger import get_logger

    log = get_logger(layer="silver", source="appearances")
    log.info("Entity resolution complete", context={"records": 4200, "dupes_removed": 17})
    log.warning("Null player_id found", context={"match_id": "abc-123", "rows": 3})
    log.error("Schema violation", context={"field": "minutes_played", "value": -5})
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
JSONL_PATH = LOGS_DIR / "pipeline.jsonl"

# ── ANSI colour codes ─────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREY   = "\033[90m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BRED   = "\033[1;91m"

LEVEL_COLORS = {
    "DEBUG":    GREY,
    "INFO":     GREEN,
    "WARNING":  YELLOW,
    "ERROR":    RED,
    "CRITICAL": BRED,
}

LAYER_COLORS = {
    "ingestion":     "\033[35m",   # magenta
    "bronze":        "\033[33m",   # orange-ish
    "silver":        "\033[34m",   # blue
    "enriched":      "\033[32m",   # green
    "gold":          "\033[33m",   # yellow
    "feature_store": "\033[35m",   # purple-ish
    "ml":            "\033[36m",   # cyan
    "app":           "\033[37m",   # white
}


class PipelineLogger:
    """
    Structured logger that writes both human-readable console output
    and machine-readable JSONL for downstream monitoring.
    """

    def __init__(self, layer: str, source: str):
        self.layer  = layer
        self.source = source
        self._std   = logging.getLogger(f"{layer}.{source}")
        if not self._std.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(logging.Formatter("%(message)s"))
            self._std.addHandler(h)
            self._std.setLevel(logging.DEBUG)
            self._std.propagate = False

    def _write(self, level: str, message: str, context: dict[str, Any] | None = None):
        ts  = datetime.now(timezone.utc).isoformat()
        ctx = context or {}

        # ── JSONL record ──────────────────────────────────────────────────────
        record = {
            "ts":      ts,
            "level":   level,
            "layer":   self.layer,
            "source":  self.source,
            "message": message,
            "context": ctx,
        }
        try:
            with open(JSONL_PATH, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass  # never let logging crash the pipeline

        # ── Console output ────────────────────────────────────────────────────
        lc = LEVEL_COLORS.get(level, "")
        lay_c = LAYER_COLORS.get(self.layer, "")
        ctx_str = ("  " + GREY + json.dumps(ctx) + RESET) if ctx else ""
        ts_short = ts[11:23]  # HH:MM:SS.mmm

        line = (
            f"{GREY}{ts_short}{RESET} "
            f"{lc}{level:<8}{RESET} "
            f"{lay_c}[{self.layer}/{self.source}]{RESET} "
            f"{message}"
            f"{ctx_str}"
        )
        self._std.info(line)

    def debug(self, msg: str, context: dict | None = None):
        self._write("DEBUG", msg, context)

    def info(self, msg: str, context: dict | None = None):
        self._write("INFO", msg, context)

    def warning(self, msg: str, context: dict | None = None):
        self._write("WARNING", msg, context)

    def error(self, msg: str, context: dict | None = None):
        self._write("ERROR", msg, context)

    def critical(self, msg: str, context: dict | None = None):
        self._write("CRITICAL", msg, context)

    def exception(self, msg: str, exc: Exception, context: dict | None = None):
        """Log an exception with full traceback in JSONL, clean summary in console."""
        ctx = dict(context or {})
        ctx["exception_type"] = type(exc).__name__
        ctx["exception_msg"]  = str(exc)
        ctx["traceback"]      = traceback.format_exc()
        self._write("ERROR", f"{msg}: {type(exc).__name__}: {exc}", ctx)


def get_logger(layer: str, source: str) -> PipelineLogger:
    """Factory — returns a PipelineLogger for the given layer/source."""
    return PipelineLogger(layer=layer, source=source)


def read_log_records(n: int = 200) -> list[dict]:
    """Read the last N records from the JSONL log file."""
    if not JSONL_PATH.exists():
        return []
    lines = JSONL_PATH.read_text().strip().splitlines()
    records = []
    for line in lines[-n:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def clear_logs():
    """Wipe the log file (useful in tests)."""
    if JSONL_PATH.exists():
        JSONL_PATH.write_text("")


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    log = get_logger("silver", "appearances")
    log.info("Starting entity resolution", context={"partition": "2024-11-03"})
    log.warning("Null player_id", context={"match_id": "abc-123", "rows": 3})
    log.error("Schema violation", context={"field": "minutes_played", "value": -5})
    try:
        raise ValueError("Simulated division by zero in feature computation")
    except Exception as e:
        log.exception("Feature computation failed", e, context={"feature": "workload_14d"})

    records = read_log_records(10)
    print(f"\nLogged {len(records)} records to {JSONL_PATH}")
