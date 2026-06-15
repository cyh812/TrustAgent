import gradio as gr

from app.services.account_service import profile_values_for_request, save_profile_info, start_task_for_account
from app.styles import PROFILE_CSS


def start_chat_task(account_id):
    return start_task_for_account("chat", account_id)


def start_qa_task(account_id):
    return start_task_for_account("qa", account_id)


def start_plan_task(account_id):
    return start_task_for_account("plan", account_id)


def return_to_login():
    return gr.update(value="<meta http-equiv='refresh' content='0;url=/login'>")


def build_profile_demo():
    with gr.Blocks(title="个人信息 - TrustAgent") as demo:
        gr.HTML(f"<style>{PROFILE_CSS}</style>")

        with gr.Row():
            gr.Markdown("# 个人信息")
            back_to_login_btn = gr.Button("退出登录", variant="secondary", scale=0)

        profile_status = gr.Markdown("")
        redirect_html = gr.HTML("")

        with gr.Column(elem_classes=["profile-panel"]):
            account_id = gr.Textbox(label="账号ID", interactive=False)
            password_key = gr.Textbox(label="密钥", type="password")
            name = gr.Textbox(label="姓名", placeholder="请输入姓名")
            phone = gr.Textbox(label="手机号", placeholder="请输入手机号")
            save_profile_btn = gr.Button("保存个人信息", variant="primary")

        with gr.Column(elem_classes=["task-entry-panel"]):
            quota_text = gr.Markdown("聊天：0 次；问答：0 次；规划：0 次。")
            with gr.Row():
                chat_btn = gr.Button("进入聊天任务", variant="secondary")
                qa_btn = gr.Button("进入问答任务", variant="secondary")
                plan_btn = gr.Button("进入规划任务", variant="secondary")

        back_to_login_btn.click(
            return_to_login,
            outputs=[redirect_html],
        )

        save_profile_btn.click(
            save_profile_info,
            inputs=[account_id, password_key, name, phone],
            outputs=[profile_status, password_key, quota_text],
        )

        chat_btn.click(
            start_chat_task,
            inputs=[account_id],
            outputs=[profile_status, redirect_html],
        )
        qa_btn.click(
            start_qa_task,
            inputs=[account_id],
            outputs=[profile_status, redirect_html],
        )
        plan_btn.click(
            start_plan_task,
            inputs=[account_id],
            outputs=[profile_status, redirect_html],
        )

        demo.load(
            profile_values_for_request,
            outputs=[profile_status, account_id, password_key, name, phone, quota_text],
        )

    return demo
