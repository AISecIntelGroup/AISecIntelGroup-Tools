"""Heuristic RAG answer scoring (offline, no LLM API)."""

from __future__ import annotations

import re

from rag_audit_engine.models import AuditRecord, AuditScores, HallucinationRisk

_REFUSAL_PATTERNS = re.compile(
    r"\b(i (can't|cannot)|i'm unable|no information|don't know)\b",
    re.I,
)
_TOKEN = re.compile(r"[a-z0-9]+", re.I)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "are",
        "at",
        "be",
        "for",
        "how",
        "in",
        "is",
        "of",
        "on",
        "the",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
    }
)


def _tokenize(text: str, *, drop_stopwords: bool = False) -> set[str]:
    tokens = {m.group(0).lower() for m in _TOKEN.finditer(text)}
    if drop_stopwords:
        tokens -= _STOPWORDS
    return tokens


def _grounding_score(context: str, answer: str) -> tuple[float, list[str]]:
    context_tokens = _tokenize(context)
    answer_tokens = _tokenize(answer)
    flags: list[str] = []

    if not answer_tokens:
        flags.append("EMPTY_ANSWER")
        return 0.0, flags

    overlap = answer_tokens & context_tokens
    precision = len(overlap) / len(answer_tokens)
    unsupported = answer_tokens - context_tokens

    if precision < 0.3:
        flags.append("LOW_GROUNDING")
    if len(unsupported) / len(answer_tokens) > 0.6:
        flags.append("POSSIBLE_HALLUCINATION")

    return min(1.0, precision), flags


def _alignment_score(answer: str, query: str | None) -> float:
    if not answer.strip():
        return 0.0
    if _REFUSAL_PATTERNS.search(answer):
        return 0.2
    if not query:
        return 1.0
    query_tokens = _tokenize(query, drop_stopwords=True)
    answer_tokens = _tokenize(answer)
    if not query_tokens:
        return 1.0
    overlap = len(query_tokens & answer_tokens) / len(query_tokens)
    return min(1.0, max(0.4, overlap))


def _hallucination_risk(grounded: float, flags: list[str]) -> HallucinationRisk:
    if "POSSIBLE_HALLUCINATION" in flags or grounded < 0.25:
        return "high"
    if "LOW_GROUNDING" in flags or grounded < 0.5:
        return "medium"
    return "low"


def score_record(
    *,
    record_id: str,
    context: str,
    answer: str,
    query: str | None = None,
) -> AuditRecord:
    grounded, flags = _grounding_score(context, answer)
    aligned = _alignment_score(answer, query)
    overall = (grounded + aligned) / 2
    risk = _hallucination_risk(grounded, flags)

    notes = ""
    if "POSSIBLE_HALLUCINATION" in flags:
        notes = "Answer contains many tokens not present in retrieved context."

    return AuditRecord(
        id=record_id,
        context=context,
        answer=answer,
        query=query,
        scores=AuditScores(
            grounded=round(grounded, 4),
            aligned=round(aligned, 4),
            overall=round(overall, 4),
            hallucination_risk=risk,
        ),
        flags=flags,
        notes=notes,
    )
