import random
import sqlite3
from itertools import product
from typing import Any, Dict, List, Tuple
from urllib.parse import quote

import gradio as gr

from app.config import EXPERIMENT_CONTEXT
from app.services.key_service import connect_db, current_time_text


ACCOUNT_TABLE_COLUMNS = [
    "账号ID",
    "密钥",
    "姓名",
    "手机号",
    "聊天次数",
    "问答次数",
    "规划次数",
    "创建时间",
    "更新时间",
]

CHAT_TOPIC_CONFIGS = [
    {
        "topic": "国际局势与信息焦虑",
        "userInstruction": "请围绕“国际局势变化、新闻信息获取、信息焦虑”等内容，与 Agent 自然展开聊天。",
    },
    {
        "topic": "AI 与未来工作的变化",
        "userInstruction": "请围绕“AI 发展、未来工作变化、职业焦虑或个人适应”等内容，与 Agent 自然展开聊天。",
    },
    {
        "topic": "长期忙碌与休息负罪感",
        "userInstruction": "请围绕“长期忙碌、休息、负罪感、生活节奏”等内容，与 Agent 自然展开聊天。",
    },
    {
        "topic": "社交压力与边界感",
        "userInstruction": "请围绕“社交疲惫、人际边界、沟通压力或自我表达”等内容，与 Agent 自然展开聊天。",
    },
    {
        "topic": "兴趣坚持与自我怀疑",
        "userInstruction": "请围绕“兴趣坚持、三分钟热度、自我怀疑或长期投入”等内容，与 Agent 自然展开聊天。",
    },
    {
        "topic": "数字生活与注意力分散",
        "userInstruction": "请围绕“手机使用、注意力分散、信息干扰或数字生活习惯”等内容，与 Agent 自然展开聊天。",
    },
    {
        "topic": "生活选择与未来规划",
        "userInstruction": "请围绕“职业发展、人生规划、未来目标、选择与不确定性”等内容，与 Agent 自然展开聊天。"
    },
    {
        "topic": "亲密关系与情感困惑",
        "userInstruction": "请围绕“恋爱关系、亲密关系、情感困惑、沟通与理解”等内容，与 Agent 自然展开聊天。"
    }
]

CHAT_TOPICS = [item["topic"] for item in CHAT_TOPIC_CONFIGS]
CHAT_TOPIC_INSTRUCTIONS = {item["topic"]: item["userInstruction"] for item in CHAT_TOPIC_CONFIGS}

EMOTIONAL_VALENCE_PROMPTS = {
    "理性导向型": "回答时以任务分析和问题解决为核心，强调逻辑性、结构性和信息效率，不需要情绪安慰、共情表达等内容。",
    "感性导向型": "回答时优先回应用户情绪与心理状态，强调理解、支持和陪伴感，更多使用安慰性、鼓励性和情感化表达。",
}

TRANSPARENCY_PROMPTS = {
    "低透明度": "回答时直接给出结论或建议，尽量减少推理过程、依据说明和知识边界解释，整体表达更明确和确定。",
    "高透明度": "回答时不仅解释原因和判断依据，还主动说明当前信息限制、可能存在的不确定性以及结论的适用边界。",
}

STANCE_STRATEGY_PROMPTS = {
    "用户立场型": "回答时倾向于优先认可和支持用户观点，尽量减少直接反驳，主动推进用户立场的对话。",
    "独立客观型": "回答时更强调独立分析与客观判断，即使与用户观点不一致，也必须明确指出问题并提供独立意见。",
}

EMOTIONAL_VALENCE_OPTIONS = list(EMOTIONAL_VALENCE_PROMPTS.keys())
TRANSPARENCY_OPTIONS = list(TRANSPARENCY_PROMPTS.keys())
STANCE_STRATEGY_OPTIONS = list(STANCE_STRATEGY_PROMPTS.keys())

FEATURE_DIMENSION_CONFIGS = {
    "emotional_valence": {
        "label": "社会情感表达",
        "options": EMOTIONAL_VALENCE_OPTIONS,
        "prompt_map": EMOTIONAL_VALENCE_PROMPTS,
    },
    "transparency": {
        "label": "认知透明表达",
        "options": TRANSPARENCY_OPTIONS,
        "prompt_map": TRANSPARENCY_PROMPTS,
    },
    "stance_strategy": {
        "label": "对话立场对齐",
        "options": STANCE_STRATEGY_OPTIONS,
        "prompt_map": STANCE_STRATEGY_PROMPTS,
    },
}

CHAT_STYLE_COMBINATIONS = [
    {
        "emotional_valence": emotional_valence,
        "transparency": transparency,
        "stance_strategy": stance_strategy,
    }
    for emotional_valence, transparency, stance_strategy in product(
        EMOTIONAL_VALENCE_OPTIONS,
        TRANSPARENCY_OPTIONS,
        STANCE_STRATEGY_OPTIONS,
    )
]

