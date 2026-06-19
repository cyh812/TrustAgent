from html import escape
from typing import Any, Dict, List

import gradio as gr

from agent.planning_agent import STAGES, STAGE_TITLES, handle_feedback, initial_state, stream_stage
from app.services.account_service import get_account, request_account_id
from app.services.experiment_service import format_message_html
from app.services.key_service import current_time_text
from app.services.user_data_service import save_planning_record


def build_plan_context_for_request(request: gr.Request) -> Dict[str, str]:
    account_id = request_account_id(request)
    account = get_account(account_id)
    if not account:
        return {}
    return {
        "account_id": account_id,
        "experiment_key": str(account.get("password_key") or "-"),
        "subject_name": str(account.get("name") or ""),
        "phone": str(account.get("phone") or ""),
        "task_name": "规划",
        "planning_topic": "旅行",
    }


def plan_records_to_messages(records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    messages = []
    for record in records or []:
        if not isinstance(record, dict):
            continue
        user_content = str(record.get("user") or "").strip()
        assistant_content = str(record.get("assistant") or "").strip()
        if user_content:
            messages.append({"role": "user", "content": user_content})
        if assistant_content:
            messages.append({"role": "assistant", "content": assistant_content})
    return messages


def render_planning_window(records, state=None, context=None):
    state = state or initial_state()
    topic = escape(str((context or {}).get("planning_topic") or "旅行"))

    items = [
        '<div class="custom-chat-window planning-chat-window">',
        f"""
        <div class="custom-topic-card">
            <div class="custom-topic-label">本次规划主题</div>
            <div class="custom-topic-body">请围绕“{topic}”完成分阶段规划。</div>
        </div>
        """,
    ]

    if not records:
        items.append('<div class="custom-chat-empty">请输入你的旅行需求，例如：我想从杭州去大阪玩 3 天，2 个人，预算 12000 元；或从北京去三亚玩 4 天。</div>')
        items.append("</div>")
        return "".join(items)

    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("type") == "stage_rating":
            items.append(render_stage_rating_card(record=record, state=state))
            continue
        user_content = format_message_html(record.get("user", ""))
        assistant_text = str(record.get("assistant") or "")
        intermediate_outputs = [
            str(item or "").strip()
            for item in (record.get("intermediate_outputs") or [])
            if str(item or "").strip()
        ]
        process_outputs = intermediate_outputs[:-1] if len(intermediate_outputs) > 1 else []
        final_output = intermediate_outputs[-1] if intermediate_outputs else assistant_text
        assistant_content = format_message_html(final_output)
        process_html = render_planning_process(process_outputs)
        assistant_html = ""
        if str(final_output or "").strip() or process_html:
            assistant_html = f"""
                <div class="custom-message custom-message-assistant">
                    <div class="custom-message-label">TrustAgent</div>
                    <div class="custom-message-body">{assistant_content}</div>
                </div>
            """
        items.append(
            f"""
            <section class="custom-chat-turn">
                {render_user_message(user_content)}
                {process_html}
                {assistant_html}
            </section>
            """
        )

    items.append("</div>")
    return "".join(items)


def render_user_message(user_content):
    if not str(user_content or "").strip():
        return ""
    return f"""
    <div class="custom-message custom-message-user">
        <div class="custom-message-label">你</div>
        <div class="custom-message-body">{user_content}</div>
    </div>
    """


def render_planning_process(process_outputs):
    if not process_outputs:
        return ""

    items = ['<div class="planning-process-stack">']
    for output in process_outputs:
        items.append(
            f"""
            <div class="planning-process-card">
                <div class="planning-process-label">思考过程</div>
                <div class="planning-process-body">{format_message_html(output)}</div>
            </div>
            """
        )
    items.append("</div>")
    return "".join(items)


def render_stage_progress(state=None):
    state = state or initial_state()
    current_stage = str(state.get("current_stage") or "need")
    stage_results = state.get("stage_results", {}) or {}
    done = bool(state.get("done"))
    parts = ['<div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:12px;">']

    for stage_key in STAGES:
        title = STAGE_TITLES[stage_key]
        completed = title in stage_results
        active = stage_key == current_stage and not completed and not done
        dot_color = "#16a34a" if completed else "#94a3b8"
        border_color = "#bbf7d0" if completed else ("#cbd5e1" if active else "#e2e8f0")
        bg_color = "#f0fdf4" if completed else ("#f8fafc" if active else "#ffffff")
        text_color = "#166534" if completed else ("#334155" if active else "#64748b")
        connector = '<span style="color:#cbd5e1;margin-left:2px;">-</span>' if stage_key != STAGES[-1] else ""
        parts.append(
            f"""
            <span style="display:inline-flex;align-items:center;gap:6px;border:1px solid {border_color};
                         background:{bg_color};color:{text_color};border-radius:999px;
                         padding:4px 9px;font-size:12px;font-weight:600;white-space:nowrap;">
                <span style="width:8px;height:8px;border-radius:999px;background:{dot_color};display:inline-block;"></span>
                {escape(title)}
            </span>{connector}
            """
        )

    parts.append("</div>")
    return "".join(parts)


def render_stage_rating_card(state=None, record=None):
    state = state or initial_state()
    record = record or {}
    rating_stage = escape(str(record.get("stage") or state.get("rating_stage") or "当前阶段"))
    rating_score = str(record.get("stage_rating") or "").strip()
    progress_html = str(record.get("stage_progress_html") or "").strip() or render_stage_progress(state)
    body_text = (
        f"你已确认“{rating_stage}”阶段可行，阶段评分：{escape(rating_score)} 分。"
        if rating_score
        else f"你已确认“{rating_stage}”阶段可行。请在下方选择 1-7 分后继续。"
    )
    return f"""
    <div class="custom-topic-card planning-rating-card">
        <div class="custom-topic-label">阶段评分</div>
        <div class="custom-topic-body">{body_text}</div>
        {progress_html}
    </div>
    """


def initialize_planning_session(records, request: gr.Request):
    context = build_plan_context_for_request(request)
    state = initial_state()
    return context, state, render_planning_window(records, state, context)


def hidden_stage_rating_controls():
    return gr.update(visible=False, value=None), gr.update(visible=False), gr.update(visible=False)


def visible_stage_rating_controls(state=None):
    state = state or {}
    is_final_rating = state.get("done") or state.get("current_stage") == "done"
    button_text = "结束实验并保存" if is_final_rating else "确认评分并继续"
    button_variant = "stop" if is_final_rating else "primary"
    return (
        gr.update(visible=True, value=None),
        gr.update(visible=True, value=button_text, variant=button_variant),
        gr.update(visible=True),
    )


def append_stage_rating_record(records, state, rating_stage=""):
    rating_stage = str(rating_stage or state.get("rating_stage") or "当前阶段").strip()
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        if record.get("type") == "stage_rating" and str(record.get("stage") or "") == rating_stage and not record.get("stage_rating"):
            return

    records.append(
        {
            "type": "stage_rating",
            "turn_index": len(records) + 1,
            "stage": rating_stage,
            "stage_rating": "",
            "stage_rating_timestamp": "",
            "stage_progress_html": render_stage_progress(state),
        }
    )


def respond_planning(message, records, state, context=None):
    if not message or not str(message).strip():
        score_update, button_update, row_update = (
            visible_stage_rating_controls(state)
            if (state or {}).get("awaiting_stage_rating")
            else hidden_stage_rating_controls()
        )
        yield "", render_planning_window(records, state, context), records, state, gr.update(), score_update, button_update, row_update
        return

    user_message = str(message).strip()
    records = list(records or [])
    state = dict(state or initial_state())

    if state.get("awaiting_stage_rating"):
        yield (
            "",
            render_planning_window(records, state, context),
            records,
            state,
            gr.update(interactive=False),
            *visible_stage_rating_controls(state),
        )
        return

    if state.get("done") or state.get("current_stage") == "done":
        yield (
            "",
            render_planning_window(records, state, context),
            records,
            state,
            gr.update(interactive=False),
            gr.update(visible=False, value=None),
            gr.update(visible=False),
            gr.update(visible=False),
        )
        return

    if records and not state.get("awaiting_user_info"):
        state = handle_feedback(state, user_message)
        last_intent = ""
        if state.get("interaction_log"):
            last_intent = str(state["interaction_log"][-1].get("classified_intent") or "")
        if last_intent == "continue":
            rating_stage = ""
            if state.get("interaction_log"):
                rating_stage = str(state["interaction_log"][-1].get("stage") or "")
            records.append(
                {
                    "turn_index": len(records) + 1,
                    "stage": rating_stage or "阶段确认",
                    "user": user_message,
                    "user_timestamp": current_time_text(),
                    "assistant": "",
                    "assistant_timestamp": "",
                }
            )
            state["awaiting_stage_rating"] = True
            state["rating_stage"] = rating_stage
            append_stage_rating_record(records, state, rating_stage or "当前阶段")
            yield (
                "",
                render_planning_window(records, state, context),
                records,
                state,
                gr.update(interactive=False),
                *visible_stage_rating_controls(state),
            )
            return

        if state.get("done") or state.get("current_stage") == "done":
            records.append(
                {
                    "turn_index": len(records) + 1,
                    "stage": "流程结束",
                    "user": user_message,
                    "user_timestamp": current_time_text(),
                    "assistant": "规划流程已结束。",
                    "assistant_timestamp": current_time_text(),
                }
            )
            yield (
                "",
                render_planning_window(records, state, context),
                records,
                state,
                gr.update(interactive=False),
                gr.update(visible=False, value=None),
                gr.update(visible=False),
                gr.update(visible=False),
            )
            return

    stage_key = str(state.get("current_stage") or "need")
    stage_title = STAGE_TITLES.get(stage_key, "总体需求理解")
    record = {
        "turn_index": len(records) + 1,
        "stage": stage_title,
        "user": user_message,
        "user_timestamp": current_time_text(),
        "assistant": "",
        "assistant_timestamp": "",
    }
    records.append(record)
    yield "", render_planning_window(records, state, context), records, state, gr.update(), gr.update(visible=False, value=None), gr.update(visible=False), gr.update(visible=False)

    try:
        next_state = state
        for event in stream_stage(state, user_message):
            next_state = dict(event.get("state") or next_state)
            record["assistant"] = str(event.get("output") or "")
            record["intermediate_outputs"] = list(event.get("intermediate_outputs") or [])
            if event.get("type") == "final":
                record["assistant_timestamp"] = current_time_text()
            yield "", render_planning_window(records, next_state, context), records, next_state, gr.update(), gr.update(visible=False, value=None), gr.update(visible=False), gr.update(visible=False)
    except Exception as exc:
        record["assistant"] = f"规划 Agent 调用失败：{exc}"
        record["assistant_timestamp"] = current_time_text()
        yield "", render_planning_window(records, state, context), records, state, gr.update(), gr.update(visible=False, value=None), gr.update(visible=False), gr.update(visible=False)


def submit_planning_stage_rating(score, records, state, context=None):
    records = list(records or [])
    state = dict(state or initial_state())
    clean_score = str(score or "").strip()
    if not clean_score:
        yield (
            "",
            render_planning_window(records, state, context),
            records,
            state,
            gr.update(interactive=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
        )
        return

    rating_stage = str(state.get("rating_stage") or "").strip()
    rating_timestamp = current_time_text()
    updated_rating_card = False
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        if record.get("type") != "stage_rating":
            continue
        if not rating_stage or str(record.get("stage") or "") == rating_stage:
            record["stage_rating"] = clean_score
            record["stage_rating_timestamp"] = rating_timestamp
            updated_rating_card = True
            break
    if not updated_rating_card:
        records.append(
            {
                "type": "stage_rating",
                "turn_index": len(records) + 1,
                "stage": rating_stage or "当前阶段",
                "stage_rating": clean_score,
                "stage_rating_timestamp": rating_timestamp,
                "stage_progress_html": render_stage_progress(state),
            }
        )

    state["awaiting_stage_rating"] = False
    state["rating_stage"] = ""
    if state.get("done") or state.get("current_stage") == "done":
        yield (
            "",
            render_planning_window(records, state, context),
            records,
            state,
            gr.update(interactive=False),
            gr.update(visible=False, value=None),
            gr.update(visible=False),
            gr.update(visible=False),
        )
        return

    pending_next_stage = str(state.get("pending_next_stage") or "").strip()
    if pending_next_stage:
        state["current_stage"] = pending_next_stage
        state["pending_next_stage"] = ""
        if pending_next_stage == "done":
            state["done"] = True
            yield (
                "",
                render_planning_window(records, state, context),
                records,
                state,
                gr.update(interactive=False),
                gr.update(visible=False, value=None),
                gr.update(visible=False),
                gr.update(visible=False),
            )
            return

    stage_key = str(state.get("current_stage") or "need")
    stage_title = STAGE_TITLES.get(stage_key, "总体需求理解")
    user_message = ""
    record = {
        "turn_index": len(records) + 1,
        "stage": stage_title,
        "user": user_message,
        "user_timestamp": current_time_text(),
        "assistant": "",
        "assistant_timestamp": "",
    }
    records.append(record)
    yield (
        "",
        render_planning_window(records, state, context),
        records,
        state,
        gr.update(interactive=False),
        gr.update(visible=False, value=None),
        gr.update(visible=False),
        gr.update(visible=False),
    )

    try:
        next_state = state
        for event in stream_stage(state, user_message):
            next_state = dict(event.get("state") or next_state)
            record["assistant"] = str(event.get("output") or "")
            record["intermediate_outputs"] = list(event.get("intermediate_outputs") or [])
            if event.get("type") == "final":
                record["assistant_timestamp"] = current_time_text()
            is_final_done = bool(next_state.get("done") or next_state.get("current_stage") == "done")
            if event.get("type") == "final" and is_final_done:
                next_state["awaiting_stage_rating"] = True
                next_state["rating_stage"] = STAGE_TITLES.get("final", "完整旅行方案汇总")
                append_stage_rating_record(records, next_state, next_state["rating_stage"])
                yield (
                    "",
                    render_planning_window(records, next_state, context),
                    records,
                    next_state,
                    gr.update(interactive=False),
                    *visible_stage_rating_controls(next_state),
                )
                continue

            message_update = gr.update(interactive=True) if event.get("type") == "final" else gr.update(interactive=False)
            yield (
                "",
                render_planning_window(records, next_state, context),
                records,
                next_state,
                message_update,
                gr.update(visible=False, value=None),
                gr.update(visible=False),
                gr.update(visible=False),
            )
    except Exception as exc:
        record["assistant"] = f"规划 Agent 调用失败：{exc}"
        record["assistant_timestamp"] = current_time_text()
        yield (
            "",
            render_planning_window(records, state, context),
            records,
            state,
            gr.update(interactive=True),
            gr.update(visible=False, value=None),
            gr.update(visible=False),
            gr.update(visible=False),
        )


def submit_planning_stage_rating_or_save(score, records, state, context=None, started_at=""):
    state = dict(state or initial_state())
    is_final_rating = state.get("done") or state.get("current_stage") == "done"

    if not is_final_rating:
        for result in submit_planning_stage_rating(score, records, state, context):
            yield (*result, gr.update(), gr.update(), gr.update())
        return

    records = list(records or [])
    clean_score = str(score or "").strip()
    if not clean_score:
        yield (
            "",
            render_planning_window(records, state, context),
            records,
            state,
            gr.update(interactive=False),
            gr.update(visible=True),
            gr.update(visible=True, value="结束实验并保存", variant="stop"),
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
        )
        return

    rating_stage = str(state.get("rating_stage") or "").strip()
    rating_timestamp = current_time_text()
    updated_rating_card = False
    for record in reversed(records):
        if not isinstance(record, dict) or record.get("type") != "stage_rating":
            continue
        if not rating_stage or str(record.get("stage") or "") == rating_stage:
            record["stage_rating"] = clean_score
            record["stage_rating_timestamp"] = rating_timestamp
            updated_rating_card = True
            break

    if not updated_rating_card:
        records.append(
            {
                "type": "stage_rating",
                "turn_index": len(records) + 1,
                "stage": rating_stage or "当前阶段",
                "stage_rating": clean_score,
                "stage_rating_timestamp": rating_timestamp,
                "stage_progress_html": render_stage_progress(state),
            }
        )

    state["awaiting_stage_rating"] = False
    state["rating_stage"] = ""
    save_status, message_update, send_update, _unused_end_update, redirect_update = save_planning_record(
        records,
        started_at,
        state,
        context,
    )
    yield (
        "",
        render_planning_window(records, state, context),
        records,
        state,
        message_update,
        gr.update(visible=False, value=None),
        gr.update(visible=False),
        gr.update(visible=False),
        save_status,
        send_update,
        redirect_update,
    )
