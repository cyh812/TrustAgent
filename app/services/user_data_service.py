import json
import re
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import gradio as gr

from agent.llm_agent import get_llm_settings
from app.config import EXPERIMENT_CONTEXT
from app.config import PROJECT_ROOT
from app.config import RUNTIME_CONFIG
from app.services.experiment_service import build_chat_system_prompt
from app.services.key_service import connect_db, current_time_text


USER_RECORD_COLUMNS = ["记录ID", "账号ID", "密钥", "任务", "姓名", "开始时间", "结束时间", "消息数"]
USER_RECORD_TASK_ALL = "全部任务"
USER_RECORD_TASK_CHOICES = [USER_RECORD_TASK_ALL, "聊天", "问答", "规划"]


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


def get_context_value(name: str, default: str = "-", context=None) -> str:
    context = context or EXPERIMENT_CONTEXT
    value = str(context.get(name, default) or default).strip()
    return value or default


def count_chat_messages(records: List[Dict[str, Any]]) -> int:
    return sum(
        2
        for record in records or []
        if isinstance(record, dict)
        and str(record.get("user") or "").strip()
        and str(record.get("assistant") or "").strip()
    )


def normalize_custom_records(chat_records):
    return list(chat_records or [])


def apply_final_chat_rating(chat_records, trust_score):
    clean_score = str(trust_score or "").strip()
    if not clean_score:
        return

    complete_records = [
        record
        for record in chat_records or []
        if isinstance(record, dict) and str(record.get("assistant") or "").strip()
    ]
    if not complete_records:
        return

    latest_record = complete_records[-1]
    if latest_record.get("rating") in (None, ""):
        latest_record["rating"] = clean_score
        latest_record["rating_timestamp"] = current_time_text()


def collect_chat_ratings(chat_records):
    return [
        {
            "turn_index": record.get("turn_index"),
            "rating": str(record.get("rating") or "").strip(),
            "rating_timestamp": str(record.get("rating_timestamp") or "").strip(),
        }
        for record in chat_records or []
        if isinstance(record, dict) and record.get("rating") not in (None, "")
    ]


def save_chat_record(chat_records, started_at, trust_score, chat_context=None):
    chat_context = chat_context or EXPERIMENT_CONTEXT
    custom_records = normalize_custom_records(chat_records)
    apply_final_chat_rating(custom_records, trust_score)
    chat_ratings = collect_chat_ratings(custom_records)
    started_time = str(started_at or "").strip() or current_time_text()
    ended_time = current_time_text()
    account_id = get_context_value("account_id", context=chat_context)
    experiment_key = get_context_value("experiment_key", context=chat_context)
    subject_name = get_context_value("subject_name", context=chat_context)
    task_name = get_context_value("task_name", "聊天", context=chat_context)
    llm_settings = get_llm_settings()

    payload = {
        "metadata": {
            "account_id": account_id,
            "experiment_key": experiment_key,
            "subject_name": subject_name,
            "task_name": task_name,
            "chat_config_id": get_context_value("chat_config_id", "", context=chat_context),
            "chat_topic": get_context_value("chat_topic", "", context=chat_context),
            "chat_user_instruction": get_context_value("chat_user_instruction", "", context=chat_context),
            "emotional_valence_level": get_context_value("emotional_valence_level", "", context=chat_context),
            "transparency_level": get_context_value("transparency_level", "", context=chat_context),
            "stance_strategy_level": get_context_value("stance_strategy_level", "", context=chat_context),
            "trust_score": str(trust_score or "").strip(),
            "trust_scores": chat_ratings,
            "started_at": started_time,
            "ended_at": ended_time,
        },
        "runtime_config": {
            "system_prompt": build_chat_system_prompt(chat_context) if task_name == "聊天" else str(RUNTIME_CONFIG["system_prompt"]),
            "temperature": float(RUNTIME_CONFIG["temperature"]),
            "max_tokens": int(RUNTIME_CONFIG["max_tokens"]),
            "model": llm_settings.model,
            "provider": llm_settings.provider,
            "base_url": llm_settings.base_url,
        },
        "custom_chat_records": custom_records,
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
                count_chat_messages(custom_records),
                json.dumps(payload, ensure_ascii=False, indent=2),
            ),
        )

    return (
        f"聊天实验已结束，记录已保存。账号：`{account_id}`；密钥：`{experiment_key}`；信任评分：`{trust_score or '未评分'}`。",
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(value=f"<meta http-equiv='refresh' content='0;url=/profile?account_id={account_id}'>"),
    )



def save_planning_record(planning_records, started_at, planning_state, planning_context=None):
    planning_context = planning_context or EXPERIMENT_CONTEXT
    records = list(planning_records or [])
    state = dict(planning_state or {})
    started_time = str(started_at or "").strip() or current_time_text()
    ended_time = current_time_text()
    account_id = get_context_value("account_id", context=planning_context)
    experiment_key = get_context_value("experiment_key", context=planning_context)
    subject_name = get_context_value("subject_name", context=planning_context)
    llm_settings = get_llm_settings()

    payload = {
        "metadata": {
            "account_id": account_id,
            "experiment_key": experiment_key,
            "subject_name": subject_name,
            "task_name": "规划",
            "planning_topic": get_context_value("planning_topic", "旅行", context=planning_context),
            "started_at": started_time,
            "ended_at": ended_time,
        },
        "runtime_config": {
            "temperature": float(RUNTIME_CONFIG["temperature"]),
            "max_tokens": int(RUNTIME_CONFIG["max_tokens"]),
            "model": llm_settings.model,
            "provider": llm_settings.provider,
            "base_url": llm_settings.base_url,
        },
        "planning_state": state,
        "planning_records": records,
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
                "规划",
                started_time,
                ended_time,
                count_chat_messages(records),
                json.dumps(payload, ensure_ascii=False, indent=2),
            ),
        )

    return (
        f"规划实验已结束，记录已保存。账号：`{account_id}`。",
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(value=f"<meta http-equiv='refresh' content='0;url=/profile?account_id={quote(account_id)}'>"),
    )


