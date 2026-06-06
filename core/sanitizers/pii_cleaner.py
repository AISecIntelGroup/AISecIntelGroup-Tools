"""PII detection and redaction using Microsoft Presidio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PIICleaner:
    """Mask or remove personally identifiable information from text."""

    language: str = "en"
    entities: list[str] | None = None

    def _analyzer(self) -> Any:
        from presidio_analyzer import AnalyzerEngine

        return AnalyzerEngine()

    def _anonymizer(self) -> Any:
        from presidio_anonymizer import AnonymizerEngine

        return AnonymizerEngine()

    def clean(self, text: str) -> str:
        """Return text with detected PII entities replaced by placeholders."""
        analyzer = self._analyzer()
        anonymizer = self._anonymizer()
        results = analyzer.analyze(
            text=text,
            language=self.language,
            entities=self.entities,
        )
        return anonymizer.anonymize(text=text, analyzer_results=results).text
