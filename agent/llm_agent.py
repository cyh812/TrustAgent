import os
import inspect
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    base_url: Optional[str]
    api_key_env: str


def _load_dotenv_if_exists() -> None:
    """Load simple KEY=VALUE pairs from project .env into process env once."""
    if os.getenv("_TRUSTAGENT_DOTENV_LOADED") == "1":
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        os.environ["_TRUSTAGENT_DOTENV_LOADED"] = "1"
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value

    os.environ["_TRUSTAGENT_DOTENV_LOADED"] = "1"


def _read_env(primary_key: str, fallback_key: Optional[str] = None, default: Optional[str] = None):
    value = os.getenv(primary_key)
    if value is None and fallback_key:
        value = os.getenv(fallback_key)
    if value is None:
        return default
    return value


def get_llm_settings() -> LLMSettings:
    """Read LLM settings from environment variables."""
    _load_dotenv_if_exists()
    provider = (
        _read_env("LLM_PROVIDER", "TRUSTAGENT_LLM_PROVIDER", "openrouter")
        .strip()
        .lower()
    )

    if provider == "openrouter":
        return LLMSettings(
            provider=provider,
            model=_read_env("OPENROUTER_MODEL", "TRUSTAGENT_LLM_MODEL", "openrouter/auto"),
            base_url=_read_env("OPENROUTER_BASE_URL", "OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key_env="OPENROUTER_API_KEY",
        )

    if provider == "deepseek":
        return LLMSettings(
            provider=provider,
            model=_read_env("TRUSTAGENT_LLM_MODEL", default="deepseek-chat"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key_env="DEEPSEEK_API_KEY",
        )

    return LLMSettings(
        provider=provider,
        model=_read_env("TRUSTAGENT_LLM_MODEL", default="gpt-4o-mini"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        api_key_env="OPENAI_API_KEY",
    )


def _build_chat_model(temperature: float, max_tokens: int):
    settings = get_llm_settings()
    api_key = os.getenv(settings.api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing environment variable: {settings.api_key_env}")

    model_kwargs = {
        "model": settings.model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "streaming": True,
    }

    if settings.provider == "openrouter":
        try:
            from langchain_openrouter import ChatOpenRouter

            ctor_params = inspect.signature(ChatOpenRouter.__init__).parameters
            kwargs = dict(model_kwargs)

            if "api_key" in ctor_params:
                kwargs["api_key"] = api_key
            elif "openrouter_api_key" in ctor_params:
                kwargs["openrouter_api_key"] = api_key

            if settings.base_url:
                if "base_url" in ctor_params:
                    kwargs["base_url"] = settings.base_url
                elif "openrouter_base_url" in ctor_params:
                    kwargs["openrouter_base_url"] = settings.base_url

            return ChatOpenRouter(**kwargs)
        except ImportError:
            pass

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        if settings.provider == "openrouter":
            raise RuntimeError(
                "Missing dependency for OpenRouter. Install `langchain-openrouter` or "
                "`langchain-openai` (plus `langchain`)."
            ) from exc
        raise RuntimeError(
            "Missing dependency: install langchain-openai and langchain before using the LLM API."
        ) from exc

    return ChatOpenAI(
        **model_kwargs,
        api_key=api_key,
        base_url=settings.base_url,
    )


def _convert_history(history: List[Dict[str, str]], system_prompt: str, user_message: str):
    try:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: install langchain-core before using the LLM API."
        ) from exc

    messages = []
    if system_prompt and system_prompt.strip():
        messages.append(SystemMessage(content=system_prompt.strip()))

    for item in history or []:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_message))
    return messages


def stream_chat_reply(
    user_message: str,
    history: List[Dict[str, str]],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
) -> Iterable[str]:
    """Stream a chat response through the configured LangChain chat model."""
    messages = _convert_history(
        history=history,
        system_prompt=system_prompt,
        user_message=user_message,
    )
    first_token_timeout = _read_float_env("LLM_FIRST_TOKEN_TIMEOUT", 15.0)
    retry_count = _read_int_env("LLM_STREAM_RETRY_COUNT", 1)

    for attempt in range(retry_count + 1):
        token_seen = False
        token_queue: "queue.Queue[object]" = queue.Queue()

        def run_stream() -> None:
            try:
                llm = _build_chat_model(temperature=temperature, max_tokens=max_tokens)
                for chunk in llm.stream(messages):
                    content = getattr(chunk, "content", "")
                    if isinstance(content, str) and content:
                        token_queue.put(content)
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict):
                                text = part.get("text")
                                if text:
                                    token_queue.put(text)
                token_queue.put(None)
            except Exception as exc:
                token_queue.put(exc)

        threading.Thread(target=run_stream, daemon=True).start()

        while True:
            try:
                item = token_queue.get(timeout=first_token_timeout if not token_seen else None)
            except queue.Empty:
                if attempt < retry_count:
                    break
                raise TimeoutError(f"LLM first token timeout after {first_token_timeout:.1f}s")

            if item is None:
                return
            if isinstance(item, Exception):
                raise item

            token_seen = True
            yield str(item)

        # No token was produced before timeout. Retry by starting a fresh request.


def _read_float_env(name: str, default: float) -> float:
    _load_dotenv_if_exists()
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _read_int_env(name: str, default: int) -> int:
    _load_dotenv_if_exists()
    try:
        return max(0, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default
