# Architecture

## Overview

AutoResearch Council Arena is three systems composed together:

1. **Autoresearch experiment loop** (`run.py`) — the outer loop that manages git state, decides KEEP/DISCARD, and enforces the cost limit.
2. **LLM Council pipeline** (`evaluate.py`) — the frozen evaluation harness that runs three stages of multi-model consensus.
3. **Web dashboard** (`backend/server.py` + `frontend/`) — FastAPI SSE server and React UI for live observation.

These systems are loosely coupled: the experiment loop forks `evaluate.py` as a subprocess, and communicates with the web server only via the filesystem (`events.jsonl`, `artifact.md`, `results.tsv`).

---

## Component Map

```
┌────────────────────────────────────────────────────────────────────────┐
│  run.py  — experiment loop                                             │
│                                                                        │
│  ┌─── subprocess ──────────────────────────────────────────────────┐  │
│  │  evaluate.py  — FROZEN                                          │  │
│  │                                                                 │  │
│  │  Stage 1: query_models_parallel(COUNCIL_MODELS)                │  │
│  │           → proposals {A, B, C, D}                             │  │
│  │                                                                 │  │
│  │  Stage 2: query_models_parallel(COUNCIL_MODELS)                │  │
│  │           with shuffled letter assignments                     │  │
│  │           → aggregate avg_position per version                 │  │
│  │                                                                 │  │
│  │  Stage 3: query_model(CHAIRMAN_MODEL)                          │  │
│  │           → WINNER + COUNCIL_SCORE + CRITIQUE                  │  │
│  │                                                                 │  │
│  │  writes: winning_proposal.md, critique.md                      │  │
│  │  appends: events.jsonl (stage1/2/3_complete events)            │  │
│  │  prints: "council_score: 87" / "winner: B"  (grep-able)       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  reads stdout → extract council_score, winner                         │
│  if KEEP: copy winning_proposal.md → artifact.md, git commit          │
│  appends: results.tsv                                                  │
│  appends: events.jsonl (run_start + iteration_result events)          │
└────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────────┐
                    │  events.jsonl (IPC + persistent log)    │
                    └──────────┬──────────────────────────────┘
                               │ tail (2s poll)
                    ┌──────────▼───────────┐
                    │  backend/server.py   │
                    │  FastAPI + SSE       │
                    │  port 8001           │
                    └──────────┬───────────┘
                               │ SSE + REST (proxied via Vite)
                    ┌──────────▼───────────┐
                    │  frontend/           │
                    │  React + Vite        │
                    │  port 5173           │
                    └──────────────────────┘
```

---

## Data Flow

### Per-Iteration

```
artifact.md          ──┐
program.md           ──┤
results.tsv          ──┤──→ evaluate.py ──→ winning_proposal.md
critique.md          ──┤                └──→ critique.md
tried_strategies.md  ──┘                └──→ events.jsonl (append)
                                         └──→ stdout: "council_score: N" / "winner: X"

run.py reads stdout
├── KEEP:  winning_proposal.md → artifact.md → git commit
└── DISCARD: no-op (artifact.md unchanged)

run.py appends to results.tsv
run.py appends one line to tried_strategies.md (both KEEP and DISCARD)
```

### Across Iterations

```
iteration 1 → KEEP  → artifact.md = v1 → git commit (branch tip = v1)
iteration 2 → DISCARD → artifact.md = v1 (unchanged)
iteration 3 → KEEP  → artifact.md = v2 → git commit (branch tip = v2)
```

Branch tip always equals the current best artifact. This is the autoresearch invariant.

---

## `evaluate.py` — Pipeline Stages

### Stage 1: Parallel Proposal Generation

All four council models receive the same prompt concurrently via `asyncio.gather`. The prompt includes:

- `program.md` — objectives, evaluation criteria, constraints
- `artifact.md` — current version to improve
- Last 5 rows of `results.tsv` — experiment history
- `critique.md` — chairman's previous feedback

Each model responds with a complete improved version. Models that fail (timeout, API error) are silently excluded. Successful responses are assigned letters A, B, C, D in council model order.

### Stage 2: Anonymous Ranking

The same four council models rank all versions, including the current artifact as **Version E** (the baseline to beat).

**Positional bias mitigation:** Letter assignments are shuffled each iteration. A model whose proposal was "A" in Stage 1 might appear as "D" in Stage 2. Rankings are aggregated in display-letter space, then mapped back to original identifiers.

