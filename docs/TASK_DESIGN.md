# Task Design: Why This Task, Why This Artifact

This document explains the design of the current experiment task and the reasoning behind every choice — the topic, the scoring rubric, the starting artifact, and how they work together to produce observable hill-climbing behavior.

---

## The Task

**Write a step-by-step technical tutorial: "How to Build a Minimal LLM Evaluation Loop in Python."**

Target audience: ML engineers and AI developers who are comfortable with Python, have used LLM APIs, and want to move from one-off prompt experiments to systematic, automated optimization.

---

## Why This Topic

### Self-referential proof

The system running this experiment is itself a minimal LLM evaluation loop. A tutorial about this kind of system is the most honest artifact this council could produce — it demonstrates the thesis by example. The system improving a tutorial about systems like itself is the same self-referential proof the original persuasive essay was attempting, but grounded in concrete implementation detail rather than rhetoric.

### Audience alignment

The target audience (ML engineers) is the same audience that would use this system. Every improvement the council makes to the tutorial is directly useful to the people most likely to read it. This is not a toy task.

### Practical testability

Unlike persuasive writing, technical accuracy is checkable. "Does this code run?" has a binary answer. "Is the metric extraction pattern correct?" can be verified. This grounds the evaluation in something more objective than rhetorical taste.

---

## Why the Previous Task (Persuasive Essay) Failed to Show Progressive Improvement

The original `program.md` asked for a persuasive essay. That task produced 1 KEEP (score=95) followed by 8 consecutive DISCARDs. This was not a system failure — it was a task design failure.

**Root causes:**

1. **Correlated dimensions.** A persuasive essay's quality dimensions (ethos, pathos, logos, structure, evidence) improve together. One good rewrite fixes most of them simultaneously. The council scored 95 on the first iteration because a competent model can produce a near-complete persuasive essay in one pass.

2. **Strong LLM prior.** All frontier LLMs have been trained on the same corpus of high-quality persuasive writing. They converge to the same "good essay" template, so subsequent proposals are similar and the chairman quickly identifies diminishing returns.

3. **Tight word limit.** At 1500 words, a short essay has limited surface area. There is only so much that can be improved before the council is rearranging the same ideas.

4. **Calibration mismatch.** The starting artifact was deliberately weak (the "weak draft"), which caused an enormous first jump. The bar was set at 95 in one step, leaving almost no headroom.

The persuasive essay task is not wrong — it is wrong *for demonstrating hill-climbing*. It is too easy to do well and too hard to do better.

---

## Why the Tutorial Task Produces Progressive Improvement

A technical tutorial has five dimensions that are **orthogonal** — independently improvable without necessarily affecting the others:

| Dimension | 0–20 pts | Can be improved without touching |
|-----------|----------|----------------------------------|
| **Correctness** | Code runs without error | Clarity, depth |
| **Completeness** | All essential steps covered | Code quality, depth |
| **Clarity** | Reader can follow step by step | Correctness, depth |
| **Code quality** | Idiomatic Python, no hardcoded secrets | Completeness, clarity |
| **Depth** | Explains *why*, not just *how* | Correctness, completeness |

**Example of orthogonality in practice:**
- A tutorial can have correct, runnable code (Correctness=18) but skip cost tracking entirely (Completeness=8).
- It can be complete and well-explained (Clarity=17) but use hardcoded API keys (Code quality=6).
- It can explain every design decision in depth (Depth=16) but have a buggy retry loop (Correctness=9).

Each iteration of the council can plausibly improve exactly one dimension by 3–5 points without moving others. A run of 10 iterations can show a genuine climb from ~55 → 75 → 85 → 90+.

**Why LLMs don't converge immediately:**
Frontier models do not have a shared "perfect tutorial" template the way they have a shared "good essay" template. The ideal tutorial depends on the specific API, the specific audience, the specific tradeoffs — details that require the council to reason about the task rather than recall a template.

---

## Starting Artifact Design

The starting artifact is calibrated at approximately **50–55 / 100**.

**Design principles:**
- Correct enough to be a recognizable tutorial (not garbage)
- Incomplete enough that several dimensions are clearly missing
- Code that works for the happy path but fails silently on errors
- Explanations that describe *what* without explaining *why*
- No discussion of cost, timeouts, or production concerns

**Target scores at baseline:**

| Dimension | Target | Rationale |
|-----------|--------|-----------|
| Correctness | 12/20 | Core loop works; error handling absent |
| Completeness | 10/20 | Basic steps covered; cost tracking, git, parallel calls missing |
| Clarity | 13/20 | Readable but jumps into code without context |
| Code quality | 8/20 | Hardcoded API key; no type hints; no error handling |
| Depth | 7/20 | "What's next" is a bullet list, not a rationale |
| **Total** | **~50/100** | Well below ceiling; multiple clear improvement paths |

This calibration ensures the first iteration scores ~65 (not 95), leaving a long improvement arc.

---

## Configuration Changes

These `config.py` values accompany the new task:

| Setting | Old | New | Reason |
|---------|-----|-----|--------|
| `IMPROVEMENT_THRESHOLD` | 2 | 1 | At high scores, +1 is real progress |

A threshold of 2 made sense when the artifact could jump from 60 → 80 in one step. At fine-grained scores of 85–92, a +1 improvement is genuine and should be KEETed.

---

## What a Healthy Run Looks Like

```
Iter 1:  KEEP  score=64   winner=C  (improved clarity + basic structure)
Iter 2:  DISCARD score=62  winner=D  (code change regressed completeness)
Iter 3:  KEEP  score=68   winner=A  (added error handling → code quality +4)
Iter 4:  DISCARD score=67  winner=B
Iter 5:  KEEP  score=72   winner=C  (added cost tracking → completeness +5)
Iter 6:  DISCARD score=70
Iter 7:  KEEP  score=76   winner=D  (explained design decisions → depth +6)
...
Iter 15: KEEP  score=88   winner=A  (near ceiling; fine-grained polish)
```

Gradual slope. Multiple dimensions improving in sequence. The council explores the space rather than converging in one step.

---

## The Deeper Point

The persuasive essay asked the council to produce good writing. The tutorial asks the council to produce good *teaching* — a harder, more compositional task where quality accumulates across multiple distinct attributes. This is the kind of task where multi-model councils have a genuine advantage over single-model iteration: different models have different strengths (one writes cleaner code, one explains concepts more clearly, one catches missing edge cases), and those strengths map directly onto the orthogonal scoring dimensions.

The council is not just iterating — it is exploring a multi-dimensional quality space, one dimension at a time.
