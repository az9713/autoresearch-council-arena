# Task Design: Why This Task, Why This Artifact

This document explains the design of the current experiment task and the reasoning behind every choice — the topic, the scoring rubric, the starting artifact, and how they work together to produce observable hill-climbing behavior.

---

## The Task

**Write a comprehensive pytest test suite for a Python REST API client class (`TaskClient`).**

The test file exercises a hypothetical task-management API client's CRUD operations, error handling, and edge cases using proper mocking and pytest best practices.

---

## Why This Topic

### Combinatorial improvement space

A test suite is a collection of independent test functions. Each function can be added, improved, or refactored independently. There are dozens of possible test cases (5 CRUD operations × success/failure paths × edge cases), and no model can add all of them in one pass. This creates a naturally incremental improvement trajectory.

### Structural vs. content tension

Improving test isolation (adding mocks, fixtures) is a fundamentally different kind of change than adding test cases (coverage). A model that refactors the file for better isolation will not simultaneously add 5 new error handling tests. This forces models to choose one dimension per iteration.

### Code is token-efficient

Python test code is dense — a 200-line test file contains far more scoreable content than 200 lines of prose. The 5000-word limit provides ample room for progressive improvement without hitting length constraints early.

### No canonical template

There is no single "good test suite" that all LLMs converge to. The specific combination of test cases, assertion patterns, fixture design, and error scenarios is project-specific and requires compositional reasoning rather than template recall.

### Chairman can evaluate by reading

Test function names, assertion specificity, mock setup patterns, fixture usage, and parametrize decorators are all visible in the text. The chairman (gpt-4o-mini) can score each dimension by reading the code — no execution required.

---

## Previous Tasks and Why They Failed

### Task 1: Persuasive Essay (1 KEEP, score 95 → plateau)

**Root causes:**
1. **Correlated dimensions.** A persuasive essay's quality dimensions improve together. One good rewrite fixes most of them simultaneously.
2. **Strong LLM prior.** All frontier LLMs converge to the same "good essay" template.
3. **Tight word limit.** Limited surface area for incremental improvement.
4. **Calibration mismatch.** The weak starting draft caused an enormous first jump to 95.

### Task 2: Technical Tutorial (2 KEEPs in 48 iterations, 88 → 94 → 96)

**Root causes:**
1. **Off-topic starting artifact.** The `artifact_initial.md` was a vague 300-word essay about autoresearch/council, while `program.md` asked for a tutorial on LLM evaluation loops. Models wrote from scratch instead of improving incrementally.
2. **First-iteration rewrite scored 88.** With the starting artifact being off-topic, the first proposal was essentially a complete rewrite, immediately near ceiling.
3. **Binary dimensions.** CORRECTNESS and COMPLETENESS are nearly binary — the code either runs or it doesn't, the steps are either present or missing. These maxed out in 1–2 iterations.
4. **Threshold bug.** `IMPROVEMENT_THRESHOLD = 1` with strict `>` meant `score > best + 1` required +2 minimum. Iteration 4 scored 95 (vs best of 94) but was rejected: `95 > 94 + 1 → 95 > 95 → False`.

**Key lesson:** The starting artifact must be **on-topic** and **recognizable** so that models improve it incrementally rather than replacing it wholesale. And scoring dimensions must have **continuous, layered** improvement paths, not binary pass/fail.

---

## Why the Test Suite Task Produces Progressive Improvement

### Five orthogonal dimensions

| Dimension | 0–20 pts | Independent from |
|-----------|----------|-----------------|
| **Case coverage** | All CRUD ops? Edge cases? Success + failure? | Isolation, maintainability |
| **Assertion quality** | Specific field checks? Descriptive messages? | Case coverage, isolation |
| **Isolation** | Mocked HTTP? Fixtures? No shared state? | Assertion quality, error handling |
| **Error handling** | Timeouts, 4xx, 5xx, malformed JSON tested? | Case coverage, maintainability |
| **Maintainability** | Descriptive names? Fixtures? Parametrize? | Isolation, error handling |

### Example of orthogonality in practice

- A test suite can have great case coverage (15 test functions) but terrible isolation (all tests make real HTTP calls). Fixing isolation requires restructuring the entire file — a separate, large change.
- A suite can have perfect mocking (isolation=18) but only test `create` and `get` (case coverage=10). Adding `update`, `delete`, and `list` tests is independent work.
- A suite can test all error codes (error handling=17) but use generic names like `test1`, `test2` (maintainability=8). Renaming functions and adding docstrings is cosmetic, not structural.

