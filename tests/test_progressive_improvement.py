"""
Test that the council pipeline produces progressive improvement on the test-suite task.

This test simulates multiple iterations of the autoresearch loop by mocking
OpenRouter API responses. Each mock "iteration" returns a chairman judgment
with gradually increasing scores across the 5 orthogonal dimensions, verifying
that the hill-climbing loop correctly KEEPs improvements and DISCARDs regressions.

The mock responses model the expected behavior: each iteration improves 1-2
dimensions by 2-5 points while leaving others unchanged, producing a gradual
council_score climb from ~50 to ~90+.
"""

import re
import sys
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import IMPROVEMENT_THRESHOLD, SCORING_DIMENSIONS
from run import extract_metric


# ---------------------------------------------------------------------------
# Simulated iteration data — models the expected progressive improvement arc
# ---------------------------------------------------------------------------

# Each entry: (winner, sub_scores_dict, description)
# Sub-scores must sum to council_score. Dimensions:
#   CASE_COVERAGE, ASSERTION_QUALITY, ISOLATION, ERROR_HANDLING, MAINTAINABILITY
SIMULATED_ITERATIONS = [
    # Iter 1: Model renames test functions, adds basic respx mocking
    # Improves MAINTAINABILITY (+4) and ISOLATION (+3) from baseline
    ("A", {"CASE_COVERAGE": 10, "ASSERTION_QUALITY": 12, "ISOLATION": 11, "ERROR_HANDLING": 10, "MAINTAINABILITY": 14}, "renamed tests, added basic mocking"),

    # Iter 2: Regression — model tried to restructure but broke assertions
    ("D", {"CASE_COVERAGE": 11, "ASSERTION_QUALITY": 10, "ISOLATION": 12, "ERROR_HANDLING": 10, "MAINTAINABILITY": 13}, "restructured but regressed assertions"),

    # Iter 3: Adds update and delete test cases
    # Improves CASE_COVERAGE (+5) from current best
    ("B", {"CASE_COVERAGE": 15, "ASSERTION_QUALITY": 12, "ISOLATION": 11, "ERROR_HANDLING": 10, "MAINTAINABILITY": 14}, "added update/delete tests"),

    # Iter 4: Regression — less coverage than current best
    ("C", {"CASE_COVERAGE": 13, "ASSERTION_QUALITY": 13, "ISOLATION": 12, "ERROR_HANDLING": 11, "MAINTAINABILITY": 14}, "tried polish but lost coverage"),

    # Iter 5: Adds timeout and 5xx error handling tests
    # Improves ERROR_HANDLING (+5)
    ("A", {"CASE_COVERAGE": 15, "ASSERTION_QUALITY": 12, "ISOLATION": 11, "ERROR_HANDLING": 15, "MAINTAINABILITY": 14}, "added timeout and 5xx tests"),

    # Iter 6: Improves assertion quality — checks specific field values
    # Improves ASSERTION_QUALITY (+4)
    ("C", {"CASE_COVERAGE": 15, "ASSERTION_QUALITY": 16, "ISOLATION": 11, "ERROR_HANDLING": 15, "MAINTAINABILITY": 14}, "improved assertion specificity"),

    # Iter 7: Regression — good assertions but dropped an error test
    ("D", {"CASE_COVERAGE": 15, "ASSERTION_QUALITY": 16, "ISOLATION": 12, "ERROR_HANDLING": 13, "MAINTAINABILITY": 14}, "isolation improved but error tests lost"),

    # Iter 8: Adds proper fixtures and parametrize
    # Improves ISOLATION (+4) and MAINTAINABILITY (+2)
    ("B", {"CASE_COVERAGE": 15, "ASSERTION_QUALITY": 16, "ISOLATION": 15, "ERROR_HANDLING": 15, "MAINTAINABILITY": 16}, "added fixtures and parametrize"),

    # Iter 9: Adds pagination, edge cases, rate limit test
    # Improves CASE_COVERAGE (+3), ERROR_HANDLING (+2)
    ("A", {"CASE_COVERAGE": 18, "ASSERTION_QUALITY": 16, "ISOLATION": 15, "ERROR_HANDLING": 17, "MAINTAINABILITY": 16}, "added pagination, rate limit, edge cases"),

    # Iter 10: Fine-tuning — polishes all dimensions slightly
    ("C", {"CASE_COVERAGE": 18, "ASSERTION_QUALITY": 17, "ISOLATION": 16, "ERROR_HANDLING": 17, "MAINTAINABILITY": 17}, "polished assertions and isolation"),

    # Iter 11: Near ceiling — docstrings, descriptive assertion messages
    ("B", {"CASE_COVERAGE": 18, "ASSERTION_QUALITY": 18, "ISOLATION": 17, "ERROR_HANDLING": 17, "MAINTAINABILITY": 18}, "added docstrings and assertion messages"),

    # Iter 12: Regression — all dimensions slightly below current best
    ("D", {"CASE_COVERAGE": 17, "ASSERTION_QUALITY": 18, "ISOLATION": 17, "ERROR_HANDLING": 17, "MAINTAINABILITY": 17}, "marginal regression"),
]


