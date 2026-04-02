# Model Reference

All models are accessed via [OpenRouter](https://openrouter.ai) using a single API key. Pricing is per million tokens (input / output) as of April 2026 — verify current rates at openrouter.ai/models.

---

## Current Lineup

| Role | Letter | OpenRouter Slug | Provider | $/1M in | $/1M out |
|------|--------|----------------|----------|---------|---------|
| Council | A | `openai/gpt-5.4-nano` | OpenAI | $0.20 | $1.25 |
| Council | B | `anthropic/claude-3-5-haiku` | Anthropic | $0.80 | $4.00 |
| Council | C | `google/gemini-3.1-flash-lite-preview` | Google | $0.25 | $1.50 |
| Council | D | `x-ai/grok-3-mini-beta` | xAI | $0.30 | $0.50 |
| Chairman | — | `openai/gpt-4o-mini` | OpenAI | $0.15 | $0.60 |

---

## Role Definitions

### Council Models (A / B / C / D)

Council models serve two roles every iteration:

**Stage 1 — Proposer:** Each model independently generates a complete improved version of `artifact.md`. All four run in parallel via `asyncio.gather`. The prompt is identical for all four — diversity comes from the models' intrinsic training, not from assigned personas.

**Stage 2 — Evaluator:** The same four models rank all versions (A/B/C/D + E, where E is the current artifact) anonymously. Letter assignments are shuffled each iteration to prevent positional bias. Each ranker outputs a `FINAL RANKING: X > Y > Z > ...` line, parsed by regex and aggregated into an average position score.

### Chairman Model

The chairman runs only in Stage 3. It receives:
- All four proposals with their original labels (A/B/C/D)
- The current artifact as Version E
- The aggregated Stage 2 rankings (avg_position per version)

It outputs a structured verdict:
```
WINNER: [A-E]
COUNCIL_SCORE: [1-100]

CRITIQUE:
[3-5 sentences]
```

**Critical rule: the chairman must not appear in `COUNCIL_MODELS`.** If the same model is both a council member and chairman, it would judge its own Stage 1 proposal — a direct conflict of interest that invalidates the scoring. `config.py` does not enforce this automatically; it is the operator's responsibility.

---

## Model Selection Rationale

The four council models are chosen for **diversity across reasoning axes**. Diversity is what makes the council useful — if all four models have similar priors, they will converge on the same proposal and ranking, reducing the system to a single model with extra API calls.

| Model | Axis | Why chosen |
|-------|------|-----------|
| `gpt-5.4-nano` | Analytical / structured | Strong at logical argument structure, precision, concise editing |
| `claude-3-5-haiku` | Creative / nuanced | Strong at tone, persuasion, rhetorical effectiveness |
| `gemini-3.1-flash-lite-preview` | Fast / broad | Wide knowledge base, efficient at synthesis |
| `grok-3-mini-beta` | Contrarian / reasoning | Challenges consensus, lightweight chain-of-thought |

The chairman (`gpt-4o-mini`) is chosen for:
- Conflict-free: not in the council
- Strong at structured output parsing (WINNER/COUNCIL_SCORE/CRITIQUE format)
- Low cost per Stage 3 call (~$0.001/iteration)
- Consistent scoring: same scale across iterations

---

## Cost Breakdown Per Iteration

Token estimates assume ~1,200 tokens input / ~800 tokens output for Stage 1, ~4,000 tokens input / ~200 tokens output for Stage 2, and ~5,000 tokens input / ~300 tokens output for Stage 3.

### Stage 1 — Proposals

| Model | In cost | Out cost | Total |
|-------|---------|---------|-------|
| gpt-5.4-nano (A) | $0.00024 | $0.00100 | $0.00124 |
| claude-3-5-haiku (B) | $0.00096 | $0.00320 | $0.00416 |
| gemini-3.1-flash (C) | $0.00030 | $0.00120 | $0.00150 |
| grok-3-mini (D) | $0.00036 | $0.00040 | $0.00076 |
| **Stage 1 total** | | | **$0.00766** |

### Stage 2 — Rankings

| Model | In cost | Out cost | Total |
|-------|---------|---------|-------|
| gpt-5.4-nano (A) | $0.00080 | $0.00025 | $0.00105 |
| claude-3-5-haiku (B) | $0.00320 | $0.00080 | $0.00400 |
| gemini-3.1-flash (C) | $0.00100 | $0.00030 | $0.00130 |
| grok-3-mini (D) | $0.00120 | $0.00010 | $0.00130 |
| **Stage 2 total** | | | **$0.00765** |

### Stage 3 — Chairman

| Model | In cost | Out cost | Total |
|-------|---------|---------|-------|
| gpt-4o-mini | $0.00075 | $0.00018 | **$0.00093** |

### Summary

| | Cost |
|--|------|
| Per iteration | **~$0.016–0.019** |
| 5-iteration test run | **~$0.08–0.10** |
| Default $5 limit | **~260–310 iterations** |
| Overnight run (~8 hrs, 2 min/iter) | **~$3.80** |

> Claude Haiku (B) accounts for ~60% of total cost. Replacing it with a cheaper model (e.g., `google/gemini-2.5-flash-preview` at $0.15/$0.60) would cut the per-iteration cost roughly in half.

---

## Swapping Models

To swap any model, edit `config.py`:

```python
COUNCIL_MODELS = [
    "openai/gpt-5.4-nano",                   # A
    "anthropic/claude-3-5-haiku",            # B  ← change this
    "google/gemini-3.1-flash-lite-preview",  # C
    "x-ai/grok-3-mini-beta",                # D
]
CHAIRMAN_MODEL = "openai/gpt-4o-mini"       # must not appear above
```

Rules:
1. All slugs must be valid OpenRouter model IDs — verify at [openrouter.ai/models](https://openrouter.ai/models)
2. `CHAIRMAN_MODEL` must not match any entry in `COUNCIL_MODELS`
3. At least 2 council models must successfully respond in Stage 1 and Stage 2, or the iteration crashes
4. Do not change models mid-run — scores from before and after the change are not comparable

To test a new model before committing to a full run:

```bash
# Temporarily add it to COUNCIL_MODELS, then:
uv run python evaluate.py
# Watch for its response in Stage 1 output
```

---

## Minimum Viable Configuration

The system can run with as few as 2 council models (e.g., if 2 models fail in a given iteration). However, Stage 2 requires at least 2 valid rankings to produce a meaningful aggregate. If fewer than 2 rankings are parseable, `evaluate.py` exits with code 1 and `run.py` logs a CRASH.

For production use, keep all 4 council models active. If one model is consistently failing (API outage, removed from OpenRouter), replace it in `config.py`.
