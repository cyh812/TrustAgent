import os
import sys
from pathlib import Path
from typing import Dict

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

APP_TITLE = "TrustAgent 实验系统"
DEFAULT_EXPERIMENT_KEYS = set()
EXPERIMENT_KEY_DB = PROJECT_ROOT / "data" / "experiment_keys.db"

RUNTIME_CONFIG: Dict[str, object] = {
    "system_prompt": "你是 TrustAgent，一个谨慎、清晰、可解释的智能助手。",
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "openrouter/auto",
}

EXPERIMENT_CONTEXT: Dict[str, str] = {
    "subject_name": "-",
}

MODEL_OPTIONS = [
    "openrouter/auto",
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat",
]