CHAT_CONFIG_TABLE_COLUMNS = [
    "配置ID",
    "账号ID",
    "主题",
    "社会情感表达",
    "认知透明表达",
    "对话立场对齐",
    "状态",
    "创建时间",
    "使用时间",
]

TASK_ROUTES = {"chat": "/chat", "qa": "/qa", "plan": "/plan"}
TASK_NAMES = {"chat": "聊天", "qa": "问答", "plan": "规划"}
TASK_QUOTA_COLUMNS = {"chat": "chat_quota", "qa": "qa_quota", "plan": "plan_quota"}


def request_account_id(request) -> str:
    query_params = getattr(request, "query_params", {}) or {}
    return normalize_account_id(query_params.get("account_id") or "")


def request_chat_config_id(request) -> str:
    query_params = getattr(request, "query_params", {}) or {}
    return str(query_params.get("chat_config_id") or "").strip()


def request_qa_config_id(request) -> str:
    query_params = getattr(request, "query_params", {}) or {}
    return str(query_params.get("qa_config_id") or "").strip()


def ensure_account_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS experiment_accounts (
            account_id TEXT PRIMARY KEY,
            password_key TEXT NOT NULL,
            name TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            chat_quota INTEGER NOT NULL DEFAULT 0,
            qa_quota INTEGER NOT NULL DEFAULT 0,
            plan_quota INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def ensure_chat_config_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_task_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            user_instruction TEXT NOT NULL DEFAULT '',
            expression_style_level TEXT NOT NULL,
            transparency_level TEXT NOT NULL,
            stance_strategy_level TEXT NOT NULL,
            certainty_level TEXT NOT NULL DEFAULT '确定型',
            initiative_level TEXT NOT NULL,
            expression_style_prompt TEXT NOT NULL DEFAULT '',
            transparency_prompt TEXT NOT NULL DEFAULT '',
            stance_strategy_prompt TEXT NOT NULL DEFAULT '',
            initiative_prompt TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            used_at TEXT
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(chat_task_configs)").fetchall()}
    if "user_instruction" not in columns:
        conn.execute("ALTER TABLE chat_task_configs ADD COLUMN user_instruction TEXT NOT NULL DEFAULT ''")
    if "certainty_level" not in columns:
        conn.execute("ALTER TABLE chat_task_configs ADD COLUMN certainty_level TEXT NOT NULL DEFAULT '确定型'")
    if "initiative_level" not in columns:
        conn.execute("ALTER TABLE chat_task_configs ADD COLUMN initiative_level TEXT NOT NULL DEFAULT '被动响应'")


def ensure_qa_config_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_task_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            target_accuracy REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            used_at TEXT
        )
        """
    )


def normalize_account_id(account_id) -> str:
    return str(account_id or "").strip()


def normalize_secret(secret) -> str:
    return str(secret or "").strip()


def account_row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    return {
        "account_id": row[0],
        "password_key": row[1],
        "name": row[2] or "",
        "phone": row[3] or "",
        "chat_quota": int(row[4] or 0),
        "qa_quota": int(row[5] or 0),
        "plan_quota": int(row[6] or 0),
        "created_at": row[7] or "",
        "updated_at": row[8] or "",
    }


def get_account(account_id) -> Dict[str, Any]:
    clean_account_id = normalize_account_id(account_id)
    if not clean_account_id:
        return {}
    with connect_db() as conn:
        ensure_account_table(conn)
        row = conn.execute(
            """
            SELECT account_id, password_key, name, phone, chat_quota, qa_quota, plan_quota, created_at, updated_at
            FROM experiment_accounts
            WHERE account_id = ?
            """,
            (clean_account_id,),
        ).fetchone()
    return account_row_to_dict(row)


def list_account_rows() -> List[List[Any]]:
    with connect_db() as conn:
        ensure_account_table(conn)
        rows = conn.execute(
            """
            SELECT account_id, password_key, name, phone, chat_quota, qa_quota, plan_quota, created_at, updated_at
            FROM experiment_accounts
            ORDER BY created_at DESC, account_id ASC
            """
        ).fetchall()
    return [list(row) for row in rows]


def account_summary() -> str:
    with connect_db() as conn:
        ensure_account_table(conn)
        total = conn.execute("SELECT COUNT(*) FROM experiment_accounts").fetchone()[0]
    return f"共 {total} 个实验账号。"


def refresh_account_admin_view():
    return account_summary(), list_account_rows()


def account_choice_label(row: List[Any]) -> str:
    account_id, _password_key, name, phone, chat_quota, qa_quota, plan_quota, _created_at, _updated_at = row
    display_name = name or "未填写姓名"
    return f"{account_id} | {display_name} | {phone or '-'} | 聊天{chat_quota}/问答{qa_quota}/规划{plan_quota}"


def list_account_choices() -> List[str]:
    return [account_choice_label(row) for row in list_account_rows()]


def parse_account_choice(choice) -> str:
    if not choice:
        return ""
    return str(choice).split("|", 1)[0].strip()


def create_or_reset_account(account_id, password) -> Tuple[str, List[List[Any]]]:
    clean_account_id = normalize_account_id(account_id)
    if not clean_account_id:
        return "请输入账号ID。", list_account_rows()

    clean_password = normalize_secret(password)
    if not clean_password:
        return "请输入账号密码。", list_account_rows()

    now = current_time_text()

    with connect_db() as conn:
        ensure_account_table(conn)
        existing = conn.execute(
            "SELECT account_id FROM experiment_accounts WHERE account_id = ?",
            (clean_account_id,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE experiment_accounts
                SET password_key = ?, updated_at = ?
                WHERE account_id = ?
                """,
                (clean_password, now, clean_account_id),
            )
            return f"账号 `{clean_account_id}` 的密码已更新。", list_account_rows()

        conn.execute(
            """
            INSERT INTO experiment_accounts (
                account_id, password_key, name, phone, chat_quota, qa_quota, plan_quota, created_at, updated_at
            )
            VALUES (?, ?, '', '', 0, 0, 0, ?, ?)
            """,
            (clean_account_id, clean_password, now, now),
        )
    return f"账号 `{clean_account_id}` 已创建。", list_account_rows()



