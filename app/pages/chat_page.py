import gradio as gr

from app.services.experiment_service import render_custom_chat, respond_custom_chat
from app.services.key_service import current_time_text
from app.services.user_data_service import save_chat_record
from app.styles import EXPERIMENT_CSS


def build_chat_demo():
    with gr.Blocks(title="聊天 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        chat_records_state = gr.State([])
        chat_llm_history_state = gr.State([])
        chat_started_at_state = gr.State("")

        with gr.Row(elem_classes=["task-header"]):
            with gr.Column(scale=8, elem_classes=["top-title"]):
                gr.Markdown("# 可信智能体实验 - 聊天")
            with gr.Column(scale=2, min_width=160, elem_classes=["task-end-action"]):
                end_experiment_btn = gr.Button("结束实验", variant="stop")

        with gr.Column(elem_classes=["chat-panel", "free-chat-workspace"]):
            chat_window = gr.HTML(
                value=render_custom_chat([]),
                elem_id="custom-chat-window",
            )

            with gr.Group(elem_classes=["composer-wrap"]):
                chat_message = gr.Textbox(
                    placeholder="输入消息后按 Enter 发送；Shift + Enter 换行。",
                    elem_id="composer",
                    lines=2,
                    container=True,
                )
                chat_send_btn = gr.Button("➤", variant="primary", elem_classes=["send-inside-btn"])

            save_status = gr.Markdown("")

        chat_message.submit(
            respond_custom_chat,
            inputs=[chat_message, chat_records_state, chat_llm_history_state],
            outputs=[chat_message, chat_window, chat_records_state, chat_llm_history_state],
        )
        chat_send_btn.click(
            respond_custom_chat,
            inputs=[chat_message, chat_records_state, chat_llm_history_state],
            outputs=[chat_message, chat_window, chat_records_state, chat_llm_history_state],
        )
        end_experiment_btn.click(
            save_chat_record,
            inputs=[chat_records_state, chat_llm_history_state, chat_started_at_state],
            outputs=[save_status, chat_message, chat_send_btn, end_experiment_btn],
        )
        demo.load(
            current_time_text,
            outputs=[chat_started_at_state],
        )

    return demo
