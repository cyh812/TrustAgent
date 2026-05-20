import sqlite3
from itertools import permutations
from typing import Any, Dict, List, Tuple
from urllib.parse import quote

import gradio as gr

from app.config import EXPERIMENT_CONTEXT
from app.services.key_service import connect_db, current_time_text, make_key


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
]

CHAT_TOPICS = [item["topic"] for item in CHAT_TOPIC_CONFIGS]
CHAT_TOPIC_INSTRUCTIONS = {item["topic"]: item["userInstruction"] for item in CHAT_TOPIC_CONFIGS}

EMOTIONAL_VALENCE_PROMPTS = {
    "理性导向": "回答时以分析和事实为主，尽量减少情绪安慰和共情表达。",
    "感性导向": "回答时优先表达理解和支持，强调情绪回应与共情。",
    "中立导向": "回答时先简要回应用户感受，再提供客观分析和建议。",
}

TRANSPARENCY_PROMPTS = {
    "低透明": "直接给出观点或建议，不主动解释判断依据。",
    "中透明": "给出观点时简要说明主要理由，并适度提示适用条件。",
    "高透明": "明确说明判断依据、关键假设、局限和可能的替代情况。",
}

STANCE_STRATEGY_PROMPTS = {
    "用户立场": "优先贴近用户的观点和感受，以支持和认同为主要回应方式。",
    "协商导向": "先认可用户观点的合理性，再温和补充其他角度。",
    "独立客观": "保持相对中立和独立的视角，不主动贴近用户立场。",
}

CERTAINTY_PROMPTS = {
    "确定型": "使用明确肯定的语气表达结论，尽量减少保留性表述。",
    "开放型": "使用“可能”“也许”等措辞，呈现多种合理可能性。",
    "不确定型": "明确指出信息不足和判断局限，强调结论存在较大不确定性。",
}

INITIATIVE_PROMPTS = {
    "被动响应": "只回答用户当前问题，不主动追问或扩展话题。",
    "适应主动": "在回答后适度追问或补充，引导对话自然深入。",
    "高主动": "主动规划讨论方向，持续提出问题和下一步建议。",
}

EMOTIONAL_VALENCE_OPTIONS = list(EMOTIONAL_VALENCE_PROMPTS.keys())
TRANSPARENCY_OPTIONS = list(TRANSPARENCY_PROMPTS.keys())
STANCE_STRATEGY_OPTIONS = list(STANCE_STRATEGY_PROMPTS.keys())
CERTAINTY_OPTIONS = list(CERTAINTY_PROMPTS.keys())
INITIATIVE_OPTIONS = list(INITIATIVE_PROMPTS.keys())

FEATURE_DIMENSION_CONFIGS = {
    "emotional_valence": {
        "label": "情感效价",
        "options": EMOTIONAL_VALENCE_OPTIONS,
        "prompt_map": EMOTIONAL_VALENCE_PROMPTS,
    },
    "transparency": {
        "label": "透明度水平",
        "options": TRANSPARENCY_OPTIONS,
        "prompt_map": TRANSPARENCY_PROMPTS,
    },
    "stance_strategy": {
        "label": "立场策略",
        "options": STANCE_STRATEGY_OPTIONS,
        "prompt_map": STANCE_STRATEGY_PROMPTS,
    },
    "certainty": {
        "label": "表达确定性",
        "options": CERTAINTY_OPTIONS,
        "prompt_map": CERTAINTY_PROMPTS,
    },
    "initiative": {
        "label": "主动性水平",
        "options": INITIATIVE_OPTIONS,
        "prompt_map": INITIATIVE_PROMPTS,
    },
}

BALANCED_OPTION_ORDERS = list(permutations((0, 1, 2)))

