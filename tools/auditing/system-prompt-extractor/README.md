# system-prompt-extractor

OWASP LLM07 (System Prompt Leakage) testing tool. Sends a library of known
extraction techniques to a target LLM endpoint and scores how easily the
system prompt can be recovered.

**For authorized security testing only.** Only run this against systems you
own or have explicit, documented permission to test. The `--confirm-authorized`
flag is required at runtime as an acknowledgment of this.

## Install

```bash
cd tools/auditing/system-prompt-extractor
pip install -r requirements.txt
```

## Quick start

Preview the payload library without sending anything:

```bash
python extractor.py --dry-run --category all
```

Run against an OpenAI-compatible chat endpoint:

```bash
python extractor.py \
  --target https://api.example.com/v1/chat/completions \
  --header "Authorization: Bearer $API_KEY" \
  --model gpt-4o-mini \
  --category direct,roleplay \
  --confirm-authorized \
  --output report.json
```

Run the full technique set, including multi-turn:

```bash
python extractor.py --target <url> --header "Authorization: Bearer $KEY" \
  --category all --confirm-authorized --output report.json
```

## Targeting a non-OpenAI-shaped API

Provide a request template with `{{PROMPT}}` (and optionally `{{MODEL}}`)
placeholders, plus the dot-path to the response text:

```bash
python extractor.py \
  --target https://internal-api.example.com/chat \
  --request-template my_template.json \
  --response-path result.answer \
  --confirm-authorized
```

`my_template.json`:

```json
{
  "user_input": "{{PROMPT}}",
  "session_id": "audit-test"
}
```

Note: multi-turn techniques (`--category multi_turn`) currently require an
OpenAI-style `messages` array in the template, since they need to carry
conversation history across turns. Single-turn categories work with any
template shape.

## Categories

| Category | Techniques | Description |
|---|---|---|
| `direct` | 10 | Direct or lightly disguised asks |
| `roleplay` | 8 | Persona/fictional framing |
| `encoding` | 8 | Obfuscated output requests (base64, translation, etc.) |
| `completion` | 5 | Prefix-injection / fill-in-the-blank tricks |
| `multi_turn` | 4 | Multi-step conversational sequences |

Default run uses `direct,roleplay` (highest yield, lowest false-positive rate).
Pass `--category all` for full coverage.

## Output

Writes a JSON report (`--output`, default `report.json`) with a 0-100
**exposure score**, per-technique results, and a plain-text summary printed
to stdout. The exposure score is a risk-weighted proportion of techniques
that triggered a likely leak, not a guarantee, always spot-check flagged
responses before putting them in a client deliverable.

## Responsible-use design notes

- Requests are paced (`--delay`, default 1.5s) and back off on HTTP 429/5xx
  using `Retry-After` when present. This exists to keep test runs from
  overwhelming a target and to keep results representative of normal
  traffic, not to disguise the tool's activity.
- The tool does not rotate IPs, spoof user agents, or otherwise attempt to
  evade a target's rate limiting, WAF, or bot detection. If a target blocks
  the tool, that's a legitimate finding, in an authorized engagement the
  standard fix is coordinating an allowlist with the client, not routing
  around their defenses.
- `--confirm-authorized` is required before any live request is sent.

## Extending

Add new techniques by editing the relevant YAML file under `payloads/`, no
code changes needed. Each entry needs `id`, `name`, `description`, `prompt`
(or `turns` for multi-turn), and `risk_weight` (0-1, used in the exposure
score calculation).