Each ranker produces a `FINAL RANKING: B > E > A > C > D` line. Rankings are parsed via regex. Models that fail or produce unparseable output are excluded from aggregation. Results are sorted by **average position** (lower = ranked higher by peers).

### Stage 3: Chairman Judgment

The chairman (`openai/gpt-4o-mini`) receives:

- All proposals with their original letter labels (A/B/C/D)
- Current artifact as Version E
- Aggregated rankings from Stage 2

The chairman outputs:
```
WINNER: [A-E]
SCORE_CORRECTNESS: [0-20]
SCORE_COMPLETENESS: [0-20]
SCORE_CLARITY: [0-20]
SCORE_CODE_QUALITY: [0-20]
SCORE_DEPTH: [0-20]
COUNCIL_SCORE: [sum, 0-100]

CRITIQUE:
[3-5 sentences]
```

`evaluate.py` parses each sub-score independently, clamps each to `[0, 20]`, and **computes the total itself** — the chairman's stated `COUNCIL_SCORE` is ignored. This prevents arithmetic errors from affecting the metric.

**Word count guard:** If the winning proposal exceeds `MAX_ARTIFACT_WORDS`, it falls back to E. This prevents the system from drifting toward verbose outputs.

### Why Multi-Dimensional Scoring?

**The single-score anchoring problem.**

When the chairman assigns one score (1–100) it has no objective anchor. The first time it sees a good proposal it assigns 95. On subsequent iterations, even if a new proposal is genuinely better, the chairman has no criteria-specific reason to score it 96 or 97 — it simply "looks about 88" based on general impression. The first score becomes an implicit ceiling.

This was observed in practice: after iteration 1 scored 95, peers consistently ranked new proposals *above* the current artifact (Version E avg_pos ≈ 3.5–4.0), yet the chairman scored them 88–92 every time. The council agreed the proposals were better; the chairman's single score could not express that.

**Why sub-scores fix it.**

Each dimension has a specific description that anchors the score to observable facts:

| Dimension | Anchored question |
|-----------|------------------|
| CORRECTNESS | Does the code run without modification? |
| COMPLETENESS | Are all essential steps present? |
| CLARITY | Can an intermediate Python reader follow it? |
| CODE_QUALITY | No hardcoded secrets? Error handling present? |
| DEPTH | Does it explain *why*, not just *how*? |

A tutorial that adds proper error handling moves `SCORE_CODE_QUALITY` from 8 to 14 — a concrete, justifiable change. The other four dimensions don't move. The total score rises by 6 points, reflecting a real improvement in one dimension.

This makes it much harder to max out in a single iteration (all five dimensions would need to be near-perfect simultaneously) and makes it harder for the chairman to anchor — each dimension is judged against its own criteria, not against a remembered previous total.

**Configuration.** Dimensions are defined in `SCORING_DIMENSIONS` in `config.py` — a list of `(key, description)` tuples. Change them when you change tasks. The prompt, parser, and UI all derive from this list automatically.

---

## `run.py` — Experiment Loop

### Hill-Climbing Logic

```python
improved = (score > best_score + IMPROVEMENT_THRESHOLD) and (winner != "E")
```

Two conditions must both be true:
1. Score exceeds the current best by at least `IMPROVEMENT_THRESHOLD` (default: 2 points)
2. The winner is a new proposal, not Version E (the current artifact)

If `winner == "E"`, the existing artifact was judged best. No improvement, no commit.

### Git Discipline

