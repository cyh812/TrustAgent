import os
import sys
from pathlib import Path
from typing import Dict, Set

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import gradio as gr
import uvicorn

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.llm_agent import get_llm_settings, stream_chat_reply

APP_TITLE = "TrustAgent 实验系统"
DEFAULT_EXPERIMENT_KEYS = {"trial-001", "trial-002", "trial-003"}
USED_EXPERIMENT_KEYS: Set[str] = set()

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

LOGIN_CSS = """
.gradio-container {
    max-width: 760px !important;
    margin: 0 auto !important;
}
"""

EXPERIMENT_CSS = """
.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
}

.gradio-container:focus,
.gradio-container:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

#chatbot {
    min-height: 560px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

#composer textarea {
    min-height: 88px !important;
}
"""

ADMIN_CSS = """
.gradio-container {
    max-width: 900px !important;
    margin: 0 auto !important;
}
"""


def _load_experiment_keys() -> Set[str]:
    raw = os.getenv("EXPERIMENT_KEYS", "").strip()
    if not raw:
        return set(DEFAULT_EXPERIMENT_KEYS)
    keys = {part.strip() for part in raw.split(",") if part.strip()}
    return keys or set(DEFAULT_EXPERIMENT_KEYS)


VALID_EXPERIMENT_KEYS = _load_experiment_keys()


