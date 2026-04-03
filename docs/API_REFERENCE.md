# API Reference

The FastAPI backend runs on **http://localhost:8001**. Interactive documentation (Swagger UI) is available at http://localhost:8001/docs and OpenAPI JSON at http://localhost:8001/openapi.json.

---

## Endpoints

### `GET /api/status`

Returns the current run state.

**Response**

```jsonc
{
  "iteration": 12,          // total iterations completed
  "best_score": 87,         // highest council_score achieved
  "artifact_words": 842,    // word count of current artifact.md
  "running": true           // true if events.jsonl exists
}
```

**Notes**
- `running` is a proxy: it checks whether `events.jsonl` exists. It does not verify that `run.py` is actively executing.
- `best_score` is computed from `results.tsv` (KEEP rows only). Returns 0 if no iterations have been kept.

---

### `GET /api/results`

Returns the full iteration log.

**Response** — array of iteration objects

```jsonc
[
  {
    "commit": "da864d6",
    "council_score": "87",
    "status": "KEEP",
    "description": "Iter 4 winner=B",
    "timestamp": "2026-04-02T17:12:03Z"
  },
  {
    "commit": "da864d6",
    "council_score": "78",
    "status": "DISCARD",
    "description": "Iter 2 winner=A",
    "timestamp": "2026-04-02T17:06:41Z"
  }
]
```

**Status values**

| Value | Meaning |
|-------|---------|
| `KEEP` | Score improved; `artifact.md` was updated and committed |
| `DISCARD` | No improvement; `artifact.md` unchanged |
| `TIMEOUT` | `evaluate.py` exceeded the 5-minute wall-clock budget |
| `CRASH` | `evaluate.py` exited with a non-zero exit code |
| `PARSE_FAILURE` | Could not extract `council_score` or `winner` from stdout |
| `PLATEAU` | Informational: last N iterations were all DISCARD |

**Notes**
- All fields are strings (parsed directly from the TSV). `council_score` should be cast to `int` before arithmetic.
- DISCARD rows share the same `commit` hash as the preceding KEEP (branch tip was unchanged).

---

### `GET /api/artifact`

Returns the current `artifact.md` content.

**Response**

```jsonc
{
  "content": "# Recursive Self-Intelligence\n\n..."
}
```

**Notes**
- Returns empty string if `artifact.md` does not exist.
- Content is raw Markdown. The frontend renders it with `react-markdown`.

---

### `GET /api/history`

Returns the last 20 git commits on the current branch.

**Response** — array of commit objects

```jsonc
[
  {"commit": "da864d6", "message": "Iter 4: score=87 winner=B"},
  {"commit": "1a37103", "message": "Iter 1: score=82 winner=B"},
  {"commit": "f346ae2", "message": "Initial commit: autoresearch-council-arena"}
]
```

**Notes**
- Returns empty array if git is unavailable or the repository has no commits.
- Only KEEP iterations produce commits. The number of entries equals the number of KEEPs + 1 (initial commit).

---

### `GET /api/stream`

Server-Sent Events stream. Pushes new events from `events.jsonl` as they are appended by `evaluate.py`, plus a periodic heartbeat.

**Response** — `text/event-stream`

The connection remains open indefinitely. Each event is a `data: {...}\n\n` frame.

#### Event Types

**`connected`** — sent immediately on connection

```json
{"type": "connected"}
```

**`stage1_complete`** — Stage 1 proposals generated

```jsonc
{
  "type": "stage1_complete",
  "proposals": {
    "A": "first 500 characters of proposal A...",
    "B": "first 500 characters of proposal B...",
    "C": "first 500 characters of proposal C...",
    "D": "first 500 characters of proposal D..."
  }
}
```

Note: Proposal text is truncated to 500 characters in the event. Full text is only written to `winning_proposal.md` for the winner.

**`stage2_complete`** — Stage 2 rankings aggregated

```jsonc
{
  "type": "stage2_complete",
  "rankings": [
    {"letter": "B", "display_letter": "D", "avg_position": 0.75, "votes": 4},
    {"letter": "E", "display_letter": "A", "avg_position": 1.25, "votes": 4},
    {"letter": "A", "display_letter": "C", "avg_position": 2.00, "votes": 3},
    {"letter": "C", "display_letter": "B", "avg_position": 2.50, "votes": 4},
    {"letter": "D", "display_letter": "E", "avg_position": 3.50, "votes": 4}
  ],
  "shuffle_map": {"D": "B", "A": "E", "C": "A", "B": "C", "E": "D"}
}
```

- `letter` — original label (A/B/C/D = proposals, E = current artifact)
- `display_letter` — anonymized label used during ranking
- `avg_position` — mean rank (0-indexed; lower = ranked higher)
- `votes` — number of rankers who included this version
- `shuffle_map` — maps display letter → original letter

**`stage3_complete`** — Chairman verdict

```jsonc
{
  "type": "stage3_complete",
  "winner": "B",
  "council_score": 87,
  "critique": "The winning proposal effectively opens with a concrete cost comparison..."
}
```

**`run_start`** — emitted by `run.py` at loop startup (not evaluate.py)

```jsonc
{
  "type": "run_start",
  "run_tag": "20260402_170824",
  "timestamp": "2026-04-02T17:08:24Z",
  "cost_limit_usd": 5.0,
  "initial_usage_usd": 12.3456
}
```

- `run_tag` — timestamp string used as the git branch suffix (`autoresearch/{run_tag}`)
- `cost_limit_usd` — value from `.env`, or `null` if no limit is set
- `initial_usage_usd` — cumulative OpenRouter spend at loop startup; the cost limit is measured as `current - initial`

**`iteration_result`** — emitted by `run.py` after each KEEP or DISCARD

```jsonc
{
  "type": "iteration_result",
  "iteration": 4,
  "status": "KEEP",
  "council_score": 87,
  "winner": "B",
  "best_score": 87,
  "commit": "da864d6",
  "spent_usd": 0.0821,
  "timestamp": "2026-04-02T17:12:03Z"
}
```

- `status` — `KEEP` or `DISCARD` (not TIMEOUT/CRASH — those don't reach this event)
- `council_score` — raw score from Stage 3 (same value as `results.tsv`)
- `best_score` — best score after this iteration (updated if KEEP)
- `commit` — git commit hash (same as previous KEEP for DISCARDs)
- `spent_usd` — cumulative USD spent this run at time of event

**`heartbeat`** — sent every 2 seconds

```jsonc
{
  "type": "heartbeat",
  "iteration": 12,
  "best_score": 87
}
```

---

## Error Handling

All endpoints return HTTP 200 with empty/default values when files don't exist (e.g., before the first iteration). They do not return 404 or 500 for missing data.

The SSE stream does not send an explicit error event if `evaluate.py` crashes. The frontend detects stalled runs by comparing the `heartbeat.iteration` value against the polling interval.

---

## Rate Limits

There are no rate limits. All endpoints are local-only (CORS allows `localhost:5173` and `127.0.0.1:5173` only).
