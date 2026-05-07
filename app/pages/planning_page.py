import gradio as gr

from app.styles import EXPERIMENT_CSS


def build_planning_demo():
    with gr.Blocks(title="规划 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        with gr.Column(elem_classes=["top-title"]):
            gr.Markdown("# 可信智能体实验 - 规划")

        with gr.Column(elem_classes=["chat-panel", "planning-workspace"]):
            gr.Markdown("### 规划\n\n规划任务页面待扩展。")

    return demo
