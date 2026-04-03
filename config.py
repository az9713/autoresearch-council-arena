import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_TIMEOUT = 120  # seconds per model call

# --- Council models ---
# One per axis: analytical, creative, fast/broad, contrarian/open-source
# All available via OpenRouter (single API key).
# Swap any model by editing this list — no other code changes needed.
COUNCIL_MODELS = [
    "meta-llama/llama-4-maverick",              # A — open-source / diverse perspective
    "anthropic/claude-3-5-haiku",               # B — creative / nuanced
    "google/gemini-3.1-flash-lite-preview",     # C — fast / broad knowledge
    "x-ai/grok-3-mini-beta",                    # D — contrarian / reasoning
]

# Chairman synthesizes Stage 3. Must not appear in COUNCIL_MODELS (no conflict).
CHAIRMAN_MODEL = "openai/gpt-4o-mini"

# --- Experiment loop ---
IMPROVEMENT_THRESHOLD = 0   # any strict score improvement is a KEEP (score > best_score)

# --- Scoring dimensions ---
# Each dimension is scored 0-20 by the chairman. They must sum to 100.
# Edit these to match the "Evaluation Criteria" section of program.md.
# The key (e.g. "CASE_COVERAGE") appears verbatim in the chairman prompt and response.
SCORING_DIMENSIONS = [
    ("CASE_COVERAGE",      "Does the test suite cover all CRUD operations (create, read, update, delete, list)? Are both success and failure paths tested? Are edge cases covered (empty list, not found, duplicate, pagination)?"),
    ("ASSERTION_QUALITY",  "Are assertions specific and meaningful? Do tests check response bodies, status codes, and side effects? Are error messages in assertions descriptive? No tautological assertions like 'assert result is not None'?"),
    ("ISOLATION",          "Are tests properly isolated from external services? Is HTTP properly mocked (respx, unittest.mock, or responses)? Are fixtures used? Can tests run in any order? No shared mutable state between tests?"),
    ("ERROR_HANDLING",     "Does the suite test error scenarios: network timeouts, 4xx responses, 5xx responses, malformed JSON, rate limiting, authentication failures? Are exception types and messages checked?"),
    ("MAINTAINABILITY",    "Are tests well-organized with descriptive names? Are there helper fixtures to reduce duplication? Is parametrize used where appropriate? Are there docstrings for non-obvious tests? Is test data realistic?"),
]
EXPERIMENT_TIMEOUT = 300    # 5-minute wall-clock budget per iteration (matches autoresearch)
MAX_ARTIFACT_WORDS = 5000   # hard-reject proposals exceeding this (higher for code artifacts)
PLATEAU_WINDOW = 10         # warn after this many consecutive DISCARDs

# --- Cost limit ---
# Loaded from .env. Set to None to disable.
_cost_limit_str = os.getenv("COST_LIMIT_USD")
COST_LIMIT_USD: float | None = float(_cost_limit_str) if _cost_limit_str else None

