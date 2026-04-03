"""
backend/server.py — FastAPI SSE server.

Adapted from karpathy/llm-council backend/main.py.
Streams live iteration events to the React frontend via Server-Sent Events.

Endpoints:
  GET  /api/status        — current iteration number, best score, artifact word count
  GET  /api/results       — full results.tsv as JSON array
  GET  /api/artifact      — current artifact.md content
  GET  /api/history       — git log as JSON
  GET  /api/stream        — SSE stream of events emitted by run.py via events.jsonl

The experiment loop (run.py) appends JSON lines to events.jsonl.
This server tails events.jsonl and pushes each new line to connected SSE clients.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Add project root to path so imports work when run from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="autoresearch-council-arena")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ROOT = Path(__file__).parent.parent
RESULTS_FILE = ROOT / "results.tsv"
ARTIFACT_FILE = ROOT / "artifact.md"
EVENTS_FILE = ROOT / "events.jsonl"
STOP_FLAG = ROOT / "stop.flag"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_results() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    lines = RESULTS_FILE.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return []
    headers = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if line.strip():
            values = line.split("\t")
            rows.append(dict(zip(headers, values)))
    return rows


def read_artifact() -> str:
    if not ARTIFACT_FILE.exists():
        return ""
    return ARTIFACT_FILE.read_text(encoding="utf-8")


def git_log() -> list[dict]:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--oneline", "-20"],
            capture_output=True,
            text=True,
            check=True,
        )
        entries = []
        for line in result.stdout.strip().splitlines():
            parts = line.split(" ", 1)
            entries.append({"commit": parts[0], "message": parts[1] if len(parts) > 1 else ""})
        return entries
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/status")
async def get_status():
    results = read_results()
    keeps = [r for r in results if r.get("status") == "KEEP"]
    best_score = max((int(r["council_score"]) for r in keeps if r["council_score"].isdigit()), default=0)
    artifact = read_artifact()
    return {
        "iteration": len(results),
        "best_score": best_score,
        "artifact_words": len(artifact.split()),
        "running": EVENTS_FILE.exists(),
    }


@app.get("/api/results")
async def get_results():
    return read_results()


@app.get("/api/artifact")
async def get_artifact():
    return {"content": read_artifact()}


@app.get("/api/history")
async def get_history():
    return git_log()


@app.post("/api/stop")
async def stop_run():
    """Write stop.flag — run.py checks for this at the start of each iteration
    and exits gracefully after the current iteration completes."""
    STOP_FLAG.write_text("stop", encoding="utf-8")
    print(f"[server] STOP requested — wrote {STOP_FLAG}", flush=True)
    return {"status": "stop_requested", "flag_path": str(STOP_FLAG)}


@app.get("/api/stream")
async def stream_events():
    """SSE endpoint — tails events.jsonl and pushes new lines to the client.

    Event types (from evaluate.py):
      stage1_complete  — proposals generated
      stage2_complete  — rankings computed
      stage3_complete  — winner + score + critique
    Additional events injected here:
      iteration_complete — summary of the iteration outcome
    """
    async def event_generator():
        # Ensure the file exists
        EVENTS_FILE.touch()
        position = EVENTS_FILE.stat().st_size  # start at end — only new events

        # Send a heartbeat so the browser doesn't time out
        yield "data: {\"type\": \"connected\"}\n\n"

        while True:
            current_size = EVENTS_FILE.stat().st_size
            if current_size > position:
                with EVENTS_FILE.open("r", encoding="utf-8") as f:
                    f.seek(position)
                    new_data = f.read()
                position = current_size

                for line in new_data.splitlines():
                    line = line.strip()
                    if line:
                        yield f"data: {line}\n\n"

            # Also push latest status as a periodic heartbeat
            results = read_results()
            keeps = [r for r in results if r.get("status") == "KEEP"]
            best = max(
                (int(r["council_score"]) for r in keeps if r.get("council_score", "").isdigit()),
                default=0,
            )
            yield f"data: {{\"type\": \"heartbeat\", \"iteration\": {len(results)}, \"best_score\": {best}}}\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=False)
