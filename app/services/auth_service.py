import gradio as gr

from app.config import EXPERIMENT_CONTEXT
from app.services.key_service import consume_experiment_key


TASK_ROUTES = {
    "聊天": "/chat",
    "问答": "/qa",
    "规划": "/plan",
}


def login_and_enter(experiment_key, subject_name, task_name):
    key = (experiment_key or "").strip()
    name = (subject_name or "").strip()
    task = (task_name or "").strip()

    if not key:
        return (
            "请输入实验密钥。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
            gr.update(value=task_name),
        )
    if not name:
        return (
            "请输入被试姓名。",
            gr.update(value=""),
            gr.update(value=experiment_key),
            gr.update(value=""),
            gr.update(value=task_name),
        )
    if task not in TASK_ROUTES:
        return (
            "请选择实验任务。",
            gr.update(value=""),
            gr.update(value=experiment_key),
            gr.update(value=subject_name),
            gr.update(value="问答"),
        )

    is_valid, status_text = consume_experiment_key(key, name)
    if not is_valid:
        return (
            status_text,
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
            gr.update(value=task_name),
        )

    EXPERIMENT_CONTEXT["subject_name"] = name
    EXPERIMENT_CONTEXT["experiment_key"] = key
    EXPERIMENT_CONTEXT["task_name"] = task
    return (
        status_text,
        gr.update(value=f"<meta http-equiv='refresh' content='0;url={TASK_ROUTES[task]}'>"),
        gr.update(value=""),
        gr.update(value=name),
        gr.update(value=task),
    )
