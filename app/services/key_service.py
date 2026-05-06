import secrets
import sqlite3
from datetime import datetime
from typing import List, Tuple

from app.config import EXPERIMENT_KEY_DB


KEY_TABLE_COLUMNS = ["密钥", "状态", "使用者", "创建时间", "使用时间"]


def current_time_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connect_db() -> sqlite3.Connection:
    EXPERIMENT_KEY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(EXPERIMENT_KEY_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS experiment_keys (
            key TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            used_at TEXT,
            used_by TEXT
        )
        """
    )
    return conn


def make_key(prefix: str = "") -> str:
    clean_prefix = (prefix or "").strip()
    token = secrets.token_urlsafe(12).replace("-", "").replace("_", "").upper()
    if clean_prefix:
        return f"{clean_prefix}-{token}"
    return token


def generate_experiment_keys(count, prefix="") -> Tuple[str, List[List[str]]]:
    key_count = max(1, min(int(count or 1), 500))
    created_at = current_time_text()
    generated: List[str] = []

    with connect_db() as conn:
        while len(generated) < key_count:
            key = make_key(prefix)
            try:
                conn.execute(
                    "INSERT INTO experiment_keys (key, created_at) VALUES (?, ?)",
                    (key, created_at),
                )
            except sqlite3.IntegrityError:
                continue
            generated.append(key)

    return f"已生成 {len(generated)} 个一次性密钥。", list_key_rows()


def list_key_rows() -> List[List[str]]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT key, created_at, used_at, used_by
            FROM experiment_keys
            ORDER BY created_at DESC, key ASC
            """
        ).fetchall()

    table_rows: List[List[str]] = []
    for key, created_at, used_at, used_by in rows:
        status = "已使用" if used_at else "未使用"
        table_rows.append(
            [
                key,
                status,
                used_by or "",
                created_at or "",
                used_at or "",
            ]
        )
    return table_rows


def key_status_summary() -> str:
    with connect_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM experiment_keys").fetchone()[0]
        used = conn.execute(
            "SELECT COUNT(*) FROM experiment_keys WHERE used_at IS NOT NULL"
        ).fetchone()[0]

    unused = total - used
    return f"共 {total} 个密钥；未使用 {unused} 个；已使用 {used} 个。"


def refresh_key_admin_view():
    return key_status_summary(), list_key_rows()


def consume_experiment_key(key: str, subject_name: str) -> Tuple[bool, str]:
    clean_key = (key or "").strip()
    clean_name = (subject_name or "").strip()

    with connect_db() as conn:
        row = conn.execute(
            "SELECT used_at FROM experiment_keys WHERE key = ?",
            (clean_key,),
        ).fetchone()
        if row is None:
            return False, "密钥无效。"
        if row[0]:
            return False, "该密钥已使用，无法重复进入。"

        updated = conn.execute(
            """
            UPDATE experiment_keys
            SET used_at = ?, used_by = ?
            WHERE key = ? AND used_at IS NULL
            """,
            (current_time_text(), clean_name, clean_key),
        ).rowcount

    if not updated:
        return False, "该密钥已使用，无法重复进入。"
    return True, f"验证通过，欢迎 {clean_name}，正在跳转到实验页面..."
