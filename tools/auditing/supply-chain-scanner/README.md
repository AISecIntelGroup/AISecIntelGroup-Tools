# Supply Chain Scanner (LLM03)

Scan Python `requirements.txt` files for known CVEs using [pip-audit](https://github.com/pypa/pip-audit). Maps to **OWASP Top 10 for LLM Applications — LLM03: Supply Chain**.

Developed by [AISecIntel Group](https://github.com/aisecintelgroup) for open-source LLM security tooling.

## Install

```bash
cd tools/auditing/supply-chain-scanner
pip install -e ".[dev]"
```

## Quick start

```bash
# Single file
supply-chain-scan -r requirements.txt

# Entire repository (monorepo)
supply-chain-scan --discover --root /path/to/repo --format human

# CI-friendly: fail only on critical/high
supply-chain-scan --discover --root . --fail-on high -f json
```

## Output formats

| Format | Flag | Use case |
|--------|------|----------|
| JSON | `-f json` (default) | Integrations, dashboards |
| Human | `-f human` | Terminal / demos |
| SARIF | `-f sarif` | GitHub Advanced Security, SARIF viewers |

### JSON envelope

```json
{
  "scanner": "aisecintel-supply-chain-scanner",
  "version": "0.1.0",
  "scanned_files": ["tools/defense/prompt-guard/requirements.txt"],
  "findings": [
    {
      "file": "...",
      "package": "example",
      "installed_version": "1.0.0",
      "vulnerabilities": [
        { "id": "CVE-2024-0000", "severity": "high", "description": "..." }
      ]
    }
  ],
  "summary": {
    "total": 1,
    "by_severity": { "critical": 0, "high": 1, "medium": 0, "low": 0 }
  }
}
```

> **Note:** v0.1.0 uses this stable envelope. Older `scan_libs.py` printed raw pip-audit JSON.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings at/above `--fail-on`, or `--fail-on none` |
| `1` | Vulnerabilities found at/above threshold |
| `2` | Missing files or no targets |
| `3` | pip-audit failure or unparseable output |

## GitHub Actions

```yaml
- name: Install supply-chain scanner
  run: pip install -e tools/auditing/supply-chain-scanner

- name: Audit Python dependencies
  run: supply-chain-scan --discover --root . --fail-on high -f human
```

## Backward compatibility

```bash
python scan_libs.py -r requirements.txt
```

Prefer `supply-chain-scan` for new integrations.

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

Tests mock `pip-audit` and do not call the live OSV API.

## License

MIT (see repository root).
