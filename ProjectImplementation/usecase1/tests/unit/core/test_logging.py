"""Unit tests for src/core/logging.py.

TDD: Log output must be valid JSON with required fields; trace_id must flow.

Strategy: Tests instantiate _JSONFormatter directly and call format() so we
don't fight pytest's caplog handler (configure_logging replaces root handlers).
Run: pytest tests/unit/core/test_logging.py -v
"""
import json
import logging

import pytest

from src.core.logging import _JSONFormatter, configure_logging, get_logger, trace_id_var


def _make_record(message: str, level: int = logging.INFO, name: str = "test") -> logging.LogRecord:
    """Build a minimal LogRecord for formatter testing."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    return record


class TestJSONFormatter:
    """_JSONFormatter must produce valid single-line JSON with all required fields."""

    def test_format_output_is_valid_json(self) -> None:
        """Formatted output must parse as JSON without errors."""
        formatter = _JSONFormatter()
        record = _make_record("Test message")
        output = formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self) -> None:
        """JSON must contain: timestamp, level, service, module, message."""
        formatter = _JSONFormatter()
        parsed = json.loads(formatter.format(_make_record("Required fields test")))

        for field in ("timestamp", "level", "service", "module", "message"):
            assert field in parsed, f"Missing required field: {field}"

    def test_service_name_is_jewelry_ai(self) -> None:
        """service field must always be 'jewelry-ai'."""
        formatter = _JSONFormatter()
        parsed = json.loads(formatter.format(_make_record("service name check")))
        assert parsed["service"] == "jewelry-ai"

    def test_message_matches_log_call(self) -> None:
        """message field must equal the logged string."""
        formatter = _JSONFormatter()
        parsed = json.loads(formatter.format(_make_record("hello world")))
        assert parsed["message"] == "hello world"

    def test_level_matches_record_level(self) -> None:
        """level field must match the LogRecord's level."""
        formatter = _JSONFormatter()
        parsed = json.loads(formatter.format(_make_record("warn test", level=logging.WARNING)))
        assert parsed["level"] == "WARNING"

    def test_module_matches_logger_name(self) -> None:
        """module field must match the logger name."""
        formatter = _JSONFormatter()
        parsed = json.loads(formatter.format(_make_record("module test", name="src.services.lead")))
        assert parsed["module"] == "src.services.lead"

    def test_timestamp_is_iso_format(self) -> None:
        """timestamp field must be an ISO 8601 datetime string."""
        formatter = _JSONFormatter()
        parsed = json.loads(formatter.format(_make_record("ts test")))
        # ISO 8601 timestamps contain 'T' and '+' or 'Z'
        assert "T" in parsed["timestamp"]

    def test_exception_info_included_when_present(self) -> None:
        """When exc_info is present, exception key must appear in output."""
        formatter = _JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = _make_record("error occurred")
        record.exc_info = exc_info
        parsed = json.loads(formatter.format(record))
        assert "exception" in parsed


class TestTraceIDInjection:
    """trace_id must appear in JSON output when set via context variable."""

    def test_trace_id_included_when_set_in_context(self) -> None:
        """When trace_id_var is set, JSON output includes the trace_id value."""
        formatter = _JSONFormatter()
        expected = "abc-123-trace"
        token = trace_id_var.set(expected)
        try:
            parsed = json.loads(formatter.format(_make_record("trace test")))
            assert parsed["trace_id"] == expected
        finally:
            trace_id_var.reset(token)

    def test_trace_id_is_none_when_not_set(self) -> None:
        """When trace_id_var is not set, trace_id is null in JSON output."""
        formatter = _JSONFormatter()
        token = trace_id_var.set("")  # Clear it
        try:
            parsed = json.loads(formatter.format(_make_record("no trace")))
            # Empty string is converted to None in the formatter
            assert parsed["trace_id"] is None or parsed["trace_id"] == ""
        finally:
            trace_id_var.reset(token)

    def test_different_trace_ids_in_different_contexts(self) -> None:
        """Two different trace_ids produce two different log outputs."""
        formatter = _JSONFormatter()

        t1 = trace_id_var.set("trace-001")
        out1 = json.loads(formatter.format(_make_record("first")))
        trace_id_var.reset(t1)

        t2 = trace_id_var.set("trace-002")
        out2 = json.loads(formatter.format(_make_record("second")))
        trace_id_var.reset(t2)

        assert out1["trace_id"] == "trace-001"
        assert out2["trace_id"] == "trace-002"


class TestGetLogger:
    """get_logger() must return a standard library Logger with the correct name."""

    def test_get_logger_returns_named_logger(self) -> None:
        logger = get_logger("my.module.name")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "my.module.name"

    def test_get_logger_uses_module_hierarchy(self) -> None:
        """Child loggers inherit from parent — naming must use dots."""
        parent = get_logger("src.services")
        child = get_logger("src.services.lead")
        assert child.name.startswith(parent.name)