def normalize_record_task(task_name=None) -> str:
    clean_task = str(task_name or "").strip()
    if not clean_task or clean_task == USER_RECORD_TASK_ALL:
        return ""
    return clean_task


def list_user_record_rows(account_id=None, task_name=None) -> List[List[Any]]:
    clean_account_id = str(account_id or "").strip()
    clean_task = normalize_record_task(task_name)
    where_parts = []
    params = []
    if clean_account_id:
        where_parts.append("account_id = ?")
        params.append(clean_account_id)
    if clean_task:
        where_parts.append("task_name = ?")
        params.append(clean_task)
    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    with connect_db() as conn:
        ensure_record_table(conn)
        rows = conn.execute(
            f"""
            SELECT id, account_id, experiment_key, task_name, subject_name, started_at, ended_at, message_count
            FROM experiment_records
            {where_sql}
            ORDER BY ended_at DESC, id DESC
            """,
            tuple(params),
        ).fetchall()
    return [list(row) for row in rows]


def user_record_summary() -> str:
    rows = list_user_record_rows()
    return f"Total records: {len(rows)}."


def list_user_account_rows() -> List[List[Any]]:
    with connect_db() as conn:
        ensure_record_table(conn)
        rows = conn.execute(
            """
            SELECT account_id,
                   COALESCE(NULLIF(MAX(subject_name), ''), '-') AS subject_name,
                   COUNT(*) AS record_count,
                   MAX(ended_at) AS last_ended_at
            FROM experiment_records
            GROUP BY account_id
            ORDER BY MAX(ended_at) DESC, account_id ASC
            """
        ).fetchall()
    return [list(row) for row in rows]


def user_account_choice_label(row: List[Any]) -> str:
    account_id, subject_name, record_count, last_ended_at = row
    return f"{account_id} | {subject_name or '-'} | {record_count} records | {last_ended_at or '-'}"


def list_user_record_choices() -> Tuple[str, List[str], List[List[Any]]]:
    account_rows = list_user_account_rows()
    total_records = len(list_user_record_rows())
    summary = f"{len(account_rows)} users have records; {total_records} records in total. Select a user to view records."
    return summary, [user_account_choice_label(row) for row in account_rows], []


def parse_account_choice(choice) -> str:
    if not choice:
        return ""
    return str(choice).split("|", 1)[0].strip()


def select_user_record_account(choice, task_name=USER_RECORD_TASK_ALL):
    account_id = parse_account_choice(choice)
    clean_task = normalize_record_task(task_name)
    task_label = clean_task or "全部任务"
    if not account_id:
        return "Select a user.", [], "No user selected. Export is unavailable.", gr.update(value=None)

    rows = list_user_record_rows(account_id, clean_task)
    return (
        f"Account `{account_id}` has {len(rows)} `{task_label}` records.",
        rows,
        f"You can export `{task_label}` records for the selected user.",
        gr.update(value=None),
    )


def safe_export_name(value: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_.-]+", "_", str(value or "").strip())
    return safe or "unknown"


def export_user_records_zip(choice, task_name=USER_RECORD_TASK_ALL):
    account_id = parse_account_choice(choice)
    if not account_id:
        return "Select a user before exporting.", gr.update(value=None)

    clean_task = normalize_record_task(task_name)
    where_task_sql = "AND task_name = ?" if clean_task else ""
    params = [account_id]
    if clean_task:
        params.append(clean_task)

    with connect_db() as conn:
        ensure_record_table(conn)
        rows = conn.execute(
            f"""
            SELECT id, transcript_json
            FROM experiment_records
            WHERE account_id = ?
            {where_task_sql}
            ORDER BY ended_at ASC, id ASC
            """,
            tuple(params),
        ).fetchall()

    if not rows:
        task_label = clean_task or "all tasks"
        return f"Account `{account_id}` has no `{task_label}` records to export.", gr.update(value=None)

    export_dir = PROJECT_ROOT / "data" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    task_part = safe_export_name(clean_task or "all")
    zip_path = export_dir / f"trustagent_{safe_export_name(account_id)}_{task_part}_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for record_id, transcript_json in rows:
            try:
                payload = json.loads(transcript_json)
                content = json.dumps(payload, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                content = transcript_json
            zip_file.writestr(f"record_{record_id}.json", content)

    if not zip_path.exists():
        return "Export failed: zip file was not created.", gr.update(value=None)

    download_url = f"/exports/{zip_path.name}"
    task_label = clean_task or "all tasks"
    return (
        f"Exported {len(rows)} `{task_label}` records for account `{account_id}`. "
        f"[Download zip]({download_url})",
        str(zip_path.resolve()),
    )


# Legacy helpers kept for compatibility with older imports/callbacks.
def parse_record_id(choice) -> Optional[int]:
    if not choice:
        return None
    first_part = str(choice).split("|", 1)[0].strip()
    try:
        return int(first_part)
    except ValueError:
        return None


def load_user_record(choice, task_name=USER_RECORD_TASK_ALL):
    account_id = parse_account_choice(choice)
    rows = list_user_record_rows(account_id, task_name) if account_id else []
    task_label = normalize_record_task(task_name) or "全部任务"
    return f"Account `{account_id}` has {len(rows)} `{task_label}` records.", rows


def refresh_user_record_view():
    summary, choices, rows = list_user_record_choices()
    return (
        summary,
        gr.update(choices=choices, value=None),
        rows,
        "Select a user before exporting.",
        gr.update(value=None),
    )
