# Contributing

## Development Setup

```bash
git clone https://github.com/az9713/autoresearch-council-arena
cd autoresearch-council-arena

# Python environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Python dependencies
uv pip install httpx python-dotenv fastapi uvicorn

# Frontend dependencies
cd frontend && npm install && cd ..

# Environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

## Project Conventions

### File Roles

| File | Mutability | Notes |
|------|-----------|-------|
| `evaluate.py` | **FROZEN** | Never modify after a run starts. Scores must be stable. |
| `run.py` | Editable | Loop logic, git integration, cost tracking |
| `openrouter.py` | Editable | API client |
| `config.py` | Editable | All tunable parameters |
| `program.md` | Editable (human) | Steer the optimization topic and criteria |
| `artifact.md` | Auto-updated | Written by `run.py` on KEEP; do not hand-edit during a run |

### Coding Style

- Python: no type-checker enforcement, but add type annotations to public functions
- Docstrings: first line is a one-liner; use multi-line for non-obvious logic
- No `print()` outside of debug context — use `print(..., flush=True)` in subprocess code so output is not buffered
- React: functional components only, no class components, no external state management

### Metric Extraction Pattern

`run.py` extracts metrics from `evaluate.py` stdout using the autoresearch grep pattern:

```python
for line in log_text.splitlines():
    if line.startswith("council_score:"):
        return line.split(":", 1)[1].strip()
```

If you add new metrics, print them to stdout in the same format: `metric_name: value`. Do not print this format for anything that is not a metric (it will be silently ignored if the key doesn't match, but it's confusing).

### Events

`evaluate.py` emits events by appending to `events.jsonl`:

```python
def _emit_event(event: dict) -> None:
    with EVENT_FILE.open("a") as f:
        f.write(json.dumps(event) + "\n")
```

Event types are consumed by `backend/server.py` and forwarded to the frontend. If you add a new event type, update `App.jsx` to handle it.

## Running Components Individually

### Backend only

```bash
uv run python -m uvicorn backend.server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend only

```bash
cd frontend && npm run dev
```

### Single evaluation (one iteration, no loop)

```bash
uv run python evaluate.py
```

This runs one full Stage 1 → 2 → 3 pipeline and writes `winning_proposal.md` and `critique.md`. Useful for testing model responses without the full loop.

### Experiment loop only (no dashboard)

```bash
uv run python run.py
```

## Changing Models

Edit `COUNCIL_MODELS` in `config.py`. Requirements:

1. All models must be available on [OpenRouter](https://openrouter.ai/models)
2. At least 2 models must return valid responses in Stage 1 and Stage 2
3. The model ID must be the exact OpenRouter slug (e.g., `openai/gpt-5.4-nano`, not `gpt-5.4-nano`)

To test a new model without changing the full council, temporarily replace one entry and run a single iteration:

```bash
uv run python evaluate.py
```

## Adding a New Optimization Topic

1. Create a new `program.md` with your topic, audience, criteria, and constraints
2. Write a weak initial `artifact.md` (intentionally low quality — maximum improvement arc)
3. Run `bash start.sh`

The system will optimize `artifact.md` according to the criteria in `program.md`.

## Debugging

### `evaluate.py` crashes silently

Run it directly to see the full traceback:

```bash
uv run python evaluate.py
```

### Rankings are always parsing to None

Check that the model returns `FINAL RANKING: X > Y > Z` exactly. Some models wrap it in markdown code blocks. The regex is:

```python
re.search(r"FINAL RANKING:\s*([A-E][A-E >]*[A-E])", text)
```

### Frontend shows stale data

The SSE stream starts tailing `events.jsonl` from the current file position (end of file at connection time). If the frontend loads after an iteration completes, it won't see that iteration's events — only future ones. The 5-second polling keeps `status`, `results`, and `artifact` up to date regardless.

### CORS errors in the browser

The backend allows `localhost:5173` and `127.0.0.1:5173` only. If Vite runs on a different port (it increments from 5173 if the port is in use), add the port to `allow_origins` in `backend/server.py` and restart the backend.

## Known Limitations

- **No authentication.** The backend is local-only and has no auth. Do not expose port 8001 publicly.
- **`events.jsonl` is never rotated.** Long runs accumulate all events in one file. The SSE server reads from the current position, so it stays fast, but the file will grow indefinitely.
- **Stage 2 proposals are truncated to 500 chars in events.** The full text is only available in `winning_proposal.md` (winner only) or by re-running `evaluate.py`.
- **Single run per directory.** Running two experiment loops in the same directory simultaneously will corrupt `events.jsonl` and `results.tsv`. Use separate directories for parallel experiments.
