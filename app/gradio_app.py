import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import gradio as gr
import uvicorn

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.llm_agent import get_llm_settings, stream_chat_reply

APP_TITLE = "TrustAgent 实验系统"
DEFAULT_EXPERIMENT_KEYS = {"ABCD", "trial-002", "trial-003"}
USED_EXPERIMENT_KEYS: Set[str] = set()

RUNTIME_CONFIG: Dict[str, object] = {
    "system_prompt": "你是 TrustAgent，一个谨慎、清晰、可解释的智能助手。",
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "openrouter/auto",
}

EXPERIMENT_CONTEXT: Dict[str, str] = {
    "subject_name": "-",
}

MODEL_OPTIONS = [
    "openrouter/auto",
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat",
]

LOGIN_CSS = """
.gradio-container {
    max-width: 760px !important;
    width: 760px !important;
    margin: 0 auto !important;
}

/* 隐藏底部 footer */
footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}
"""

EXPERIMENT_CSS = """
/* 整体固定更宽，不随内容收缩 */
.gradio-container {
    max-width: 1500px !important;
    width: 1500px !important;
    margin: 0 auto !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
}

/* 去掉聚焦时的奇怪外框 */
.gradio-container:focus,
.gradio-container:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

/* 隐藏底部 footer */
footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}

/* 页面顶部 */
.top-title h1 {
    margin-top: 4px !important;
    margin-bottom: 8px !important;
    font-size: 34px !important;
    font-weight: 700 !important;
}

.top-subtitle {
    color: #64748b;
    margin-bottom: 12px;
}

/* 场景切换整行 */
.scene-switch {
    width: 100%;
    margin-top: 4px;
    margin-bottom: 12px;
    padding: 10px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background: #ffffff;
}

/* 主体左右两栏 */
.main-layout {
    margin-top: 6px;
    align-items: flex-start !important;
}

/* 左侧阅读材料区域整体：固定从上往下紧凑排列 */
.reading-column {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    align-items: stretch !important;
    gap: 8px !important;
    align-self: flex-start !important;
    min-height: unset !important;
}

/* 阅读材料开关按钮：宽度与左栏一致 */
.reading-toggle-btn {
    margin: 0 !important;
    padding: 0 !important;
}

.reading-toggle-btn button {
    width: 100% !important;
    margin: 0 !important;
}

/* 左侧阅读材料面板 */
.reading-panel {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    background: #fafafa;
    min-height: 820px;
    margin-top: 0 !important;
}

/* 右侧对话面板 */
.chat-panel {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    background: #ffffff;
    min-height: 680px;
}

/* 题目切换窗口 */
.question-panel {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px;
    background: #f8fafc;
    margin-bottom: 12px;
}

/* 聊天框 */
#chatbot {
    min-height: 360px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

/* ===== 评分窗口 ===== */
.rating-panel {
    margin-top: 0px;
    margin-bottom: 0px;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 12px;
    background: #f8fafc;
}

.rating-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}

.trust-confirm-btn button {
    width: 100% !important;
    height: 40px !important;
}

/* ===== 输入框 + 内嵌发送按钮 ===== */
.composer-wrap {
    position: relative !important;
    width: 100% !important;
    margin-top: 10px !important;
}

/* Textbox 外层 */
#composer {
    width: 100% !important;
}

/* Textarea 本体，给右下角按钮留空间 */
#composer textarea {
    min-height: 48px !important;
    padding-right: 70px !important;
    padding-bottom: 42px !important;
    border-radius: 16px !important;
}

/* 内嵌发送按钮 */
.send-inside-btn {
    position: absolute !important;
    right: 14px !important;
    bottom: 14px !important;
    z-index: 20 !important;
    width: 42px !important;
    min-width: 42px !important;
    height: 42px !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 9999px !important;
    overflow: hidden !important;
}

.send-inside-btn > *,
.send-inside-btn button {
    width: 42px !important;
    min-width: 42px !important;
    height: 42px !important;
    border-radius: 9999px !important;
    overflow: hidden !important;
    padding: 0 !important;
    font-size: 18px !important;
    line-height: 1 !important;
}
"""

