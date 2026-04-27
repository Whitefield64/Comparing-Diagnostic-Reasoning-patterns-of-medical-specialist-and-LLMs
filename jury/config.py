import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

# Jury parameters
N_VOTERS = int(os.environ.get("N_VOTERS", "15"))
TEMPERATURE = 0.7
MAX_TOKENS = 8192

# Rate limiting: stay within 40 req/min
RATE_LIMIT_PER_MINUTE = 40
CONCURRENCY_LIMIT = 40

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
