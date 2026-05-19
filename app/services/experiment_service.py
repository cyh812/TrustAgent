from html import escape

import gradio as gr

from agent.llm_agent import get_llm_settings, stream_chat_reply
from app.config import CHAT_SYSTEM_PROMPT_TEMPLATE, EXPERIMENT_CONTEXT, MODEL_OPTIONS, RUNTIME_CONFIG
from app.services.data_service import QUESTION_BANK, READING_MATERIAL
from app.services.key_service import current_time_text

CHAT_MAX_TURNS = 6


def snapshot_experiment_context():
    return dict(EXPERIMENT_CONTEXT)


def normalize_history(history):
    normalized = []
    for item in history or []:
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized.append({"role": item["role"], "content": item["content"]})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user_content, assistant_content = item
            if user_content is not None:
                normalized.append({"role": "user", "content": str(user_content)})
            if assistant_content is not None:
                normalized.append({"role": "assistant", "content": str(assistant_content)})
        elif hasattr(item, "role") and hasattr(item, "content"):
            normalized.append({"role": item.role, "content": item.content})
    return normalized


def custom_chat_records_to_messages(records):
    messages = []
    for record in records or []:
        if not isinstance(record, dict):
            continue

        user_content = str(record.get("user") or "").strip()
        if user_content:
            messages.append({"role": "user", "content": user_content})

        assistant_content = str(record.get("assistant") or "").strip()
        if assistant_content:
            messages.append({"role": "assistant", "content": assistant_content})
            continue

        selected_option = record.get("selected_option")
        options = record.get("assistant_options") or []
        if selected_option and isinstance(options, list):
            for option in options:
                if not isinstance(option, dict):
                    continue
                if str(option.get("id")) == str(selected_option):
                    selected_content = str(option.get("content") or "").strip()
                    if selected_content:
                        messages.append({"role": "assistant", "content": selected_content})
                    break
    return messages


def format_message_html(content):
    text = str(content or "")
    escaped_text = escape(text)
    try:
        import markdown

        return markdown.markdown(
            escaped_text,
            extensions=["extra", "sane_lists", "nl2br"],
            output_format="html5",
        )
    except Exception:
        pass

    try:
        from markdown_it import MarkdownIt

        return MarkdownIt("commonmark", {"breaks": True, "html": False}).render(escaped_text)
    except Exception:
        return escaped_text.replace("\n", "<br>")


def current_chat_task_intro(context=None):
    context = context or EXPERIMENT_CONTEXT
    instruction = str(context.get("chat_user_instruction") or "").strip()
    if instruction:
        return instruction

    topic = str(context.get("chat_topic") or "").strip()
    if topic:
        return f"请围绕“{topic}”与 Agent 自然展开聊天。"
    return "本次聊天主题尚未配置。"


def build_chat_system_prompt(context=None):
    context = context or EXPERIMENT_CONTEXT
    return CHAT_SYSTEM_PROMPT_TEMPLATE.format(
        emotional_valence_prompt=str(context.get("emotional_valence_prompt") or "").strip(),
        transparency_prompt=str(context.get("transparency_prompt") or "").strip(),
        stance_strategy_prompt=str(context.get("stance_strategy_prompt") or "").strip(),
        certainty_prompt=str(context.get("certainty_prompt") or "").strip(),
        initiative_prompt=str(context.get("initiative_prompt") or "").strip(),
    )


def render_custom_chat(records, context=None):
    intro = format_message_html(current_chat_task_intro(context))
    items = [
        '<div class="custom-chat-window">',
        f"""
        <div class="custom-topic-card">
            <div class="custom-topic-label">本次聊天主题</div>
            <div class="custom-topic-body">{intro}</div>
        </div>
        """,
    ]

    if not records:
        items.append('<div class="custom-chat-empty">对话尚未开始。</div>')
        items.append("</div>")
        return "".join(items)

    for record in records:
        if not isinstance(record, dict):
            continue

        user_content = format_message_html(record.get("user", ""))
        assistant_content = format_message_html(record.get("assistant", ""))
        items.append(
            f"""
            <section class="custom-chat-turn">
                <div class="custom-message custom-message-user">
                    <div class="custom-message-label">你</div>
                    <div class="custom-message-body">{user_content}</div>
                </div>
            """
        )

        options = record.get("assistant_options") or []
        if options:
            items.append('<div class="custom-answer-options">')
            for option in options:
                if not isinstance(option, dict):
                    continue
                option_id = escape(str(option.get("id") or ""))
                option_title = escape(str(option.get("title") or f"回答 {option_id}"))
                option_content = format_message_html(option.get("content", ""))
                selected_class = " selected" if str(record.get("selected_option")) == option_id else ""
                items.append(
                    f"""
                    <div class="custom-answer-card{selected_class}">
                        <div class="custom-answer-title">{option_title}</div>
                        <div class="custom-answer-body">{option_content}</div>
                    </div>
                    """
                )
            items.append("</div>")
        else:
            items.append(
                f"""
                <div class="custom-message custom-message-assistant">
                    <div class="custom-message-label">TrustAgent</div>
                    <div class="custom-message-body">{assistant_content}</div>
                </div>
                """
            )

        rating = record.get("rating")
        if rating is not None:
            items.append(f'<div class="custom-turn-rating">本轮评分：{escape(str(rating))}</div>')

        items.append("</section>")

    items.append("</div>")
    return "".join(items)


