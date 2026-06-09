import gradio as gr

from app.services.account_service import (
    ACCOUNT_TABLE_COLUMNS,
    CHAT_CONFIG_TABLE_COLUMNS,
    CHAT_TOPICS,
    EMOTIONAL_VALENCE_OPTIONS,
    STANCE_STRATEGY_OPTIONS,
    TRANSPARENCY_OPTIONS,
    assign_chat_task_config,
    assign_qa_quota,
    assign_plan_quota,
    assign_balanced_chat_task_configs,
    create_or_reset_account,
    delete_account_and_records,
    initial_chat_config_admin_view,
    initial_qa_config_admin_view,
    initial_plan_config_admin_view,
    refresh_chat_config_admin_view,
    refresh_qa_config_admin_view,
    refresh_account_admin_view,
    refresh_plan_config_admin_view,
)
from app.services.user_data_service import (
    USER_RECORD_COLUMNS,
    USER_RECORD_TASK_ALL,
    USER_RECORD_TASK_CHOICES,
    export_user_records_zip,
    list_user_record_choices,
    refresh_user_record_view,
    select_user_record_account,
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
                            account_password = gr.Textbox(
                                label="账号密码",
                                placeholder="请输入账号密码",
                                type="password",
                            )

                        with gr.Row():
                            generate_btn = gr.Button("创建/更新账号密码", variant="primary")
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
                                label="按账号ID选择用户",
                                interactive=True,
                                scale=5,
                            )
                            user_record_task_select = gr.Dropdown(
                                choices=USER_RECORD_TASK_CHOICES,
                                value=USER_RECORD_TASK_ALL,
                                label="按任务类型筛选",
                                interactive=True,
                                scale=2,
                            )
                            export_user_record_btn = gr.Button(
                                "导出筛选记录",
                                variant="primary",
                                scale=2,
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

                        export_user_record_status = gr.Markdown("请选择用户后导出。")
                        export_user_record_file = gr.File(
                            label="导出压缩包",
                            interactive=False,
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
                                    label="单独增加聊天主题",
                                    interactive=True,
                                )

                            with gr.Column(scale=5):
                                emotional_valence_level = gr.Radio(
                                    choices=EMOTIONAL_VALENCE_OPTIONS,
                                    value=EMOTIONAL_VALENCE_OPTIONS[0],
                                    label="社会情感表达",
                                    interactive=True,
                                )
                                transparency_level = gr.Radio(
                                    choices=TRANSPARENCY_OPTIONS,
                                    value=TRANSPARENCY_OPTIONS[0],
                                    label="认知透明表达",
                                    interactive=True,
                                )
                                stance_strategy_level = gr.Radio(
                                    choices=STANCE_STRATEGY_OPTIONS,
                                    value=STANCE_STRATEGY_OPTIONS[0],
                                    label="对话立场对齐",
                                    interactive=True,
                                )

                        with gr.Row():
                            add_chat_config_btn = gr.Button("批量增加 8 次聊天任务", variant="primary")
                            add_single_chat_config_btn = gr.Button("单独增加 1 次聊天任务", variant="secondary")
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
                    with gr.Column(elem_classes=["admin-section"]):
                        gr.Markdown("## 问答任务配置")
                        qa_config_summary, qa_account_choices, _qa_account_rows = initial_qa_config_admin_view()

                        with gr.Row():
                            qa_account_select = gr.Dropdown(
                                choices=qa_account_choices,
                                value=None,
                                label="账号",
                                interactive=True,
                                scale=6,
                            )
                            qa_quota_count = gr.Number(
                                label="增加问答任务次数",
                                value=1,
                                precision=0,
                                interactive=True,
                                scale=2,
                            )
                            qa_target_accuracy = gr.Radio(
                                choices=["60%", "80%"],
                                value="60%",
                                label="LLM目标准确率",
                                interactive=True,
                                scale=2,
                            )

                        with gr.Row():
                            add_qa_quota_btn = gr.Button("增加问答任务", variant="primary")
                            refresh_qa_config_btn = gr.Button("刷新账号列表", variant="secondary")

                        qa_config_status = gr.Markdown("等待配置。")
                        qa_config_summary_box = gr.Markdown(qa_config_summary)

                with gr.Tab("规划任务配置"):
                    with gr.Column(elem_classes=["admin-section"]):
                        gr.Markdown("## 规划任务配置")
                        plan_config_summary, plan_account_choices, _plan_account_rows = initial_plan_config_admin_view()

                        with gr.Row():
                            plan_account_select = gr.Dropdown(
                                choices=plan_account_choices,
                                value=None,
                                label="账号",
                                interactive=True,
                                scale=7,
                            )
                            plan_quota_count = gr.Number(
                                label="增加规划任务次数",
                                value=1,
                                precision=0,
                                interactive=True,
                                scale=2,
                            )

                        with gr.Row():
                            add_plan_quota_btn = gr.Button("增加规划任务", variant="primary")
                            refresh_plan_config_btn = gr.Button("刷新账号列表", variant="secondary")

                        plan_config_status = gr.Markdown("等待配置。")
                        plan_config_summary_box = gr.Markdown(plan_config_summary)

        generate_btn.click(
            create_or_reset_account,
            inputs=[admin_account_id, account_password],
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
            refresh_qa_config_admin_view,
            outputs=[
                qa_config_summary_box,
                qa_account_select,
                account_table,
            ],
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
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
        ).then(
            refresh_qa_config_admin_view,
            outputs=[
                qa_config_summary_box,
                qa_account_select,
                account_table,
            ],
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
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
                export_user_record_status,
                export_user_record_file,
            ],
        ).then(
            refresh_qa_config_admin_view,
            outputs=[
                qa_config_summary_box,
                qa_account_select,
                account_table,
            ],
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
                account_table,
            ],
        )

        user_record_select.change(
            select_user_record_account,
            inputs=[user_record_select, user_record_task_select],
            outputs=[
                user_record_summary_box,
                user_record_table,
                export_user_record_status,
                export_user_record_file,
            ],
        )

        user_record_task_select.change(
            select_user_record_account,
            inputs=[user_record_select, user_record_task_select],
            outputs=[
                user_record_summary_box,
                user_record_table,
                export_user_record_status,
                export_user_record_file,
            ],
        )

        export_user_record_btn.click(
            export_user_records_zip,
            inputs=[user_record_select, user_record_task_select],
            outputs=[export_user_record_status, export_user_record_file],
        )

        refresh_user_record_btn.click(
            refresh_user_record_view,
            outputs=[
                user_record_summary_box,
                user_record_select,
                user_record_table,
                export_user_record_status,
                export_user_record_file,
            ],
        )

        add_chat_config_btn.click(
            assign_balanced_chat_task_configs,
            inputs=[chat_account_select],
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
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
                account_table,
            ],
        )

        add_single_chat_config_btn.click(
            assign_chat_task_config,
            inputs=[
                chat_account_select,
                chat_topic,
                emotional_valence_level,
                transparency_level,
                stance_strategy_level,
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
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
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

        add_plan_quota_btn.click(
            assign_plan_quota,
            inputs=[plan_account_select, plan_quota_count],
            outputs=[plan_config_status, account_table],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
                account_table,
            ],
        ).then(
            refresh_chat_config_admin_view,
            outputs=[
                chat_config_summary_box,
                chat_account_select,
                chat_config_table,
                account_table,
            ],
        )

        add_qa_quota_btn.click(
            assign_qa_quota,
            inputs=[qa_account_select, qa_quota_count, qa_target_accuracy],
            outputs=[qa_config_status, account_table],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        ).then(
            refresh_qa_config_admin_view,
            outputs=[
                qa_config_summary_box,
                qa_account_select,
                account_table,
            ],
        ).then(
            refresh_chat_config_admin_view,
            outputs=[
                chat_config_summary_box,
                chat_account_select,
                chat_config_table,
                account_table,
            ],
        ).then(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
                account_table,
            ],
        )

        refresh_qa_config_btn.click(
            refresh_qa_config_admin_view,
            outputs=[
                qa_config_summary_box,
                qa_account_select,
                account_table,
            ],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        )

        refresh_plan_config_btn.click(
            refresh_plan_config_admin_view,
            outputs=[
                plan_config_summary_box,
                plan_account_select,
                account_table,
            ],
        ).then(
            refresh_account_admin_view,
            outputs=[account_summary_box, account_table],
        )

    return demo