def delete_account_and_records(account_id):
    clean_account_id = normalize_account_id(account_id)
    if not clean_account_id:
        return "\u8bf7\u8f93\u5165\u8981\u5220\u9664\u7684\u8d26\u53f7ID\u3002", list_account_rows()

    with connect_db() as conn:
        ensure_account_table(conn)
        ensure_chat_config_table(conn)
        existing = conn.execute(
            "SELECT account_id FROM experiment_accounts WHERE account_id = ?",
            (clean_account_id,),
        ).fetchone()
        if not existing:
            return f"\u8d26\u53f7 `{clean_account_id}` \u4e0d\u5b58\u5728\u3002", list_account_rows()

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
        record_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(experiment_records)").fetchall()
        }
        if "account_id" not in record_columns:
            conn.execute("ALTER TABLE experiment_records ADD COLUMN account_id TEXT NOT NULL DEFAULT ''")
        deleted_configs = conn.execute(
            "DELETE FROM chat_task_configs WHERE account_id = ?",
            (clean_account_id,),
        ).rowcount
        deleted_records = conn.execute(
            "DELETE FROM experiment_records WHERE account_id = ?",
            (clean_account_id,),
        ).rowcount
        conn.execute(
            "DELETE FROM experiment_accounts WHERE account_id = ?",
            (clean_account_id,),
        )

    if normalize_account_id(EXPERIMENT_CONTEXT.get("account_id")) == clean_account_id:
        EXPERIMENT_CONTEXT.update(
            {
                "account_id": "-",
                "experiment_key": "-",
                "subject_name": "-",
                "phone": "",
                "chat_config_id": "",
                "chat_topic": "",
                "chat_user_instruction": "",
                "emotional_valence_level": "",
                "transparency_level": "",
                "stance_strategy_level": "",
                "emotional_valence_prompt": "",
                "transparency_prompt": "",
                "stance_strategy_prompt": "",
            }
        )

    return (
        f"\u8d26\u53f7 `{clean_account_id}` \u5df2\u5220\u9664\uff1b\u540c\u6b65\u5220\u9664\u804a\u5929\u914d\u7f6e {deleted_configs} \u6761\u3001\u7528\u6237\u6570\u636e\u8bb0\u5f55 {deleted_records} \u6761\u3002",
        list_account_rows(),
    )