CHAT_CONFIG_TABLE_COLUMNS = [
    "配置ID",
    "账号ID",
    "主题",
    "情感效价",
    "透明度水平",
    "立场策略",
    "表达确定性",
    "主动性水平",
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


def create_or_reset_account(account_id, key_prefix="TA") -> Tuple[str, List[List[Any]]]:
    clean_account_id = normalize_account_id(account_id)
    if not clean_account_id:
        return "请输入账号ID。", list_account_rows()

    now = current_time_text()
    password_key = make_key(key_prefix)

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
                (password_key, now, clean_account_id),
            )
            return f"账号 `{clean_account_id}` 的密钥已重新生成：`{password_key}`", list_account_rows()

        conn.execute(
            """
            INSERT INTO experiment_accounts (
                account_id, password_key, name, phone, chat_quota, qa_quota, plan_quota, created_at, updated_at
            )
            VALUES (?, ?, '', '', 0, 1, 1, ?, ?)
            """,
            (clean_account_id, password_key, now, now),
        )
    return f"账号 `{clean_account_id}` 已创建，密钥：`{password_key}`", list_account_rows()



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
                "certainty_level": "",
                "initiative_level": "",
                "emotional_valence_prompt": "",
                "transparency_prompt": "",
                "stance_strategy_prompt": "",
                "certainty_prompt": "",
                "initiative_prompt": "",
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
                   stance_strategy_level, certainty_level, initiative_level, status, created_at, used_at
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
                certainty_level,
                initiative_level,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    certainty_level,
    initiative_level,
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
        "certainty": str(certainty_level or "").strip(),
        "initiative": str(initiative_level or "").strip(),
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
            feature_values["certainty"],
            feature_values["initiative"],
            now,
        )
    ]
    insert_chat_task_configs(account_id, rows_to_insert, now)
    return f"已为账号 `{account_id}` 增加 1 次聊天任务：{selected_topic}。", list_chat_config_rows(), list_account_rows()