ADMIN_CSS = """
.gradio-container {
    max-width: 900px !important;
    width: 900px !important;
    margin: 0 auto !important;
}

/* 隐藏底部 footer */
footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}
"""


def _load_experiment_keys() -> Set[str]:
    raw = os.getenv("EXPERIMENT_KEYS", "").strip()
    if not raw:
        return set(DEFAULT_EXPERIMENT_KEYS)
    keys = {part.strip() for part in raw.split(",") if part.strip()}
    return keys or set(DEFAULT_EXPERIMENT_KEYS)


VALID_EXPERIMENT_KEYS = _load_experiment_keys()
DATA_FILE = PROJECT_ROOT / "data" / "data.json"


def _load_experiment_data() -> Dict[str, object]:
    if not DATA_FILE.exists():
        return {"reading_material": "", "questions": []}

    raw_obj = None
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            raw_text = DATA_FILE.read_text(encoding=encoding)
            raw_obj = json.loads(raw_text)
            break
        except Exception:
            continue

    if not isinstance(raw_obj, dict):
        return {"reading_material": "", "questions": []}

    reading_material = str(raw_obj.get("reading_material", "")).strip()
    questions: List[Dict[str, str]] = []

    blocks = raw_obj.get("blocks", [])
    if isinstance(blocks, list):
        for block_index, block in enumerate(blocks, start=1):
            if not isinstance(block, dict):
                continue

            block_name = str(block.get("block_name", f"Block{block_index}")).strip()
            block_questions = block.get("questions", [])
            if not isinstance(block_questions, list):
                continue

            for q_index, item in enumerate(block_questions, start=1):
                if not isinstance(item, dict):
                    continue

                qid = str(item.get("question_id", f"Q{q_index}")).strip()
                question_text = str(item.get("question", "")).strip()
                options = item.get("options", {})
                answer_key = str(item.get("answer", "")).strip()
                explanation = str(item.get("explanation", "")).strip()

                option_choices: List[str] = []
                answer_text = answer_key
                if isinstance(options, dict):
                    for opt_key, opt_val in options.items():
                        k = str(opt_key).strip()
                        v = str(opt_val).strip()
                        option_choices.append(f"{k}. {v}")
                    if answer_key in options:
                        answer_text = f"{answer_key}. {str(options[answer_key]).strip()}"

                questions.append(
                    {
                        "block_name": block_name,
                        "question_id": qid,
                        "question": question_text,
                        "choices": option_choices,
                        "answer_key": answer_key,
                        "answer_text": answer_text,
                        "explanation": explanation,
                    }
                )

    return {
        "reading_material": reading_material,
        "questions": questions,
    }


EXPERIMENT_DATA = _load_experiment_data()
READING_MATERIAL = str(EXPERIMENT_DATA.get("reading_material", ""))
QUESTION_BANK = EXPERIMENT_DATA.get("questions", [])


def _safe_question_index(index: int) -> int:
    if not QUESTION_BANK:
        return 0
    return max(0, min(index, len(QUESTION_BANK) - 1))


def _question_payload(index: int):
    if not QUESTION_BANK:
        return "### 题目切换\n暂无题目数据。", [], "第 0 / 0 题"

    idx = _safe_question_index(index)
    q = QUESTION_BANK[idx]
    title = f"### {q['block_name']} · {q['question_id']}\n\n{q['question']}"
    progress = f"第 {idx + 1} / {len(QUESTION_BANK)} 题"
    return title, q["choices"], progress


def _build_question_prompt(index: int):
    if not QUESTION_BANK:
        return "", "暂无题目数据。"

    idx = _safe_question_index(index)
    q = QUESTION_BANK[idx]
    options_text = "\n".join(q["choices"])

    user_visible_text = (
        f"{q['block_name']} · {q['question_id']}\n"
        f"{q['question']}\n"
        f"{options_text}"
    )

    llm_prompt = (
        "请根据已给出的阅读材料，回答下面单选题。"
        "只输出你推荐的选项字母（A/B/C/D），不要解释。\n\n"
        f"题目编号：{q['question_id']}\n"
        f"题目：{q['question']}\n"
        f"选项：\n{options_text}"
    )
    return llm_prompt, user_visible_text


