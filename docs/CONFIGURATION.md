# Configuration Reference

All runtime configuration is in `config.py`. All secrets are in `.env`.

---

## `.env`

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys). The key needs credits loaded for the models specified in `COUNCIL_MODELS` and `CHAIRMAN_MODEL`.

The `.env` file is gitignored. Never commit it.

---

## `config.py` — Full Reference

### API Settings

```python
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_TIMEOUT = 120  # seconds per model call
```

**`API_TIMEOUT`** — per-call timeout in seconds. If a single model call hangs longer than this, it returns `None` and is excluded from that stage. The 5-minute wall-clock budget (`EXPERIMENT_TIMEOUT`) applies to the entire `evaluate.py` subprocess.

### Council Models

```python
COUNCIL_MODELS = [
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-flash-preview",
    "meta-llama/llama-4-maverick",
]
CHAIRMAN_MODEL = "anthropic/claude-sonnet-4"
```

**`COUNCIL_MODELS`** — the four models used in Stage 1 (propose) and Stage 2 (rank). Letters A/B/C/D are assigned in list order. To swap a model, replace its ID — no other code changes are needed.

Model IDs must be valid [OpenRouter model slugs](https://openrouter.ai/models). Check OpenRouter for exact IDs; they sometimes differ from official model names.

**`CHAIRMAN_MODEL`** — the Stage 3 judge. Does not need to match any council model. Default is Claude Sonnet 4 for its strong editorial judgment and consistent scoring.

**Minimum viable council size:** At least 2 models must return valid proposals in Stage 1 and valid rankings in Stage 2. If fewer than 2 rankings are parseable, `evaluate.py` exits with code 1 and `run.py` logs a CRASH.

### Experiment Loop

```python
IMPROVEMENT_THRESHOLD = 2
EXPERIMENT_TIMEOUT = 300
MAX_ARTIFACT_WORDS = 3000
PLATEAU_WINDOW = 10
```

**`IMPROVEMENT_THRESHOLD`** — minimum score delta to accept a new version. Prevents noise-driven commits where the score fluctuates by 1-2 points. Increase for stricter hill-climbing; set to 0 to accept any improvement.

**`EXPERIMENT_TIMEOUT`** — wall-clock seconds before `run.py` kills the `evaluate.py` subprocess. 300s (5 minutes) matches karpathy/autoresearch. Increase if models are consistently timing out.

**`MAX_ARTIFACT_WORDS`** — if the winning proposal exceeds this word count, Stage 3 falls back to E (current artifact). Prevents the system from producing unmanageably long outputs. Default 3000 is generous; adjust to match your `program.md` word limit.

**`PLATEAU_WINDOW`** — number of consecutive DISCARDs before printing a plateau warning. This is informational only — the loop does not stop or change behavior. When a plateau is detected, consider editing `program.md` to introduce new exploration directions.

### Cost Limit

```python
COST_LIMIT_USD: float | None = 5.00
```

**`COST_LIMIT_USD`** — stops the experiment loop after spending this many USD. Checked before each iteration using real billing data from `https://openrouter.ai/api/v1/auth/key`.

Set to `None` to run indefinitely (manual Ctrl+C only). Set to a smaller value (e.g., `1.00`) to test the system cheaply before a long run.

**How it works:**
1. At startup, `run.py` queries the initial credit balance.
2. Before each iteration, it queries the current balance.
3. If `initial - current >= COST_LIMIT_USD`, the loop exits cleanly.
4. If the balance API is unavailable, the limit is silently skipped for that iteration.

---

## `program.md` — Human Control Point

`program.md` is not part of `config.py`, but it is the primary way to steer the system during a run.

```markdown
# Arena: Persuasive Writing Optimization

## Topic
What the artifact should argue or demonstrate.

## Target Audience
Who this is written for and what their priors are.

## Evaluation Criteria
1. Criterion one
2. Criterion two
...

## Constraints
- Word limit
- Prohibited content

## Exploration Directions
Specific strategies for council models to try.

## NEVER STOP
(Required directive — do not remove)
```

**Edit `program.md` between iterations** to change direction when the system plateaus. The next iteration will use the updated objectives.

Do not remove the `## NEVER STOP` section — it is part of the Stage 1 system prompt contract and models may interpret its absence as permission to stop.

**`Exploration Directions`** is the most useful lever. When the system converges on a local maximum, add new strategic directions here. Example additions:

```markdown
- Try a completely different opening: start with a failure case, not a success
- Use a numbered argument structure instead of prose paragraphs
- Cut the argument to 500 words — force maximum density
```

---

## Frontend Configuration

### Vite Proxy

The frontend proxies all `/api/*` requests to the backend. Configured in `frontend/vite.config.js`:

```js
server: {
  proxy: {
    '/api': 'http://localhost:8001'
  }
}
```

If you change the backend port (default 8001), update this config.

### CORS

The backend's CORS allowlist in `backend/server.py`:

```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
```

If Vite assigns a different port (it increments from 5173 if the port is in use), add the new port here and restart the backend.

---

## Environment Variables Summary

| Variable | Source | Required | Description |
|----------|--------|----------|-------------|
| `OPENROUTER_API_KEY` | `.env` | Yes | OpenRouter API key |

All other settings are in `config.py` (Python constants, not environment variables).
