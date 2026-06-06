"""Pydantic-based schema integrity verification."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class SchemaGuard:
    """Validate arbitrary payloads against a Pydantic model."""

    def __init__(self, model: type[T]) -> None:
        self.model = model

    def validate(self, payload: dict[str, Any]) -> T:
        return self.model.model_validate(payload)

    def is_valid(self, payload: dict[str, Any]) -> bool:
        try:
            self.validate(payload)
            return True
        except ValidationError:
            return False


def validate_payload(model: type[T], payload: dict[str, Any]) -> T:
    """Convenience wrapper for one-off validation."""
    return SchemaGuard(model).validate(payload)
