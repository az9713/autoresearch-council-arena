# Monitoring Guide

How to read the live dashboard and terminal output to understand whether your experiment is healthy, plateauing, or broken.

---

## The Two-Minute Check

Do this every time you glance at a running experiment:

1. **Best Score** (sidebar) — is it higher than last time you checked?
2. **Score chart** (sidebar) — upward slope, or flat?
3. **Latest critique** (Stage 3 tab) — is the chairman repeating the same complaint?
4. **KEEP:DISCARD ratio** (sidebar) — if worse than 1:8, edit `program.md`

---

## Left Sidebar

The sidebar is always visible regardless of which tab is active. Check it first.

| Field | Healthy | Warning |
|-------|---------|---------|
| **Best Score** | Climbing over time | Stuck at the same value for many iterations |
| **KEEPs** | Growing steadily | Zero KEEPs after 10+ iterations |
| **DISCARDs** | 3–5× more than KEEPs | 10×+ more than KEEPs |
| **Artifact words** | Stable or growing slowly | Approaching 3000 (the hard cap) |

**KEEP:DISCARD ratio** is the single most important health signal. A normal run produces roughly 1 KEEP for every 3–5 DISCARDs. The council is exploring — most proposals don't improve on the current best, and that's correct behavior.

---

## Score Chart

A line chart of `council_score` for every iteration. Green dots mark KEEPs.

| Pattern | Interpretation | Action |
|---------|---------------|--------|
| Climbing trend with green dots | Healthy — system is finding genuine improvements | None |
| Flat line, no green dots for 10+ iterations | Plateau at a local maximum | Edit `program.md` — add new Exploration Directions |
| Sharp early jump, then flat | Hit a high score quickly; council is stuck | Try radically different structural approaches |
| Oscillating ±3–5 points, no KEEPs | Normal noise — threshold is absorbing fluctuations | Wait a few more iterations before acting |
| Sudden drop | A model failed; chairman fell back to Version E | Check terminal for CRASH or PARSE_FAILURE |
| Score never above 40 | Artifact quality is genuinely low, or criteria are too strict | Review `program.md` evaluation criteria |

**Score noise is normal.** The chairman scores on a 1–100 scale and the same text can score 85 one iteration and 82 the next. The `IMPROVEMENT_THRESHOLD = 2` absorbs this. Watch the trend over 10+ iterations, not individual values.

---

## Stage 1 · Proposals Tab

Auto-activates when Stage 1 completes. Shows four proposal cards (A/B/C/D) with model names and word counts.

**What to watch:**

| Signal | Interpretation | Action |
|--------|---------------|--------|
| One model consistently much longer than others | That model may be padding — verbose ≠ better | Note which model; check if it keeps winning |
| All proposals look nearly identical | Council lacks diversity; models are converging | Swap one model for something more divergent |
| One or more cards missing | That model failed the API call | Check terminal for `[openrouter] Error querying...` |
| Word counts approaching 3000 | Risk of hitting `MAX_ARTIFACT_WORDS` cap | Tighten word limit in `program.md` |

---

## Stage 2 · Rankings Tab

Bar chart — each bar is a version's "street cred": a normalized score from average peer ranking position. Higher bar = ranked better by peers.

**What to watch:**

| Signal | Interpretation | Action |
|--------|---------------|--------|
| **Version E has the highest bar** | Current artifact outranked all proposals — expect DISCARD | Normal; act if it persists 5+ iterations |
| One proposal dominates every iteration | Council consistently prefers one model's style | Check if that model is also winning Stage 3 |
| All bars roughly equal | No consensus — council is divided | Chairman's judgment becomes the deciding factor |
| Version E always last | Current artifact is clearly weak — proposals always beat it | Expect frequent KEEPs; watch score climb |
| Bars wildly inconsistent between iterations | High variance in rankings; models disagree strongly | Normal for creative tasks; less normal for structured tasks |

**Version E is your baseline.** Every proposal must beat it to have a chance at KEEP. If E consistently wins Stage 2, the system is stuck — the council can't find anything better than what it already has.

---

## Stage 3 · Verdict Tab

The most actionable tab. Check it after every iteration.

### Score Dial

A circular gauge showing the chairman's `council_score` (1–100) for the winning version.

| Range | Interpretation |
|-------|---------------|
| 0–40 | Low quality — artifact needs significant work |
| 40–65 | Developing — meaningful content but clear weaknesses |
| 65–80 | Good — solid argument, minor improvements possible |
| 80–90 | Strong — high quality, hard to improve further |
| 90–100 | Exceptional — expect plateau; council will struggle to beat this |

The score is intended to be **comparable across iterations** — 87 in iteration 5 should mean the same as 87 in iteration 50. If you see scores jumping wildly (e.g., 90 → 40 → 85), the chairman is being inconsistent, which undermines hill-climbing.

### KEEP / DISCARD Badge

- **KEEP (green)** — score improved by ≥2 points AND winner was not Version E. Artifact updated, git committed.
- **DISCARD (red)** — no improvement, or winner was E. Artifact unchanged.

A DISCARD is not a failure — it means the system correctly rejected a proposal that didn't beat the current best.

### The Critique

**Read this every few iterations.** The chairman writes 3–5 sentences explaining what worked, what didn't, and what to try next. This critique is fed directly into the Stage 1 prompt for all four council models in the next iteration.