- A new branch `autoresearch/{timestamp}` is created at startup
- Only KEEP iterations produce commits
- The branch tip is always the current best artifact
- `results.tsv` is never committed (it's in `.gitignore`) — only `artifact.md` and `critique.md`

### Cost Limiting

At startup, `run.py` queries `https://openrouter.ai/api/v1/auth/key` and records `initial_usage` from the `usage` field (cumulative USD spent since key creation). Before each iteration, it reads the current `usage` again and computes `spent = current_usage - initial_usage`. If `spent >= COST_LIMIT_USD`, the loop stops cleanly.

This uses real billing data from OpenRouter, not an estimate. Works for both credit-limited and unlimited keys because it tracks cumulative usage rather than remaining balance. Set `COST_LIMIT_USD` in `.env` to control the limit (blank or absent = no limit).

### Failure Modes

| Condition | Behavior |
|-----------|----------|
| `evaluate.py` timeout (>300s) | Log TIMEOUT, continue |
| `evaluate.py` non-zero exit | Log CRASH, continue |
| stdout parse failure | Log PARSE_FAILURE, continue |
| 3 consecutive CRASH/PARSE_FAILURE | Sleep 60s before retry |
| Plateau (`PLATEAU_WINDOW` consecutive DISCARDs) | Emit `run_end`, exit gracefully |
| `stop.flag` present at iteration start | Emit `run_end`, exit gracefully |
| Cost limit reached | Emit `run_end`, exit gracefully |
| Ctrl+C | Immediate exit — no `run_end` event |

---

## `backend/server.py` — SSE Server

The server does not participate in the experiment loop — it is read-only. It:

1. Tails `events.jsonl` by tracking file position, waking every 2 seconds
2. Pushes new JSON lines as `data: {...}\n\n` SSE frames
3. Injects a `heartbeat` event with current iteration count and best score every 2 seconds

CORS is restricted to `localhost:5173` / `127.0.0.1:5173`. The server is started with `--reload` for development convenience.

---

## Frontend Architecture

The React frontend is intentionally minimal (no build-time framework, no routing, no state management library). State is managed with `useState` + `useEffect`.

**Data sources:**

| Source | Frequency | Data |
|--------|-----------|------|
| `GET /api/status` | Every 5s (poll) | iteration, best_score, artifact_words |
| `GET /api/results` | Every 5s (poll) | Full results.tsv as JSON |
| `GET /api/artifact` | Every 5s (poll) | Current artifact text |
| `GET /api/stream` | Persistent SSE | Stage events, auto-tab-switch |

**Tab auto-switching:** When an SSE event arrives, the active tab switches to match the just-completed stage:
- `stage1_complete` → switch to Stage 1 tab
- `stage2_complete` → switch to Stage 2 tab
- `stage3_complete` → switch to Stage 3 tab

---

## File Encoding Contracts

| File | Producer | Consumer | Format |
|------|----------|----------|--------|
| `artifact.md` | `run.py` (KEEP), initial human | `evaluate.py`, `backend/server.py`, frontend | UTF-8 Markdown |
| `program.md` | Human | `evaluate.py` | UTF-8 Markdown |
| `critique.md` | `evaluate.py` | `evaluate.py` (next iteration) | UTF-8 plain text |
| `tried_strategies.md` | `run.py` | `evaluate.py` (Stage 1 prompt) | UTF-8, one line per iteration, append-only within a run |
| `winning_proposal.md` | `evaluate.py` | `run.py` | UTF-8 Markdown |
| `events.jsonl` | `evaluate.py`, `run.py` | `backend/server.py` | UTF-8, one JSON object per line, append-only across runs |
| `run.log` | `start.sh` (`tee`) | Human inspection | UTF-8 plain text, overwritten each `bash start.sh` |
| `results.tsv` | `run.py` | `evaluate.py`, `backend/server.py` | UTF-8, tab-separated, header row |

---

## Design Decisions

### Why `events.jsonl` instead of a message queue?

JSONL append is atomic per-line on all modern OS/filesystems for writes under 4KB (each event is well under this). No Redis, no pub/sub infrastructure, no daemon. The SSE server's 2-second poll latency is acceptable for a system where each iteration takes 1-5 minutes.

`events.jsonl` is cleared at the start of each run (along with `results.tsv`, `critique.md`, and `winning_proposal.md`) so every `bash start.sh` is a clean slate. Within a run it is append-only. `run.py` emits `run_start` at startup and `iteration_result` after each KEEP/DISCARD, making it a complete machine-readable run log (complementing the human-readable `run.log` created by `tee` in `start.sh`).

### Why fork `evaluate.py` as a subprocess?

The safety timeout is enforced at the OS process level via `subprocess.run(timeout=EXPERIMENT_TIMEOUT)`. A Python `asyncio.wait_for` cannot reliably kill hung network calls. The subprocess also provides clean stdout capture for metric extraction — the autoresearch grep pattern (`council_score: 87`, `winner: B`).

### Why commit after evaluation, not before?

Base autoresearch commits the modified training script before evaluation and reverts on DISCARD. This works because the artifact is a Python file that can be git-reset. Here, the "artifact" is the winning proposal, which only exists after Stage 3 runs. Committing after evaluation is the only option. The branch-tip invariant is preserved.

### How is the stop signal communicated from the UI to `run.py`?

The backend and experiment loop are separate processes with no shared memory. The signal uses a **flag file** (`stop.flag`):

1. User clicks Stop Run in the dashboard
2. Frontend calls `POST /api/stop`
3. Backend writes `stop.flag` to the project root
4. `run.py` checks `stop.flag` at the start of each iteration — if it exists, calls `graceful_exit()` and breaks

This is the same filesystem-coupling pattern used for `events.jsonl` IPC. No sockets, no signals, no inter-process communication beyond the filesystem. `stop.flag` is deleted by `graceful_exit()` and also cleared on the next `bash start.sh`.

The same `graceful_exit()` path handles all three clean exit conditions (plateau, stop button, cost limit), ensuring `run_end` is always emitted and logs are always consistent.

### How does our time budget compare to Karpathy's?

In karpathy/autoresearch, `TIME_BUDGET = 300` is a **minimum guaranteed training duration**. Inside `train.py`, the loop accumulates actual GPU wall-clock time per step (`total_training_time += dt`) and only exits when it has consumed at least 300 seconds of compute:

```python
if step > 10 and total_training_time >= TIME_BUDGET:
    break
```

Each iteration always uses the full 5-minute budget. This makes sense because neural network training is compute-bound — more time means more gradient steps and a better model.

Our `EXPERIMENT_TIMEOUT = 300` is fundamentally different: it is a **safety kill switch** applied externally via `subprocess.run(timeout=300)`. A normal iteration completes in 30–90 seconds (9 LLM API calls) and is never held to 300 seconds. If evaluate.py somehow hangs, the subprocess is killed and the iteration is logged as TIMEOUT.

The correct analog to Karpathy's fixed time budget is our **fixed call structure**: every iteration always runs all 3 stages with all 4 council models — 4 proposals + 4 rankings + 1 chairman judgment = 9 API calls. This is the unit of work, not wall-clock time. LLM API calls are network-bound; there is no meaningful way to make them "train longer."

### Why do council models repeat similar proposals, and how does `tried_strategies.md` fix it?

**Root cause — structural difference from Karpathy's single-agent loop:**

In karpathy/autoresearch there is one LLM agent that iterates over time. It reads `train.py`, makes a targeted edit, and its git history records exactly what it changed and what happened. On the next iteration it reads `git log --oneline` as part of its context and knows which approaches have already been tried.

In our system there are four parallel models with no memory across iterations. Each iteration they receive:

| Signal | Content | Problem |
|--------|---------|---------|
| `artifact.md` | Current best version | Only changes on KEEP — identical for all DISCARDs |
| `results.tsv` | `score | status | description` | Shows *that* something was tried, not *what* |
| `critique.md` | Chairman's one critique | One paragraph — the only qualitative signal |

The models have no memory of what they individually proposed. With temperature=0.7 and the same prompt, models converge to the same obvious improvements (add structure, add evidence, sharpen the thesis). On consecutive DISCARDs where the artifact is unchanged, each iteration is nearly identical from the model's perspective.

This is the equivalent of an autoresearch agent that cannot read `git log` — it would also repeat the same changes.

**Fix — `tried_strategies.md`:**

After every iteration (KEEP or DISCARD), `run.py` appends a one-line entry to `tried_strategies.md`:

```
Iter 1 (DISCARD, score=72): Added statistical evidence but opening remained weak.
Iter 2 (KEEP,    score=81): Restructured with problem→solution arc — now the current artifact.
Iter 3 (DISCARD, score=79): Tried emotional appeals but lost analytical credibility.
```

This file is included in the Stage 1 prompt under a `STRATEGIES ALREADY TRIED` header. Models are explicitly instructed not to repeat listed strategies and to try something different. This mirrors the role of `git log` in Karpathy's single-agent loop — a growing record of what has been attempted and whether it worked.

`tried_strategies.md` is cleared on each `bash start.sh` (clean slate) and is never committed to git.

### Why freeze `evaluate.py`?

Scoring stability. If the evaluator changes between iteration 10 and iteration 50, a score of 87 in each is not comparable. The loop loses its objective and the git log becomes meaningless. `evaluate.py` plays the role of `prepare.py` in autoresearch — fixed infrastructure around a changing artifact.
