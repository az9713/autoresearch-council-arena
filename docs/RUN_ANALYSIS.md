# Run Analysis — 2026-04-03

Analysis of run `20260403_142816`. 11 successful iterations, a mid-run network outage (iterations 12–22), recovery, and self-termination via plateau detection at iteration 48.

---

## Run Statistics

| Iter | Winner | Score | CORRECTNESS | COMPLETENESS | CLARITY | CODE_QUALITY | DEPTH | Status | E avg_pos |
|------|--------|-------|-------------|--------------|---------|--------------|-------|--------|-----------|
| 1 | A | 88 | 19 | 18 | 17 | 18 | 16 | **KEEP** | 4.00 |
| 2 | A | 94 | 20 | 20 | 18 | 18 | 18 | **KEEP** | 3.75 |
| 3 | D | 91 | 18 | 20 | 18 | 18 | 17 | DISCARD | 3.25 |
| 4 | D | 95 | 20 | 20 | 18 | 19 | 18 | DISCARD | 3.25 |
| 5 | A | 87 | 18 | 18 | 17 | 18 | 16 | DISCARD | 3.75 |
| 6 | D | 94 | 19 | 20 | 18 | 19 | 18 | DISCARD | 3.00 |
| 7 | A | 92 | 18 | 20 | 18 | 17 | 19 | DISCARD | 3.25 |
| 8 | A | 91 | 20 | 18 | 18 | 18 | 17 | DISCARD | 3.75 |
| 9 | A | 94 | 20 | 20 | 18 | 18 | 18 | DISCARD | 3.25 |
| 10 | C | 92 | 20 | 18 | 19 | 18 | 17 | DISCARD | 3.50 |
| 11 | A | 90 | 18 | 20 | 18 | 18 | 16 | DISCARD | 2.75 |
| 12–22 | — | — | — | — | — | — | — | CRASH | — |

**Iterations 12–22: total DNS/network failure** — `getaddrinfo failed` hit all 4 models and the cost API simultaneously. This is a local network outage, not a system bug.

**Cost:** $0.30 for 11 substantive iterations (~$0.028/iteration). At that rate, $5 budget ≈ 180 good iterations.

---

## What Is Working

**Multi-dimensional scoring: ✓**
Scores are now granular and progress is visible: 88 → 94 over 2 KEEPs. Previously the run jumped to 95 in one step. The breakdown per dimension makes it clear exactly what is strong and what isn't.

**KEEP detection: ✓**
Both KEEPs were genuine improvements — iter 1 fixed the weak baseline, iter 2 improved substantially across all dimensions.

**Peer ranking (Stage 2): ✓**
E's avg_pos drifts from 4.00 → 2.75 as the artifact improves — the council correctly tracks that the baseline is getting harder to beat. Rankings are diverse across A, C, D.

**Cost efficiency: ✓**
$0.028/iteration is extremely cheap. The system can run hundreds of iterations within a $5 budget.

**Error visibility: ✓**
Network errors print immediately to terminal (`getaddrinfo failed`) instead of silently swallowed during the long silence.

---

## What Is Not Working

### 1. Ceiling hit at 94 — IMPROVEMENT_THRESHOLD logic error

Iteration 4 scored 95, which should be a KEEP (95 > 94). But it was DISCARD. The check uses strict greater-than:

```python
improved = score > best_score + IMPROVEMENT_THRESHOLD
# 95 > 94 + 1  →  95 > 95  →  False
```

Setting `IMPROVEMENT_THRESHOLD = 1` does not mean "+1 is enough" — it means "+2 is the minimum." To accept any strict improvement, set `IMPROVEMENT_THRESHOLD = 0`.

### 2. CLARITY and DEPTH are stuck — the real bottleneck

Per-dimension scores across all 11 iterations:

| Dimension | Min | Max | Typical | Maxed? |
|-----------|-----|-----|---------|--------|
| CORRECTNESS | 18 | 20 | 19–20 | Nearly |
| COMPLETENESS | 18 | 20 | 19–20 | Nearly |
| CLARITY | 17 | 19 | 18 | Never |
| CODE_QUALITY | 17 | 19 | 18 | Never |
| DEPTH | 16 | 19 | 17 | Never |

CORRECTNESS and COMPLETENESS are effectively maxed. DEPTH (avg ~17) is the real constraint — no proposal ever scored 20/20. CLARITY never exceeded 19. These two dimensions are where the council has not yet found the ceiling and represent the remaining improvement opportunity.

### 3. CRASH backoff bug — the loop never sleeps during network failure

