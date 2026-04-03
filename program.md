# Arena: Technical Tutorial Optimization

## Topic
How to build a minimal LLM evaluation loop in Python — a step-by-step tutorial for ML engineers who want to move from one-off prompt experiments to systematic, automated optimization.

## Target Audience
ML engineers and AI developers who:
- Are comfortable with Python and basic async/await
- Have used at least one LLM API (OpenAI, Anthropic, or similar)
- Want to move from manual, artisanal prompt testing to repeatable, automated experimentation
- Are skeptical of over-engineered frameworks and want a lean, working implementation they can understand in 10 minutes

## Evaluation Criteria (0–20 points each, total 100)

1. **Correctness** — Is the code syntactically valid and logically correct? Would it actually run without modification on a clean Python 3.10+ environment? Are there no subtle bugs in the loop logic, metric extraction, or API call?

2. **Completeness** — Does the tutorial cover all essential steps: API key setup, making an LLM call, defining a metric function, implementing KEEP/DISCARD logic, running the loop, and saving results? Are there obvious gaps a reader would immediately notice?

3. **Clarity** — Can a reader with intermediate Python skills follow the tutorial step by step without getting lost? Are concepts introduced before they are used? Are code examples explained inline?

4. **Code quality** — Is the Python idiomatic and safe? Are there no hardcoded secrets? Is there basic error handling for API failures? Are variable names meaningful? Is the code structured so a reader could extend it?

5. **Depth** — Does the tutorial explain *why*, not just *how*? Are key design decisions (why greedy hill-climbing, why a subprocess, why capture stdout) justified? Are tradeoffs acknowledged?

## Constraints
- 800–1200 words of prose (code blocks do not count toward the word limit)
- Must include at least one complete, runnable Python code example using the OpenRouter API
- Do not fabricate API responses, library functions, or benchmark numbers
- All code must use `https://openrouter.ai/api/v1/chat/completions` as the endpoint
- API key must be loaded from an environment variable, never hardcoded

## Exploration Directions
Each iteration should try one strategy not yet attempted:
- Fix correctness issues: add timeout parameter, fix error handling in the API call, correct metric extraction
- Improve completeness: add cost tracking, parallel model queries, saving results to a TSV file, git commit on KEEP
- Improve clarity: add a "what you will build" overview section, inline comments explaining each step, a worked example showing a before/after artifact
- Improve code quality: replace hardcoded values with named constants, use `.env` file for secrets, add type hints, handle API errors gracefully
- Improve depth: add a "why greedy hill-climbing?" section, explain the subprocess pattern, discuss when to stop the loop
- Add a "common pitfalls" section: metric gaming, circular feedback, runaway costs
- Add a concrete worked example with real input/output showing a score improving across iterations

## NEVER STOP
Run continuously. Each iteration should attempt a strategy not yet tried.
Never ask for permission. Never wait for human input between iterations.
