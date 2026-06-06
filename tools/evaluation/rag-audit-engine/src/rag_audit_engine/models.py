"""Data models for RAG audit results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

HallucinationRisk = Literal["low", "medium", "high"]


class AuditScores(BaseModel):
    grounded: float = Field(ge=0.0, le=1.0)
    aligned: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)
    hallucination_risk: HallucinationRisk


class AuditRecord(BaseModel):
    id: str
    context: str
    answer: str
    query: str | None = None
    scores: AuditScores
    flags: list[str] = Field(default_factory=list)
    notes: str = ""
