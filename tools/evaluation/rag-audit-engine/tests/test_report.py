from rag_audit_engine.models import AuditRecord, AuditScores
from rag_audit_engine.report import build_envelope, format_human, should_fail


def _record(overall: float) -> AuditRecord:
    return AuditRecord(
        id="1",
        context="ctx",
        answer="ans",
        scores=AuditScores(
            grounded=overall,
            aligned=overall,
            overall=overall,
            hallucination_risk="low",
        ),
    )


def test_should_fail_on_threshold() -> None:
    report = build_envelope([_record(0.9), _record(0.3)], fail_below=0.5)
    assert should_fail("threshold", report["summary"]) is True
    assert should_fail("none", report["summary"]) is False


def test_build_envelope_schema() -> None:
    report = build_envelope([_record(0.8)], fail_below=0.5)
    assert report["scanner"] == "aisecintel-rag-audit-engine"
    assert report["version"] == "0.1.0"
    assert report["summary"]["total"] == 1


def test_format_human_contains_summary() -> None:
    report = build_envelope([_record(0.8)], fail_below=0.5)
    text = format_human(report)
    assert "avg_overall" in text or "Summary" in text
    assert "Record 1" in text
