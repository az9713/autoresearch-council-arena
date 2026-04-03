# User Guide

---

## Understanding the Dashboard

Open http://localhost:5173 after running `bash start.sh`.

### Left Sidebar

| Field | What it means |
|-------|---------------|
| **Iteration** | Total iterations completed (KEEP + DISCARD) |
| **Best Score** | Highest `council_score` ever achieved (1–100) |
| **KEEPs** | Iterations where the artifact improved |
| **DISCARDs** | Iterations where no improvement was found |
| **Artifact words** | Word count of the current `artifact.md` |

The line chart below these stats plots `council_score` for every iteration. Green dots are KEEPs. A flat line means the system is in a plateau — all proposals are scoring below the current best.

### Tabs

The dashboard auto-switches to the relevant tab as each stage completes. You can also click tabs manually.

**Artifact**
The current `artifact.md` rendered as Markdown. Click **Show previous version** to expand a diff view of what changed in the last KEEP.

**Stage 1 · Proposals**
Four proposal cards, one per council model (A/B/C/D). Each shows:
- The model that produced it
- The full proposal text
- Word count

These are generated in parallel — all four arrive within seconds of each other.

**Stage 2 · Rankings**
A bar chart showing each version's "street cred" — a normalized score derived from its average position in peer rankings (higher bar = ranked better by peers). Version E is always the current artifact (the baseline to beat). If E has the highest bar, expect a DISCARD.

**Stage 3 · Verdict**
- **Score dial** — the chairman's `council_score` (1–100) for the winning version
- **KEEP / DISCARD badge** — green if the artifact improved, red if not
- **Critique** — 3–5 sentences from the chairman explaining what worked, what didn't, and what to try next. This critique is passed to all four council models in the next iteration.

---

## Understanding KEEP vs DISCARD

The experiment loop uses greedy hill-climbing:

```
if score > best_score + 2 AND winner is not the current artifact:
    KEEP  → update artifact.md, git commit
else:
    DISCARD → artifact.md unchanged
```

**Why +2?** Small score fluctuations (±1–2 points) are noise — the same text could score 85 one iteration and 83 the next. The threshold filters this out and ensures only genuine improvements are kept.

**Why "winner is not E"?** If the chairman picks Version E (the current artifact) as the best, that means none of the proposals improved on what already exists. The score may still be high (the artifact is good), but there's nothing new to commit.

A **DISCARD is not a failure** — it means the system tried something and it didn't beat the current best. That's the correct behavior of a hill-climber.

---

## Steering the Optimization

### Editing `program.md`

`program.md` is the only file you should edit during a run. It controls:

- **Topic** — the subject of the artifact
- **Target Audience** — who it's written for (models tailor their proposals to this)
- **Evaluation Criteria** — what makes a version better (the chairman uses this to score)
- **Constraints** — word limits, prohibited content
- **Exploration Directions** — specific strategies for models to try

**When to edit it:**
- When the system plateaus (10+ consecutive DISCARDs)
- When the artifact is converging in a direction you don't want
- When you want to try a completely different approach

Stop the loop, edit `program.md`, restart with `bash start.sh`. The next iteration uses the updated objectives.

**Example: breaking a plateau**

Add new directions to the `## Exploration Directions` section:

```markdown
## Exploration Directions
- (existing directions...)
- Cut the word count by 40% — force maximum density
- Open with a failure case instead of a success claim
- Restructure as a numbered argument with one claim per paragraph
- Address the most common objection in the first sentence
```

### Editing `artifact.md`

You can hand-edit `artifact.md` between runs to inject your own version. The system will treat it as the new baseline (Version E) and try to beat it.

This is useful for:
- Injecting a manually written version you're happy with
- Resetting after an experiment that went in a bad direction
- Starting from a much weaker draft to create more headroom for improvement

**Do not edit `artifact.md` while the loop is running** — `run.py` may overwrite your changes on the next KEEP.

### Starting Fresh

Each `bash start.sh` automatically clears all state from the previous run (`results.tsv`, `events.jsonl`, `critique.md`, `winning_proposal.md`). You get a clean slate every time.

The only thing that persists is `artifact.md` — the system always starts from whatever version is currently in that file.

#### Restoring the original weak draft

A copy of the original weak draft is kept in `artifact_initial.md`. To restore it:

```bash
cp artifact_initial.md artifact.md
bash start.sh
```