def assign_balanced_chat_task_configs(
    account_choice,
    topics,
    emotional_valence_level,
    emotional_valence_locked,
    transparency_level,
    transparency_locked,
    stance_strategy_level,
    stance_strategy_locked,
    certainty_level,
    certainty_locked,
    initiative_level,
    initiative_locked,
):
    account_id = parse_account_choice(account_choice)
    if not account_id:
        return "请选择账号。", list_chat_config_rows(), list_account_rows()
    if not get_account(account_id):
        return f"账号 `{account_id}` 不存在。", list_chat_config_rows(), list_account_rows()

    try:
        account_number = int(account_id)
    except ValueError:
        return "账号ID需要为数字，才能进行基于ID的平衡分配。", list_chat_config_rows(), list_account_rows()

    selected_topics = normalize_topic_selection(topics)
    if len(selected_topics) not in (3, 6):
        return "请选择 3 个或 6 个聊天主题。", list_chat_config_rows(), list_account_rows()

    feature_values = {
        "emotional_valence": str(emotional_valence_level or "").strip(),
        "transparency": str(transparency_level or "").strip(),
        "stance_strategy": str(stance_strategy_level or "").strip(),
        "certainty": str(certainty_level or "").strip(),
        "initiative": str(initiative_level or "").strip(),
    }
    feature_locks = {
        "emotional_valence": bool(emotional_valence_locked),
        "transparency": bool(transparency_locked),
        "stance_strategy": bool(stance_strategy_locked),
        "certainty": bool(certainty_locked),
        "initiative": bool(initiative_locked),
    }

    invalid_labels = validate_feature_values(feature_values)
    if invalid_labels:
        return f"请完整选择特征维度：{', '.join(invalid_labels)}。", list_chat_config_rows(), list_account_rows()

    unlocked_keys = [key for key, locked in feature_locks.items() if not locked]
    if len(unlocked_keys) != 1:
        return "请恰好锁定 4 个特征维度，并保留 1 个维度未锁定。", list_chat_config_rows(), list_account_rows()

    unlocked_key = unlocked_keys[0]
    unlocked_config = FEATURE_DIMENSION_CONFIGS[unlocked_key]
    unlocked_options = unlocked_config["options"]
    if len(unlocked_options) != 3:
        return f"{unlocked_config['label']} 需要恰好 3 个子维度才能平衡分配。", list_chat_config_rows(), list_account_rows()

    order = BALANCED_OPTION_ORDERS[account_number % len(BALANCED_OPTION_ORDERS)]
    balanced_values = [unlocked_options[index] for index in order]

    now = current_time_text()
    rows_to_insert = []
    for index, selected_topic in enumerate(selected_topics):
        row_values = dict(feature_values)
        row_values[unlocked_key] = balanced_values[index % len(balanced_values)]
        rows_to_insert.append(
            (
                account_id,
                selected_topic,
                CHAT_TOPIC_INSTRUCTIONS[selected_topic],
                row_values["emotional_valence"],
                row_values["transparency"],
                row_values["stance_strategy"],
                row_values["certainty"],
                row_values["initiative"],
                now,
            )
        )

    insert_chat_task_configs(account_id, rows_to_insert, now)
    topic_text = "、".join(selected_topics)
    return (
        f"已为账号 `{account_id}` 批量增加 {len(rows_to_insert)} 次聊天任务；"
        f"未锁定维度：{unlocked_config['label']}；主题：{topic_text}。",
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
                   stance_strategy_level, certainty_level, initiative_level
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
        "certainty_level": row[6],
        "initiative_level": row[7],
        "emotional_valence_prompt": EMOTIONAL_VALENCE_PROMPTS.get(row[3], ""),
        "transparency_prompt": TRANSPARENCY_PROMPTS.get(row[4], ""),
        "stance_strategy_prompt": STANCE_STRATEGY_PROMPTS.get(row[5], ""),
        "certainty_prompt": CERTAINTY_PROMPTS.get(row[6], ""),
        "initiative_prompt": INITIATIVE_PROMPTS.get(row[7], ""),
    }


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
                   stance_strategy_level, certainty_level, initiative_level
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
        "certainty_level": row[6],
        "initiative_level": row[7],
        "emotional_valence_prompt": EMOTIONAL_VALENCE_PROMPTS.get(row[3], ""),
        "transparency_prompt": TRANSPARENCY_PROMPTS.get(row[4], ""),
        "stance_strategy_prompt": STANCE_STRATEGY_PROMPTS.get(row[5], ""),
        "certainty_prompt": CERTAINTY_PROMPTS.get(row[6], ""),
        "initiative_prompt": INITIATIVE_PROMPTS.get(row[7], ""),
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
        EXPERIMENT_CONTEXT["certainty_level"] = str(chat_config["certainty_level"])
        EXPERIMENT_CONTEXT["initiative_level"] = str(chat_config["initiative_level"])
        EXPERIMENT_CONTEXT["emotional_valence_prompt"] = str(chat_config["emotional_valence_prompt"])
        EXPERIMENT_CONTEXT["transparency_prompt"] = str(chat_config["transparency_prompt"])
        EXPERIMENT_CONTEXT["stance_strategy_prompt"] = str(chat_config["stance_strategy_prompt"])
        EXPERIMENT_CONTEXT["certainty_prompt"] = str(chat_config["certainty_prompt"])
        EXPERIMENT_CONTEXT["initiative_prompt"] = str(chat_config["initiative_prompt"])
        return (
            f"正在进入{task_name}任务，主题：{chat_config['topic']}；剩余次数：{int(refreshed.get(quota_column) or 0)}。",
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
        "certainty_level": str(chat_config["certainty_level"]),
        "initiative_level": str(chat_config["initiative_level"]),
        "emotional_valence_prompt": str(chat_config["emotional_valence_prompt"]),
        "transparency_prompt": str(chat_config["transparency_prompt"]),
        "stance_strategy_prompt": str(chat_config["stance_strategy_prompt"]),
        "certainty_prompt": str(chat_config["certainty_prompt"]),
        "initiative_prompt": str(chat_config["initiative_prompt"]),
    }