Each dimension requires different work. Improving one does not automatically improve others. Some improvements even compete for attention within a single iteration.

### Why LLMs cannot converge in one iteration

1. **Combinatorial test space.** There are 20+ distinct test cases that could be written. No model writes all of them in one pass — they prioritize some and miss others.
2. **Refactoring vs. adding.** Introducing `respx` mocking restructures the entire file. Adding parametrize decorators is a different kind of change. These compete for model attention.
3. **Word budget pressure.** At 300 lines max, models must choose between breadth (more tests) and depth (better assertions, fixtures, docstrings). Different models make different tradeoffs.
4. **No template recall.** Unlike essays or tutorials, there is no standard "good test suite" in training data for this specific API. Models must compose from first principles.

---

## Starting Artifact Design

The starting artifact is calibrated at approximately **50 / 100**.

### Design principles
- **On-topic**: It is clearly a pytest test file for the TaskClient API — models will improve it, not rewrite from scratch
- **Recognizable but flawed**: Has the right structure (imports, test functions, assertions) but specific weaknesses per dimension
- **Specific, targetable gaps**: Each dimension has clear, independent deficiencies that a model can address in one iteration

### Target scores at baseline

| Dimension | Target | Specific weaknesses |
|-----------|--------|-------------------|
| Case coverage | 10/20 | Only tests `create` and `get`. No `update`, `delete`, or `list` with filters. No edge cases (empty list, pagination, create with minimal fields). |
| Assertion quality | 12/20 | Uses `assert result is not None` and `assert result` instead of checking specific fields. No assertion messages. Only checks key existence, not values. |
| Isolation | 8/20 | Makes real HTTP calls (no mocking). Tests depend on execution order via `global created_id`. Module-level mutable state. Client re-created in every test. |
| Error handling | 10/20 | One 404 test using bare `except Exception`. No timeout, 5xx, auth, rate limit, or malformed response tests. |
| Maintainability | 10/20 | Functions named `test1`–`test4`. No fixtures. Duplicated client construction. Generic docstrings. No parametrize. |
| **Total** | **~50/100** | Well below ceiling; multiple clear, independent improvement paths |

### Why ~50 is the right starting point

At 50/100, the first iteration should score approximately **55–62** — a genuine improvement but not a ceiling hit. With 5 orthogonal dimensions each having 10+ points of headroom, the improvement arc extends across 10–15 KEEPs:

```
Iter 1:  KEEP  ~57  (renames test functions, adds basic respx mocking)
Iter 3:  KEEP  ~63  (adds update and delete test cases)
Iter 5:  KEEP  ~69  (adds timeout and 5xx error tests)
Iter 7:  KEEP  ~74  (improves assertions — checks specific field values)
Iter 10: KEEP  ~80  (adds parametrize for priority values, fixtures)
Iter 13: KEEP  ~85  (adds rate limit test, pagination test, edge cases)
Iter 16: KEEP  ~89  (polishes maintainability, adds docstrings)
Iter 19: KEEP  ~92  (fine-tuning across all dimensions)
```

---

## Configuration Changes

| Setting | Previous | Current | Reason |
|---------|----------|---------|--------|
| `IMPROVEMENT_THRESHOLD` | 1 | 0 | The old threshold used strict `>`: `score > best + 1` required +2. With threshold=0, any strict improvement (`score > best`) is a KEEP. At high scores, +1 is genuine progress. |
| `MAX_ARTIFACT_WORDS` | 3000 | 5000 | Code artifacts are denser than prose. 5000 words accommodates a 200–300 line test file without hitting the limit prematurely. |
| `SCORING_DIMENSIONS` | Tutorial-specific (CORRECTNESS, COMPLETENESS, CLARITY, CODE_QUALITY, DEPTH) | Test-suite-specific (CASE_COVERAGE, ASSERTION_QUALITY, ISOLATION, ERROR_HANDLING, MAINTAINABILITY) | Dimensions must match the evaluation criteria in program.md. |

---

## The Deeper Point

The persuasive essay was too easy. The tutorial was the right idea but miscalibrated. The test suite task succeeds where they failed because:

1. **On-topic starting artifact** prevents first-iteration rewrite (the #1 failure mode)
2. **Combinatorial improvement space** prevents single-iteration convergence
3. **Structural vs. content tension** forces models to choose one improvement per iteration
4. **Continuous dimensions** (not binary) provide a smooth gradient from 50 to 95

The council is exploring a multi-dimensional quality space where each dimension has many independent improvement steps. This is exactly the kind of problem where iterative hill-climbing should produce a visible, gradual climb.
