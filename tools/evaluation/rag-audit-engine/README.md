# RAG Audit Engine (LLM09)

Score RAG pipeline answers for **grounding** (faithfulness to retrieved context) and **alignment** (relevance to the user question). Maps to **OWASP Top 10 for LLM Applications — LLM09: Overreliance**.

Developed by [AISecIntel Group](https://github.com/aisecintelgroup) as open-source LLM security evaluation tooling.

v0.1.0 uses fast **offline heuristics** (token overlap). No live LLM API required — suitable for CI and local dev.

## Install

```bash
cd tools/evaluation/rag-audit-engine
pip install -e ".[dev]"
```

## Quick start

```bash
# Single context + answer
rag-audit \
  --context "Refunds are allowed within 30 days of purchase." \
  --answer "You can return items within 30 days." \
  --query "What is the refund policy?"

# Batch JSONL
rag-audit --input tests/fixtures/sample_batch.jsonl -f human

# CI gate: fail if any record scores below 0.6
rag-audit --input batch.jsonl --fail-below 0.6
```

## Scoring dimensions

| Score | Meaning |
|-------|---------|
| `grounded` | Share of answer tokens supported by context |
| `aligned` | Query term overlap (or non-empty / non-refusal check) |
| `overall` | Average of grounded + aligned |
| `hallucination_risk` | `low` / `medium` / `high` heuristic |

### Flags

- `LOW_GROUNDING` — weak context overlap
- `EMPTY_ANSWER` — blank response
- `POSSIBLE_HALLUCINATION` — many answer tokens absent from context

## Output formats

| Format | Flag | Use case |
|--------|------|----------|
| JSON | `-f json` (default) | Integrations, dashboards |
| Human | `-f human` | Terminal / consulting demos |

### JSON envelope

```json
{
  "scanner": "aisecintel-rag-audit-engine",
  "version": "0.1.0",
  "records": [
    {
      "id": "1",
      "context": "...",
      "answer": "...",
      "scores": {
        "grounded": 0.82,
        "aligned": 1.0,
        "overall": 0.91,
        "hallucination_risk": "low"
      },
      "flags": [],
      "notes": ""
    }
  ],
  "summary": {
    "total": 1,
    "failed": 0,
    "avg_overall": 0.91,
    "fail_below": 0.5
  }
}
```

## Batch input

**JSON array** or **JSONL**, each record:

```json
{
  "id": "optional-id",
  "context": "retrieved chunks",
  "answer": "model response",
  "query": "optional user question"
}
```

Wrapped form `{ "records": [ ... ] }` is also accepted for JSON files.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | All records at/above `--fail-below`, or `--fail-on none` |
| `1` | One or more records below threshold |
| `2` | Missing arguments or invalid input file |
| `3` | Reserved for internal errors |

## GitHub Actions

```yaml
- name: Install RAG audit engine
  run: pip install -e tools/evaluation/rag-audit-engine

- name: Audit RAG fixture set
  run: rag-audit --input tools/evaluation/rag-audit-engine/tests/fixtures/sample_batch.jsonl --fail-below 0.4
```

## Backward compatibility

```bash
python main.py --context "..." --answer "..."
```

Prefer `rag-audit` for new integrations.

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## Roadmap (post-v1)

- Optional embedding-based grounding
- LLM-as-judge adapter (pluggable, off by default)
- Promptfoo / CI report exporters

## License

MIT (see repository root).
