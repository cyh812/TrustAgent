import gradio as gr

from app.services.auth_service import login_and_enter
from app.styles import LOGIN_CSS


def build_login_demo():
    with gr.Blocks(title="登录 - TrustAgent") as demo:
        gr.HTML(f"<style>{LOGIN_CSS}</style>")
        gr.Markdown("# 登录")
        gr.Markdown("请输入实验密钥与被试姓名。密钥一次有效，用后作废。")

        gate_key = gr.Textbox(
            label="实验密钥",
            placeholder="请输入密钥",
            type="password",
        )
        gate_subject = gr.Textbox(
            label="被试姓名",
            placeholder="请输入被试姓名",
        )
        gate_task = gr.Radio(
            choices=["聊天", "问答", "规划"],
            value="问答",
            label="实验任务",
            interactive=True,
        )
        gate_submit = gr.Button("验证并进入", variant="primary")
        gate_status = gr.Markdown("等待验证。")
        redirect_html = gr.HTML("")

        gate_submit.click(
            login_and_enter,
            inputs=[gate_key, gate_subject, gate_task],
            outputs=[gate_status, redirect_html, gate_key, gate_subject, gate_task],
        )
    return demo
