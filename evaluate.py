"""
evaluate.py — FROZEN three-stage council pipeline.

This file is the frozen evaluation harness (equivalent to prepare.py in autoresearch).
DO NOT MODIFY after initial setup. The autoresearch loop discipline requires that the
evaluator never changes — only artifact.md is editable.

Adapted from karpathy/llm-council three-stage pipeline:
  Stage 1: All council models propose improved versions in parallel
  Stage 2: Anonymous ranking — "Version A/B/C/D/E" (E = current artifact baseline)
  Stage 3: Chairman selects winner, assigns council_score, writes critique

Outputs to stdout (grep-able by run.py):
  council_score: XX
  winner: X

Writes to disk:
  winning_proposal.md  — the winning version text (read by run.py)
  critique.md          — chairman's qualitative feedback (read next iteration)
"""

import asyncio
import json
import random
import re
import sys
from pathlib import Path

from config import (
    CHAIRMAN_MODEL,
    COUNCIL_MODELS,
    MAX_ARTIFACT_WORDS,
    SCORING_DIMENSIONS,
)
from openrouter import query_model, query_models_parallel


# ---------------------------------------------------------------------------
# Stage 1: Parallel proposal generation
# ---------------------------------------------------------------------------

STAGE1_SYSTEM = """\
You are a council member in a competitive writing improvement arena.
Your proposal competes against proposals from other AI models.
The council will anonymously rank all proposals — including the current version.
Write to WIN."""

def _build_stage1_prompt(program: str, artifact: str, history: str, critique: str, tried_strategies: str = "") -> str:
    parts = [
        f"PROGRAM OBJECTIVES:\n{program}",
        f"CURRENT ARTIFACT:\n{artifact}",
    ]
    if tried_strategies.strip():
        parts.append(
            f"STRATEGIES ALREADY TRIED — do not repeat these, propose something meaningfully different:\n{tried_strategies}"
        )
    if history.strip():
        parts.append(f"RECENT EXPERIMENT HISTORY (last 5 iterations):\n{history}")
    if critique.strip():
        parts.append(f"PREVIOUS COUNCIL CRITIQUE (use this to avoid past mistakes):\n{critique}")
    parts.append(
        "YOUR TASK:\n"
        "Produce a complete improved version of the artifact.\n"
        "- Output ONLY the full improved text. No preamble, no meta-commentary.\n"
        "- Make a specific, meaningful improvement (not just cosmetic rewording).\n"
        "- Stay within word limits specified in the program.\n"
        "- Consider the critique and try a strategy not listed in STRATEGIES ALREADY TRIED."
    )
    return "\n\n---\n\n".join(parts)


