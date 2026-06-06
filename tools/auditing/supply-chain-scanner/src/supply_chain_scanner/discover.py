"""Discover requirements.txt files under a repository root."""

from __future__ import annotations

from pathlib import Path

EXCLUDE_DIR_NAMES = frozenset(
    {
        ".venv",
        "venv",
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
    }
)


def discover_requirements(root: Path) -> list[Path]:
    """Return sorted paths to requirements.txt files under root."""
    root = root.resolve()
    if not root.is_dir():
        return []

    found: list[Path] = []
    for path in root.rglob("requirements.txt"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        found.append(path)

    return sorted(found)
