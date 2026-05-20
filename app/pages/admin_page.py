import gradio as gr

from app.services.account_service import (
    ACCOUNT_TABLE_COLUMNS,
    CHAT_CONFIG_TABLE_COLUMNS,
    CHAT_TOPICS,
    CERTAINTY_OPTIONS,
    EMOTIONAL_VALENCE_OPTIONS,
    INITIATIVE_OPTIONS,
    STANCE_STRATEGY_OPTIONS,
    TRANSPARENCY_OPTIONS,
    assign_balanced_chat_task_configs,
    create_or_reset_account,
    delete_account_and_records,
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


ADMIN_PAGE_EXTRA_CSS = """
.admin-dataframe-wrap {
    max-height: 360px;
    overflow: auto;
}
.admin-dataframe-wrap .wrap,
.admin-dataframe-wrap .table-wrap {
    max-height: 330px;
    overflow: auto;
}
"""


def build_admin_demo():
    with gr.Blocks(title="管理 - TrustAgent") as demo:
        gr.HTML(f"<style>{ADMIN_CSS}{ADMIN_PAGE_EXTRA_CSS}</style>")
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
                            delete_account_btn = gr.Button("\u5220\u9664\u8d26\u53f7\u53ca\u6570\u636e\u8bb0\u5f55", variant="stop")
                            refresh_btn = gr.Button("刷新账号列表", variant="secondary")

                        account_action_result = gr.Markdown("等待操作。")
                        account_summary, initial_rows = refresh_account_admin_view()
                        account_summary_box = gr.Markdown(account_summary)
                        with gr.Column(elem_classes=["admin-dataframe-wrap"]):
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
                        with gr.Column(elem_classes=["admin-dataframe-wrap"]):
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
                                chat_topic = gr.CheckboxGroup(
                                    choices=CHAT_TOPICS,
                                    value=CHAT_TOPICS[:3],
                                    label="聊天主题（多选，请选 3 个或 6 个）",
                                    interactive=True,
                                )

                            with gr.Column(scale=5):
                                with gr.Row():
                                    emotional_valence_level = gr.Radio(
                                        choices=EMOTIONAL_VALENCE_OPTIONS,
                                        value=EMOTIONAL_VALENCE_OPTIONS[0],
                                        label="情感效价",
                                        interactive=True,
                                        scale=5,
                                    )
                                    emotional_valence_locked = gr.Checkbox(
                                        label="锁定",
                                        value=True,
                                        interactive=True,
                                        scale=1,
                                    )

                                with gr.Row():
                                    transparency_level = gr.Radio(
                                        choices=TRANSPARENCY_OPTIONS,
                                        value=TRANSPARENCY_OPTIONS[0],
                                        label="透明度水平",
                                        interactive=True,
                                        scale=5,
                                    )
                                    transparency_locked = gr.Checkbox(
                                        label="锁定",
                                        value=True,
                                        interactive=True,
                                        scale=1,
                                    )

                                with gr.Row():
                                    stance_strategy_level = gr.Radio(
                                        choices=STANCE_STRATEGY_OPTIONS,
                                        value=STANCE_STRATEGY_OPTIONS[0],
                                        label="立场策略",
                                        interactive=True,
                                        scale=5,
                                    )
                                    stance_strategy_locked = gr.Checkbox(
                                        label="锁定",
                                        value=True,
                                        interactive=True,
                                        scale=1,
                                    )

                                with gr.Row():
                                    certainty_level = gr.Radio(
                                        choices=CERTAINTY_OPTIONS,
                                        value=CERTAINTY_OPTIONS[0],
                                        label="表达确定性",
                                        interactive=True,
                                        scale=5,
                                    )
                                    certainty_locked = gr.Checkbox(
                                        label="锁定",
                                        value=True,
                                        interactive=True,
                                        scale=1,
                                    )

                                with gr.Row():
                                    initiative_level = gr.Radio(
                                        choices=INITIATIVE_OPTIONS,
                                        value=INITIATIVE_OPTIONS[0],
                                        label="主动性水平",
                                        interactive=True,
                                        scale=5,
                                    )
                                    initiative_locked = gr.Checkbox(
                                        label="锁定",
                                        value=False,
                                        interactive=True,
                                        scale=1,
                                    )

                        with gr.Row():
                            add_chat_config_btn = gr.Button("批量增加聊天任务", variant="primary")
                            refresh_chat_config_btn = gr.Button("刷新配置列表", variant="secondary")

                        chat_config_status = gr.Markdown("等待配置。")
                        chat_config_summary_box = gr.Markdown(chat_config_summary)
                        with gr.Column(elem_classes=["admin-dataframe-wrap"]):
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
        ).then(
            refresh_chat_config_admin_view,
            outputs=[
                chat_config_summary_box,
                chat_account_select,
                chat_config_table,
                account_table,
            ],
        )

        refresh_btn.click(
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

        delete_account_btn.click(
            delete_account_and_records,
            inputs=[admin_account_id],
            outputs=[account_action_result, account_table],
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
        ).then(
            refresh_user_record_view,
            outputs=[
                user_record_summary_box,
                user_record_select,
                user_record_table,
                user_record_detail,
                user_record_json,
            ],
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
            assign_balanced_chat_task_configs,
            inputs=[
                chat_account_select,
                chat_topic,
                emotional_valence_level,
                emotional_valence_locked,
                transparency_level,
                transparency_locked,
                stance_strategy_level,
                stance_strategy_locked,
                certainty_level,
                certainty_locked,
                initiative_level,
                initiative_locked,
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
