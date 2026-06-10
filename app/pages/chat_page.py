import gradio as gr

from app.services.experiment_service import (
    confirm_custom_chat_rating_or_save,
    initialize_custom_chat_window,
    initialize_custom_chat_session,
    render_custom_chat,
    respond_custom_chat,
)
from app.services.key_service import current_time_text
from app.styles import EXPERIMENT_CSS


def build_chat_demo():
    with gr.Blocks(title="聊天 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        chat_records_state = gr.State([])
        chat_llm_history_state = gr.State([])
        chat_started_at_state = gr.State("")
        chat_context_state = gr.State({})

        with gr.Row(elem_classes=["task-header"]):
            with gr.Column(elem_classes=["top-title"]):
                gr.Markdown("# 可信智能体实验 - 聊天")

        with gr.Column(elem_classes=["chat-panel", "free-chat-workspace"]):
            chat_window = gr.HTML(
                value=render_custom_chat([]),
                elem_id="custom-chat-window",
            )

            with gr.Row(visible=False, elem_classes=["trust-end-row"]) as trust_rating_row:
                trust_score = gr.Radio(
                    choices=[str(i) for i in range(1, 8)],
                    value=None,
                    label="请你对当前LLM Agent表现所产生的信任感水平进行打分",
                    visible=False,
                    interactive=True,
                    elem_classes=["custom-trust-radio"],
                    scale=8,
                )
                confirm_trust_score_btn = gr.Button(
                    "确认打分",
                    variant="primary",
                    visible=False,
                    scale=2,
                    elem_classes=["trust-end-btn"],
                )

            with gr.Group(elem_classes=["composer-wrap"]):
                chat_message = gr.Textbox(
                    placeholder="输入消息后点击发送按钮。",
                    elem_id="composer",
                    lines=2,
                    container=True,
                )
                chat_send_btn = gr.Button(
                    "\u27a4",
                    variant="primary",
                    elem_classes=["send-inside-btn"],
                )
            save_status = gr.Markdown("")
            redirect_html = gr.HTML("")

        chat_message.submit(
            respond_custom_chat,
            inputs=[chat_message, chat_records_state, chat_llm_history_state, chat_context_state, trust_score],
            outputs=[
                chat_message,
                chat_window,
                chat_records_state,
                chat_llm_history_state,
                chat_message,
                chat_send_btn,
                trust_score,
                confirm_trust_score_btn,
                trust_rating_row,
            ],
            concurrency_limit=8,
        )
        chat_send_btn.click(
            respond_custom_chat,
            inputs=[chat_message, chat_records_state, chat_llm_history_state, chat_context_state, trust_score],
            outputs=[
                chat_message,
                chat_window,
                chat_records_state,
                chat_llm_history_state,
                chat_message,
                chat_send_btn,
                trust_score,
                confirm_trust_score_btn,
                trust_rating_row,
            ],
            concurrency_limit=8,
        )
        confirm_trust_score_btn.click(
            confirm_custom_chat_rating_or_save,
            inputs=[
                trust_score,
                chat_records_state,
                chat_llm_history_state,
                chat_started_at_state,
                chat_context_state,
            ],
            outputs=[
                chat_window,
                chat_records_state,
                chat_llm_history_state,
                chat_message,
                chat_send_btn,
                trust_score,
                confirm_trust_score_btn,
                trust_rating_row,
                save_status,
                redirect_html,
            ],
        )
        demo.load(
            current_time_text,
            outputs=[chat_started_at_state],
        )
        demo.load(
            initialize_custom_chat_session,
            inputs=[chat_records_state],
            outputs=[chat_context_state, chat_window],
        )

    return demo
