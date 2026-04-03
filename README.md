# AutoResearch Council Arena

**4 AIs compete to write the best argument for why they should exist. The best version survives.**

An autonomous writing optimizer that combines two frameworks by Andrej Karpathy:

- **[autoresearch](https://github.com/karpathy/autoresearch)** — greedy hill-climbing experiment loop (commit → evaluate → keep/discard → repeat forever)
- **[llm-council](https://github.com/karpathy/llm-council)** — multi-model consensus pipeline (parallel proposals → anonymous ranking → chairman synthesis)

The demo topic — *"Autoresearch + LLM Council is the simplest, cheapest way to achieve recursive self-intelligence"* — is itself proof of concept: the system is continuously improving the argument for its own existence.

> **Status: early development.** This project has not been extensively tested. Expect rough edges, especially around Windows path handling, port conflicts, and OpenRouter model availability. Contributions and bug reports welcome.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      run.py  (NEVER STOP)                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  evaluate.py  (FROZEN)                   │   │
│  │                                                          │   │
│  │  Stage 1 ─ Parallel Proposals                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│  │  │GPT-5.4n│ │Haiku3.5│ │Gem3.1  │ │Grok3mn │ → A B C D │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘           │   │
│  │                                                          │   │
│  │  Stage 2 ─ Anonymous Ranking (shuffled letters)         │   │
│  │  Same 4 models rank A B C D E (E = current artifact)    │   │
│  │  → aggregate avg_position per version                   │   │
│  │                                                          │   │
│  │  Stage 3 ─ Chairman Judgment                            │   │
│  │  GPT-4o Mini selects winner, assigns score 1–100        │   │
│  │  → winning_proposal.md  +  critique.md                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  score > best + threshold?                                      │
│    KEEP    → write artifact.md, git commit, update best_score   │
│    DISCARD → artifact.md unchanged, no commit                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                    events.jsonl  (append-only IPC)
                              │
               backend/server.py  (FastAPI SSE, port 8001)
                              │
                     frontend/  (React + Vite, port 5173)
```

**9 API calls per iteration** · ~$0.019/iteration · ~$1.90 per 100 iterations.

---

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- [Node.js](https://nodejs.org/) 18+
- An [OpenRouter](https://openrouter.ai/) API key with credits

### Setup

```bash
git clone https://github.com/az9713/autoresearch-council-arena
cd autoresearch-council-arena

cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY
```

### Run

```bash
bash start.sh
```

| URL | Service |
|-----|---------|
| http://localhost:5173 | Live dashboard |
| http://localhost:8001 | REST API + SSE |
| http://localhost:8001/docs | Swagger UI |

Press **Ctrl+C** to stop everything.

---

## Project Structure

```
autoresearch-council-arena/
├── run.py              # Experiment loop — greedy hill-climbing, git commits, cost limit
├── evaluate.py         # FROZEN — three-stage council pipeline (never modify)
├── openrouter.py       # Async LLM client (asyncio.gather parallel calls)
├── config.py           # Models, thresholds, cost limit
├── program.md          # Human control point: topic, audience, evaluation criteria
├── artifact.md         # Current best version (auto-updated on KEEP)
│
├── backend/
│   └── server.py       # FastAPI SSE server
│
├── frontend/
│   └── src/
│       ├── App.jsx          # Layout, SSE consumer, 5s polling
│       ├── Stage1.jsx       # Proposals tab (A/B/C/D with model labels)
│       ├── Stage2.jsx       # Rankings tab (street-cred bar chart)
│       ├── Stage3.jsx       # Verdict tab (score dial, critique, KEEP/DISCARD)
│       ├── ArtifactView.jsx # Current artifact with expandable previous version
│       └── ResultsChart.jsx # Score-over-time line chart (Recharts)
│
├── start.sh            # One-command launcher
├── pyproject.toml      # Python dependencies
└── .env.example        # API key template
```

**Auto-generated at runtime:**

| File | Committed | Description |
|------|-----------|-------------|
| `events.jsonl` | No | Append-only log — stage events (evaluate.py) + run/iteration events (run.py); persists across runs |
| `run.log` | No | Human-readable terminal output from the last `bash start.sh`; overwritten each restart |
| `winning_proposal.md` | No | Latest winning proposal (read by `run.py` on KEEP) |
| `critique.md` | **Yes** | Chairman critique — committed on KEEP and fed back into Stage 1 next iteration |
| `results.tsv` | No | Full iteration log (commit, score, status, timestamp) |

---

## Configuration

### `.env`

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

### `config.py` — Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `COUNCIL_MODELS` | 4 models (see below) | Proposers and evaluators |
| `CHAIRMAN_MODEL` | `gpt-4o-mini` | Stage 3 judge (must not be in COUNCIL_MODELS) |
| `IMPROVEMENT_THRESHOLD` | `2` | Minimum score delta to KEEP |
| `EXPERIMENT_TIMEOUT` | `300` | Wall-clock budget per iteration (seconds) |
| `MAX_ARTIFACT_WORDS` | `3000` | Hard cap — proposals over this fall back to E |
| `PLATEAU_WINDOW` | `10` | Consecutive DISCARDs before plateau warning |
| `COST_LIMIT_USD` | `5.00` | Stop when this much has been spent (set in `.env`, blank = no limit) |

### Model Selection

The four council models are chosen for diversity across reasoning axes:

| Letter | Model | Axis |
|--------|-------|------|
| A | `openai/gpt-5.4-nano` | Analytical / structured reasoning |
| B | `anthropic/claude-3-5-haiku` | Creative / nuanced prose |
| C | `google/gemini-3.1-flash-lite-preview` | Fast / broad knowledge |
| D | `x-ai/grok-3-mini-beta` | Contrarian / reasoning |
| Chairman | `openai/gpt-4o-mini` | Stage 3 judge (conflict-free) |

Swap any model by editing `COUNCIL_MODELS` in `config.py` — no other changes needed. All models must be valid [OpenRouter slugs](https://openrouter.ai/models).

### Customizing the Topic

Edit `program.md` to change what the system optimizes. It defines the topic, target audience, evaluation criteria, constraints, and exploration directions. This is the **only human control point** during a run — edit it between iterations to steer the optimization or break a plateau.

---

## Live Dashboard

The React frontend auto-switches tabs as each stage completes:

| Tab | Shows |
|-----|-------|
| **Artifact** | Current `artifact.md` with expandable previous version |
| **Stage 1 · Proposals** | All four proposals with model labels and word counts |
| **Stage 2 · Rankings** | Aggregate rankings with "street cred" bar visualization |
| **Stage 3 · Verdict** | WINNER, COUNCIL_SCORE dial, KEEP/DISCARD status, critique |

The left sidebar shows iteration count, best score, KEEP/DISCARD totals, word count, and a score-over-time line chart.

---

## Cost

| Component | Calls/iteration | Estimated cost |
|-----------|----------------|----------------|
| Stage 1 — 4 proposals (A/B/C/D) | 4 | ~$0.008 |
| Stage 2 — 4 anonymous rankings | 4 | ~$0.010 |
| Stage 3 — 1 chairman judgment | 1 | ~$0.001 |
| **Total** | **9** | **~$0.019** |

Claude Haiku (council B) is the most expensive model in the lineup — it dominates Stage 1 and Stage 2 costs. The default `COST_LIMIT_USD = 5.00` gives ~260 iterations. Cost is tracked in real time via OpenRouter's credits API — no estimating.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step setup and first quick wins |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Dashboard walkthrough, steering, long runs, custom topics |
| [docs/MONITORING.md](docs/MONITORING.md) | Reading the dashboard signals, score patterns, when to act |
| [docs/MODELS.md](docs/MODELS.md) | Model lineup, roles, pricing, conflict rules, swapping guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Data flow, component map, design decisions |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | All REST endpoints and SSE event types |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Full config reference with explanations |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Dev setup, conventions, debugging guide |

---

## Verification

```bash
# Evaluate.py works standalone (one iteration, no loop)
uv run python evaluate.py
# Expected output includes: "council_score: XX" and "winner: X"

# Stage 1 parallelism — should complete in ~8s, not ~32s
time uv run python evaluate.py 2>&1 | grep "Stage 1 complete"

# Git discipline — only KEEP iterations produce commits
git log --oneline

# Three-file discipline — evaluate.py has 1 commit, artifact.md has many
git log --follow evaluate.py
git log --follow artifact.md
```

---

## Credits

Built on:
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — autonomous experiment loop, greedy hill-climbing, git discipline
- [karpathy/llm-council](https://github.com/karpathy/llm-council) — three-stage pipeline, FastAPI + SSE, async OpenRouter client

Both frameworks by [Andrej Karpathy](https://github.com/karpathy). This project is their natural synthesis.