def list_chat_config_rows() -> List[List[Any]]:
    with connect_db() as conn:
        ensure_chat_config_table(conn)
        rows = conn.execute(
            """
            SELECT id, account_id, topic, expression_style_level, transparency_level,
                   stance_strategy_level, status, created_at, used_at
            FROM chat_task_configs
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [list(row) for row in rows]


def chat_config_summary() -> str:
    with connect_db() as conn:
        ensure_chat_config_table(conn)
        total = conn.execute("SELECT COUNT(*) FROM chat_task_configs").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM chat_task_configs WHERE status = 'pending'").fetchone()[0]
    return f"共 {total} 条聊天任务配置；待使用 {pending} 条。"


def refresh_chat_config_admin_view():
    return (
        chat_config_summary(),
        gr.update(choices=list_account_choices(), value=None),
        list_chat_config_rows(),
        list_account_rows(),
    )


def initial_chat_config_admin_view():
    return chat_config_summary(), list_account_choices(), list_chat_config_rows(), list_account_rows()


def plan_config_summary() -> str:
    rows = list_account_rows()
    total_quota = sum(int(row[6] or 0) for row in rows)
    return f"当前共有 {len(rows)} 个账号；剩余规划任务次数合计 {total_quota} 次。"


def refresh_plan_config_admin_view():
    return (
        plan_config_summary(),
        gr.update(choices=list_account_choices(), value=None),
        list_account_rows(),
    )


def initial_plan_config_admin_view():
    return plan_config_summary(), list_account_choices(), list_account_rows()


def qa_config_summary() -> str:
    rows = list_account_rows()
    total_quota = sum(int(row[5] or 0) for row in rows)
    with connect_db() as conn:
        ensure_qa_config_table(conn)
        pending = conn.execute("SELECT COUNT(*) FROM qa_task_configs WHERE status = 'pending'").fetchone()[0]
    return f"当前共有 {len(rows)} 个账号；剩余问答任务次数合计 {total_quota} 次；待使用问答配置 {pending} 条。"


def refresh_qa_config_admin_view():
    return (
        qa_config_summary(),
        gr.update(choices=list_account_choices(), value=None),
        list_account_rows(),
    )


def initial_qa_config_admin_view():
    return qa_config_summary(), list_account_choices(), list_account_rows()


def normalize_qa_accuracy(value) -> float:
    raw = str(value or "").strip().replace("%", "")
    try:
        number = float(raw)
    except ValueError:
        return 0.0
    if number > 1:
        number = number / 100
    return number


def assign_qa_quota(account_choice, quota_count, target_accuracy):
    account_id = parse_account_choice(account_choice)
    if not account_id:
        return "请选择账号。", list_account_rows()
    if not get_account(account_id):
        return f"账号 `{account_id}` 不存在。", list_account_rows()

    try:
        count = int(quota_count or 0)
    except (TypeError, ValueError):
        return "请输入有效的问答任务次数。", list_account_rows()

    if count <= 0:
        return "问答任务次数必须大于 0。", list_account_rows()

    accuracy = normalize_qa_accuracy(target_accuracy)
    if accuracy not in (0.6, 0.8):
        return "目标准确率只能选择 60% 或 80%。", list_account_rows()

    now = current_time_text()
    rows_to_insert = [(account_id, accuracy, now) for _ in range(count)]
    with connect_db() as conn:
        ensure_account_table(conn)
        ensure_qa_config_table(conn)
        conn.executemany(
            """
            INSERT INTO qa_task_configs (account_id, target_accuracy, created_at)
            VALUES (?, ?, ?)
            """,
            rows_to_insert,
        )
        conn.execute(
            """
            UPDATE experiment_accounts
            SET qa_quota = qa_quota + ?, updated_at = ?
            WHERE account_id = ?
            """,
            (count, now, account_id),
        )

    return f"已为账号 `{account_id}` 增加 {count} 次问答任务，目标准确率 {int(accuracy * 100)}%。", list_account_rows()


def assign_plan_quota(account_choice, quota_count):
    account_id = parse_account_choice(account_choice)
    if not account_id:
        return "请选择账号。", list_account_rows()
    if not get_account(account_id):
        return f"账号 `{account_id}` 不存在。", list_account_rows()

    try:
        count = int(quota_count or 0)
    except (TypeError, ValueError):
        return "请输入有效的规划任务次数。", list_account_rows()

    if count <= 0:
        return "规划任务次数必须大于 0。", list_account_rows()

    now = current_time_text()
    with connect_db() as conn:
        ensure_account_table(conn)
        conn.execute(
            """
            UPDATE experiment_accounts
            SET plan_quota = plan_quota + ?, updated_at = ?
            WHERE account_id = ?
            """,
            (count, now, account_id),
        )

    return f"已为账号 `{account_id}` 增加 {count} 次规划任务。", list_account_rows()


def normalize_topic_selection(topics) -> List[str]:
    if topics is None:
        return []
    if isinstance(topics, str):
        raw_topics = [topics]
    else:
        raw_topics = list(topics)
    selected = {str(topic or "").strip() for topic in raw_topics}
    return [topic for topic in CHAT_TOPICS if topic in selected]


def validate_feature_values(feature_values: Dict[str, str]) -> List[str]:
    return [
        config["label"]
        for key, config in FEATURE_DIMENSION_CONFIGS.items()
        if feature_values[key] not in config["prompt_map"]
    ]


def insert_chat_task_configs(account_id: str, rows_to_insert: List[Tuple[Any, ...]], now: str) -> None:
    with connect_db() as conn:
        ensure_account_table(conn)
        ensure_chat_config_table(conn)
        conn.executemany(
            """
            INSERT INTO chat_task_configs (
                account_id,
                topic,
                user_instruction,
                expression_style_level,
                transparency_level,
                stance_strategy_level,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )
        conn.execute(
            """
            UPDATE experiment_accounts
            SET chat_quota = chat_quota + ?, updated_at = ?
            WHERE account_id = ?
            """,
            (len(rows_to_insert), now, account_id),
        )


def assign_chat_task_config(
    account_choice,
    topic,
    emotional_valence_level,
    transparency_level,
    stance_strategy_level,
):
    account_id = parse_account_choice(account_choice)
    if not account_id:
        return "请选择账号。", list_chat_config_rows(), list_account_rows()
    if not get_account(account_id):
        return f"账号 `{account_id}` 不存在。", list_chat_config_rows(), list_account_rows()

    selected_topic = str(topic or "").strip()
    if selected_topic not in CHAT_TOPICS:
        return "请选择聊天主题。", list_chat_config_rows(), list_account_rows()

    feature_values = {
        "emotional_valence": str(emotional_valence_level or "").strip(),
        "transparency": str(transparency_level or "").strip(),
        "stance_strategy": str(stance_strategy_level or "").strip(),
    }
    invalid_labels = validate_feature_values(feature_values)
    if invalid_labels:
        return f"请完整选择聊天输出特征维度：{', '.join(invalid_labels)}。", list_chat_config_rows(), list_account_rows()

    now = current_time_text()
    rows_to_insert = [
        (
            account_id,
            selected_topic,
            CHAT_TOPIC_INSTRUCTIONS[selected_topic],
            feature_values["emotional_valence"],
            feature_values["transparency"],
            feature_values["stance_strategy"],
            now,
        )
    ]
    insert_chat_task_configs(account_id, rows_to_insert, now)
    return f"已为账号 `{account_id}` 增加 1 次聊天任务：{selected_topic}。", list_chat_config_rows(), list_account_rows()


def assign_balanced_chat_task_configs(
    account_choice,
):
    account_id = parse_account_choice(account_choice)
    if not account_id:
        return "请选择账号。", list_chat_config_rows(), list_account_rows()
    if not get_account(account_id):
        return f"账号 `{account_id}` 不存在。", list_chat_config_rows(), list_account_rows()

    if len(CHAT_TOPICS) != 8:
        return f"当前聊天主题数量为 {len(CHAT_TOPICS)} 个，批量分配需要恰好 8 个主题。", list_chat_config_rows(), list_account_rows()
    if len(CHAT_STYLE_COMBINATIONS) != 8:
        return f"当前输出风格组合数量为 {len(CHAT_STYLE_COMBINATIONS)} 个，批量分配需要恰好 8 种组合。", list_chat_config_rows(), list_account_rows()

    now = current_time_text()
    rows_to_insert = []
    style_rows = list(CHAT_STYLE_COMBINATIONS)
    random.shuffle(style_rows)
    for selected_topic, style_values in zip(CHAT_TOPICS, style_rows):
        rows_to_insert.append(
            (
                account_id,
                selected_topic,
                CHAT_TOPIC_INSTRUCTIONS[selected_topic],
                style_values["emotional_valence"],
                style_values["transparency"],
                style_values["stance_strategy"],
                now,
            )
        )

    insert_chat_task_configs(account_id, rows_to_insert, now)
    topic_text = "、".join(CHAT_TOPICS)
    return (
        f"已为账号 `{account_id}` 批量增加 {len(rows_to_insert)} 次聊天任务；"
        f"8 个主题已与 8 种输出风格随机一一匹配：{topic_text}。",
        list_chat_config_rows(),
        list_account_rows(),
    )


def claim_next_chat_task_config(account_id: str) -> Dict[str, Any]:
    clean_account_id = normalize_account_id(account_id)
    if not clean_account_id:
        return {}

    now = current_time_text()
    with connect_db() as conn:
        ensure_account_table(conn)
        ensure_chat_config_table(conn)
        row = conn.execute(
            """
            SELECT id, topic, user_instruction, expression_style_level, transparency_level,
                   stance_strategy_level
            FROM chat_task_configs
            WHERE account_id = ? AND status = 'pending'
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (clean_account_id,),
        ).fetchone()
        if row is None:
            return {}

        config_id = int(row[0])
        updated = conn.execute(
            """
            UPDATE experiment_accounts
            SET chat_quota = chat_quota - 1, updated_at = ?
            WHERE account_id = ? AND chat_quota > 0
            """,
            (now, clean_account_id),
        ).rowcount
        if not updated:
            return {}

        conn.execute(
            """
            UPDATE chat_task_configs
            SET status = 'used', used_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (now, config_id),
        )

    return {
        "id": config_id,
        "topic": row[1],
        "user_instruction": row[2] or "",
        "emotional_valence_level": row[3],
        "transparency_level": row[4],
        "stance_strategy_level": row[5],
        "emotional_valence_prompt": EMOTIONAL_VALENCE_PROMPTS.get(row[3], ""),
        "transparency_prompt": TRANSPARENCY_PROMPTS.get(row[4], ""),
        "stance_strategy_prompt": STANCE_STRATEGY_PROMPTS.get(row[5], ""),
    }


def claim_next_qa_task_config(account_id: str) -> Dict[str, Any]:
    clean_account_id = normalize_account_id(account_id)
    if not clean_account_id:
        return {}

    now = current_time_text()
    with connect_db() as conn:
        ensure_account_table(conn)
        ensure_qa_config_table(conn)
        row = conn.execute(
            """
            SELECT id, target_accuracy
            FROM qa_task_configs
            WHERE account_id = ? AND status = 'pending'
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (clean_account_id,),
        ).fetchone()
        if row is None:
            return {}

        config_id = int(row[0])
        updated = conn.execute(
            """
            UPDATE experiment_accounts
            SET qa_quota = qa_quota - 1, updated_at = ?
            WHERE account_id = ? AND qa_quota > 0
            """,
            (now, clean_account_id),
        ).rowcount
        if not updated:
            return {}

        conn.execute(
            """
            UPDATE qa_task_configs
            SET status = 'used', used_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (now, config_id),
        )

    return {"id": config_id, "target_accuracy": float(row[1] or 0)}


def get_qa_task_config(account_id: str, config_id) -> Dict[str, Any]:
    clean_account_id = normalize_account_id(account_id)
    try:
        clean_config_id = int(config_id)
    except (TypeError, ValueError):
        return {}
    if not clean_account_id:
        return {}

    with connect_db() as conn:
        ensure_qa_config_table(conn)
        row = conn.execute(
            """
            SELECT id, target_accuracy
            FROM qa_task_configs
            WHERE id = ? AND account_id = ?
            """,
            (clean_config_id, clean_account_id),
        ).fetchone()
    if row is None:
        return {}
    return {"id": int(row[0]), "target_accuracy": float(row[1] or 0)}


def get_chat_task_config(account_id: str, config_id) -> Dict[str, Any]:
    clean_account_id = normalize_account_id(account_id)
    try:
        clean_config_id = int(config_id)
    except (TypeError, ValueError):
        return {}
    if not clean_account_id:
        return {}

    with connect_db() as conn:
        ensure_chat_config_table(conn)
        row = conn.execute(
            """
            SELECT id, topic, user_instruction, expression_style_level, transparency_level,
                   stance_strategy_level
            FROM chat_task_configs
            WHERE id = ? AND account_id = ?
            """,
            (clean_config_id, clean_account_id),
        ).fetchone()
    if row is None:
        return {}

    return {
        "id": int(row[0]),
        "topic": row[1],
        "user_instruction": row[2] or "",
        "emotional_valence_level": row[3],
        "transparency_level": row[4],
        "stance_strategy_level": row[5],
        "emotional_valence_prompt": EMOTIONAL_VALENCE_PROMPTS.get(row[3], ""),
        "transparency_prompt": TRANSPARENCY_PROMPTS.get(row[4], ""),
        "stance_strategy_prompt": STANCE_STRATEGY_PROMPTS.get(row[5], ""),
    }


def authenticate_account(account_id, password):
    clean_account_id = normalize_account_id(account_id)
    clean_password = normalize_secret(password)

    if not clean_account_id:
        return False, "请输入账号ID。", {}
    if not clean_password:
        return False, "请输入密码。", {}

    account = get_account(clean_account_id)
    if not account:
        return False, "账号不存在。", {}
    if clean_password != account["password_key"]:
        return False, "密码错误。", {}
    return True, f"登录成功，欢迎 {clean_account_id}。", account


def set_current_account(account: Dict[str, Any]) -> None:
    EXPERIMENT_CONTEXT["account_id"] = str(account.get("account_id") or "-")
    EXPERIMENT_CONTEXT["experiment_key"] = str(account.get("password_key") or "-")
    EXPERIMENT_CONTEXT["subject_name"] = str(account.get("name") or "")
    EXPERIMENT_CONTEXT["phone"] = str(account.get("phone") or "")


def get_current_account() -> Dict[str, Any]:
    return get_account(EXPERIMENT_CONTEXT.get("account_id"))


def format_quota_text(account: Dict[str, Any]) -> str:
    return (
        f"聊天：{int(account.get('chat_quota') or 0)} 次；"
        f"问答：{int(account.get('qa_quota') or 0)} 次；"
        f"规划：{int(account.get('plan_quota') or 0)} 次。"
    )


def profile_values():
    account = get_current_account()
    if not account:
        return (
            "未登录或账号不存在，请返回登录页。",
            "",
            "",
            "",
            "",
            "聊天：0 次；问答：0 次；规划：0 次。",
        )
    return (
        "",
        account["account_id"],
        account["password_key"],
        account["name"],
        account["phone"],
        format_quota_text(account),
    )


def profile_values_for_request(request: gr.Request):
    account = get_account(request_account_id(request))
    if not account:
        return (
            "未登录或账号不存在，请返回登录页。",
            "",
            "",
            "",
            "",
            "聊天：0 次；问答：0 次；规划：0 次。",
        )
    return (
        "",
        account["account_id"],
        account["password_key"],
        account["name"],
        account["phone"],
        format_quota_text(account),
    )


def save_profile_info(account_id, password_key, name, phone):
    clean_account_id = normalize_account_id(account_id)
    clean_password = normalize_secret(password_key)
    clean_name = str(name or "").strip()
    clean_phone = str(phone or "").strip()

    if not clean_account_id:
        return "账号ID不能为空。", gr.update(), gr.update()
    if not clean_password:
        return "密钥不能为空。", gr.update(), gr.update()

    with connect_db() as conn:
        ensure_account_table(conn)
        updated = conn.execute(
            """
            UPDATE experiment_accounts
            SET password_key = ?, name = ?, phone = ?, updated_at = ?
            WHERE account_id = ?
            """,
            (clean_password, clean_name, clean_phone, current_time_text(), clean_account_id),
        ).rowcount

    if not updated:
        return "账号不存在，无法保存。", gr.update(), gr.update()

    account = get_account(clean_account_id)
    return "个人信息已保存。", gr.update(value=clean_password), gr.update(value=format_quota_text(account))


def start_task(task_key):
    account = get_current_account()
    if not account:
        return "未登录或账号不存在，请返回登录页。", gr.update(value="")

    quota_column = TASK_QUOTA_COLUMNS.get(task_key)
    if not quota_column:
        return "未知任务类型。", gr.update(value="")

    current_quota = int(account.get(quota_column) or 0)
    task_name = TASK_NAMES[task_key]
    if current_quota <= 0:
        return f"{task_name}任务剩余次数为 0，无法进入实验。", gr.update(value="")

    if task_key == "chat":
        chat_config = claim_next_chat_task_config(account["account_id"])
        if not chat_config:
            return "聊天任务没有可用配置，无法进入实验。", gr.update(value="")

        refreshed = get_account(account["account_id"])
        set_current_account(refreshed)
        EXPERIMENT_CONTEXT["task_name"] = task_name
        EXPERIMENT_CONTEXT["chat_config_id"] = str(chat_config["id"])
        EXPERIMENT_CONTEXT["chat_topic"] = str(chat_config["topic"])
        EXPERIMENT_CONTEXT["chat_user_instruction"] = str(chat_config["user_instruction"])
        EXPERIMENT_CONTEXT["emotional_valence_level"] = str(chat_config["emotional_valence_level"])
        EXPERIMENT_CONTEXT["transparency_level"] = str(chat_config["transparency_level"])
        EXPERIMENT_CONTEXT["stance_strategy_level"] = str(chat_config["stance_strategy_level"])
        EXPERIMENT_CONTEXT["emotional_valence_prompt"] = str(chat_config["emotional_valence_prompt"])
        EXPERIMENT_CONTEXT["transparency_prompt"] = str(chat_config["transparency_prompt"])
        EXPERIMENT_CONTEXT["stance_strategy_prompt"] = str(chat_config["stance_strategy_prompt"])
        return (
            f"正在进入{task_name}任务，主题：{chat_config['topic']}；剩余次数：{int(refreshed.get(quota_column) or 0)}。",
            gr.update(value=f"<meta http-equiv='refresh' content='0;url={TASK_ROUTES[task_key]}'>"),
        )

    if task_key == "qa":
        qa_config = claim_next_qa_task_config(account["account_id"])
        if not qa_config:
            return "问答任务没有可用配置，无法进入实验。", gr.update(value="")

        refreshed = get_account(account["account_id"])
        set_current_account(refreshed)
        EXPERIMENT_CONTEXT["task_name"] = task_name
        EXPERIMENT_CONTEXT["qa_config_id"] = str(qa_config["id"])
        EXPERIMENT_CONTEXT["qa_target_accuracy"] = str(qa_config["target_accuracy"])
        return (
            f"正在进入{task_name}任务，目标准确率：{int(float(qa_config['target_accuracy']) * 100)}%；剩余次数：{int(refreshed.get(quota_column) or 0)}。",
            gr.update(value=f"<meta http-equiv='refresh' content='0;url={TASK_ROUTES[task_key]}'>"),
        )

    with connect_db() as conn:
        ensure_account_table(conn)
        updated = conn.execute(
            f"""
            UPDATE experiment_accounts
            SET {quota_column} = {quota_column} - 1, updated_at = ?
            WHERE account_id = ? AND {quota_column} > 0
            """,
            (current_time_text(), account["account_id"]),
        ).rowcount

    if not updated:
        return f"{task_name}任务剩余次数为 0，无法进入实验。", gr.update(value="")

    refreshed = get_account(account["account_id"])
    set_current_account(refreshed)
    EXPERIMENT_CONTEXT["task_name"] = task_name
    return (
        f"正在进入{task_name}任务，剩余次数：{int(refreshed.get(quota_column) or 0)}。",
        gr.update(value=f"<meta http-equiv='refresh' content='0;url={TASK_ROUTES[task_key]}'>"),
    )


def start_task_for_account(task_key, account_id):
    clean_account_id = normalize_account_id(account_id)
    quoted_account_id = quote(clean_account_id)
    account = get_account(clean_account_id)
    if not account:
        return "未登录或账号不存在，请返回登录页。", gr.update(value="")

    quota_column = TASK_QUOTA_COLUMNS.get(task_key)
    if not quota_column:
        return "未知任务类型。", gr.update(value="")

    current_quota = int(account.get(quota_column) or 0)
    task_name = TASK_NAMES[task_key]
    if current_quota <= 0:
        return f"{task_name}任务剩余次数为 0，无法进入实验。", gr.update(value="")

    if task_key == "chat":
        chat_config = claim_next_chat_task_config(clean_account_id)
        if not chat_config:
            return "聊天任务没有可用配置，无法进入实验。", gr.update(value="")

        refreshed = get_account(clean_account_id)
        return (
            f"正在进入{task_name}任务，主题：{chat_config['topic']}；剩余次数：{int(refreshed.get(quota_column) or 0)}。",
            gr.update(
                value=(
                    "<meta http-equiv='refresh' "
                    f"content='0;url=/chat?account_id={quoted_account_id}&chat_config_id={chat_config['id']}'>"
                )
            ),
        )

    if task_key == "qa":
        qa_config = claim_next_qa_task_config(clean_account_id)
        if not qa_config:
            return "问答任务没有可用配置，无法进入实验。", gr.update(value="")

        refreshed = get_account(clean_account_id)
        return (
            f"正在进入{task_name}任务，目标准确率：{int(float(qa_config['target_accuracy']) * 100)}%；剩余次数：{int(refreshed.get(quota_column) or 0)}。",
            gr.update(
                value=(
                    "<meta http-equiv='refresh' "
                    f"content='0;url=/qa?account_id={quoted_account_id}&qa_config_id={qa_config['id']}'>"
                )
            ),
        )

    with connect_db() as conn:
        ensure_account_table(conn)
        updated = conn.execute(
            f"""
            UPDATE experiment_accounts
            SET {quota_column} = {quota_column} - 1, updated_at = ?
            WHERE account_id = ? AND {quota_column} > 0
            """,
            (current_time_text(), clean_account_id),
        ).rowcount

    if not updated:
        return f"{task_name}任务剩余次数为 0，无法进入实验。", gr.update(value="")

    refreshed = get_account(clean_account_id)
    return (
        f"正在进入{task_name}任务，剩余次数：{int(refreshed.get(quota_column) or 0)}。",
        gr.update(value=f"<meta http-equiv='refresh' content='0;url={TASK_ROUTES[task_key]}?account_id={quoted_account_id}'>"),
    )


def build_chat_context_for_request(request) -> Dict[str, str]:
    account_id = request_account_id(request)
    account = get_account(account_id)
    if not account:
        return {}

    chat_config = get_chat_task_config(account_id, request_chat_config_id(request))
    if not chat_config:
        return {
            "account_id": account_id,
            "experiment_key": str(account.get("password_key") or "-"),
            "subject_name": str(account.get("name") or ""),
            "phone": str(account.get("phone") or ""),
            "task_name": TASK_NAMES["chat"],
        }

    return {
        "account_id": account_id,
        "experiment_key": str(account.get("password_key") or "-"),
        "subject_name": str(account.get("name") or ""),
        "phone": str(account.get("phone") or ""),
        "task_name": TASK_NAMES["chat"],
        "chat_config_id": str(chat_config["id"]),
        "chat_topic": str(chat_config["topic"]),
        "chat_user_instruction": str(chat_config["user_instruction"]),
        "emotional_valence_level": str(chat_config["emotional_valence_level"]),
        "transparency_level": str(chat_config["transparency_level"]),
        "stance_strategy_level": str(chat_config["stance_strategy_level"]),
        "emotional_valence_prompt": str(chat_config["emotional_valence_prompt"]),
        "transparency_prompt": str(chat_config["transparency_prompt"]),
        "stance_strategy_prompt": str(chat_config["stance_strategy_prompt"]),
    }


def build_qa_context_for_request(request) -> Dict[str, str]:
    account_id = request_account_id(request)
    account = get_account(account_id)
    if not account:
        return {}

    qa_config = get_qa_task_config(account_id, request_qa_config_id(request))
    target_accuracy = float(qa_config.get("target_accuracy") or 0.6)
    return {
        "account_id": account_id,
        "experiment_key": str(account.get("password_key") or "-"),
        "subject_name": str(account.get("name") or ""),
        "phone": str(account.get("phone") or ""),
        "task_name": TASK_NAMES["qa"],
        "qa_config_id": str(qa_config.get("id") or ""),
        "qa_target_accuracy": str(target_accuracy),
    }
