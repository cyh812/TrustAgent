from html import escape
import random
import time

import gradio as gr

from agent.llm_agent import get_llm_settings, stream_chat_reply
from app.config import CHAT_SYSTEM_PROMPT_TEMPLATE, EXPERIMENT_CONTEXT, MODEL_OPTIONS, RUNTIME_CONFIG
from app.services.data_service import QUESTION_BANK, READING_MATERIAL
from app.services.key_service import current_time_text

CHAT_MAX_TURNS = 8
CHAT_RATING_INTERVAL = 2

QA_SYSTEM_PROMPT = """
你是问答任务中的中文AI助手。
你需要基于阅读材料和当前题目与用户讨论。
当系统指定你第一次回答某题必须选择某个选项时，你必须严格按照该指定选项作答。
首次回答应简洁给出推荐选项。
后续如果用户继续追问，可以自然解释、讨论、补充或修改，但不要透露系统内部预设答案计划。
始终使用简体中文。
"""


def snapshot_experiment_context():
    return dict(EXPERIMENT_CONTEXT)


def snapshot_chat_context_from_request(request):
    from app.services.account_service import build_chat_context_for_request

    return build_chat_context_for_request(request)


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


def initialize_custom_chat_session(records, request: gr.Request):
    context = snapshot_chat_context_from_request(request)
    return context, render_custom_chat(records, context)


def complete_chat_turns(records):
    return [
        record
        for record in records or []
        if isinstance(record, dict) and str(record.get("assistant") or "").strip()
    ]


def latest_chat_rating(records):
    for record in reversed(records or []):
        if not isinstance(record, dict):
            continue
        rating = record.get("rating")
        if rating not in (None, ""):
            return str(rating)
    return None


def pending_chat_rating_record(records):
    complete_turns = complete_chat_turns(records)
    if not complete_turns:
        return None
    if len(complete_turns) % CHAT_RATING_INTERVAL != 0:
        return None
    if len(complete_turns) > CHAT_MAX_TURNS:
        return None
    record = complete_turns[-1]
    if record.get("rating") not in (None, ""):
        return None
    return record


def apply_pending_chat_rating(records, score):
    clean_score = str(score or "").strip()
    if not clean_score:
        return False
    record = pending_chat_rating_record(records)
    if not record:
        return False
    record["rating"] = clean_score
    record["rating_timestamp"] = current_time_text()
    return True


