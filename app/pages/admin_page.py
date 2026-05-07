import gradio as gr

from app.services.key_service import (
    KEY_TABLE_COLUMNS,
    generate_experiment_keys,
    refresh_key_admin_view,
)
from app.services.user_data_service import (
    USER_RECORD_COLUMNS,
    list_user_record_choices,
    load_user_record,
    refresh_user_record_view,
)
from app.styles import ADMIN_CSS


def build_admin_demo():
    with gr.Blocks(title="管理 - TrustAgent") as demo:
        gr.HTML(f"<style>{ADMIN_CSS}</style>")
        with gr.Column(elem_classes=["admin-shell"]):
            with gr.Column(elem_classes=["admin-header"]):
                gr.Markdown("# 后台管理")
                gr.Markdown("管理实验密钥、用户数据记录与各任务配置。")

            with gr.Tabs(elem_classes=["admin-menu"]):
                with gr.Tab("密钥管理"):
                    with gr.Column(elem_classes=["admin-section"]):
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

                with gr.Tab("用户数据记录"):
                    with gr.Column(elem_classes=["admin-section"]):
                        gr.Markdown("## 用户数据记录查看")
                        user_record_summary, user_record_choices, user_record_rows = list_user_record_choices()

                        with gr.Row(elem_classes=["user-record-toolbar"]):
                            user_record_select = gr.Dropdown(
                                choices=user_record_choices,
                                value=None,
                                label="按密钥选择用户记录",
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
                    with gr.Column(elem_classes=["admin-section", "admin-placeholder"]):
                        gr.Markdown("## 聊天任务配置")
                        gr.Markdown("页面待扩展。")

                with gr.Tab("问答任务配置"):
                    with gr.Column(elem_classes=["admin-section", "admin-placeholder"]):
                        gr.Markdown("## 问答任务配置")
                        gr.Markdown("页面待扩展。")

                with gr.Tab("规划任务配置"):
                    with gr.Column(elem_classes=["admin-section", "admin-placeholder"]):
                        gr.Markdown("## 规划任务配置")
                        gr.Markdown("页面待扩展。")

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

    return demo
