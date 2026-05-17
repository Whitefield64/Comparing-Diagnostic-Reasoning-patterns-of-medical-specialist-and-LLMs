import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

_DEFAULT_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
GENERATION_MODELS = [
    model.strip()
    for model in os.environ.get("GENERATION_MODELS", _DEFAULT_MODEL).split(",")
    if model.strip()
]

GENERATION_TEMPERATURE = float(os.environ.get("GENERATION_TEMPERATURE", "0.7"))
GENERATION_MAX_TOKENS = int(os.environ.get("GENERATION_MAX_TOKENS", "8192"))
GENERATION_OUTPUT_DIR = Path(os.environ.get("GENERATION_OUTPUT_DIR", "cases_llm"))
GENERATION_MIN_WORDS = int(os.environ.get("GENERATION_MIN_WORDS", "1400"))
GENERATION_EXPANSION_ATTEMPTS = int(os.environ.get("GENERATION_EXPANSION_ATTEMPTS", "1"))

RATE_LIMIT_PER_MINUTE = int(os.environ.get("GENERATION_RATE_LIMIT_PER_MINUTE", "40"))
CONCURRENCY_LIMIT = int(os.environ.get("GENERATION_CONCURRENCY_LIMIT", "3"))