def _normalize_history(history):
    normalized = []
    for item in history or []:
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized.append({
                "role": item["role"],
                "content": item["content"],
            })
    return normalized


def _empty_rating_state():
    return gr.update(value=None)


def _stream_auto_prompt(llm_prompt, chat_prompt, chat_history, llm_history):
    chat_history = _normalize_history(chat_history)
    llm_history = _normalize_history(llm_history)

    context_history = list(llm_history)
    chat_history.append({"role": "user", "content": chat_prompt})
    chat_history.append({"role": "assistant", "content": ""})
    llm_history.append({"role": "user", "content": llm_prompt})
    llm_history.append({"role": "assistant", "content": ""})

    empty_score = _empty_rating_state()

    try:
        for token in stream_chat_reply(
            user_message=llm_prompt,
            history=context_history,
            system_prompt=str(RUNTIME_CONFIG["system_prompt"]),
            temperature=float(RUNTIME_CONFIG["temperature"]),
            max_tokens=int(RUNTIME_CONFIG["max_tokens"]),
        ):
            chat_history[-1]["content"] += token
            llm_history[-1]["content"] += token
            yield chat_history, llm_history, empty_score
    except Exception as exc:
        error_text = f"LLM 调用失败：{exc}"
        chat_history[-1]["content"] = error_text
        llm_history[-1]["content"] = error_text
        yield chat_history, llm_history, empty_score


def switch_to_prev_question(index):
    if not QUESTION_BANK:
        title, choices, progress = _question_payload(0)
        return (
            0,
            gr.update(value=title),
            gr.update(choices=choices, value=None, interactive=False),
            gr.update(value=""),
            gr.update(value=progress),
        )

    next_idx = _safe_question_index(int(index or 0) - 1)
    title, choices, progress = _question_payload(next_idx)
    return (
        next_idx,
        gr.update(value=title),
        gr.update(choices=choices, value=None, interactive=True),
        gr.update(value=""),
        gr.update(value=progress),
    )


def switch_to_next_question(index):
    if not QUESTION_BANK:
        title, choices, progress = _question_payload(0)
        return (
            0,
            gr.update(value=title),
            gr.update(choices=choices, value=None, interactive=False),
            gr.update(value=""),
            gr.update(value=progress),
        )

    next_idx = _safe_question_index(int(index or 0) + 1)
    title, choices, progress = _question_payload(next_idx)
    return (
        next_idx,
        gr.update(value=title),
        gr.update(choices=choices, value=None, interactive=True),
        gr.update(value=""),
        gr.update(value=progress),
    )


def submit_question_answer(selected_option, index):
    if not QUESTION_BANK:
        return "暂无题目数据。"

    idx = _safe_question_index(int(index or 0))
    question = QUESTION_BANK[idx]

    if not selected_option:
        return "请先选择一个选项。"

    selected_text = str(selected_option).strip()
    selected_key = selected_text.split(".", 1)[0].strip()
    correct_key = str(question.get("answer_key", "")).strip()
    correct_text = str(question.get("answer_text", correct_key)).strip()
    explanation = str(question.get("explanation", "")).strip() or "暂无解释。"

    is_correct = selected_key == correct_key
    status = "回答正确" if is_correct else "回答错误"
    return (
        f"**{status}**  \n"
        f"你的选择：`{selected_text}`  \n"
        f"正确答案：`{correct_text}`  \n"
        f"解释：{explanation}"
    )


