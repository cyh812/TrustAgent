import gradio as gr

from app.config import EXPERIMENT_CONTEXT, USED_EXPERIMENT_KEYS
from app.services.data_service import VALID_EXPERIMENT_KEYS


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
    if key not in VALID_EXPERIMENT_KEYS:
        return (
            "密钥无效。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )
    if key in USED_EXPERIMENT_KEYS:
        return (
            "该密钥已使用，无法重复进入。",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=subject_name),
        )

    USED_EXPERIMENT_KEYS.add(key)
    EXPERIMENT_CONTEXT["subject_name"] = name
    return (
        f"验证通过，欢迎 {name}，正在跳转到实验页面...",
        gr.update(value="<meta http-equiv='refresh' content='0;url=/experiment'>"),
        gr.update(value=""),
        gr.update(value=name),
    )
