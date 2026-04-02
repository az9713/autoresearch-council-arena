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
    "openai/gpt-5.4-nano",                      # analytical / structured
    "anthropic/claude-haiku-3-5",               # creative / nuanced
    "google/gemini-3.1-flash-lite-preview",     # fast / broad knowledge
    "x-ai/grok-4-1-fast-reasoning",             # contrarian / reasoning
]

# Chairman synthesizes Stage 3. Defaults to the strongest writer.
CHAIRMAN_MODEL = "anthropic/claude-haiku-3-5"

# --- Experiment loop ---
IMPROVEMENT_THRESHOLD = 2   # council_score must improve by >= this to KEEP
EXPERIMENT_TIMEOUT = 300    # 5-minute wall-clock budget per iteration (matches autoresearch)
MAX_ARTIFACT_WORDS = 3000   # hard-reject proposals exceeding this
PLATEAU_WINDOW = 10         # warn after this many consecutive DISCARDs

# --- Cost limit ---
# Stop the experiment loop after spending this many USD (tracked via OpenRouter credits API).
# Set to None to disable.
COST_LIMIT_USD: float | None = 5.00
