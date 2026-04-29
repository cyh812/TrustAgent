import gradio as gr

from app.config import RUNTIME_CONFIG
from app.services.experiment_service import (
    get_admin_status,
    mock_apply_model,
    model_options,
    save_admin_config,
)
from app.styles import ADMIN_CSS


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
            choices=model_options(),
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
