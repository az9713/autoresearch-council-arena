# Quick Start

Get from zero to a running experiment in 10 minutes.

---

## Step 1 — Install Prerequisites

You need three tools. Check if you already have them:

```bash
uv --version       # need 0.4+
node --version     # need 18+
gh --version       # optional, only needed to push to GitHub
```

**Install `uv`** (Python package manager):
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install Node.js:** download from https://nodejs.org/ (LTS version).

---

## Step 2 — Get an OpenRouter API Key

1. Go to https://openrouter.ai and sign up
2. Go to **Keys** → **Create Key**
3. Add credits — $5 is plenty for a first run (the default cost limit)

---

## Step 3 — Clone and Configure

```bash
git clone https://github.com/az9713/autoresearch-council-arena
cd autoresearch-council-arena

cp .env.example .env
```

Open `.env` in any text editor and set your key:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

---

## Step 4 — Run

```bash
bash start.sh
```

You should see:

```
[start] Installing Python dependencies...
[start] Installing frontend dependencies...
[start] Starting backend on http://localhost:8001 ...
[start] Starting frontend on http://localhost:5173 ...
[start] Starting experiment loop (Ctrl+C to stop)...
[run] Starting autoresearch-council-arena run: 20260402_170824
[run] Branch: autoresearch/20260402_170824
[run] Starting credit balance: $5.0000

[run] ===== Iteration 1 | best_score=0 | spent=$0.0000 =====
[evaluate] Stage 1: generating proposals...
```

Open **http://localhost:5173** in your browser. The dashboard will auto-update as each stage completes.

---

## Step 5 — Watch Your First Iteration

The dashboard auto-switches tabs as each stage finishes:

1. **Stage 1 · Proposals** — four proposals appear (A/B/C/D), one per model
2. **Stage 2 · Rankings** — the bar chart shows which version peers ranked highest
3. **Stage 3 · Verdict** — the chairman picks a winner and assigns a score

Back in the terminal:

```
[run] KEEP — score 82 (+82 improvement)
```

That's it — the first improved version is committed to git. Check the **Artifact** tab to see the new version.

---

## Quick Wins

### Win 1: See a KEEP in under 5 minutes

The first iteration almost always produces a KEEP because `best_score` starts at 0. Any score > 2 wins. Watch the score dial in the Stage 3 tab spin up and the terminal print `KEEP`.

### Win 2: Watch the score chart grow

After 3–5 iterations, switch to the **Artifact** tab and click **Show previous version** to see what changed. The score chart in the sidebar plots every iteration — green dots are KEEPs.

### Win 3: Read the critique

The chairman writes a 3–5 sentence critique after every iteration. Find it in the Stage 3 tab under the score dial. This is the feedback the next iteration's proposers will use.

### Win 4: Check the git log

```bash
git log --oneline
```

Every KEEP is a commit. The branch tip is always the current best.

```
da864d6  Iter 4: score=87 winner=B
1a37103  Iter 1: score=82 winner=B
f346ae2  Initial commit: autoresearch-council-arena
```

### Win 5: Change the topic

Stop the loop (Ctrl+C), edit `program.md`, restart:

```bash
# Edit program.md — change Topic, Audience, or add Exploration Directions
bash start.sh
```

The next iteration will use your new objectives.

---

## Stopping

**Ctrl+C** in the terminal stops everything (experiment loop + backend + frontend).

The experiment state is preserved: `artifact.md` holds the best version, `results.tsv` has the full log, and git has every KEEP committed. Re-run `bash start.sh` to continue from where you left off.

---

## Cost Check

The terminal prints your running spend every iteration:

```
[run] ===== Iteration 5 | best_score=87 | spent=$0.0823 =====
```

The default limit is **$5.00** (~260 iterations). Change it in `.env`:

```bash
COST_LIMIT_USD=1.00    # stop after $1 — good for testing
# remove the line entirely to run until Ctrl+C
```

---

## Something Went Wrong?

| Symptom | Fix |
|---------|-----|
| `ERROR: .env not found` | Run `cp .env.example .env` and add your API key |
| `ERROR: 'uv' not found` | Install uv — see Step 1 |
| Port 5173 already in use | Frontend moves to 5174 automatically — check terminal output for the actual URL |
| `council_score` never appears | Run `uv run python evaluate.py` directly to see the full error |
| Score stuck, all DISCARDs | Edit `program.md` → add new Exploration Directions → restart |

For more, see [docs/CONTRIBUTING.md](CONTRIBUTING.md#debugging).