def initialize_custom_chat_window(records, context=None):
    return render_custom_chat(records, context)


def initialize_custom_chat_session(records):
    context = snapshot_experiment_context()
    return context, render_custom_chat(records, context)


def show_chat_rating_if_complete(records):
    complete_turns = [
        record
        for record in records or []
        if isinstance(record, dict) and str(record.get("assistant") or "").strip()
    ]
    if len(complete_turns) >= CHAT_MAX_TURNS:
        return gr.update(visible=True)
    return gr.update(visible=False, value=None)


def empty_rating_state():
    return gr.update(value=None)


def switch_experiment_scene(scene):
    selected_scene = scene or "问答"
    is_chat = selected_scene == "聊天"
    is_question = selected_scene == "问答"
    is_planning = selected_scene == "规划"

    return (
        gr.update(visible=is_question),
        gr.update(visible=is_chat),
        gr.update(visible=is_planning),
        gr.update(visible=is_question),
    )


def safe_question_index(index: int) -> int:
    if not QUESTION_BANK:
        return 0
    return max(0, min(index, len(QUESTION_BANK) - 1))


def question_payload(index: int):
    if not QUESTION_BANK:
        return "### 题目切换\n暂无题目数据。", [], "第 0 / 0 题"

    idx = safe_question_index(index)
    q = QUESTION_BANK[idx]
    title = f"### {q['block_name']} · {q['question_id']}\n\n{q['question']}"
    progress = f"第 {idx + 1} / {len(QUESTION_BANK)} 题"
    return title, q["choices"], progress


def build_question_prompt(index: int):
    if not QUESTION_BANK:
        return "", "暂无题目数据。"

    idx = safe_question_index(index)
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


def stream_auto_prompt(llm_prompt, chat_prompt, chat_history, llm_history):
    chat_history = normalize_history(chat_history)
    llm_history = normalize_history(llm_history)

    context_history = list(llm_history)
    chat_history.append({"role": "user", "content": chat_prompt})
    chat_history.append({"role": "assistant", "content": ""})
    llm_history.append({"role": "user", "content": llm_prompt})
    llm_history.append({"role": "assistant", "content": ""})

    empty_score = empty_rating_state()

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
        title, choices, progress = question_payload(0)
        return (
            0,
            gr.update(value=title),
            gr.update(choices=choices, value=None, interactive=False),
            gr.update(value=""),
            gr.update(value=progress),
        )

    next_idx = safe_question_index(int(index or 0) - 1)
    title, choices, progress = question_payload(next_idx)
    return (
        next_idx,
        gr.update(value=title),
        gr.update(choices=choices, value=None, interactive=True),
        gr.update(value=""),
        gr.update(value=progress),
    )


def switch_to_next_question(index):
    if not QUESTION_BANK:
        title, choices, progress = question_payload(0)
        return (
            0,
            gr.update(value=title),
            gr.update(choices=choices, value=None, interactive=False),
            gr.update(value=""),
            gr.update(value=progress),
        )

    next_idx = safe_question_index(int(index or 0) + 1)
    title, choices, progress = question_payload(next_idx)
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

    idx = safe_question_index(int(index or 0))
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
    chat_history = normalize_history(chat_history)
    llm_history = normalize_history(llm_history)
    if llm_history:
        yield chat_history, llm_history, empty_rating_state()
        return

    material_prompt = (
        "请阅读并记住下面的阅读材料，后续会基于该材料进行多轮选择题分析。"
        "请先回复“已收到阅读材料”。\n\n"
        f"{READING_MATERIAL}"
    )
    for updated_chat, updated_llm, score_update in stream_auto_prompt(
        llm_prompt=material_prompt,
        chat_prompt="【系统初始化】已发送阅读材料，请先建立背景。",
        chat_history=chat_history,
        llm_history=llm_history,
    ):
        chat_history, llm_history = updated_chat, updated_llm
        yield chat_history, llm_history, score_update

    question_prompt, question_text = build_question_prompt(int(question_index or 0))
    if question_prompt:
        for updated_chat, updated_llm, score_update in stream_auto_prompt(
            llm_prompt=question_prompt,
            chat_prompt=f"【系统自动出题】\n{question_text}",
            chat_history=chat_history,
            llm_history=llm_history,
        ):
            chat_history, llm_history = updated_chat, updated_llm
            yield chat_history, llm_history, score_update