def initialize_llm_session(chat_history, llm_history, question_index):
    chat_history = _normalize_history(chat_history)
    llm_history = _normalize_history(llm_history)
    if llm_history:
        empty_score = _empty_rating_state()
        yield chat_history, llm_history, empty_score
        return

    material_prompt = (
        "请阅读并记住下面的阅读材料，后续会基于该材料进行多轮选择题分析。"
        "请先回复“已收到阅读材料”。\n\n"
        f"{READING_MATERIAL}"
    )
    for updated_chat, updated_llm, score_update in _stream_auto_prompt(
        llm_prompt=material_prompt,
        chat_prompt="【系统初始化】已发送阅读材料，请先建立背景。",
        chat_history=chat_history,
        llm_history=llm_history,
    ):
        chat_history, llm_history = updated_chat, updated_llm
        yield chat_history, llm_history, score_update

    question_prompt, question_text = _build_question_prompt(int(question_index or 0))
    if question_prompt:
        for updated_chat, updated_llm, score_update in _stream_auto_prompt(
            llm_prompt=question_prompt,
            chat_prompt=f"【系统自动出题】\n{question_text}",
            chat_history=chat_history,
            llm_history=llm_history,
        ):
            chat_history, llm_history = updated_chat, updated_llm
            yield chat_history, llm_history, score_update


def auto_recommend_current_question(question_index, chat_history, llm_history):
    question_prompt, question_text = _build_question_prompt(int(question_index or 0))
    if not question_prompt:
        empty_score = _empty_rating_state()
        yield _normalize_history(chat_history), _normalize_history(llm_history), empty_score
        return

    for updated_chat, updated_llm, score_update in _stream_auto_prompt(
        llm_prompt=question_prompt,
        chat_prompt=f"【系统自动出题】\n{question_text}",
        chat_history=chat_history,
        llm_history=llm_history,
    ):
        yield updated_chat, updated_llm, score_update


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


def get_admin_status():
    settings = get_llm_settings()
    base_url = settings.base_url or "默认 provider endpoint"
    return f"""
### 当前后端状态
Provider: `{settings.provider}`

Model（环境）: `{settings.model}`

Base URL: `{base_url}`

API Key 环境变量: `{settings.api_key_env}`
"""


def save_admin_config(system_prompt, temperature, max_tokens, model_name):
    current_prompt = str(RUNTIME_CONFIG["system_prompt"])
    RUNTIME_CONFIG["system_prompt"] = (system_prompt or "").strip() or current_prompt
    RUNTIME_CONFIG["temperature"] = float(temperature)
    RUNTIME_CONFIG["max_tokens"] = int(max_tokens)
    RUNTIME_CONFIG["model"] = (model_name or "").strip() or str(RUNTIME_CONFIG["model"])
    return "配置已保存。实验页面后续对话将读取当前配置。"


def mock_apply_model(model_name):
    RUNTIME_CONFIG["model"] = (model_name or "").strip() or str(RUNTIME_CONFIG["model"])
    return f"[示意] 已切换模型为：{RUNTIME_CONFIG['model']}（未真实热更新到底层 provider）"


def confirm_trust_rating(_score_value):
    return None


def respond(message, history, llm_history):
    if not message or not str(message).strip():
        empty_score = _empty_rating_state()
        return "", history, llm_history, empty_score

    user_message = str(message).strip()
    chat_history = _normalize_history(history)
    llm_history = _normalize_history(llm_history)

    context_history = list(llm_history)
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": ""})
    llm_history.append({"role": "user", "content": user_message})
    llm_history.append({"role": "assistant", "content": ""})

    empty_score = _empty_rating_state()

    try:
        for token in stream_chat_reply(
            user_message=user_message,
            history=context_history,
            system_prompt=str(RUNTIME_CONFIG["system_prompt"]),
            temperature=float(RUNTIME_CONFIG["temperature"]),
            max_tokens=int(RUNTIME_CONFIG["max_tokens"]),
        ):
            chat_history[-1]["content"] += token
            llm_history[-1]["content"] += token
            yield "", chat_history, llm_history, empty_score
    except Exception as exc:
        error_text = f"LLM 调用失败：{exc}"
        chat_history[-1]["content"] = error_text
        llm_history[-1]["content"] = error_text
        yield "", chat_history, llm_history, empty_score


def toggle_reading_panel(is_visible):
    new_visible = not bool(is_visible)
    button_text = "关闭阅读材料" if new_visible else "打开阅读材料"
    return (
        new_visible,
        gr.update(visible=new_visible),
        gr.update(value=button_text),
    )


