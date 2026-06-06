#!/usr/bin/env python3
"""Backward-compatible CLI entry. Prefer: prompt-guard"""

from prompt_guard.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
