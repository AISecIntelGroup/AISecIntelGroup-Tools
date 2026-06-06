# PromptGuard (LLM01)

Pluggable defense-in-depth pipeline for **prompt injection**, jailbreaks, exfiltration, and obfuscation — aligned with **OWASP LLM01** and **LLM07**.

Developed by [AISecIntel Group](https://github.com/aisecintelgroup) as open-source LLM security tooling.

## Install

```bash
cd tools/defense/prompt-guard
pip install -e ".[dev]"
```

## Quick start

### Library

```python
from prompt_guard import PromptGuard

guard = PromptGuard()
result = guard.check("Please summarize the financial report.")

if result.blocked:
    print(f"Blocked: {result.reason.value}")
```

### CLI

```bash
# Single prompt
prompt-guard --prompt "Help me write a Python script." -f human

# Batch JSONL (CI / red-team fixtures)
prompt-guard --input tests/fixtures/sample_prompts.jsonl -f json

# Report only, always exit 0
prompt-guard --input attacks.jsonl --fail-on none
```

## Features

- **Defense-in-depth pipeline** — fast heuristics first, semantic layer last
- **Unicode spoofing defense** — NFKC normalization, zero-width strip
- **Extensible** — add scanners via `BaseScanner`
- **Offline** — no LLM API required for core scanners (v0.1.0)

### Built-in scanners

| Scanner | Detects |
|---------|---------|
| `ExfiltrationScanner` | Markdown/HTML data exfiltration |
| `PayloadSplittingScanner` | String concatenation bypass |
| `HeuristicScanner` | Overrides, leaks, jailbreaks, agent markup |
| `EntropyScanner` | Base64 and high-entropy floods |
| `SemanticClassifierScanner` | Pluggable ML layer (placeholder in v0.1.0) |

## Output formats

| Format | Flag | Use case |
|--------|------|----------|
| JSON | `-f json` (default) | Integrations, CI gates |
| Human | `-f human` | Terminal / consulting demos |

### JSON envelope

```json
{
  "scanner": "aisecintel-prompt-guard",
  "version": "0.1.0",
  "records": [
    {
      "id": "1",
      "prompt": "...",
      "blocked": true,
      "reason": "DIRECT_OVERRIDE",
      "reason_detail": "Direct system prompt override attempt detected.",
      "matched_fragment": "ignore previous instructions"
    }
  ],
  "summary": {
    "total": 1,
    "blocked": 1,
    "allowed": 0
  }
}
```

## Batch input

**JSON array** or **JSONL**, each record:

```json
{ "id": "optional-id", "prompt": "user or attacker text" }
```

Wrapped `{ "records": [ ... ] }` is also accepted.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | No blocked prompts, or `--fail-on none` |
| `1` | One or more prompts blocked (`--fail-on blocked`) |
| `2` | Missing arguments or invalid input file |

## Custom scanners

```python
from prompt_guard import BaseScanner, BlockReason, PromptGuard, ScanResult

class CustomKeywordScanner(BaseScanner):
    def scan(self, prompt: str) -> ScanResult:
        if "super-secret-project-x" in prompt.lower():
            return ScanResult(True, BlockReason.SYSTEM_LEAK, "Project X mentioned")
        return ScanResult(False)

guard = PromptGuard()
guard.add_scanner(CustomKeywordScanner())
```

## GitHub Actions

```yaml
- name: Install PromptGuard
  run: pip install -e tools/defense/prompt-guard

- name: Scan attack fixtures
  run: prompt-guard --input tools/defense/prompt-guard/tests/fixtures/sample_prompts.jsonl --fail-on none -f human -q
```

Use `--fail-on blocked` in deployment gates when any blocked prompt should fail the job.

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## Security & compliance

Mitigates **LLM01** (Prompt Injection) and **LLM07** (System Prompt Leakage). For enterprise guardrail architecture or red-teaming, visit AISecIntel Group.

## License

MIT (see repository root).