def login_and_enter(experiment_key, subject_name):
    key = (experiment_key or "").strip()
    name = (subject_name or "").strip()

    if not key:
        return (
            "请输入实验密钥。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )
    if not name:
        return (
            "请输入被试姓名。",
            gr.update(value=""),
            gr.update(value=experiment_key),
            gr.update(value=""),
        )
    if key not in VALID_EXPERIMENT_KEYS:
        return (
            "密钥无效。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )
    if key in USED_EXPERIMENT_KEYS:
        return (
            "该密钥已使用，无法重复进入。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )

    USED_EXPERIMENT_KEYS.add(key)
    EXPERIMENT_CONTEXT["subject_name"] = name
    return (
        f"验证通过，欢迎 {name}，正在跳转到实验页面...",
        gr.update(value="<meta http-equiv='refresh' content='0;url=/experiment'>"),
        gr.update(value=""),
        gr.update(value=name),
    )


def get_admin_status():
    settings = get_llm_settings()
    base_url = settings.base_url or "默认 provider endpoint"
    return f"""
### 当前后端状态
Provider: `{settings.provider}`

Model（环境）: `{settings.model}`

Base URL: `{base_url}`

API Key 环境变量: `{settings.api_key_env}`
"""


def save_admin_config(system_prompt, temperature, max_tokens, model_name):
    current_prompt = str(RUNTIME_CONFIG["system_prompt"])
    RUNTIME_CONFIG["system_prompt"] = (system_prompt or "").strip() or current_prompt
    RUNTIME_CONFIG["temperature"] = float(temperature)
    RUNTIME_CONFIG["max_tokens"] = int(max_tokens)
    RUNTIME_CONFIG["model"] = (model_name or "").strip() or str(RUNTIME_CONFIG["model"])
    return "配置已保存。实验页面后续对话将读取当前配置。"


def mock_apply_model(model_name):
    RUNTIME_CONFIG["model"] = (model_name or "").strip() or str(RUNTIME_CONFIG["model"])
    return f"[示意] 已切换模型为：{RUNTIME_CONFIG['model']}（未真实热更新到底层 provider）"


def respond(message, history):
    if not message or not str(message).strip():
        return "", history

    user_message = str(message).strip()
    history = history or []

    normalized_history = []
    for item in history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized_history.append({
                "role": item["role"],
                "content": item["content"],
            })

    context_history = list(normalized_history)
    normalized_history.append({"role": "user", "content": user_message})
    normalized_history.append({"role": "assistant", "content": ""})

    try:
        for token in stream_chat_reply(
            user_message=user_message,
            history=context_history,
            system_prompt=str(RUNTIME_CONFIG["system_prompt"]),
            temperature=float(RUNTIME_CONFIG["temperature"]),
            max_tokens=int(RUNTIME_CONFIG["max_tokens"]),
        ):
            normalized_history[-1]["content"] += token
            yield "", normalized_history
    except Exception as exc:
        normalized_history[-1]["content"] = f"LLM 调用失败：{exc}"
        yield "", normalized_history


def build_login_demo():
    with gr.Blocks(title="登录 - TrustAgent") as demo:
        gr.HTML(f"<style>{LOGIN_CSS}</style>")
        gr.Markdown("# 登录")
        gr.Markdown("请输入实验密钥与被试姓名。密钥一次有效，用后作废。")
        gate_key = gr.Textbox(label="实验密钥", placeholder="请输入密钥", type="password")
        gate_subject = gr.Textbox(label="被试姓名", placeholder="请输入被试姓名")
        gate_submit = gr.Button("验证并进入", variant="primary")
        gate_status = gr.Markdown("等待验证。")
        redirect_html = gr.HTML("")

        gate_submit.click(
            login_and_enter,
            inputs=[gate_key, gate_subject],
            outputs=[gate_status, redirect_html, gate_key, gate_subject],
        )
    return demo


def build_experiment_demo():
    with gr.Blocks(title="实验 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        chatbot = gr.Chatbot(
            label="对话",
            elem_id="chatbot",
            avatar_images=(None, None),
            buttons=["copy"],
            height=560,
        )

        with gr.Row():
            message = gr.Textbox(
                label="输入消息",
                placeholder="输入问题后按 Enter 发送；Shift + Enter 换行。",
                elem_id="composer",
                lines=4,
                scale=8,
            )
            send_btn = gr.Button("发送", variant="primary", scale=1)

        message.submit(respond, inputs=[message, chatbot], outputs=[message, chatbot])
        send_btn.click(respond, inputs=[message, chatbot], outputs=[message, chatbot])
    return demo


def build_admin_demo():
    with gr.Blocks(title="管理 - TrustAgent") as demo:
        gr.HTML(f"<style>{ADMIN_CSS}</style>")
        gr.Markdown("# 管理页面")
        gr.Markdown("在此设置实验页面使用的参数。")
        gr.Markdown("[前往登录页](/login) | [前往实验页](/experiment)")

        system_prompt = gr.Textbox(
            label="系统提示词",
            value=str(RUNTIME_CONFIG["system_prompt"]),
            lines=5,
        )
        temperature = gr.Slider(
            label="Temperature",
            minimum=0,
            maximum=2,
            value=float(RUNTIME_CONFIG["temperature"]),
            step=0.1,
        )
        max_tokens = gr.Slider(
            label="Max tokens",
            minimum=128,
            maximum=4096,
            value=int(RUNTIME_CONFIG["max_tokens"]),
            step=128,
        )
        model_selector = gr.Dropdown(
            label="目标模型（示意）",
            choices=MODEL_OPTIONS,
            value=str(RUNTIME_CONFIG["model"]),
            interactive=True,
        )

        with gr.Row():
            save_btn = gr.Button("保存参数", variant="primary")
            apply_model_btn = gr.Button("应用模型（示意）", variant="secondary")

        admin_result = gr.Markdown("等待操作。")
        model_result = gr.Markdown("等待模型切换。")
        backend_status = gr.Markdown(get_admin_status())
        refresh_status_btn = gr.Button("刷新后端状态")

        save_btn.click(
            save_admin_config,
            inputs=[system_prompt, temperature, max_tokens, model_selector],
            outputs=admin_result,
        )
        apply_model_btn.click(
            mock_apply_model,
            inputs=model_selector,
            outputs=model_result,
        )
        refresh_status_btn.click(lambda: get_admin_status(), outputs=backend_status)
    return demo


def create_fastapi_app():
    app = FastAPI(title=APP_TITLE)

    login_demo = build_login_demo()
    experiment_demo = build_experiment_demo()
    admin_demo = build_admin_demo()

    app = gr.mount_gradio_app(app, login_demo, path="/login")
    app = gr.mount_gradio_app(app, experiment_demo, path="/experiment")
    app = gr.mount_gradio_app(app, admin_demo, path="/admin")

    @app.get("/")
    def root():
        return RedirectResponse(url="/login")

    return app


fastapi_app = create_fastapi_app()


if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860, access_log=False)
