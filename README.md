# autoresearch-council-arena

**4 AIs compete to write the best argument for why they should exist. The best version survives.**

An autonomous writing optimizer that combines two frameworks by Andrej Karpathy:

- **[autoresearch](https://github.com/karpathy/autoresearch)** — the experiment loop (commit → evaluate → keep/discard → repeat forever)
- **[llm-council](https://github.com/karpathy/llm-council)** — the evaluation pipeline (parallel proposals → anonymous ranking → chairman synthesis)

Each iteration, 4 language models compete to improve the current draft. They then anonymously rank each other's proposals. A chairman picks the winner and assigns a `council_score`. If the score improves, the artifact is updated and committed. Otherwise, discarded. The loop runs overnight.

---

## Demo topic

> "Autoresearch + LLM Council is the simplest, cheapest way to achieve recursive self-intelligence."

The system argues for its own existence — and its quality of argument is the proof of its thesis.

---

## How it works

```
┌──────────────────────── autoresearch loop ────────────────────────┐
│                                                                    │
│   ┌──────────── llm-council pipeline (per iteration) ──────────┐  │
│   │                                                             │  │
│   │  Stage 1: 4 models propose improved artifact (parallel)    │  │
│   │  Stage 2: Anonymous ranking — "Version A/B/C/D/E"          │  │
│   │           (E = current artifact as baseline)                │  │
│   │  Stage 3: Chairman picks winner, assigns council_score      │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                            ↓                                       │
│   council_score > best + threshold?                                │
│     YES → KEEP (write winning version, git commit)                 │
│     NO  → DISCARD (no commit, log to results.tsv)                  │
│                            ↓                                       │
│   Log to results.tsv, save critique.md, repeat forever             │
└────────────────────────────────────────────────────────────────────┘
```

**9 API calls per iteration** (~$0.005–0.02 depending on models).  
**~200 iterations per hour** possible.  
**~$1–4 for an overnight run.**

---

## File structure

```
autoresearch-council-arena/
├── evaluate.py     FROZEN — three-stage council pipeline (don't edit)
├── artifact.md     EDITABLE — the writing being optimized
├── program.md      GUIDANCE — topic, audience, criteria (edit to change the task)
├── config.py       Council models, chairman, thresholds
├── openrouter.py   Async LLM client
├── run.py          Autonomous experiment loop
├── results.tsv     Experiment log (auto-generated)
├── critique.md     Latest chairman critique (auto-generated)
├── backend/        FastAPI SSE server
└── frontend/       React dashboard
```

The three-file discipline from autoresearch is strictly followed:
- `evaluate.py` is frozen (never modified after setup)
- `artifact.md` is the only file that changes between iterations
- `program.md` is the human's control point

---

## Setup

**1. Prerequisites**
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Node.js 18+ and npm
- An [OpenRouter](https://openrouter.ai/) API key

**2. Clone and configure**
```bash
git clone https://github.com/YOUR_USERNAME/autoresearch-council-arena
cd autoresearch-council-arena
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

**3. Run**
```bash
bash start.sh
```

Opens:
- **http://localhost:5173** — live dashboard
- **http://localhost:8001** — backend API

The experiment loop starts automatically and runs until you press `Ctrl+C`.

---

## Customizing the task

Edit `program.md` to change the topic, audience, and evaluation criteria.  
Edit `artifact.md` to change the starting draft (weaker start = more dramatic improvement arc).  
Edit `config.py` to swap models.

**Model selection** (from `config.py`):

| Slot | Default | Axis |
|------|---------|------|
| 1 | `openai/gpt-4o` | Analytical / structured |
| 2 | `anthropic/claude-sonnet-4` | Creative / nuanced |
| 3 | `google/gemini-2.5-flash-preview` | Fast / broad knowledge |
| 4 | `meta-llama/llama-4-maverick` | Contrarian / open-source |

Swap any model by editing the `COUNCIL_MODELS` list — no other code changes needed.  
All models must be available on [OpenRouter](https://openrouter.ai/models).

---

## Cost breakdown

| Component | Calls/iter | Est. cost/iter |
|-----------|-----------|----------------|
| Stage 1 (4 proposals) | 4 | ~$0.008 |
| Stage 2 (4 rankings) | 4 | ~$0.006 |
| Stage 3 (1 chairman) | 1 | ~$0.004 |
| **Total** | **9** | **~$0.018** |

100 iterations ≈ $1.80. Overnight run (500 iterations) ≈ $9.

Reduce cost by using cheaper models in `COUNCIL_MODELS` (e.g. `google/gemini-2.5-flash-preview` for all slots).

---

## Verification checklist

```bash
# 1. Three-file discipline: evaluate.py should have 1 commit, artifact.md many
git log --follow evaluate.py
git log --follow artifact.md

# 2. Council pipeline works standalone
python evaluate.py
# Expect: "council_score: XX" and "winner: X" in stdout

# 3. Greedy logic: check results.tsv after 10 iterations
# Only KEEP commits should appear in git log
git log --oneline

# 4. Parallel Stage 1: should complete in ~8s (not ~32s)
time python evaluate.py 2>&1 | grep "Stage 1 complete"
```

---

## Credits

Built on:
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — autonomous ML experiment loop
- [karpathy/llm-council](https://github.com/karpathy/llm-council) — multi-model consensus pipeline

Both frameworks by [Andrej Karpathy](https://github.com/karpathy). This project is their natural synthesis.
