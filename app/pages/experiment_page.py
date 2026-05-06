import gradio as gr

from app.services.data_service import READING_MATERIAL
from app.services.experiment_service import (
    auto_recommend_current_question,
    confirm_trust_rating,
    initialize_llm_session,
    question_payload,
    respond,
    respond_chat,
    submit_question_answer,
    switch_experiment_scene,
    switch_to_next_question,
    switch_to_prev_question,
    toggle_reading_panel,
)
from app.styles import EXPERIMENT_CSS


def build_experiment_demo():
    with gr.Blocks(title="实验 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        reading_panel_visible = gr.State(True)
        question_index_state = gr.State(0)
        llm_history_state = gr.State([])
        chat_llm_history_state = gr.State([])
        initial_question_title, initial_choices, initial_progress = question_payload(0)

        with gr.Column(elem_classes=["top-title"]):
            gr.Markdown("# 可信智能体实验")

        with gr.Row():
            with gr.Column(elem_classes=["scene-switch"]):
                scene_selector = gr.Radio(
                    choices=["聊天", "问答", "规划"],
                    value="问答",
                    label="实验场景切换",
                    interactive=True,
                )

        with gr.Row(elem_classes=["main-layout"]):
            with gr.Column(scale=4, elem_classes=["reading-column"]) as reading_column:
                toggle_reading_btn = gr.Button(
                    "关闭阅读材料",
                    variant="secondary",
                    elem_classes=["reading-toggle-btn"],
                )

                with gr.Column(visible=True, elem_classes=["reading-panel"]) as reading_panel:
                    gr.Markdown("### 阅读材料")
                    gr.Textbox(
                        value=READING_MATERIAL,
                        lines=35,
                        interactive=True,
                        placeholder="这里可以放入阅读理解材料……",
                    )

            with gr.Column(scale=8, elem_classes=["chat-panel"]):
                with gr.Column(visible=True) as qa_workspace:
                    with gr.Column(elem_classes=["question-panel"]):
                        question_progress = gr.Markdown(initial_progress)
                        question_md = gr.Markdown(initial_question_title)
                        question_options = gr.Radio(
                            choices=initial_choices,
                            value=None,
                            interactive=bool(initial_choices),
                        )
                        with gr.Row():
                            prev_question_btn = gr.Button("上一题", variant="secondary")
                            next_question_btn = gr.Button("下一题", variant="secondary")
                            confirm_answer_btn = gr.Button("确定", variant="primary")
                        answer_feedback = gr.Markdown("")

                    chatbot = gr.Chatbot(
                        label="对话",
                        elem_id="qa-chatbot",
                        avatar_images=(None, None),
                        buttons=["copy"],
                        height=360,
                    )

                    with gr.Column(elem_classes=["rating-panel"]):
                        with gr.Row():
                            with gr.Column(scale=7):
                                trust_score = gr.Radio(
                                    choices=[str(i) for i in range(1, 8)],
                                    value=None,
                                    label=None,
                                    show_label=False,
                                    interactive=True,
                                )
                            with gr.Column(scale=3, min_width=120):
                                trust_confirm_btn = gr.Button(
                                    "信任评分",
                                    variant="secondary",
                                    elem_classes=["trust-confirm-btn"],
                                )

                    with gr.Group(elem_classes=["composer-wrap"]):
                        message = gr.Textbox(
                            placeholder="输入问题后按 Enter 发送；Shift + Enter 换行。",
                            elem_id="composer",
                            lines=2,
                            container=True,
                        )
                        send_btn = gr.Button("➤", variant="primary", elem_classes=["send-inside-btn"])

                with gr.Column(visible=False, elem_classes=["free-chat-workspace"]) as chat_workspace:
                    chat_chatbot = gr.Chatbot(
                        label="聊天",
                        elem_id="free-chatbot",
                        avatar_images=(None, None),
                        buttons=["copy"],
                        height=560,
                    )

                    with gr.Group(elem_classes=["composer-wrap"]):
                        chat_message = gr.Textbox(
                            placeholder="输入消息后按 Enter 发送；Shift + Enter 换行。",
                            elem_id="chat-composer",
                            lines=2,
                            container=True,
                        )
                        chat_send_btn = gr.Button("➤", variant="primary", elem_classes=["send-inside-btn"])

                with gr.Column(visible=False, elem_classes=["planning-workspace"]) as planning_workspace:
                    gr.Markdown(
                        "### 规划\n\n规划任务页面待扩展。"
                    )

        scene_selector.change(
            switch_experiment_scene,
            inputs=[scene_selector],
            outputs=[qa_workspace, chat_workspace, planning_workspace, reading_column],
        )

        chat_message.submit(
            respond_chat,
            inputs=[chat_message, chat_chatbot, chat_llm_history_state],
            outputs=[chat_message, chat_chatbot, chat_llm_history_state],
        )
        chat_send_btn.click(
            respond_chat,
            inputs=[chat_message, chat_chatbot, chat_llm_history_state],
            outputs=[chat_message, chat_chatbot, chat_llm_history_state],
        )

        message.submit(
            respond,
            inputs=[message, chatbot, llm_history_state],
            outputs=[message, chatbot, llm_history_state, trust_score],
        )
        send_btn.click(
            respond,
            inputs=[message, chatbot, llm_history_state],
            outputs=[message, chatbot, llm_history_state, trust_score],
        )

        trust_confirm_btn.click(
            confirm_trust_rating,
            inputs=[trust_score],
            outputs=[],
        )

        toggle_reading_btn.click(
            toggle_reading_panel,
            inputs=[reading_panel_visible],
            outputs=[reading_panel_visible, reading_panel, toggle_reading_btn],
        )

        prev_question_btn.click(
            switch_to_prev_question,
            inputs=[question_index_state],
            outputs=[question_index_state, question_md, question_options, answer_feedback, question_progress],
        ).then(
            auto_recommend_current_question,
            inputs=[question_index_state, chatbot, llm_history_state],
            outputs=[chatbot, llm_history_state, trust_score],
        )

        next_question_btn.click(
            switch_to_next_question,
            inputs=[question_index_state],
            outputs=[question_index_state, question_md, question_options, answer_feedback, question_progress],
        ).then(
            auto_recommend_current_question,
            inputs=[question_index_state, chatbot, llm_history_state],
            outputs=[chatbot, llm_history_state, trust_score],
        )

        confirm_answer_btn.click(
            submit_question_answer,
            inputs=[question_options, question_index_state],
            outputs=[answer_feedback],
        )

        demo.load(
            initialize_llm_session,
            inputs=[chatbot, llm_history_state, question_index_state],
            outputs=[chatbot, llm_history_state, trust_score],
        )

    return demo
