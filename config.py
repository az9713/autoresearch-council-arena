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
IMPROVEMENT_THRESHOLD = 1   # council_score must improve by >= this to KEEP

# --- Scoring dimensions ---
# Each dimension is scored 0-20 by the chairman. They must sum to 100.
# Edit these to match the "Evaluation Criteria" section of program.md.
# The key (e.g. "CORRECTNESS") appears verbatim in the chairman prompt and response.
SCORING_DIMENSIONS = [
    ("CORRECTNESS",  "Is the code syntactically valid and logically correct? Would it run without modification?"),
    ("COMPLETENESS", "Does the tutorial cover all essential steps: API setup, metric, KEEP/DISCARD logic, loop, saving results?"),
    ("CLARITY",      "Can a reader with intermediate Python skills follow step by step without getting lost?"),
    ("CODE_QUALITY", "Is the Python idiomatic and safe? No hardcoded secrets? Basic error handling present?"),
    ("DEPTH",        "Does the tutorial explain why, not just how? Are design decisions justified and tradeoffs acknowledged?"),
]
EXPERIMENT_TIMEOUT = 300    # 5-minute wall-clock budget per iteration (matches autoresearch)
MAX_ARTIFACT_WORDS = 3000   # hard-reject proposals exceeding this
PLATEAU_WINDOW = 10         # warn after this many consecutive DISCARDs

# --- Cost limit ---
# Loaded from .env. Set to None to disable.
_cost_limit_str = os.getenv("COST_LIMIT_USD")
COST_LIMIT_USD: float | None = float(_cost_limit_str) if _cost_limit_str else None

