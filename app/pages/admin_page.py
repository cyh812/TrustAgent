import gradio as gr

from app.services.key_service import (
    KEY_TABLE_COLUMNS,
    generate_experiment_keys,
    refresh_key_admin_view,
)
from app.styles import ADMIN_CSS


def build_admin_demo():
    with gr.Blocks(title="管理 - TrustAgent") as demo:
        gr.HTML(f"<style>{ADMIN_CSS}</style>")
        gr.Markdown("# 后台管理")
        gr.Markdown("[前往登录页](/login) | [前往实验页](/experiment)")

        gr.Markdown("## 一次性实验密钥")

        with gr.Row():
            key_count = gr.Slider(
                label="生成数量",
                minimum=1,
                maximum=500,
                value=10,
                step=1,
            )
            key_prefix = gr.Textbox(
                label="密钥前缀（可选）",
                value="TA",
                placeholder="例如 TA",
            )

        with gr.Row():
            generate_btn = gr.Button("生成密钥", variant="primary")
            refresh_btn = gr.Button("刷新列表", variant="secondary")

        key_action_result = gr.Markdown("等待操作。")
        key_summary, initial_rows = refresh_key_admin_view()
        key_summary_box = gr.Markdown(key_summary)
        key_table = gr.Dataframe(
            headers=KEY_TABLE_COLUMNS,
            value=initial_rows,
            interactive=False,
            label="密钥列表",
        )

        generate_btn.click(
            generate_experiment_keys,
            inputs=[key_count, key_prefix],
            outputs=[key_action_result, key_table],
        ).then(
            refresh_key_admin_view,
            outputs=[key_summary_box, key_table],
        )

        refresh_btn.click(
            refresh_key_admin_view,
            outputs=[key_summary_box, key_table],
        )

    return demo
