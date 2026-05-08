import sqlite3
from typing import Any, Dict, List, Tuple

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
CHAT_TOPIC_INSTRUCTIONS = {
    item["topic"]: item["userInstruction"]
    for item in CHAT_TOPIC_CONFIGS
}

EMOTIONAL_VALENCE_PROMPTS = {
    "理性导向": "请使用冷静、克制、低情绪化的表达风格。\n回答应更像观察与判断，而不是安慰、鼓励或陪伴。\n避免使用等情绪性表达,不主动提供情绪价值。",
    "感性导向": "请使用感性、共情性的表达风格。",
}

TRANSPARENCY_PROMPTS = {
    "低透明": "直接给出回应或判断，不给解释过程。\n回答越简短越好。默认不要使用列表式建议或分点展开。优先给出一句到两句核心判断。",
    "高透明": "明确说明结论、主要依据、关键假设和可能限制。\n在相关时指出不确定性、适用边界或替代解释。\n可以用结构化方式帮助用户理解为什么这样回答。\n不要只给结论而不说明依据。",
}

STANCE_STRATEGY_PROMPTS = {
    "顺应型": "优先顺着用户当前的表达和意图回应。",
    "协商型": "先承认用户观点中合理的部分，再温和补充或修正。",
    "批判型": "优先检查用户表述中的逻辑跳跃、过度概括、风险判断或自我否定。",
}

CERTAINTY_PROMPTS = {
    "确定表达": "使用相对明确、肯定、稳定的表达方式。\n不要使用“可能”“也许”“不一定”等弱化词。\n可以清楚指出问题、结论或建议的方向。\n不要把本可以明确回答的内容说得含糊不清。",
    "不确定表达": "使用更审慎、保留、不绝对化的表达方式。\n在涉及判断、预测、归因或建议时，多使用“我不确定”“可能”“看起来”“有一种情况是”“还需要看”等表达。",
}

EMOTIONAL_VALENCE_OPTIONS = list(EMOTIONAL_VALENCE_PROMPTS.keys())
TRANSPARENCY_OPTIONS = list(TRANSPARENCY_PROMPTS.keys())
STANCE_STRATEGY_OPTIONS = list(STANCE_STRATEGY_PROMPTS.keys())
CERTAINTY_OPTIONS = list(CERTAINTY_PROMPTS.keys())

CHAT_CONFIG_TABLE_COLUMNS = [
    "配置ID",
    "账号ID",
    "主题",
    "情感效价",
    "透明度水平",
    "立场策略",
    "表达确定性",
    "状态",
    "创建时间",
    "使用时间",
]

TASK_ROUTES = {
    "chat": "/chat",
    "qa": "/qa",
    "plan": "/plan",
}

TASK_NAMES = {
    "chat": "聊天",
    "qa": "问答",
    "plan": "规划",
}

TASK_QUOTA_COLUMNS = {
    "chat": "chat_quota",
    "qa": "qa_quota",
    "plan": "plan_quota",
}


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
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(chat_task_configs)").fetchall()
    }
    if "user_instruction" not in columns:
        conn.execute("ALTER TABLE chat_task_configs ADD COLUMN user_instruction TEXT NOT NULL DEFAULT ''")


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


def list_chat_config_rows() -> List[List[Any]]:
    with connect_db() as conn:
        ensure_chat_config_table(conn)
        rows = conn.execute(
            """
            SELECT id, account_id, topic, expression_style_level, transparency_level,
                   stance_strategy_level, initiative_level, status, created_at, used_at
            FROM chat_task_configs
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [list(row) for row in rows]


def chat_config_summary() -> str:
    with connect_db() as conn:
        ensure_chat_config_table(conn)
        total = conn.execute("SELECT COUNT(*) FROM chat_task_configs").fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM chat_task_configs WHERE status = 'pending'"
        ).fetchone()[0]
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


def assign_chat_task_config(
    account_choice,
    topic,
    emotional_valence_level,
    transparency_level,
    stance_strategy_level,
    certainty_level,
):
    account_id = parse_account_choice(account_choice)
    if not account_id:
        return "请选择账号。", list_chat_config_rows(), list_account_rows()
    account = get_account(account_id)
    if not account:
        return f"账号 `{account_id}` 不存在。", list_chat_config_rows(), list_account_rows()

    selected_topic = str(topic or "").strip()
    if selected_topic not in CHAT_TOPICS:
        return "请选择聊天主题。", list_chat_config_rows(), list_account_rows()

    emotional_valence = str(emotional_valence_level or "").strip()
    transparency = str(transparency_level or "").strip()
    stance_strategy = str(stance_strategy_level or "").strip()
    certainty = str(certainty_level or "").strip()
    if (
        emotional_valence not in EMOTIONAL_VALENCE_PROMPTS
        or transparency not in TRANSPARENCY_PROMPTS
        or stance_strategy not in STANCE_STRATEGY_PROMPTS
        or certainty not in CERTAINTY_PROMPTS
    ):
        return "请完整选择聊天输出特征维度。", list_chat_config_rows(), list_account_rows()

    now = current_time_text()
    with connect_db() as conn:
        ensure_account_table(conn)
        ensure_chat_config_table(conn)
        conn.execute(
            """
            INSERT INTO chat_task_configs (
                account_id,
                topic,
                user_instruction,
                expression_style_level,
                transparency_level,
                stance_strategy_level,
                initiative_level,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                selected_topic,
                CHAT_TOPIC_INSTRUCTIONS[selected_topic],
                emotional_valence,
                transparency,
                stance_strategy,
                certainty,
                now,
            ),
        )
        conn.execute(
            """
            UPDATE experiment_accounts
            SET chat_quota = chat_quota + 1, updated_at = ?
            WHERE account_id = ?
            """,
            (now, account_id),
        )

    return (
        f"已为账号 `{account_id}` 增加 1 次聊天任务：{selected_topic}。",
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
                   stance_strategy_level, initiative_level
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
        "emotional_valence_prompt": EMOTIONAL_VALENCE_PROMPTS.get(row[3], ""),
        "transparency_prompt": TRANSPARENCY_PROMPTS.get(row[4], ""),
        "stance_strategy_prompt": STANCE_STRATEGY_PROMPTS.get(row[5], ""),
        "certainty_prompt": CERTAINTY_PROMPTS.get(row[6], ""),
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


def format_quota_text(account: Dict[str, Any]) -> str:
    return (
        f"聊天：{int(account.get('chat_quota') or 0)} 次；"
        f"问答：{int(account.get('qa_quota') or 0)} 次；"
        f"规划：{int(account.get('plan_quota') or 0)} 次。"
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
    set_current_account(account)
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
        EXPERIMENT_CONTEXT["emotional_valence_prompt"] = str(chat_config["emotional_valence_prompt"])
        EXPERIMENT_CONTEXT["transparency_prompt"] = str(chat_config["transparency_prompt"])
        EXPERIMENT_CONTEXT["stance_strategy_prompt"] = str(chat_config["stance_strategy_prompt"])
        EXPERIMENT_CONTEXT["certainty_prompt"] = str(chat_config["certainty_prompt"])
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
