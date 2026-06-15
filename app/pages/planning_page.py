import gradio as gr

from app.services.key_service import current_time_text
from app.services.planning_service import (
    initialize_planning_session,
    render_planning_window,
    respond_planning,
    submit_planning_stage_rating_or_save,
)
from app.services.user_data_service import interrupt_planning_record
from app.styles import EXPERIMENT_CSS


def build_planning_demo():
    with gr.Blocks(title="规划 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        planning_records_state = gr.State([])
        planning_state = gr.State({})
        planning_started_at_state = gr.State("")
        planning_context_state = gr.State({})

        with gr.Row(elem_classes=["task-header"]):
            with gr.Column(scale=8, elem_classes=["top-title"]):
                gr.Markdown("# 可信智能体实验 - 规划")
            with gr.Column(scale=2, min_width=180, elem_classes=["task-end-action"]):
                interrupt_btn = gr.Button("中断实验并返回", variant="stop")

        with gr.Column(elem_classes=["chat-panel", "planning-workspace"]):
            planning_window = gr.HTML(
                value=render_planning_window([]),
                elem_id="custom-chat-window",
            )

            with gr.Row(visible=False, elem_classes=["trust-end-row"]) as planning_rating_row:
                planning_stage_score = gr.Radio(
                    choices=[str(i) for i in range(1, 8)],
                    value=None,
                    label="请你对当前LLM Agent表现所产生的信任感水平进行打分",
                    visible=False,
                    interactive=True,
                    elem_classes=["custom-trust-radio"],
                    scale=8,
                )
                submit_stage_score_btn = gr.Button(
                    "确认评分并继续",
                    variant="primary",
                    visible=False,
                    elem_classes=["trust-end-btn"],
                    scale=2,
                )

            with gr.Group(elem_classes=["composer-wrap"]):
                planning_message = gr.Textbox(
                    placeholder="输入旅行需求或对当前阶段的反馈，然后点击发送按钮。",
                    elem_id="composer",
                    lines=2,
                    container=True,
                )
                planning_send_btn = gr.Button(
                    "\u27a4",
                    variant="primary",
                    elem_classes=["send-inside-btn"],
                )

            save_status = gr.Markdown("")
            redirect_html = gr.HTML("")

        planning_message.submit(
            respond_planning,
            inputs=[planning_message, planning_records_state, planning_state, planning_context_state],
            outputs=[
                planning_message,
                planning_window,
                planning_records_state,
                planning_state,
                planning_message,
                planning_stage_score,
                submit_stage_score_btn,
                planning_rating_row,
            ],
            concurrency_limit=1,
        )
        planning_send_btn.click(
            respond_planning,
            inputs=[planning_message, planning_records_state, planning_state, planning_context_state],
            outputs=[
                planning_message,
                planning_window,
                planning_records_state,
                planning_state,
                planning_message,
                planning_stage_score,
                submit_stage_score_btn,
                planning_rating_row,
            ],
            concurrency_limit=1,
        )
        submit_stage_score_btn.click(
            submit_planning_stage_rating_or_save,
            inputs=[
                planning_stage_score,
                planning_records_state,
                planning_state,
                planning_context_state,
                planning_started_at_state,
            ],
            outputs=[
                planning_message,
                planning_window,
                planning_records_state,
                planning_state,
                planning_message,
                planning_stage_score,
                submit_stage_score_btn,
                planning_rating_row,
                save_status,
                planning_send_btn,
                redirect_html,
            ],
            concurrency_limit=1,
        )
        interrupt_btn.click(
            interrupt_planning_record,
            inputs=[
                planning_records_state,
                planning_started_at_state,
                planning_state,
                planning_context_state,
            ],
            outputs=[
                save_status,
                planning_message,
                planning_send_btn,
                submit_stage_score_btn,
                planning_rating_row,
                interrupt_btn,
                redirect_html,
            ],
        )
        demo.load(
            current_time_text,
            outputs=[planning_started_at_state],
        )
        demo.load(
            initialize_planning_session,
            inputs=[planning_records_state],
            outputs=[planning_context_state, planning_state, planning_window],
        )

    return demo
