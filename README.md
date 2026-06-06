# AI Security Intelligence Group Tools

Open-source utilities for LLM security auditing, defense, and evaluation—aligned with the OWASP Top 10 for LLM Applications.

## Repository layout

| Path | Purpose |
|------|---------|
| [`core/`](core/) | Reusable sanitizers and validators shared across tools |
| [`core-extensions/`](core-extensions/) | Plug-ins for Garak, Promptfoo, and similar frameworks |
| [`tools/auditing/`](tools/auditing/) | Static testing and supply-chain scanning (e.g. LLM03). See [`supply-chain-scanner`](tools/auditing/supply-chain-scanner/README.md) — `supply-chain-scan --discover` |
| [`tools/defense/`](tools/defense/) | In-line guardrails and prompt injection mitigation (e.g. LLM01). See [`prompt-guard`](tools/defense/prompt-guard/README.md) — `prompt-guard` |
| [`tools/evaluation/`](tools/evaluation/) | RAG validation, hallucination checks, and compliance scoring (e.g. LLM09). See [`rag-audit-engine`](tools/evaluation/rag-audit-engine/README.md) — `rag-audit` |

## Quick start

Each tool under `tools/` is self-contained. Install dependencies from that tool’s `requirements.txt` or `pyproject.toml`, then follow the tool’s local README.

```bash
# Example: supply-chain scanner
cd tools/auditing/supply-chain-scanner
pip install -r requirements.txt
python scan_libs.py --help
```

## Contributing

1. Open an issue or discussion before large changes.
2. Run CI checks locally (see [`.github/workflows/pr-validation.yml`](.github/workflows/pr-validation.yml)).
3. Follow existing patterns in `core/` for shared logic.

## Security

Report vulnerabilities per [SECURITY.md](.github/SECURITY.md). Do not open public issues for undisclosed security bugs.

## License

[MIT License](LICENSE)
