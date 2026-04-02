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
    "openai/gpt-4o",                    # analytical / structured
    "anthropic/claude-sonnet-4",        # creative / nuanced
    "google/gemini-2.5-flash-preview",  # fast / broad knowledge
    "meta-llama/llama-4-maverick",      # contrarian / open-source
]

# Chairman synthesizes Stage 3. Defaults to the strongest writer.
CHAIRMAN_MODEL = "anthropic/claude-sonnet-4"

# --- Experiment loop ---
IMPROVEMENT_THRESHOLD = 2   # council_score must improve by >= this to KEEP
EXPERIMENT_TIMEOUT = 300    # 5-minute wall-clock budget per iteration (matches autoresearch)
MAX_ARTIFACT_WORDS = 3000   # hard-reject proposals exceeding this
PLATEAU_WINDOW = 10         # warn after this many consecutive DISCARDs