| Critique pattern | Interpretation | Action |
|-----------------|---------------|--------|
| Different feedback each iteration | Council is exploring new directions | None |
| Same complaint repeated 3+ times | Models are ignoring the critique | Add that specific direction to `program.md` Exploration Directions |
| "The current version is the best" | Winner was E — proposals offered nothing new | Add more differentiated directions to `program.md` |
| Vague or generic critique | Chairman struggled to differentiate the versions | Consider tightening evaluation criteria |

---

## Terminal Output

The terminal is the ground truth for the experiment loop. The dashboard derives from it.

### Iteration Header

```
[run] ===== Iteration 12 | best_score=87 | spent=$0.21 =====
```

| Field | Watch for |
|-------|-----------|
| `best_score` | Should climb over a long run |
| `spent` | Track against your `COST_LIMIT_USD` |

### KEEP / DISCARD Lines

```
[run] KEEP — score 89 (+2 improvement)
[run] DISCARD — score 84 vs best 87 (no improvement)
[run] DISCARD — score 87 vs best 87 (winner=E (current artifact is best))
```

The second DISCARD variant — `winner=E` — means the chairman judged the current artifact as the best version. This is a stronger signal than a close numerical loss.

### Warning Signals

```
[run] PLATEAU: last 10 iterations all DISCARD. Consider editing program.md...
```
**Act immediately.** Open `program.md` and add 3–4 new Exploration Directions. Restart the loop.

```
[run] 3 consecutive failures — sleeping 60s before retry
```
API issues. Usually self-resolves. If it persists, check your OpenRouter credits and model availability.

```
[run] COST LIMIT REACHED: $5.0023 spent (limit $5.00). Stopping.
```
Normal termination. Raise `COST_LIMIT_USD` in `.env` to continue.

```
[openrouter] Error querying openai/gpt-5.4-nano: ...
```
One model failed. The iteration continues with the remaining models. If a model fails consistently, replace it in `config.py`.

---

## Patterns and What They Mean

### Healthy run
```
Iter 1:  KEEP  score=82   ← first iteration almost always KEEP (beats score=0)
Iter 2:  DISCARD score=79
Iter 3:  DISCARD score=80
Iter 4:  KEEP  score=87   ← genuine improvement
Iter 5:  DISCARD score=85
Iter 6:  DISCARD score=86
Iter 7:  DISCARD score=84
Iter 8:  KEEP  score=90
```
Score climbing, reasonable KEEP:DISCARD ratio (~1:3). Normal.

### Plateau
```
Iter 10: DISCARD score=84 vs best 87
Iter 11: DISCARD score=85 vs best 87
Iter 12: DISCARD score=83 vs best 87
...
Iter 19: DISCARD score=86 vs best 87
[run] PLATEAU: last 10 iterations all DISCARD.
```
Score is converging around 87 but can't break through. Edit `program.md`.

### API instability
```
Iter 5: CRASH — evaluate.py exit code 1
Iter 6: CRASH — evaluate.py exit code 1
Iter 7: CRASH — evaluate.py exit code 1
[run] 3 consecutive failures — sleeping 60s before retry
```
Check OpenRouter status page and your account credits.

### Early ceiling
```
Iter 1: KEEP score=91
Iter 2: DISCARD score=88
Iter 3: DISCARD score=89
Iter 4: DISCARD score=90
```
High score on iteration 1 means the initial `artifact.md` was already quite good, or the scoring is lenient. The council will struggle to beat 91. Start with a weaker artifact for a longer improvement arc.

---

## Post-Run Log Inspection

Two files persist after a run for offline analysis:

### `run.log`

A copy of everything printed to the terminal during the last `bash start.sh` session. Created by `tee` — overwritten each time you restart.

```bash
cat run.log | grep "KEEP\|DISCARD"      # KEEP/DISCARD summary
cat run.log | grep "council_score"      # All scores
cat run.log | grep "Error querying"     # API failures
```

### `events.jsonl`

Append-only across all runs. Contains every stage event from `evaluate.py` plus `run_start` and `iteration_result` markers from `run.py`. Use `jq` to query:

```bash
# All iteration results across all runs
jq 'select(.type == "iteration_result")' events.jsonl

# All KEEP iterations with scores
jq 'select(.type == "iteration_result" and .status == "KEEP") | {iteration, council_score, commit}' events.jsonl

# Runs by tag
jq 'select(.type == "run_start") | {run_tag, timestamp, cost_limit_usd}' events.jsonl

# Stage 3 critiques
jq 'select(.type == "stage3_complete") | .critique' events.jsonl
```

`events.jsonl` is the machine-readable complement to `results.tsv`. It has more fields (spent_usd, best_score) and includes stage-level events that `results.tsv` does not.

---

## Quick Reference: When to Act

| Signal | Where to see it | Action |
|--------|----------------|--------|
| 10+ consecutive DISCARDs | Terminal / sidebar ratio | Edit `program.md` Exploration Directions |
| Critique repeating same feedback | Stage 3 critique | Add that direction explicitly to `program.md` |
| Version E winning Stage 2 repeatedly | Stage 2 bar chart | Try radically different approaches in `program.md` |
| Score stuck below 60 after 20 iterations | Score chart / sidebar | Rewrite `artifact.md` with a stronger starting draft |
| Score above 90 with no KEEPs | Score chart | Expected — you're near the ceiling for this topic |
| Word count approaching 3000 | Sidebar | Add word limit constraint to `program.md` |
| One model always missing from proposals | Stage 1 tab | Check terminal for API errors; replace model in `config.py` |
| Spend approaching cost limit | Terminal | Raise `COST_LIMIT_USD` in `.env` if you want to continue |