def build_login_demo():
    with gr.Blocks(title="登录 - TrustAgent") as demo:
        gr.HTML(f"<style>{LOGIN_CSS}</style>")
        gr.Markdown("# 登录")
        gr.Markdown("请输入实验密钥与被试姓名。密钥一次有效，用后作废。")

        gate_key = gr.Textbox(
            label="实验密钥",
            placeholder="请输入密钥",
            type="password"
        )
        gate_subject = gr.Textbox(
            label="被试姓名",
            placeholder="请输入被试姓名"
        )
        gate_submit = gr.Button("验证并进入", variant="primary")
        gate_status = gr.Markdown("等待验证。")
        redirect_html = gr.HTML("")

        gate_submit.click(
            login_and_enter,
            inputs=[gate_key, gate_subject],
            outputs=[gate_status, redirect_html, gate_key, gate_subject],
        )
    return demo


def build_experiment_demo():
    with gr.Blocks(title="实验 - TrustAgent") as demo:
        gr.HTML(f"<style>{EXPERIMENT_CSS}</style>")

        reading_panel_visible = gr.State(True)
        question_index_state = gr.State(0)
        llm_history_state = gr.State([])
        initial_question_title, initial_choices, initial_progress = _question_payload(0)

        with gr.Column(elem_classes=["top-title"]):
            gr.Markdown("# 可信智能体实验")

        with gr.Row():
            with gr.Column(elem_classes=["scene-switch"]):
                scene_selector = gr.Radio(
                    choices=["聊天", "问答", "规划"],
                    value="问答",
                    label="实验场景切换",
                    interactive=True,
                )

        with gr.Row(elem_classes=["main-layout"]):
            with gr.Column(scale=4, elem_classes=["reading-column"]):
                toggle_reading_btn = gr.Button(
                    "关闭阅读材料",
                    variant="secondary",
                    elem_classes=["reading-toggle-btn"],
                )

                with gr.Column(visible=True, elem_classes=["reading-panel"]) as reading_panel:
                    gr.Markdown("### 阅读材料")
                    reading_text = gr.Textbox(
                        value=READING_MATERIAL,
                        lines=35,
                        interactive=True,
                        placeholder="这里可以放入阅读理解材料……",
                    )

            with gr.Column(scale=8, elem_classes=["chat-panel"]):
                with gr.Column(elem_classes=["question-panel"]):
                    question_progress = gr.Markdown(initial_progress)
                    question_md = gr.Markdown(initial_question_title)
                    question_options = gr.Radio(
                        choices=initial_choices,
                        value=None,
                        interactive=bool(initial_choices),
                    )
                    with gr.Row():
                        prev_question_btn = gr.Button("上一题", variant="secondary")
                        next_question_btn = gr.Button("下一题", variant="secondary")
                        confirm_answer_btn = gr.Button("确定", variant="primary")
                    answer_feedback = gr.Markdown("")

                chatbot = gr.Chatbot(
                    label="对话",
                    elem_id="chatbot",
                    avatar_images=(None, None),
                    buttons=["copy"],
                    height=360,
                )

                with gr.Column(elem_classes=["rating-panel"]):
                    with gr.Row():
                        with gr.Column(scale=7):
                            trust_score = gr.Radio(
                                choices=[str(i) for i in range(1, 8)],
                                value=None,
                                label=None,
                                show_label=False,
                                interactive=True,
                            )
                        with gr.Column(scale=3, min_width=120):
                            trust_confirm_btn = gr.Button(
                                "信任评分",
                                variant="secondary",
                                elem_classes=["trust-confirm-btn"],
                            )

                with gr.Group(elem_classes=["composer-wrap"]):
                    message = gr.Textbox(
                        placeholder="输入问题后按 Enter 发送；Shift + Enter 换行。",
                        elem_id="composer",
                        lines=2,
                        container=True,
                    )
                    send_btn = gr.Button("➤", variant="primary", elem_classes=["send-inside-btn"])

        message.submit(
            respond,
            inputs=[message, chatbot, llm_history_state],
            outputs=[message, chatbot, llm_history_state, trust_score],
        )
        send_btn.click(
            respond,
            inputs=[message, chatbot, llm_history_state],
            outputs=[message, chatbot, llm_history_state, trust_score],
        )

        trust_confirm_btn.click(
            confirm_trust_rating,
            inputs=[trust_score],
            outputs=[],
        )

        toggle_reading_btn.click(
            toggle_reading_panel,
            inputs=[reading_panel_visible],
            outputs=[reading_panel_visible, reading_panel, toggle_reading_btn],
        )

        prev_question_btn.click(
            switch_to_prev_question,
            inputs=[question_index_state],
            outputs=[question_index_state, question_md, question_options, answer_feedback, question_progress],
        ).then(
            auto_recommend_current_question,
            inputs=[question_index_state, chatbot, llm_history_state],
            outputs=[chatbot, llm_history_state, trust_score],
        )
        next_question_btn.click(
            switch_to_next_question,
            inputs=[question_index_state],
            outputs=[question_index_state, question_md, question_options, answer_feedback, question_progress],
        ).then(
            auto_recommend_current_question,
            inputs=[question_index_state, chatbot, llm_history_state],
            outputs=[chatbot, llm_history_state, trust_score],
        )
        confirm_answer_btn.click(
            submit_question_answer,
            inputs=[question_options, question_index_state],
            outputs=[answer_feedback],
        )

        demo.load(
            initialize_llm_session,
            inputs=[chatbot, llm_history_state, question_index_state],
            outputs=[chatbot, llm_history_state, trust_score],
        )

    return demo


