import gradio as gr

from app.services.data_service import READING_MATERIAL
from app.services.experiment_service import (
    initialize_llm_session,
    question_payload,
    respond_qa,
    submit_qa_rating_and_continue,
    submit_question_answer_for_rating,
)
from app.services.key_service import current_time_text
from app.styles import EXPERIMENT_CSS


def build_qa_demo():
    with gr.Blocks(title="问答 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        reading_panel_visible = gr.State(True)
        question_index_state = gr.State(0)
        llm_history_state = gr.State([])
        qa_answer_plan_state = gr.State({})
        qa_records_state = gr.State([])
        qa_started_at_state = gr.State("")
        initial_question_title, initial_choices, initial_progress = question_payload(0)

        with gr.Column(elem_classes=["top-title"]):
            gr.Markdown("# 可信智能体实验 - 问答")

        with gr.Row(elem_classes=["main-layout"]):
            with gr.Column(scale=4, elem_classes=["reading-column"]):
                toggle_reading_btn = gr.Button(
                    "开始实验",
                    variant="primary",
                    elem_classes=["reading-toggle-btn"],
                )

                with gr.Column(visible=True, elem_classes=["reading-panel"]) as reading_panel:
                    gr.Markdown("### 阅读材料")
                    gr.Textbox(
                        value=READING_MATERIAL,
                        label="",
                        show_label=False,
                        lines=35,
                        interactive=True,
                        placeholder="这里可以放入阅读理解材料……",
                        elem_classes=["reading-material-box"],
                    )

            with gr.Column(scale=8, elem_classes=["chat-panel"]):
                with gr.Column(elem_classes=["question-panel"]):
                    question_progress = gr.Markdown(initial_progress, visible=False)
                    question_md = gr.Markdown(initial_question_title)
                    with gr.Row(elem_classes=["qa-answer-row"]):
                        question_options = gr.Radio(
                            choices=initial_choices,
                            value=None,
                            label="",
                            show_label=False,
                            container=False,
                            interactive=bool(initial_choices),
                            scale=8,
                            elem_classes=["qa-option-radio"],
                        )
                        confirm_answer_btn = gr.Button("确定", variant="primary")
                    answer_feedback = gr.Markdown("")

                with gr.Row(visible=False, elem_classes=["qa-rating-panel"]) as qa_rating_panel:
                    gr.Markdown(
                        "请你对LLM Agent表现的信任感水平进行打分",
                        elem_classes=["qa-rating-title"],
                    )
                    trust_score = gr.Radio(
                        choices=[str(i) for i in range(1, 8)],
                        value=None,
                        label="",
                        show_label=False,
                        container=False,
                        interactive=True,
                        scale=5,
                        elem_classes=["qa-inline-trust-radio"],
                    )
                    trust_confirm_btn = gr.Button(
                        "评分并进入下一题",
                        variant="primary",
                        scale=2,
                        elem_classes=["trust-confirm-btn"],
                    )

                chatbot = gr.Chatbot(
                    label="对话",
                    elem_id="qa-chatbot",
                    avatar_images=(None, None),
                    height=360,
                )

                with gr.Group(elem_classes=["composer-wrap"]):
                    message = gr.Textbox(
                        placeholder="输入问题后按 Enter 发送；Shift + Enter 换行。",
                        label="",
                        show_label=False,
                        elem_id="composer",
                        lines=2,
                        container=True,
                    )
                    send_btn = gr.Button("➤", variant="primary", elem_classes=["send-inside-btn"])
                save_status = gr.Markdown("", visible=False)
                redirect_html = gr.HTML("", visible=False)

        message.submit(
            respond_qa,
            inputs=[message, chatbot, llm_history_state],
            outputs=[message, chatbot, llm_history_state, trust_score],
        )
        send_btn.click(
            respond_qa,
            inputs=[message, chatbot, llm_history_state],
            outputs=[message, chatbot, llm_history_state, trust_score],
        )

        toggle_reading_btn.click(
            initialize_llm_session,
            inputs=[chatbot, llm_history_state, question_index_state, qa_answer_plan_state],
            outputs=[chatbot, llm_history_state, trust_score, qa_answer_plan_state, toggle_reading_btn],
        )

        confirm_answer_btn.click(
            submit_question_answer_for_rating,
            inputs=[question_options, question_index_state, qa_records_state, qa_answer_plan_state],
            outputs=[
                answer_feedback,
                qa_records_state,
                question_options,
                confirm_answer_btn,
                trust_confirm_btn,
                qa_rating_panel,
            ],
        )

        trust_confirm_btn.click(
            submit_qa_rating_and_continue,
            inputs=[
                trust_score,
                question_index_state,
                qa_records_state,
                qa_answer_plan_state,
                chatbot,
                llm_history_state,
                qa_started_at_state,
            ],
            outputs=[
                question_index_state,
                question_md,
                question_options,
                answer_feedback,
                question_progress,
                chatbot,
                llm_history_state,
                qa_records_state,
                trust_score,
                trust_confirm_btn,
                qa_rating_panel,
                confirm_answer_btn,
                save_status,
                message,
                send_btn,
                redirect_html,
            ],
        )

        demo.load(
            current_time_text,
            outputs=[qa_started_at_state],
        )

    return demo
