import gradio as gr

from app.config import EXPERIMENT_CONTEXT
from app.services.key_service import consume_experiment_key


def login_and_enter(experiment_key, subject_name):
    key = (experiment_key or "").strip()
    name = (subject_name or "").strip()

    if not key:
        return (
            "请输入实验密钥。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )
    if not name:
        return (
            "请输入被试姓名。",
            gr.update(value=""),
            gr.update(value=experiment_key),
            gr.update(value=""),
        )

    is_valid, status_text = consume_experiment_key(key, name)
    if not is_valid:
        return (
            status_text,
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )

    EXPERIMENT_CONTEXT["subject_name"] = name
    return (
        status_text,
        gr.update(value="<meta http-equiv='refresh' content='0;url=/experiment'>"),
        gr.update(value=""),
        gr.update(value=name),
    )