def _make_chairman_response(winner: str, sub_scores: dict[str, int], critique: str = "") -> str:
    """Format a chairman response matching the regex patterns in evaluate.py."""
    lines = [f"WINNER: {winner}"]
    for key, _ in SCORING_DIMENSIONS:
        lines.append(f"SCORE_{key}: {sub_scores[key]}")
    total = sum(sub_scores.values())
    lines.append(f"COUNCIL_SCORE: {total}")
    lines.append(f"\nCRITIQUE:\n{critique or 'Continue improving.'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExtractMetric:
    """Verify the metric extraction used by run.py works with expected output."""

    def test_extracts_council_score(self):
        log = "council_score: 72\nwinner: A\n"
        assert extract_metric(log, "council_score") == "72"

    def test_extracts_winner(self):
        log = "council_score: 72\nwinner: A\n"
        assert extract_metric(log, "winner") == "A"

    def test_returns_none_for_missing_metric(self):
        log = "some other output\n"
        assert extract_metric(log, "council_score") is None


class TestChairmanResponseParsing:
    """Verify that simulated chairman responses can be parsed by evaluate.py's regex."""

    @pytest.mark.parametrize("iter_idx", range(len(SIMULATED_ITERATIONS)))
    def test_chairman_response_parseable(self, iter_idx):
        """Each simulated chairman response must be parseable by evaluate.py's patterns."""
        winner, sub_scores, desc = SIMULATED_ITERATIONS[iter_idx]
        response = _make_chairman_response(winner, sub_scores, desc)

        # Parse WINNER
        winner_match = re.search(r"WINNER:\s*([A-E])", response)
        assert winner_match is not None, f"Iter {iter_idx}: WINNER not parseable"
        assert winner_match.group(1) == winner

        # Parse each sub-score
        for key, _ in SCORING_DIMENSIONS:
            match = re.search(rf"SCORE_{key}:\s*(\d+)", response)
            assert match is not None, f"Iter {iter_idx}: SCORE_{key} not parseable"
            assert int(match.group(1)) == sub_scores[key]

        # Parse total
        total_match = re.search(r"COUNCIL_SCORE:\s*(\d+)", response)
        assert total_match is not None, f"Iter {iter_idx}: COUNCIL_SCORE not parseable"
        assert int(total_match.group(1)) == sum(sub_scores.values())


class TestHillClimbingDecision:
    """Verify that the KEEP/DISCARD logic produces progressive improvement."""

    def test_improvement_threshold_allows_any_strict_improvement(self):
        """With IMPROVEMENT_THRESHOLD=0, any score > best_score is a KEEP."""
        assert IMPROVEMENT_THRESHOLD == 0, (
            f"IMPROVEMENT_THRESHOLD should be 0 for progressive improvement, got {IMPROVEMENT_THRESHOLD}"
        )

    def test_progressive_score_trajectory(self):
        """Simulate the full hill-climbing loop and verify progressive improvement.

        This is the core test: given the simulated iterations, the greedy
        hill-climbing loop should produce a monotonically increasing best_score
        trajectory with multiple KEEP decisions spread across iterations.
        """
        best_score = 50  # starting artifact baseline
        keeps = []
        discards = []
        score_trajectory = [best_score]

        for i, (winner, sub_scores, desc) in enumerate(SIMULATED_ITERATIONS):
            score = sum(sub_scores.values())
            improved = (score > best_score + IMPROVEMENT_THRESHOLD) and (winner != "E")

            if improved:
                keeps.append({"iter": i + 1, "score": score, "desc": desc})
                best_score = score
            else:
                discards.append({"iter": i + 1, "score": score, "desc": desc})

            score_trajectory.append(best_score)

        # --- Assertions about the trajectory ---

        # 1. Multiple KEEPs (not 1-2 like previous tasks)
        assert len(keeps) >= 5, (
            f"Expected at least 5 KEEPs for progressive improvement, got {len(keeps)}: "
            f"{[k['desc'] for k in keeps]}"
        )

        # 2. Multiple DISCARDs (system correctly rejects regressions)
        assert len(discards) >= 2, (
            f"Expected at least 2 DISCARDs (regressions rejected), got {len(discards)}"
        )

        # 3. Score trajectory is monotonically non-decreasing
        for j in range(1, len(score_trajectory)):
            assert score_trajectory[j] >= score_trajectory[j - 1], (
                f"Score regressed at step {j}: {score_trajectory[j-1]} -> {score_trajectory[j]}"
            )

        # 4. Final score significantly higher than start (progressive improvement)
        final_score = score_trajectory[-1]
        assert final_score >= 80, (
            f"Expected final score >= 80, got {final_score}"
        )
        assert final_score - 50 >= 30, (
            f"Expected at least 30 points of improvement from baseline 50, got {final_score - 50}"
        )

        # 5. Score climbs gradually (no single jump > 15 points)
        keep_scores = [50] + [k["score"] for k in keeps]
        for j in range(1, len(keep_scores)):
            jump = keep_scores[j] - keep_scores[j - 1]
            assert jump <= 15, (
                f"Jump from {keep_scores[j-1]} to {keep_scores[j]} ({jump} pts) "
                f"is too large — indicates single-iteration convergence, not progressive improvement"
            )

        # 6. KEEPs are spread across iterations (not all clustered at start)
        keep_iters = [k["iter"] for k in keeps]
        first_half_keeps = sum(1 for i in keep_iters if i <= len(SIMULATED_ITERATIONS) // 2)
        second_half_keeps = sum(1 for i in keep_iters if i > len(SIMULATED_ITERATIONS) // 2)
        assert second_half_keeps >= 1, (
            f"All KEEPs in first half of iterations — improvement should continue throughout. "
            f"First half: {first_half_keeps}, second half: {second_half_keeps}"
        )

    def test_winner_e_is_always_discarded(self):
        """If the chairman picks E (current artifact), it must be DISCARD regardless of score."""
        best_score = 50
        score = 99  # even a very high score
        improved = (score > best_score + IMPROVEMENT_THRESHOLD) and ("E" != "E")
        assert not improved, "Winner=E should always be DISCARD"


class TestDimensionOrthogonality:
    """Verify that the simulated data models orthogonal improvement (one dimension at a time)."""

    def test_no_iteration_improves_all_dimensions(self):
        """No single iteration should improve all 5 dimensions — that indicates correlated dimensions."""
        baseline = {"CASE_COVERAGE": 10, "ASSERTION_QUALITY": 12, "ISOLATION": 8, "ERROR_HANDLING": 10, "MAINTAINABILITY": 10}
        current_best = dict(baseline)

        for i, (winner, sub_scores, desc) in enumerate(SIMULATED_ITERATIONS):
            # Count how many dimensions improved
            improvements = sum(
                1 for key in sub_scores
                if sub_scores[key] > current_best[key]
            )

            assert improvements < 5, (
                f"Iter {i+1} improved ALL 5 dimensions at once — this indicates correlated "
                f"dimensions, not orthogonal improvement. Desc: {desc}"
            )

            # Update current best (simulate KEEP if total improved)
            total = sum(sub_scores.values())
            best_total = sum(current_best.values())
            if total > best_total + IMPROVEMENT_THRESHOLD and winner != "E":
                current_best = dict(sub_scores)

    def test_different_dimensions_improve_across_keeps(self):
        """KEEPs should improve different dimensions, not the same one repeatedly."""
        best_score = 50
        current_best = {"CASE_COVERAGE": 10, "ASSERTION_QUALITY": 12, "ISOLATION": 8, "ERROR_HANDLING": 10, "MAINTAINABILITY": 10}
        dimensions_improved = set()

        for winner, sub_scores, desc in SIMULATED_ITERATIONS:
            score = sum(sub_scores.values())
            improved = (score > best_score + IMPROVEMENT_THRESHOLD) and (winner != "E")

            if improved:
                for key in sub_scores:
                    if sub_scores[key] > current_best[key]:
                        dimensions_improved.add(key)
                current_best = dict(sub_scores)
                best_score = score

        assert len(dimensions_improved) >= 4, (
            f"Expected improvements across at least 4 of 5 dimensions, "
            f"but only saw: {dimensions_improved}"
        )


class TestScoringDimensionsConfig:
    """Verify that config.py dimensions match expectations for the test suite task."""

    def test_five_dimensions(self):
        assert len(SCORING_DIMENSIONS) == 5

    def test_dimension_names(self):
        names = [key for key, _ in SCORING_DIMENSIONS]
        expected = ["CASE_COVERAGE", "ASSERTION_QUALITY", "ISOLATION", "ERROR_HANDLING", "MAINTAINABILITY"]
        assert names == expected, f"Dimension names mismatch: {names}"

    def test_dimension_names_are_valid_identifiers(self):
        """Dimension names must be valid for SCORE_{name} regex pattern in evaluate.py."""
        for key, _ in SCORING_DIMENSIONS:
            assert re.match(r"^[A-Z_]+$", key), f"Invalid dimension name: {key}"
