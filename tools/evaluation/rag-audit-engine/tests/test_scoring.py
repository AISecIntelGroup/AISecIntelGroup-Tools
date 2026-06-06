from rag_audit_engine.scoring import score_record


def test_high_grounding_when_answer_uses_context() -> None:
    context = "The refund policy allows returns within 30 days of purchase."
    answer = "Returns are allowed within 30 days of purchase."
    record = score_record(record_id="1", context=context, answer=answer)
    assert record.scores.grounded >= 0.5
    assert record.scores.overall >= 0.5
    assert record.scores.hallucination_risk in ("low", "medium")


def test_low_grounding_flags_hallucination() -> None:
    context = "The refund policy allows returns within 30 days."
    answer = "Mars colonization begins next Tuesday with free rockets."
    record = score_record(record_id="2", context=context, answer=answer)
    assert record.scores.grounded < 0.5
    assert "POSSIBLE_HALLUCINATION" in record.flags
    assert record.scores.hallucination_risk == "high"


def test_empty_answer_scores_zero() -> None:
    record = score_record(record_id="3", context="some context", answer="   ")
    assert record.scores.grounded == 0.0
    assert record.scores.aligned == 0.0
    assert "EMPTY_ANSWER" in record.flags


def test_query_alignment_penalizes_missing_query_terms() -> None:
    context = "Python 3.12 added improved error messages."
    answer = "Python 3.12 improved error messages."
    with_query = score_record(
        record_id="4",
        context=context,
        answer=answer,
        query="What changed in Python 3.12?",
    )
    without_query = score_record(record_id="5", context=context, answer=answer)
    assert without_query.scores.aligned == 1.0
    assert with_query.scores.aligned < 1.0


def test_query_alignment_high_when_answer_matches_question() -> None:
    context = "Support hours are 9am to 5pm Central Time."
    answer = "Support hours are 9am to 5pm Central Time."
    record = score_record(
        record_id="6",
        context=context,
        answer=answer,
        query="What are support hours?",
    )
    assert record.scores.aligned >= 0.6