async def stage1_propose(
    program: str,
    artifact: str,
    history: str,
    critique: str,
    tried_strategies: str = "",
) -> dict[str, str]:
    """Stage 1: All council models propose improved versions in parallel.

    Returns {letter: proposal_text} for successful responses.
    Failed models (None response) are excluded.
    Letters are assigned in council model order: A, B, C, D.
    """
    prompt = _build_stage1_prompt(program, artifact, history, critique, tried_strategies)
    messages = [
        {"role": "system", "content": STAGE1_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    proposals = {}
    letters = "ABCD"
    for i, (model, resp) in enumerate(responses.items()):
        if resp is not None and resp.get("content"):
            proposals[letters[i]] = resp["content"]

    return proposals  # e.g. {"A": "...", "B": "...", "C": "..."}


def _model_names() -> dict[str, str]:
    """Return letter → model-slug mapping for the current council."""
    return {l: m for l, m in zip("ABCD", COUNCIL_MODELS)}


# ---------------------------------------------------------------------------
# Stage 2: Anonymous ranking
# ---------------------------------------------------------------------------

STAGE2_SYSTEM = """\
You are evaluating multiple versions of a piece of writing. The versions are anonymized.
You do not know which AI model — or whether a human — wrote each version.
Judge solely on quality."""

def _build_stage2_prompt(
    versions: dict[str, str],
    program: str,
) -> str:
    version_blocks = "\n\n".join(
        f"--- Version {letter} ---\n{text}\n--- End Version {letter} ---"
        for letter, text in versions.items()
    )
    return (
        f"EVALUATION CRITERIA (from program):\n{program}\n\n"
        f"VERSIONS TO RANK:\n\n{version_blocks}\n\n"
        "TASK:\n"
        "Rank all versions from best to worst based on the evaluation criteria.\n"
        "Briefly note your reasoning (one sentence per version), then give your final ranking.\n\n"
        "Your response MUST end with exactly this format:\n"
        "FINAL RANKING: [best] > [second] > ... > [worst]\n"
        "(Use the letter labels exactly as shown above.)"
    )


def _parse_ranking(text: str, valid_letters: set[str]) -> list[int] | None:
    """Parse 'FINAL RANKING: B > E > A > C > D' into position indices.

    Returns list of 0-based indices (position 0 = best) or None on parse failure.
    Only includes valid_letters in the result.
    """
    match = re.search(r"FINAL RANKING:\s*([A-E][A-E >]*[A-E])", text)
    if not match:
        return None
    raw = match.group(1)
    letters = [s.strip() for s in raw.split(">")]
    # Filter to only valid letters, preserve order
    filtered = [l for l in letters if l in valid_letters]
    if len(filtered) < 2:
        return None
    return filtered  # ordered list: [best, second, ...]


def _aggregate_rankings(
    all_rankings: list[list[str]],
    valid_letters: set[str],
) -> list[dict]:
    """Compute average rank position for each letter (lower = better).

    Returns sorted list of {"letter": X, "avg_position": Y, "votes": N}.
    """
    positions: dict[str, list[float]] = {l: [] for l in valid_letters}
    for ranking in all_rankings:
        for pos, letter in enumerate(ranking):
            if letter in positions:
                positions[letter].append(float(pos))

    results = []
    for letter, pos_list in positions.items():
        if pos_list:
            results.append({
                "letter": letter,
                "avg_position": sum(pos_list) / len(pos_list),
                "votes": len(pos_list),
            })
    results.sort(key=lambda x: x["avg_position"])
    return results


async def stage2_rank(
    proposals: dict[str, str],
    current_artifact: str,
    program: str,
) -> tuple[list[dict], dict[str, str]]:
    """Stage 2: Anonymous ranking of proposals + current artifact (as Version E).

    Returns (aggregate_rankings, shuffle_map) where shuffle_map is {display_letter: original_letter}.
    """
    # Add current artifact as Version E (the baseline)
    all_versions_ordered = dict(proposals)
    all_versions_ordered["E"] = current_artifact

    # Shuffle letter assignments to prevent positional bias
    original_letters = list(all_versions_ordered.keys())
    display_letters = original_letters[:]
    random.shuffle(display_letters)
    shuffle_map = {display: orig for display, orig in zip(display_letters, original_letters)}
    reverse_map = {orig: display for display, orig in shuffle_map.items()}

    # Build anonymized version dict {display_letter: text}
    anonymized: dict[str, str] = {}
    for orig_letter, text in all_versions_ordered.items():
        display_letter = reverse_map[orig_letter]
        anonymized[display_letter] = text

    # Send ranking prompt to all council models in parallel
    prompt = _build_stage2_prompt(anonymized, program)
    messages = [
        {"role": "system", "content": STAGE2_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    # Parse each model's ranking — capture full reasoning text too
    valid_display_letters = set(anonymized.keys())
    all_rankings: list[list[str]] = []
    per_model_votes: list[dict] = []

    for model, resp in responses.items():
        if resp is None or not resp.get("content"):
            print(f"[stage2] {model} returned no response — skipping vote", file=sys.stderr, flush=True)
            continue
        content = resp["content"]
        ranking = _parse_ranking(content, valid_display_letters)
        if ranking is None:
            print(f"[stage2] {model} ranking parse failed — skipping vote", file=sys.stderr, flush=True)
            print(f"[stage2] raw response tail: {content[-200:]}", file=sys.stderr, flush=True)
            continue
        # Reasoning = everything before "FINAL RANKING:"
        parts = re.split(r"FINAL RANKING:", content, maxsplit=1)
        reasoning = parts[0].strip() if len(parts) > 1 else ""
        # Map display ranking back to original letters for transparency
        original_ranking = [shuffle_map.get(l, l) for l in ranking]
        per_model_votes.append({
            "model": model,
            "display_ranking": " > ".join(ranking),
            "original_ranking": " > ".join(original_ranking),
            "reasoning": reasoning,
        })
        all_rankings.append(ranking)

    if len(all_rankings) < 2:
        return [], shuffle_map, []

    # Aggregate in display-letter space, then map back to original letters
    display_aggregate = _aggregate_rankings(all_rankings, valid_display_letters)

    # Convert display letters back to original letters for the result
    aggregate = []
    for entry in display_aggregate:
        orig = shuffle_map[entry["letter"]]
        aggregate.append({
            "letter": orig,           # original: A/B/C/D (proposals) or E (current)
            "display_letter": entry["letter"],
            "avg_position": entry["avg_position"],
            "votes": entry["votes"],
        })

    return aggregate, shuffle_map, per_model_votes


# ---------------------------------------------------------------------------
# Stage 3: Chairman judgment
# ---------------------------------------------------------------------------

STAGE3_SYSTEM = """\
You are the Chairman of an AI writing council.
Your role: select the best version, score it across specific dimensions, and provide actionable critique."""

def _build_stage3_prompt(
    proposals: dict[str, str],
    current_artifact: str,
    aggregate: list[dict],
    program: str,
) -> str:
    proposal_blocks = "\n\n".join(
        f"--- Proposal {letter} ---\n{text}\n--- End ---"
        for letter, text in proposals.items()
    )
    rank_table = "\n".join(
        f"  {r['letter']} (original label): avg_position={r['avg_position']:.2f}, votes={r['votes']}"
        for r in aggregate
    )
    # Build dimension instructions and format lines from config
    dim_instructions = "\n".join(
        f"   SCORE_{key} (0–20): {desc}"
        for key, desc in SCORING_DIMENSIONS
    )
    dim_format = "\n".join(
        f"SCORE_{key}: [integer 0-20]"
        for key, _ in SCORING_DIMENSIONS
    )
    return (
        f"PROGRAM OBJECTIVES:\n{program}\n\n"
        f"CURRENT ARTIFACT (Version E — baseline):\n{current_artifact}\n\n"
        f"COUNCIL PROPOSALS:\n{proposal_blocks}\n\n"
        f"PEER RANKING RESULTS (lower avg_position = ranked higher by peers):\n{rank_table}\n\n"
        "YOUR TASK:\n"
        "1. Select the winner (A, B, C, D, or E if none of the proposals improve on the current version).\n"
        "2. Score the WINNING version on each dimension below (0–20 each). Be strict and consistent\n"
        "   across iterations — the same quality should receive the same score every time.\n"
        f"{dim_instructions}\n"
        "   COUNCIL_SCORE is the sum of all dimension scores (0–100).\n"
        "3. Write a concise critique (3–5 sentences): what worked, what didn't, what to try next.\n\n"
        "Format your response EXACTLY as follows (these lines are machine-parsed):\n\n"
        "WINNER: [letter]\n"
        f"{dim_format}\n"
        "COUNCIL_SCORE: [sum of dimension scores]\n\n"
        "CRITIQUE:\n"
        "[your critique here]"
    )


async def stage3_judge(
    proposals: dict[str, str],
    aggregate: list[dict],
    current_artifact: str,
    program: str,
) -> dict:
    """Stage 3: Chairman selects winner, assigns score, writes critique.

    Returns {"winner": letter, "council_score": int, "critique": str, "winning_text": str}
    """
    prompt = _build_stage3_prompt(proposals, current_artifact, aggregate, program)
    messages = [
        {"role": "system", "content": STAGE3_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    resp = await query_model(CHAIRMAN_MODEL, messages)

    if resp is None or not resp.get("content"):
        print("[stage3] Chairman returned no response — defaulting to E (no improvement)", file=sys.stderr, flush=True)
        return {
            "winner": "E",
            "council_score": 0,
            "critique": "Chairman unavailable.",
            "winning_text": current_artifact,
            "chairman_full_response": "",
        }

    content = resp["content"]

    # Parse WINNER
    winner_match = re.search(r"WINNER:\s*([A-E])", content)
    winner = winner_match.group(1) if winner_match else "E"

    # Parse per-dimension sub-scores — clamp each to [0, 20]
    sub_scores = {}
    for key, _ in SCORING_DIMENSIONS:
        match = re.search(rf"SCORE_{key}:\s*(\d+)", content)
        sub_scores[key] = max(0, min(20, int(match.group(1)))) if match else 0

    # Compute total from sub-scores — don't trust chairman arithmetic
    council_score = max(1, min(100, sum(sub_scores.values())))

    # Log breakdown
    breakdown = " | ".join(f"{k}={v}" for k, v in sub_scores.items())
    print(f"[stage3] Sub-scores: {breakdown} → total={council_score}", file=sys.stderr, flush=True)

    # Parse CRITIQUE
    critique_match = re.search(r"CRITIQUE:\s*(.*)", content, re.DOTALL)
    critique = critique_match.group(1).strip() if critique_match else content

    # Resolve winning text
    all_versions = dict(proposals)
    all_versions["E"] = current_artifact
    winning_text = all_versions.get(winner, current_artifact)

    # Validate word count
    word_count = len(winning_text.split())
    if word_count > MAX_ARTIFACT_WORDS:
        print(
            f"[stage3] Winning proposal ({winner}) exceeds {MAX_ARTIFACT_WORDS} words "
            f"({word_count}) — falling back to E",
            file=sys.stderr, flush=True,
        )
        winner = "E"
        winning_text = current_artifact

    return {
        "winner": winner,
        "council_score": council_score,
        "sub_scores": sub_scores,
        "critique": critique,
        "winning_text": winning_text,
        "chairman_full_response": content,
    }


# ---------------------------------------------------------------------------
# Shared event file (for SSE server)
# ---------------------------------------------------------------------------

EVENT_FILE = Path("events.jsonl")

def _emit_event(event: dict) -> None:
    """Append a JSON event line to events.jsonl for the SSE server to stream."""
    with EVENT_FILE.open("a") as f:
        f.write(json.dumps(event) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    # Read input files
    program = Path("program.md").read_text(encoding="utf-8")
    artifact = Path("artifact.md").read_text(encoding="utf-8")
    history = ""
    if Path("results.tsv").exists():
        lines = Path("results.tsv").read_text(encoding="utf-8").splitlines()
        history = "\n".join(lines[-6:])  # header + last 5
    critique = ""
    if Path("critique.md").exists():
        critique = Path("critique.md").read_text(encoding="utf-8")
    tried_strategies = ""
    if Path("tried_strategies.md").exists():
        tried_strategies = Path("tried_strategies.md").read_text(encoding="utf-8")

    # Stage 1 — parallel proposals
    print("[evaluate] Stage 1: generating proposals...", file=sys.stderr, flush=True)
    proposals = await stage1_propose(program, artifact, history, critique, tried_strategies)

    if len(proposals) == 0:
        print("[evaluate] All council models failed in Stage 1 — aborting", file=sys.stderr, flush=True)
        sys.exit(1)

    model_names = _model_names()
    print(f"[evaluate] Stage 1 complete: {len(proposals)} proposals ({', '.join(proposals.keys())})", file=sys.stderr, flush=True)
    _emit_event({
        "type": "stage1_complete",
        "proposals": proposals,          # full text, no truncation
        "model_names": model_names,      # {"A": "openai/gpt-5.4-nano", ...}
    })

    # Stage 2 — anonymous ranking
    print("[evaluate] Stage 2: ranking proposals...", file=sys.stderr, flush=True)
    aggregate, shuffle_map, per_model_votes = await stage2_rank(proposals, artifact, program)

    if len(aggregate) < 2:
        print("[evaluate] Insufficient rankings from Stage 2 — aborting", file=sys.stderr, flush=True)
        sys.exit(1)

    print("[evaluate] Stage 2 rankings:", file=sys.stderr, flush=True)
    for r in aggregate:
        print(f"  {r['letter']} avg_pos={r['avg_position']:.2f} votes={r['votes']}", file=sys.stderr, flush=True)
    _emit_event({
        "type": "stage2_complete",
        "rankings": aggregate,
        "shuffle_map": shuffle_map,
        "votes": per_model_votes,        # per-model rankings + reasoning
        "model_names": model_names,
    })

    # Stage 3 — chairman judgment
    print("[evaluate] Stage 3: chairman judging...", file=sys.stderr, flush=True)
    result = await stage3_judge(proposals, aggregate, artifact, program)

    winner_model = model_names.get(result["winner"], CHAIRMAN_MODEL if result["winner"] == "E" else "unknown")
    print(f"[evaluate] Stage 3 complete: winner={result['winner']} score={result['council_score']}", file=sys.stderr, flush=True)
    _emit_event({
        "type": "stage3_complete",
        "winner": result["winner"],
        "winner_model": winner_model,
        "council_score": result["council_score"],
        "sub_scores": result["sub_scores"],
        "critique": result["critique"],
        "chairman_full_response": result["chairman_full_response"],
        "chairman_model": CHAIRMAN_MODEL,
        "model_names": model_names,
    })

    # Write winning proposal for run.py to read
    Path("winning_proposal.md").write_text(result["winning_text"], encoding="utf-8")

    # Write critique for next iteration
    Path("critique.md").write_text(result["critique"], encoding="utf-8")

    # Print grep-able metric lines (autoresearch pattern: grep "^council_score:")
    print(f"council_score: {result['council_score']}", flush=True)
    print(f"winner: {result['winner']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
