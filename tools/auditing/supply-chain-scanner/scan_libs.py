#!/usr/bin/env python3
"""Backward-compatible entry point. Prefer: supply-chain-scan"""

from supply_chain_scanner.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