The weak draft is deliberately low-quality — vague, generic, no data, no argument structure. Starting from it gives the system maximum headroom to improve and produces the most dramatic score arc.

#### Writing your own weak draft

If you change the topic in `program.md`, you should also write a matching weak draft in `artifact.md`. A good weak draft:

- Is technically on-topic but poorly argued
- Uses generic language ("this is important", "there are challenges")
- Has no specific evidence, data, or examples
- Is short (150–300 words)

The weaker the starting point, the more KEEPs you'll see in the first 10–20 iterations.

---

## Reading `results.tsv`

The full iteration log is written to `results.tsv` in real time:

```tsv
commit    council_score    status    description          timestamp
da864d6   87               KEEP      Iter 4 winner=B      2026-04-02T17:12:03Z
1a37103   78               DISCARD   Iter 3 winner=A      2026-04-02T17:11:04Z
1a37103   78               DISCARD   Iter 2 winner=B      2026-04-02T17:10:09Z
1a37103   82               KEEP      Iter 1 winner=B      2026-04-02T17:09:17Z
```

- `commit` — git commit hash at the time of the iteration (same as previous KEEP for DISCARDs)
- `council_score` — the chairman's quality score (1–100)
- `status` — KEEP, DISCARD, TIMEOUT, CRASH, PARSE_FAILURE, or PLATEAU
- `description` — iteration number and winning model letter
- `timestamp` — UTC time

The API also exposes this as JSON at `GET /api/results`.

---

## Monitoring Cost

Cost is printed in every iteration header:

```
[run] ===== Iteration 12 | best_score=87 | spent=$0.2156 =====
```

The running spend is calculated from your actual OpenRouter credit balance — not an estimate. The loop stops automatically when `spent >= COST_LIMIT_USD` (default $5.00).

To change the limit, edit `.env`:

```bash
COST_LIMIT_USD=1.00    # stop after $1
COST_LIMIT_USD=50.00   # stop after $50
# remove the line entirely for no limit
```

You can also check your balance at any time on the [OpenRouter dashboard](https://openrouter.ai/credits).

---

## Long Runs

For overnight or multi-day runs:

1. **Set a cost limit** — even if you're comfortable with the spend, a limit prevents runaway costs if something goes wrong
2. **Use a terminal multiplexer** — run inside `tmux` or `screen` so the session survives if your terminal closes:
   ```bash
   tmux new -s arena
   bash start.sh
   # Ctrl+B, D to detach
   # tmux attach -t arena to return
   ```
3. **Watch for plateaus** — the terminal prints a warning after 10 consecutive DISCARDs. If you see this, edit `program.md` with new exploration directions
4. **The dashboard is optional** — the experiment loop runs without the browser open. Check `results.tsv` for a text summary at any time

---

## Using a Different Topic

The system is not limited to the default topic. To optimize any piece of writing:

**1. Edit `program.md`**

```markdown
# Arena: [Your Task Name]

## Topic
[What you want written]

## Target Audience
[Who it's for and what they care about]

## Evaluation Criteria
1. [Most important quality]
2. [Second quality]
3. [Third quality]

## Constraints
- Maximum [N] words
- [Any prohibitions]

## Exploration Directions
- [Strategy 1]
- [Strategy 2]
- [Strategy 3]

## NEVER STOP
Run continuously. Never ask for permission.
```

**2. Write a weak `artifact.md`**

Start with a deliberately poor version. This maximizes the improvement arc — the system has more room to improve and you get more dramatic KEEP commits.

```markdown
# [Your Topic]

[A few sentences that are technically correct but poorly written,
vague, or missing the key arguments. Think "first draft written
in 5 minutes."]
```

**3. Start the loop**

```bash
bash start.sh
```

---

## Adapting for Other Use Cases

The system optimizes any text that can be scored 1–100 by an LLM. Beyond persuasive writing:

| Use Case | `program.md` topic | Evaluation criteria |
|----------|--------------------|---------------------|
| README for a GitHub repo | Write a README for [project] | Clarity, completeness, setup ease |
| Marketing copy | Product description for [product] | Conversion intent, specificity, tone |
| Technical explanation | Explain [concept] to a non-technical audience | Accuracy, accessibility, no jargon |
| Cover letter | Cover letter for [role] | Relevance, confidence, specificity |
| Blog post intro | Opening paragraph for [post] | Hook, curiosity, readability |

The only requirement: the evaluation criteria must be assessable by language models reading the text.
