"""
run.py — Autonomous experiment loop.

Strict adaptation of karpathy/autoresearch experiment loop pattern:
  - Git branch per run (autoresearch/{timestamp})
  - results.tsv tracks every iteration
  - Greedy hill-climbing: KEEP if council_score improves, DISCARD otherwise
  - Git tip always = current best artifact
  - Runs forever (NEVER STOP) until manually interrupted

Key adaptation from base autoresearch:
  In base autoresearch, a single agent modifies train.py, commits BEFORE evaluation,
  and reverts on DISCARD. Here, the council generates proposals inside evaluate.py,
  so we commit AFTER the winner is selected. Branch tip still always equals best-so-far.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from config import EXPERIMENT_TIMEOUT, IMPROVEMENT_THRESHOLD, PLATEAU_WINDOW

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=check,
    )


def git_current_commit() -> str:
    result = git(["rev-parse", "--short", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else "none"


def git_setup(run_tag: str) -> None:
    """Initialize git repo and create run branch if needed."""
    if not Path(".git").exists():
        git(["init"])
        git(["add", "-A"])
        git(["commit", "-m", "Initial commit: project scaffold"])

    branch = f"autoresearch/{run_tag}"
    # Try to create branch; if it exists, just check it out
    result = git(["checkout", "-b", branch], check=False)
    if result.returncode != 0:
        git(["checkout", branch])

    print(f"[run] Branch: {branch}", flush=True)


# ---------------------------------------------------------------------------
# results.tsv helpers
# ---------------------------------------------------------------------------

TSV_HEADER = "commit\tcouncil_score\tstatus\tdescription\ttimestamp\n"
TSV_FILE = Path("results.tsv")


def init_results_tsv() -> None:
    if not TSV_FILE.exists():
        TSV_FILE.write_text(TSV_HEADER, encoding="utf-8")


def append_result(commit: str, score: int | None, status: str, description: str) -> None:
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    score_str = str(score) if score is not None else "N/A"
    line = f"{commit}\t{score_str}\t{status}\t{description}\t{ts}\n"
    with TSV_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def get_last_n_results(n: int = 5) -> str:
    if not TSV_FILE.exists():
        return ""
    lines = TSV_FILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:1] + lines[max(1, len(lines) - n):])  # header + last n


def recent_statuses(n: int) -> list[str]:
    if not TSV_FILE.exists():
        return []
    lines = TSV_FILE.read_text(encoding="utf-8").splitlines()[1:]  # skip header
    return [line.split("\t")[2] for line in lines[-n:] if line.strip()]


# ---------------------------------------------------------------------------
# Metric extraction (autoresearch pattern: grep stdout for "^metric_name:")
# ---------------------------------------------------------------------------

def extract_metric(log_text: str, key: str) -> str | None:
    for line in log_text.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    print(f"[run] Starting autoresearch-council-arena run: {run_tag}", flush=True)

    git_setup(run_tag)
    init_results_tsv()

    # Clear stale events file
    Path("events.jsonl").write_text("", encoding="utf-8")

    best_score: int = 0
    iteration: int = 0

    while True:  # NEVER STOP
        iteration += 1
        print(f"\n[run] ===== Iteration {iteration} | best_score={best_score} =====", flush=True)

        # --- Run evaluate.py with fixed time budget ---
        try:
            result = subprocess.run(
                [sys.executable, "evaluate.py"],
                capture_output=True,
                text=True,
                timeout=EXPERIMENT_TIMEOUT,
            )
            log_text = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            print(f"[run] Iteration {iteration}: TIMEOUT after {EXPERIMENT_TIMEOUT}s", flush=True)
            append_result("none", None, "TIMEOUT", f"iteration {iteration} exceeded time budget")
            continue
        except Exception as e:
            print(f"[run] Iteration {iteration}: ERROR launching evaluate.py: {e}", flush=True)
            append_result("none", None, "ERROR", str(e))
            time.sleep(10)
            continue

        if result.returncode != 0:
            print(f"[run] Iteration {iteration}: evaluate.py exited with code {result.returncode}", flush=True)
            print(log_text[-500:], flush=True)
            append_result("none", None, "CRASH", f"evaluate.py exit code {result.returncode}")
            continue

        # --- Extract metrics (autoresearch grep pattern) ---
        score_str = extract_metric(log_text, "council_score")
        winner = extract_metric(log_text, "winner")

        if score_str is None or winner is None:
            print(f"[run] Iteration {iteration}: metric extraction failed", flush=True)
            print("[run] stdout tail:", log_text[-300:], flush=True)
            append_result("none", None, "PARSE_FAILURE", "could not extract council_score or winner")
            continue

        try:
            score = int(score_str)
        except ValueError:
            print(f"[run] Iteration {iteration}: invalid score value: {score_str!r}", flush=True)
            append_result("none", None, "PARSE_FAILURE", f"invalid score: {score_str}")
            continue

        # --- Greedy hill-climbing: KEEP if improved, DISCARD otherwise ---
        improved = (score > best_score + IMPROVEMENT_THRESHOLD) and (winner != "E")

        if improved:
            # Write winning version to artifact.md
            winning_text = Path("winning_proposal.md").read_text(encoding="utf-8")
            Path("artifact.md").write_text(winning_text, encoding="utf-8")

            # Commit (branch tip now = new best)
            description = f"Iter {iteration}: score={score} winner={winner}"
            git(["add", "artifact.md", "critique.md"])
            git(["commit", "-m", description])
            commit = git_current_commit()

            status = "KEEP"
            best_score = score
            print(f"[run] KEEP — score {score} (+{score - (best_score - (score - best_score))} improvement)", flush=True)

        else:
            # No commit made — branch tip unchanged
            commit = git_current_commit()
            status = "DISCARD"
            reason = "no improvement" if winner != "E" else "winner=E (current artifact is best)"
            print(f"[run] DISCARD — score {score} vs best {best_score} ({reason})", flush=True)

        append_result(commit, score, status, f"Iter {iteration} winner={winner}")

        # --- Plateau detection ---
        recent = recent_statuses(PLATEAU_WINDOW)
        if len(recent) >= PLATEAU_WINDOW and all(s == "DISCARD" for s in recent):
            msg = f"[run] PLATEAU: last {PLATEAU_WINDOW} iterations all DISCARD. Consider editing program.md to try new directions."
            print(msg, flush=True)
            append_result("none", None, "PLATEAU", msg)

        # --- API failure guard: back off if all recent runs failed ---
        recent_statuses_list = recent_statuses(3)
        if len(recent_statuses_list) == 3 and all(
            s in ("CRASH", "PARSE_FAILURE", "API_FAILURE") for s in recent_statuses_list
        ):
            print("[run] 3 consecutive failures — sleeping 60s before retry", flush=True)
            time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[run] Interrupted by user. Experiment loop stopped.", flush=True)
