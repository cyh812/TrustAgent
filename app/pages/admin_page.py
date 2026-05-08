import gradio as gr

from app.services.account_service import (
    ACCOUNT_TABLE_COLUMNS,
    CHAT_CONFIG_TABLE_COLUMNS,
    CHAT_TOPICS,
    CERTAINTY_OPTIONS,
    CERTAINTY_PROMPTS,
    EMOTIONAL_VALENCE_OPTIONS,
    EMOTIONAL_VALENCE_PROMPTS,
    STANCE_STRATEGY_OPTIONS,
    STANCE_STRATEGY_PROMPTS,
    TRANSPARENCY_OPTIONS,
    TRANSPARENCY_PROMPTS,
    assign_chat_task_config,
    create_or_reset_account,
    initial_chat_config_admin_view,
    refresh_chat_config_admin_view,
    refresh_account_admin_view,
)
from app.services.user_data_service import (
    USER_RECORD_COLUMNS,
    list_user_record_choices,
    load_user_record,
    refresh_user_record_view,
)
from app.styles import ADMIN_CSS


def prompt_detail_markdown(prompt_map):
    lines = []
    for name, prompt in prompt_map.items():
        lines.append(f"### {name}\n{prompt}")
    return "\n\n".join(lines)


def build_admin_demo():
    with gr.Blocks(title="管理 - TrustAgent") as demo:
        gr.HTML(f"<style>{ADMIN_CSS}</style>")
        with gr.Column(elem_classes=["admin-shell"]):
            with gr.Column(elem_classes=["admin-header"]):
                gr.Markdown("# 后台管理")
                gr.Markdown("管理实验账号、用户数据记录与各任务配置。")

            with gr.Tabs(elem_classes=["admin-menu"]):
                with gr.Tab("账号管理"):
                    with gr.Column(elem_classes=["admin-section"]):
                        gr.Markdown("## 实验账号")

                        with gr.Row():
                            admin_account_id = gr.Textbox(
                                label="账号ID",
                                placeholder="请输入账号ID",
                            )
                            account_key_prefix = gr.Textbox(
                                label="密钥前缀（可选）",
                                value="TA",
                                placeholder="例如 TA",
                            )

                        with gr.Row():
                            generate_btn = gr.Button("创建/重置账号密钥", variant="primary")
                            refresh_btn = gr.Button("刷新账号列表", variant="secondary")

                        account_action_result = gr.Markdown("等待操作。")
                        account_summary, initial_rows = refresh_account_admin_view()
                        account_summary_box = gr.Markdown(account_summary)
                        account_table = gr.Dataframe(
                            headers=ACCOUNT_TABLE_COLUMNS,
                            value=initial_rows,
                            interactive=False,
                            label="账号列表",
                        )

                with gr.Tab("用户数据记录"):
                    with gr.Column(elem_classes=["admin-section"]):
                        gr.Markdown("## 用户数据记录查看")
                        user_record_summary, user_record_choices, user_record_rows = list_user_record_choices()

                        with gr.Row(elem_classes=["user-record-toolbar"]):
                            user_record_select = gr.Dropdown(
                                choices=user_record_choices,
                                value=None,
                                label="按账号选择用户记录",
                                interactive=True,
                                scale=8,
                            )
                            refresh_user_record_btn = gr.Button(
                                "刷新记录",
                                variant="secondary",
                                scale=1,
                            )

                        user_record_summary_box = gr.Markdown(user_record_summary)
                        user_record_table = gr.Dataframe(
                            headers=USER_RECORD_COLUMNS,
                            value=user_record_rows,
                            interactive=False,
                            label="用户记录列表",
                        )

                        with gr.Row(elem_classes=["user-record-detail"]):
                            with gr.Column(scale=4):
                                user_record_detail = gr.Markdown("请选择一条用户记录。")
                            with gr.Column(scale=8):
                                user_record_json = gr.JSON(
                                    value={},
                                    label="完整上下文",
                                )

                with gr.Tab("聊天任务配置"):
                    with gr.Column(elem_classes=["admin-section"]):
                        gr.Markdown("## 聊天任务配置")
                        chat_config_summary, account_choices, chat_config_rows, _account_rows = initial_chat_config_admin_view()

                        with gr.Row(elem_classes=["chat-config-layout"]):
                            with gr.Column(scale=4):
                                chat_account_select = gr.Dropdown(
                                    choices=account_choices,
                                    value=None,
                                    label="账号",
                                    interactive=True,
                                )
                                chat_topic = gr.Radio(
                                    choices=CHAT_TOPICS,
                                    value=CHAT_TOPICS[0],
                                    label="聊天主题",
                                    interactive=True,
                                )

                            with gr.Column(scale=5):
                                emotional_valence_level = gr.Radio(
                                    choices=EMOTIONAL_VALENCE_OPTIONS,
                                    value=EMOTIONAL_VALENCE_OPTIONS[0],
                                    label="情感效价",
                                    interactive=True,
                                )
                                with gr.Accordion("查看/关闭情感效价 prompt 详情", open=False):
                                    gr.Markdown(prompt_detail_markdown(EMOTIONAL_VALENCE_PROMPTS))

                                transparency_level = gr.Radio(
                                    choices=TRANSPARENCY_OPTIONS,
                                    value=TRANSPARENCY_OPTIONS[0],
                                    label="透明度水平",
                                    interactive=True,
                                )
                                with gr.Accordion("查看/关闭透明度水平 prompt 详情", open=False):
                                    gr.Markdown(prompt_detail_markdown(TRANSPARENCY_PROMPTS))

                                stance_strategy_level = gr.Radio(
                                    choices=STANCE_STRATEGY_OPTIONS,
                                    value=STANCE_STRATEGY_OPTIONS[0],
                                    label="立场策略",
                                    interactive=True,
                                )
                                with gr.Accordion("查看/关闭立场策略 prompt 详情", open=False):
                                    gr.Markdown(prompt_detail_markdown(STANCE_STRATEGY_PROMPTS))

                                certainty_level = gr.Radio(
                                    choices=CERTAINTY_OPTIONS,
                                    value=CERTAINTY_OPTIONS[0],
                                    label="表达确定性",
                                    interactive=True,
                                )
                                with gr.Accordion("查看/关闭表达确定性 prompt 详情", open=False):
                                    gr.Markdown(prompt_detail_markdown(CERTAINTY_PROMPTS))

                        with gr.Row():
                            add_chat_config_btn = gr.Button("增加一次聊天任务", variant="primary")
                            refresh_chat_config_btn = gr.Button("刷新配置列表", variant="secondary")

                        chat_config_status = gr.Markdown("等待配置。")
                        chat_config_summary_box = gr.Markdown(chat_config_summary)
                        chat_config_table = gr.Dataframe(
                            headers=CHAT_CONFIG_TABLE_COLUMNS,
                            value=chat_config_rows,
                            interactive=False,
                            label="聊天任务配置列表",
                        )

                with gr.Tab("问答任务配置"):
                    with gr.Column(elem_classes=["admin-section", "admin-placeholder"]):
                        gr.Markdown("## 问答任务配置")
                        gr.Markdown("页面待扩展。")

                with gr.Tab("规划任务配置"):
                    with gr.Column(elem_classes=["admin-section", "admin-placeholder"]):
                        gr.Markdown("## 规划任务配置")
                        gr.Markdown("页面待扩展。")

        generate_btn.click(
            create_or_reset_account,
            inputs=[admin_account_id, account_key_prefix],
            outputs=[account_action_result, account_table],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        )

        refresh_btn.click(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        )

        user_record_select.change(
            load_user_record,
            inputs=[user_record_select],
            outputs=[user_record_detail, user_record_json],
        )

        refresh_user_record_btn.click(
            refresh_user_record_view,
            outputs=[
                user_record_summary_box,
                user_record_select,
                user_record_table,
                user_record_detail,
                user_record_json,
            ],
        )

        add_chat_config_btn.click(
            assign_chat_task_config,
            inputs=[
                chat_account_select,
                chat_topic,
                emotional_valence_level,
                transparency_level,
                stance_strategy_level,
                certainty_level,
            ],
            outputs=[chat_config_status, chat_config_table, account_table],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        ).then(
            refresh_chat_config_admin_view,
            outputs=[
                chat_config_summary_box,
                chat_account_select,
                chat_config_table,
                account_table,
            ],
        )

        refresh_chat_config_btn.click(
            refresh_chat_config_admin_view,
            outputs=[
                chat_config_summary_box,
                chat_account_select,
                chat_config_table,
                account_table,
            ],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        )

    return demo
