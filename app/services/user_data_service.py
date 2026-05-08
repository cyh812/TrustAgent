import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from agent.llm_agent import get_llm_settings
from app.config import EXPERIMENT_CONTEXT
from app.config import RUNTIME_CONFIG
from app.services.experiment_service import (
    build_chat_system_prompt,
    custom_chat_records_to_messages,
    normalize_history,
)
from app.services.key_service import connect_db, current_time_text


USER_RECORD_COLUMNS = ["记录ID", "账号ID", "密钥", "任务", "姓名", "开始时间", "结束时间", "消息数"]


def ensure_record_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS experiment_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL DEFAULT '',
            experiment_key TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            task_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            message_count INTEGER NOT NULL,
            transcript_json TEXT NOT NULL
        )
        """
    )
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(experiment_records)").fetchall()
    }
    if "account_id" not in columns:
        conn.execute("ALTER TABLE experiment_records ADD COLUMN account_id TEXT NOT NULL DEFAULT ''")


def get_context_value(name: str, default: str = "-") -> str:
    value = str(EXPERIMENT_CONTEXT.get(name, default) or default).strip()
    return value or default


def count_messages(*histories: List[Dict[str, Any]]) -> int:
    return sum(len(history or []) for history in histories)


def normalize_saved_chat(chat_history):
    if chat_history and all(isinstance(item, dict) and "user" in item for item in chat_history):
        return custom_chat_records_to_messages(chat_history), list(chat_history)
    return normalize_history(chat_history), []


def save_chat_record(chat_history, llm_history, started_at):
    visible_history, custom_records = normalize_saved_chat(chat_history)
    model_history = normalize_history(llm_history)
    started_time = str(started_at or "").strip() or current_time_text()
    ended_time = current_time_text()
    account_id = get_context_value("account_id")
    experiment_key = get_context_value("experiment_key")
    subject_name = get_context_value("subject_name")
    task_name = get_context_value("task_name", "聊天")
    llm_settings = get_llm_settings()

    payload = {
        "metadata": {
            "account_id": account_id,
            "experiment_key": experiment_key,
            "subject_name": subject_name,
            "task_name": task_name,
            "chat_config_id": get_context_value("chat_config_id", ""),
            "chat_topic": get_context_value("chat_topic", ""),
            "chat_user_instruction": get_context_value("chat_user_instruction", ""),
            "emotional_valence_level": get_context_value("emotional_valence_level", ""),
            "transparency_level": get_context_value("transparency_level", ""),
            "stance_strategy_level": get_context_value("stance_strategy_level", ""),
            "certainty_level": get_context_value("certainty_level", ""),
            "started_at": started_time,
            "ended_at": ended_time,
        },
        "runtime_config": {
            "system_prompt": build_chat_system_prompt() if task_name == "聊天" else str(RUNTIME_CONFIG["system_prompt"]),
            "base_system_prompt": str(RUNTIME_CONFIG["system_prompt"]),
            "temperature": float(RUNTIME_CONFIG["temperature"]),
            "max_tokens": int(RUNTIME_CONFIG["max_tokens"]),
            "model": str(RUNTIME_CONFIG["model"]),
            "provider": llm_settings.provider,
            "base_url": llm_settings.base_url,
        },
        "chat_history": visible_history,
        "custom_chat_records": custom_records,
        "llm_history": model_history,
    }

    with connect_db() as conn:
        ensure_record_table(conn)
        conn.execute(
            """
            INSERT INTO experiment_records (
                account_id,
                experiment_key,
                subject_name,
                task_name,
                started_at,
                ended_at,
                message_count,
                transcript_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                experiment_key,
                subject_name,
                task_name,
                started_time,
                ended_time,
                count_messages(visible_history),
                json.dumps(payload, ensure_ascii=False, indent=2),
            ),
        )

    return (
        f"聊天实验已结束，记录已保存。账号：`{account_id}`；密钥：`{experiment_key}`；消息数：{len(visible_history)}。",
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(value="<meta http-equiv='refresh' content='0;url=/profile'>"),
    )


def list_user_record_rows() -> List[List[Any]]:
    with connect_db() as conn:
        ensure_record_table(conn)
        rows = conn.execute(
            """
            SELECT id, account_id, experiment_key, task_name, subject_name, started_at, ended_at, message_count
            FROM experiment_records
            ORDER BY ended_at DESC, id DESC
            """
        ).fetchall()
    return [list(row) for row in rows]


def user_record_summary() -> str:
    rows = list_user_record_rows()
    return f"共 {len(rows)} 条用户实验记录。"


def record_choice_label(row: List[Any]) -> str:
    record_id, account_id, experiment_key, task_name, subject_name, _started_at, ended_at, _message_count = row
    return f"{record_id} | {account_id} | {experiment_key} | {subject_name} | {task_name} | {ended_at}"


def list_user_record_choices() -> Tuple[str, List[str], List[List[Any]]]:
    rows = list_user_record_rows()
    return user_record_summary(), [record_choice_label(row) for row in rows], rows


def parse_record_id(choice) -> Optional[int]:
    if not choice:
        return None
    first_part = str(choice).split("|", 1)[0].strip()
    try:
        return int(first_part)
    except ValueError:
        return None


def load_user_record(choice):
    record_id = parse_record_id(choice)
    if record_id is None:
        return "请选择一条用户记录。", {}

    with connect_db() as conn:
        ensure_record_table(conn)
        row = conn.execute(
            """
            SELECT id, account_id, experiment_key, task_name, subject_name, started_at, ended_at, message_count, transcript_json
            FROM experiment_records
            WHERE id = ?
            """,
            (record_id,),
        ).fetchone()

    if row is None:
        return "未找到该用户记录。", {}

    (
        saved_id,
        account_id,
        experiment_key,
        task_name,
        subject_name,
        started_at,
        ended_at,
        message_count,
        transcript_json,
    ) = row
    try:
        transcript = json.loads(transcript_json)
    except json.JSONDecodeError:
        transcript = {"raw": transcript_json}

    detail = (
        f"### 记录 #{saved_id}\n"
        f"- 账号ID：`{account_id}`\n"
        f"- 密钥：`{experiment_key}`\n"
        f"- 姓名：`{subject_name}`\n"
        f"- 任务：`{task_name}`\n"
        f"- 开始时间：`{started_at}`\n"
        f"- 结束时间：`{ended_at}`\n"
        f"- 消息数：`{message_count}`"
    )
    return detail, transcript


def refresh_user_record_view():
    summary, choices, rows = list_user_record_choices()
    return (
        summary,
        gr.update(choices=choices, value=None),
        rows,
        "请选择一条用户记录。",
        {},
    )
