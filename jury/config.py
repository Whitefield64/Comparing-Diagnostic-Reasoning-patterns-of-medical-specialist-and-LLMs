import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

# Multi-model jury: 5 voters per model
MODEL_LLAMA = "meta/llama-3.3-70b-instruct"
MODEL_GEMMA = "google/gemma-4-31b-it"
MODEL_MISTRAL = "mistralai/mistral-small-4-119b-2603"

def get_model_for_voter(voter_id: int) -> str:
    """
    Map voter ID to model:
    - voters 1-5: Llama
    - voters 6-10: Gemma
    - voters 11-15: Mistral
    """
    if 1 <= voter_id <= 5:
        return MODEL_LLAMA
    elif 6 <= voter_id <= 10:
        return MODEL_GEMMA
    else:  # 11-15
        return MODEL_MISTRAL

def get_model_short_name(voter_id: int) -> str:
    """
    Get short model name for annotator field (llama, gemma, mistral).
    """
    if 1 <= voter_id <= 5:
        return "llama"
    elif 6 <= voter_id <= 10:
        return "gemma"
    else:  # 11-15
        return "mistral"

# Jury parameters
N_VOTERS = int(os.environ.get("N_VOTERS", "15"))
TEMPERATURE = 0.7
MAX_TOKENS = 8192

# Rate limiting: stay within 40 req/min
RATE_LIMIT_PER_MINUTE = 40
CONCURRENCY_LIMIT = 40

# Batch stagger to reduce burst load on NVIDIA API
VOTER_BATCH_SIZE = int(os.environ.get("VOTER_BATCH_SIZE", "2"))  # voters per batch
VOTER_BATCH_DELAY = int(os.environ.get("VOTER_BATCH_DELAY", "15"))  # seconds between batches

# Offset resolver
FUZZY_MATCH_THRESHOLD = 90  # minimum rapidfuzz score (0-100)

# Label schema: name → numeric ID
LABEL_MAP: dict[str, int] = {
    "ABD_SELECTIVE": 1,
    "ABD_CREATIVE": 2,
    "ABD_VISUAL": 3,
    "ABD_CAUSAL": 4,
    "DED_HYPOTHETICO": 5,
    "DED_ALGORITHMIC": 6,
    "DED_HIERARCHICAL": 7,
    "DED_VALIDATION": 8,
    "IND_PATTERN": 9,
    "IND_INTUITION": 10,
    "IND_BAYESIAN": 11,
    "IND_CASEBASED": 12,
}