def show_chat_rating_if_complete(records):
    complete_turns = [
        record
        for record in records or []
        if isinstance(record, dict) and str(record.get("assistant") or "").strip()
    ]
    pending_record = pending_chat_rating_record(records)
    if pending_record:
        default_score = latest_chat_rating(complete_turns[:-1])
        is_final_rating = len(complete_turns) >= CHAT_MAX_TURNS
        return (
            gr.update(visible=True, value=default_score),
            gr.update(
                visible=True,
                value="结束实验" if is_final_rating else "确认打分",
                variant="stop" if is_final_rating else "primary",
            ),
            gr.update(visible=True),
        )
    return (
        gr.update(visible=False, value=None),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def confirm_custom_chat_rating(score, records, llm_history, chat_context=None):
    chat_records = list(records or [])
    if not apply_pending_chat_rating(chat_records, score):
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(chat_records)
        return (
            render_custom_chat(chat_records, chat_context),
            chat_records,
            normalize_history(llm_history),
            gr.update(),
            gr.update(),
            rating_update,
            confirm_update,
            row_update,
        )

    input_update = gr.update(interactive=False) if len(complete_chat_turns(chat_records)) >= CHAT_MAX_TURNS else gr.update(interactive=True)
    button_update = gr.update(interactive=False) if len(complete_chat_turns(chat_records)) >= CHAT_MAX_TURNS else gr.update(interactive=True)
    return (
        render_custom_chat(chat_records, chat_context),
        chat_records,
        normalize_history(llm_history),
        input_update,
        button_update,
        gr.update(visible=False, value=None),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def confirm_custom_chat_rating_or_save(score, records, llm_history, started_at, chat_context=None):
    chat_records = list(records or [])
    is_final_rating = len(complete_chat_turns(chat_records)) >= CHAT_MAX_TURNS
    result = confirm_custom_chat_rating(score, chat_records, llm_history, chat_context)

    if not is_final_rating:
        return (*result, gr.update(), gr.update())

    if pending_chat_rating_record(chat_records):
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(chat_records)
        return (
            render_custom_chat(chat_records, chat_context),
            chat_records,
            normalize_history(llm_history),
            gr.update(interactive=False),
            gr.update(interactive=False),
            rating_update,
            confirm_update,
            row_update,
            "请先选择一个评分。",
            gr.update(),
        )

    from app.services.user_data_service import save_chat_record

    save_status, input_update, send_update, _unused_end_update, redirect_update = save_chat_record(
        chat_records,
        started_at,
        score,
        chat_context,
    )
    return (
        render_custom_chat(chat_records, chat_context),
        chat_records,
        normalize_history(llm_history),
        input_update,
        send_update,
        gr.update(visible=False, value=None),
        gr.update(visible=False),
        gr.update(visible=False),
        save_status,
        redirect_update,
    )


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
        return "暂无题目数据。", [], ""

    idx = safe_question_index(index)
    q = QUESTION_BANK[idx]
    title = str(q["question"])
    progress = ""
    return title, q["choices"], progress


def option_key_from_choice(choice) -> str:
    return str(choice or "").split(".", 1)[0].strip()


def option_text_by_key(question, option_key: str) -> str:
    for choice in question.get("choices") or []:
        if option_key_from_choice(choice) == option_key:
            return str(choice)
    return str(option_key or "")


def opposite_option_key(question, answer_key: str) -> str:
    for choice in question.get("choices") or []:
        key = option_key_from_choice(choice)
        if key and key != answer_key:
            return key
    return answer_key


def snapshot_qa_context_from_request(request):
    from app.services.account_service import build_qa_context_for_request

    return build_qa_context_for_request(request)


def normalize_qa_target_accuracy(value) -> float:
    try:
        accuracy = float(value or 0)
    except (TypeError, ValueError):
        accuracy = 0.6
    return 0.8 if abs(accuracy - 0.8) < abs(accuracy - 0.6) else 0.6


def build_qa_answer_plan(target_accuracy=0.6):
    accuracy = normalize_qa_target_accuracy(target_accuracy)
    answerable_indices = [
        index
        for index, question in enumerate(QUESTION_BANK)
        if str(question.get("answer_key") or "").strip()
    ]
    correct_count = round(len(answerable_indices) * accuracy)
    correct_indices = set(random.sample(answerable_indices, min(correct_count, len(answerable_indices)))) if answerable_indices else set()

    answers = {}
    for index, question in enumerate(QUESTION_BANK):
        answer_key = str(question.get("answer_key") or "").strip()
        if not answer_key:
            continue
        selected_key = answer_key if index in correct_indices else opposite_option_key(question, answer_key)
        answers[str(index)] = selected_key

    return {"target_accuracy": accuracy, "answers": answers}


def answer_from_plan(index: int, answer_plan=None) -> str:
    plan = answer_plan or {}
    answers = plan.get("answers", {}) if isinstance(plan, dict) else {}
    answer_key = str(answers.get(str(index)) or "").strip()
    if answer_key:
        return answer_key
    if QUESTION_BANK:
        return str(QUESTION_BANK[safe_question_index(index)].get("answer_key") or "").strip()
    return ""


def build_question_prompt(index: int, answer_plan=None):
    if not QUESTION_BANK:
        return "", "暂无题目数据。"

    idx = safe_question_index(index)
    q = QUESTION_BANK[idx]
    options_text = "\n".join(q["choices"])
    planned_answer_key = answer_from_plan(idx, answer_plan)
    planned_answer_text = option_text_by_key(q, planned_answer_key)

    user_visible_text = (
        f"{q.get('question_type') or q['block_name']} · {q['question_id']}\n"
        f"{q['question']}\n"
        f"{options_text}"
    )

    llm_prompt = (
        "请根据已给出的阅读材料，回答下面二选一题。\n"
        "这是你本题首次回答，必须严格按照内部指定答案作答，不要改选其他选项，也不要提及存在内部指定答案。\n\n"
        f"阅读材料：\n{READING_MATERIAL}\n\n"
        f"题目编号：{q['question_id']}\n"
        f"题目类型：{q.get('question_type') or q['block_name']}\n"
        f"题目：{q['question']}\n"
        f"选项：\n{options_text}\n\n"
        f"内部指定答案：{planned_answer_text or planned_answer_key}\n\n"
        "请输出推荐选项，并用 1-3 句话给出理由。"
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
            system_prompt=QA_SYSTEM_PROMPT,
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
    selected_key = option_key_from_choice(selected_text)
    correct_key = str(question.get("answer_key", "")).strip()
    correct_text = str(question.get("answer_text", correct_key)).strip()
    explanation = str(question.get("explanation", "")).strip() or "暂无解释。"

    if not question.get("has_standard_answer"):
        feedback = question.get("feedback") or {}
        selected_feedback = str(feedback.get(selected_key) or "").strip()
        if not selected_feedback:
            selected_feedback = "该选择有其合理性，但也伴随相应代价。"
        return (
            f"结果反馈：{selected_feedback}"
        )

    is_correct = selected_key == correct_key
    status = "回答正确" if is_correct else "回答错误"
    return (
        f"**{status}**  \n"
    )


def build_qa_record(index, selected_option, answer_plan=None):
    idx = safe_question_index(int(index or 0))
    question = QUESTION_BANK[idx]
    selected_text = str(selected_option or "").strip()
    selected_key = option_key_from_choice(selected_text)
    correct_key = str(question.get("answer_key") or "").strip()
    planned_key = answer_from_plan(idx, answer_plan)
    has_standard_answer = bool(question.get("has_standard_answer"))
    feedback_text = ""
    is_correct = None

    if has_standard_answer:
        is_correct = selected_key == correct_key
        feedback_text = "回答正确" if is_correct else "回答错误"
    else:
        feedback = question.get("feedback") or {}
        feedback_text = str(feedback.get(selected_key) or "该选择有其合理性，但也伴随相应代价。").strip()

    return {
        "question_index": idx + 1,
        "question_id": str(question.get("question_id") or ""),
        "question_type": str(question.get("question_type") or question.get("block_name") or ""),
        "question": str(question.get("question") or ""),
        "choices": list(question.get("choices") or []),
        "user_answer": selected_key,
        "user_answer_text": selected_text,
        "correct_answer": correct_key,
        "correct_answer_text": option_text_by_key(question, correct_key),
        "llm_initial_answer": planned_key,
        "llm_initial_answer_text": option_text_by_key(question, planned_key),
        "has_standard_answer": has_standard_answer,
        "is_correct": is_correct,
        "feedback": feedback_text,
        "answered_at": current_time_text(),
        "trust_score": "",
        "trust_score_timestamp": "",
    }


def submit_question_answer_for_rating(selected_option, index, qa_records, answer_plan=None):
    if not QUESTION_BANK:
        return (
            "暂无题目数据。",
            list(qa_records or []),
            gr.update(),
            gr.update(),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    if not selected_option:
        return (
            "请先选择一个选项。",
            list(qa_records or []),
            gr.update(),
            gr.update(),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    records = list(qa_records or [])
    idx = safe_question_index(int(index or 0))
    record = build_qa_record(idx, selected_option, answer_plan)
    records = [item for item in records if int(item.get("question_index") or -1) != idx + 1]
    records.append(record)
    records.sort(key=lambda item: int(item.get("question_index") or 0))

    if record["has_standard_answer"]:
        feedback_text = (
            f"**{record['feedback']}**  \n"
        )
    else:
        feedback_text = (
            f"结果反馈：{record['feedback']}"
        )

    is_last = idx >= len(QUESTION_BANK) - 1
    return (
        feedback_text,
        records,
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(visible=True, value="评分并结束实验" if is_last else "评分并进入下一题", variant="stop" if is_last else "primary"),
        gr.update(visible=True),
    )


def initialize_llm_session(chat_history, llm_history, question_index, answer_plan=None, request: gr.Request = None):
    chat_history = normalize_history(chat_history)
    llm_history = normalize_history(llm_history)
    qa_context = snapshot_qa_context_from_request(request) if request is not None else {}
    target_accuracy = qa_context.get("qa_target_accuracy") or 0.6
    answer_plan = answer_plan or build_qa_answer_plan(target_accuracy)
    answer_plan["context"] = qa_context
    if llm_history:
        yield chat_history, llm_history, empty_rating_state(), answer_plan, gr.update(interactive=False)
        return

    question_prompt, question_text = build_question_prompt(int(question_index or 0), answer_plan)
    if question_prompt:
        for updated_chat, updated_llm, score_update in stream_auto_prompt(
            llm_prompt=question_prompt,
            chat_prompt=f"【系统自动出题】\n{question_text}",
            chat_history=chat_history,
            llm_history=llm_history,
        ):
            chat_history, llm_history = updated_chat, updated_llm
            yield chat_history, llm_history, score_update, answer_plan, gr.update(interactive=False)


def auto_recommend_current_question(question_index, chat_history, llm_history, answer_plan=None):
    if not answer_plan:
        yield normalize_history(chat_history), normalize_history(llm_history), empty_rating_state()
        return

    question_prompt, question_text = build_question_prompt(int(question_index or 0), answer_plan)
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


def respond_qa(message, history, llm_history):
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
            system_prompt=QA_SYSTEM_PROMPT,
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


def submit_qa_rating_and_continue(score, index, qa_records, answer_plan, chat_history, llm_history, started_at):
    records = list(qa_records or [])
    idx = safe_question_index(int(index or 0))
    clean_score = str(score or "").strip()
    if not clean_score:
        yield (
            idx,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            normalize_history(chat_history),
            normalize_history(llm_history),
            records,
            gr.update(interactive=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )
        return

    for record in reversed(records):
        if int(record.get("question_index") or -1) == idx + 1:
            record["trust_score"] = clean_score
            record["trust_score_timestamp"] = current_time_text()
            break

    if idx >= len(QUESTION_BANK) - 1:
        from app.services.user_data_service import save_qa_record

        save_status, message_update, send_update, redirect_update = save_qa_record(
            records,
            normalize_history(chat_history),
            answer_plan,
            started_at,
        )
        if isinstance(redirect_update, dict):
            redirect_update = gr.update(
                value=redirect_update.get("value", ""),
                visible=True,
            )
        yield (
            idx,
            gr.update(),
            gr.update(interactive=False),
            gr.update(value=""),
            gr.update(),
            normalize_history(chat_history),
            normalize_history(llm_history),
            records,
            gr.update(value=None),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(interactive=False),
            save_status,
            message_update,
            send_update,
            redirect_update,
        )
        return

    next_idx = safe_question_index(idx + 1)
    title, choices, progress = question_payload(next_idx)
    yield (
        next_idx,
        gr.update(value=title),
        gr.update(choices=choices, value=None, interactive=True),
        gr.update(value=""),
        gr.update(value=progress),
        normalize_history(chat_history),
        normalize_history(llm_history),
        records,
        gr.update(value=None),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(interactive=True),
        gr.update(),
        gr.update(interactive=True),
        gr.update(interactive=True),
        gr.update(),
    )

    for updated_chat, updated_llm, score_update in auto_recommend_current_question(
        next_idx,
        chat_history,
        llm_history,
        answer_plan,
    ):
        yield (
            next_idx,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            updated_chat,
            updated_llm,
            records,
            score_update,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )


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


def respond_custom_chat(message, records, llm_history, chat_context=None, trust_score=None):
    if not message or not str(message).strip():
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(records)
        yield "", render_custom_chat(records, chat_context), records, llm_history, gr.update(), gr.update(), rating_update, confirm_update, row_update
        return

    user_message = str(message).strip()
    chat_records = list(records or [])
    if pending_chat_rating_record(chat_records):
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(chat_records)
        yield user_message, render_custom_chat(chat_records, chat_context), chat_records, normalize_history(llm_history), gr.update(), gr.update(), rating_update, confirm_update, row_update
        return

    if len(chat_records) >= CHAT_MAX_TURNS:
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(chat_records)
        yield (
            "",
            render_custom_chat(chat_records, chat_context),
            chat_records,
            normalize_history(llm_history),
            gr.update(interactive=False),
            gr.update(interactive=False),
            rating_update,
            confirm_update,
            row_update,
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
        last_render_time = 0.0
        render_interval = 0.5
        for token in stream_chat_reply(
            user_message=user_message,
            history=context_history,
            system_prompt=build_chat_system_prompt(chat_context),
            temperature=float(RUNTIME_CONFIG["temperature"]),
            max_tokens=int(RUNTIME_CONFIG["max_tokens"]),
        ):
            record["assistant"] += token
            llm_history[-1]["content"] += token
            now = time.monotonic()
            if now - last_render_time >= render_interval:
                last_render_time = now
                yield "", render_custom_chat(chat_records, chat_context), chat_records, llm_history, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

        record["assistant_timestamp"] = current_time_text()
        should_pause_for_rating = pending_chat_rating_record(chat_records) is not None
        input_update = gr.update(interactive=False) if len(chat_records) >= CHAT_MAX_TURNS or should_pause_for_rating else gr.update(interactive=True)
        button_update = gr.update(interactive=False) if len(chat_records) >= CHAT_MAX_TURNS or should_pause_for_rating else gr.update(interactive=True)
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(chat_records)
        yield "", render_custom_chat(chat_records, chat_context), chat_records, llm_history, input_update, button_update, rating_update, confirm_update, row_update
    except Exception as exc:
        error_text = f"LLM 调用失败：{exc}"
        record["assistant"] = error_text
        record["assistant_timestamp"] = current_time_text()
        llm_history[-1]["content"] = error_text
        rating_update, confirm_update, row_update = show_chat_rating_if_complete(chat_records)
        yield "", render_custom_chat(chat_records, chat_context), chat_records, llm_history, gr.update(), gr.update(), rating_update, confirm_update, row_update


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
