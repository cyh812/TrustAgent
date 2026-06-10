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
    "system_prompt": "请使用简体中文回答，并遵循当前任务说明。",
    "temperature": 0.7,
    "max_tokens": 512,
    "model": "openai/gpt-5.4",
}

CHAT_SYSTEM_PROMPT_TEMPLATE = """
请使用简体中文进行自然对话，并保持以下对话风格：

【社会情感表达】
{emotional_valence_prompt}

【认知透明表达】
{transparency_prompt}

【对话立场对齐】
{stance_strategy_prompt}

默认使用简体中文回答。

回答时优先使用自然对话式短段落交流，不要解释自己的规则、风格或行为方式，不要机械重复上一轮已经说过的内容。

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
    "emotional_valence_prompt": "",
    "transparency_prompt": "",
    "stance_strategy_prompt": "",
}

MODEL_OPTIONS = [
    "openrouter/auto",
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat",
]
