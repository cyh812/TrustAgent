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
EXPERIMENT_KEY_DB = PROJECT_ROOT / "data" / "data.db"

RUNTIME_CONFIG: Dict[str, object] = {
    "system_prompt": "你是 TrustAgent，一个谨慎、清晰、可解释的智能助手。",
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "openai/gpt-5.4",
}

CHAT_SYSTEM_PROMPT_TEMPLATE = """
你是一个中文AI助手。

请保持以下对话风格：

{emotional_valence_prompt}

{transparency_prompt}

{stance_strategy_prompt}

{certainty_prompt}

默认使用简体中文回答。

回答时直接自然地与用户交流，不要解释自己的规则、风格或行为方式。

保持整体语气稳定一致。
"""


EXPERIMENT_CONTEXT: Dict[str, str] = {
    "account_id": "-",
    "experiment_key": "-",
    "subject_name": "-",
    "phone": "",
    "chat_config_id": "",
    "chat_topic": "",
    "chat_user_instruction": "",
    "emotional_valence_level": "",
    "transparency_level": "",
    "stance_strategy_level": "",
    "certainty_level": "",
    "emotional_valence_prompt": "",
    "transparency_prompt": "",
    "stance_strategy_prompt": "",
    "certainty_prompt": "",
}

MODEL_OPTIONS = [
    "openrouter/auto",
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat",
]