def build_admin_demo():
    with gr.Blocks(title="管理 - TrustAgent") as demo:
        gr.HTML(f"<style>{ADMIN_CSS}</style>")
        gr.Markdown("# 管理页面")
        gr.Markdown("在此设置实验页面使用的参数。")
        gr.Markdown("[前往登录页](/login) | [前往实验页](/experiment)")

        system_prompt = gr.Textbox(
            label="系统提示词",
            value=str(RUNTIME_CONFIG["system_prompt"]),
            lines=5,
        )
        temperature = gr.Slider(
            label="Temperature",
            minimum=0,
            maximum=2,
            value=float(RUNTIME_CONFIG["temperature"]),
            step=0.1,
        )
        max_tokens = gr.Slider(
            label="Max tokens",
            minimum=128,
            maximum=4096,
            value=int(RUNTIME_CONFIG["max_tokens"]),
            step=128,
        )
        model_selector = gr.Dropdown(
            label="目标模型（示意）",
            choices=MODEL_OPTIONS,
            value=str(RUNTIME_CONFIG["model"]),
            interactive=True,
        )

        with gr.Row():
            save_btn = gr.Button("保存参数", variant="primary")
            apply_model_btn = gr.Button("应用模型（示意）", variant="secondary")

        admin_result = gr.Markdown("等待操作。")
        model_result = gr.Markdown("等待模型切换。")
        backend_status = gr.Markdown(get_admin_status())
        refresh_status_btn = gr.Button("刷新后端状态")

        save_btn.click(
            save_admin_config,
            inputs=[system_prompt, temperature, max_tokens, model_selector],
            outputs=admin_result,
        )
        apply_model_btn.click(
            mock_apply_model,
            inputs=model_selector,
            outputs=model_result,
        )
        refresh_status_btn.click(lambda: get_admin_status(), outputs=backend_status)

    return demo


def create_fastapi_app():
    app = FastAPI(title=APP_TITLE)

    login_demo = build_login_demo()
    experiment_demo = build_experiment_demo()
    admin_demo = build_admin_demo()

    app = gr.mount_gradio_app(app, login_demo, path="/login")
    app = gr.mount_gradio_app(app, experiment_demo, path="/experiment")
    app = gr.mount_gradio_app(app, admin_demo, path="/admin")

    @app.get("/")
    def root():
        return RedirectResponse(url="/login")

    return app


fastapi_app = create_fastapi_app()


if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860, access_log=False)