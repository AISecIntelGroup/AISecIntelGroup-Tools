from prompt_guard.guard import BlockReason, ScanResult
from prompt_guard.report import (
    build_envelope,
    format_human,
    result_to_record,
    should_fail,
)


def test_result_to_record_blocked() -> None:
    result = ScanResult(True, BlockReason.DIRECT_OVERRIDE, "ignore previous")
    record = result_to_record("1", "bad prompt", result)
    assert record["blocked"] is True
    assert record["reason"] == "DIRECT_OVERRIDE"


def test_should_fail_on_blocked() -> None:
    records = [
        result_to_record("1", "ok", ScanResult(False)),
        result_to_record("2", "bad", ScanResult(True, BlockReason.SYSTEM_LEAK, "leak")),
    ]
    report = build_envelope(records)
    assert should_fail("blocked", report["summary"]) is True
    assert should_fail("none", report["summary"]) is False


def test_build_envelope_schema() -> None:
    records = [result_to_record("1", "hello", ScanResult(False))]
    report = build_envelope(records)
    assert report["scanner"] == "aisecintel-prompt-guard"
    assert report["version"] == "0.1.0"
    assert report["summary"]["allowed"] == 1


def test_format_human_contains_summary() -> None:
    records = [result_to_record("1", "hello", ScanResult(False))]
    text = format_human(build_envelope(records))
    assert "ALLOWED" in text
    assert "Summary" in text