def auto_recommend_current_question(question_index, chat_history, llm_history):
    question_prompt, question_text = build_question_prompt(int(question_index or 0))
    if not question_prompt:
        yield normalize_history(chat_history), normalize_history(llm_history), empty_rating_state()
        return

    for updated_chat, updated_llm, score_update in stream_auto_prompt(
        llm_prompt=question_prompt,
        chat_prompt=f"【系统自动出题】\n{question_text}",
        chat_history=chat_history,
        llm_history=llm_history,
    ):
        yield updated_chat, updated_llm, score_update


def respond(message, history, llm_history):
    if not message or not str(message).strip():
        return "", history, llm_history, empty_rating_state()

    user_message = str(message).strip()
    chat_history = normalize_history(history)
    llm_history = normalize_history(llm_history)

    context_history = list(llm_history)
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": ""})
    llm_history.append({"role": "user", "content": user_message})
    llm_history.append({"role": "assistant", "content": ""})

    empty_score = empty_rating_state()

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


def respond_chat(message, history, llm_history):
    for next_message, chat_history, next_llm_history, _score_update in respond(
        message,
        history,
        llm_history,
    ):
        yield next_message, chat_history, next_llm_history


def respond_custom_chat(message, records, llm_history, chat_context=None):
    if not message or not str(message).strip():
        yield "", render_custom_chat(records, chat_context), records, llm_history, gr.update(), gr.update(), show_chat_rating_if_complete(records)
        return

    user_message = str(message).strip()
    chat_records = list(records or [])
    if len(chat_records) >= CHAT_MAX_TURNS:
        yield (
            "",
            render_custom_chat(chat_records, chat_context),
            chat_records,
            normalize_history(llm_history),
            gr.update(interactive=False),
            gr.update(interactive=False),
            show_chat_rating_if_complete(chat_records),
        )
        return

    llm_history = normalize_history(llm_history)
    context_history = list(llm_history)

    record = {
        "turn_index": len(chat_records) + 1,
        "mode": "single",
        "user": user_message,
        "user_timestamp": current_time_text(),
        "assistant": "",
        "assistant_timestamp": "",
        "assistant_options": [],
        "selected_option": None,
        "rating": None,
    }
    chat_records.append(record)
    llm_history.append({"role": "user", "content": user_message})
    llm_history.append({"role": "assistant", "content": ""})

    try:
        for token in stream_chat_reply(
            user_message=user_message,
            history=context_history,
            system_prompt=build_chat_system_prompt(chat_context),
            temperature=float(RUNTIME_CONFIG["temperature"]),
            max_tokens=int(RUNTIME_CONFIG["max_tokens"]),
        ):
            record["assistant"] += token
            llm_history[-1]["content"] += token
            yield "", render_custom_chat(chat_records, chat_context), chat_records, llm_history, gr.update(), gr.update(), gr.update()

        record["assistant_timestamp"] = current_time_text()
        input_update = gr.update(interactive=False) if len(chat_records) >= CHAT_MAX_TURNS else gr.update()
        button_update = gr.update(interactive=False) if len(chat_records) >= CHAT_MAX_TURNS else gr.update()
        yield "", render_custom_chat(chat_records, chat_context), chat_records, llm_history, input_update, button_update, show_chat_rating_if_complete(chat_records)
    except Exception as exc:
        error_text = f"LLM 调用失败：{exc}"
        record["assistant"] = error_text
        record["assistant_timestamp"] = current_time_text()
        llm_history[-1]["content"] = error_text
        yield "", render_custom_chat(chat_records, chat_context), chat_records, llm_history, gr.update(), gr.update(), show_chat_rating_if_complete(chat_records)


def toggle_reading_panel(is_visible):
    new_visible = not bool(is_visible)
    button_text = "关闭阅读材料" if new_visible else "打开阅读材料"
    return (
        new_visible,
        gr.update(visible=new_visible),
        gr.update(value=button_text),
    )


def confirm_trust_rating(_score_value):
    return None


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


def model_options():
    return MODEL_OPTIONS
