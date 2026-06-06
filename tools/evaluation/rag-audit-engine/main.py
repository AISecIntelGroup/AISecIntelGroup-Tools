#!/usr/bin/env python3
"""Backward-compatible entry point. Prefer: rag-audit"""

from rag_audit_engine.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
