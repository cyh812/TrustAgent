import gradio as gr

from app.services.auth_service import login_and_enter
from app.styles import LOGIN_CSS


def build_login_demo():
    with gr.Blocks(title="登录 - TrustAgent") as demo:
        gr.HTML(f"<style>{LOGIN_CSS}</style>")
        gr.Markdown("# 登录")
        gr.Markdown("请输入账号ID与密码。密码由后台账号管理生成。")

        account_id = gr.Textbox(
            label="账号ID",
            placeholder="请输入账号ID",
        )
        password = gr.Textbox(
            label="密码",
            placeholder="请输入密码",
            type="password",
        )
        login_submit = gr.Button("登录", variant="primary")
        login_status = gr.Markdown("等待登录。")
        redirect_html = gr.HTML("")

        login_submit.click(
            login_and_enter,
            inputs=[account_id, password],
            outputs=[login_status, redirect_html, account_id, password],
        )
    return demo