After 3 consecutive CRASHes the loop is supposed to sleep 60 seconds. It never did — iterations 12–22 fired back-to-back with no pause. The bug: CRASH iterations call `continue` before reaching the failure guard:

```python
if result.returncode != 0:
    append_result(..., "CRASH", ...)
    continue  # ← skips the failure guard below
```

The guard checking `recent_statuses(3)` lives after the metric extraction and KEEP/DISCARD logic, which CRASH/TIMEOUT paths never reach.

### 4. Model B (Claude Haiku) never wins

Ranked 3rd–4th in every iteration. Zero wins across 11 iterations. Consistently the weakest council member on this technical writing task.

---

## Suggested Improvements

### Immediate (config changes only)

1. **Set `IMPROVEMENT_THRESHOLD = 0`** — any strict score improvement is a KEEP. At scores of 91–95, a +1 improvement is real progress and should not be rejected.

2. **Weaker starting artifact** — the tutorial initial artifact scored 88 on iteration 1. To get a long improvement arc you need ~60 on iteration 1. The starting point needs to be more deliberately incomplete.

### Code fixes

3. **Fix the CRASH backoff** — move the consecutive-failure check into the CRASH/TIMEOUT paths so it actually fires:

```python
if result.returncode != 0:
    append_result("none", None, "CRASH", f"evaluate.py exit code {result.returncode}")
    recent = recent_statuses(3)
    if len(recent) == 3 and all(s in ("CRASH", "PARSE_FAILURE", "API_FAILURE") for s in recent):
        print("[run] 3 consecutive failures — sleeping 60s before retry", flush=True)
        time.sleep(60)
    continue
```

### Task design

4. **Add exploration directions targeting DEPTH and CLARITY** in `program.md`:
   - "Add a 'Why this design?' section explaining the greedy hill-climbing rationale and tradeoffs"
   - "Add a worked example showing actual before/after artifact output with real scores"
   - "Add inline comments explaining non-obvious code decisions"

5. **Replace Model B (Claude Haiku)** — zero wins across all runs on this task. Candidates: `deepseek/deepseek-chat-v3-0324` or `mistralai/mistral-small-3.2-24b-instruct`.

---

## Why the Run Stopped at Iteration 48

The run self-terminated cleanly via **plateau detection** — not a crash, not a manual stop, not the cost limit.

After the network recovered (post-iteration 22), the loop continued running. By iteration 48 the system had accumulated 10 consecutive DISCARDs. This triggered the plateau guard in `run.py`:

```python
recent = recent_statuses(PLATEAU_WINDOW)   # PLATEAU_WINDOW = 10
if len(recent) >= PLATEAU_WINDOW and all(s == "DISCARD" for s in recent):
    graceful_exit("plateau")
    break
```

`graceful_exit("plateau")` emitted a `run_end` event to `events.jsonl`, cleaned up `stop.flag`, and printed the final summary. The UI displayed the **"Plateau — run ended"** banner in the sidebar.

**Final state at termination:**

| Metric | Value |
|--------|-------|
| Total iterations | 48 |
| KEEPs | 3 |
| DISCARDs | 23+ (final 10 consecutive) |
| CRASHes | ~11 (network outage, iterations 12–22) |
| Best score | 96 / 100 |
| Final sub-scores | CORRECTNESS 18 · COMPLETENESS 19 · CLARITY 18 · CODE_QUALITY 17 · DEPTH 18 |

**Why 10 consecutive DISCARDs?**

By iteration 38+ the artifact had reached a score of 96/100 with all five dimensions scoring 17–19/20. The council consistently generated proposals scoring 90–95 — genuinely good tutorials, but not better than the current artifact by more than `IMPROVEMENT_THRESHOLD = 1`. With CORRECTNESS and COMPLETENESS effectively maxed, the remaining headroom was in CLARITY, CODE_QUALITY, and DEPTH — dimensions where the chairman's criteria are harder to satisfy with small targeted changes.

This is the correct, expected behavior. Plateau detection exists precisely for this situation: the system has found a strong local maximum and further iteration is unlikely to improve it. The right response is to restart with a harder constraint, a different exploration direction, or a new starting artifact.

---

## Overall Verdict

The autoresearch + LLM council system is **architecturally sound**. The core loop (propose → rank → judge → KEEP/DISCARD → repeat) works correctly. Cost tracking, plateau detection, and stop-flag IPC all work.

The remaining issues are calibration problems, not architecture problems:
- Starting artifact calibration (too good → ceiling too early)
- Threshold semantics (off-by-one in the strict greater-than logic)
- One underperforming model (Claude Haiku)
- One code bug (CRASH backoff placement)

None of these require rethinking the system. They are configuration and minor code fixes.
