# travel_langgraph_agent_cli_v2.py

import json
import random
from typing import TypedDict, Literal, Optional, List, Dict, Any

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from langgraph.graph import StateGraph, START, END


# =========================================================
# 1. OpenRouter 配置
# =========================================================

OPENROUTER_API_KEY = ""  # 改成你的 OpenRouter Key
MODEL_NAME = ""

FLIGHT_FAIL_RATE = 0.25
HOTEL_FAIL_RATE = 0.25
RESTAURANT_FAIL_RATE = 0.30
WEATHER_FAIL_RATE = 0.10


# =========================================================
# 2. 本地模拟数据库
# =========================================================

DESTINATION_DB = {
    "京都": {
        "country": "日本",
        "gateway_city": "大阪",
        "gateway_airport": "关西国际机场",
        "attractions": ["清水寺", "伏见稻荷大社", "岚山", "金阁寺", "鸭川", "二年坂三年坂"],
        "foods": ["怀石料理", "抹茶甜品", "汤豆腐", "鳗鱼饭", "拉面"],
        "hotel_areas": ["京都站附近", "四条河原町", "祇园附近"],
        "local_transport": ["JR/Haruka", "巴士", "地铁", "步行", "出租车"],
    },
    "北京": {
        "country": "中国",
        "gateway_city": "北京",
        "gateway_airport": "首都机场/大兴机场",
        "attractions": ["故宫", "天坛", "颐和园", "长城", "什刹海", "国家博物馆"],
        "foods": ["北京烤鸭", "涮羊肉", "炸酱面", "卤煮"],
        "hotel_areas": ["王府井", "前门", "国贸", "鼓楼"],
        "local_transport": ["地铁", "公交", "打车", "步行"],
    },
    "杭州": {
        "country": "中国",
        "gateway_city": "杭州",
        "gateway_airport": "萧山国际机场",
        "attractions": ["西湖", "灵隐寺", "西溪湿地", "良渚博物院", "河坊街"],
        "foods": ["西湖醋鱼", "龙井虾仁", "片儿川", "东坡肉"],
        "hotel_areas": ["西湖边", "武林广场", "滨江", "钱江新城"],
        "local_transport": ["地铁", "公交", "步行", "共享单车"],
    },
}


# =========================================================
# 3. 工具
# =========================================================

def maybe_fail(action: str, fail_rate: float) -> Optional[str]:
    if random.random() < fail_rate:
        return f"{action}失败：供应商接口暂时不可用、库存不足或网络波动。"
    return None


@tool
def get_destination_info(destination: str) -> str:
    """
    查询目的地基础旅游信息，包括国家、入口城市、景点、美食、住宿区域和本地交通。
    本工具只使用本地模拟数据。
    """
    data = DESTINATION_DB.get(destination)

    if not data:
        data = {
            "country": "未知",
            "gateway_city": destination,
            "gateway_airport": "目的地主要机场",
            "attractions": ["城市核心景点", "当地博物馆", "特色街区", "自然景观"],
            "foods": ["当地特色餐饮"],
            "hotel_areas": ["市中心", "交通枢纽附近"],
            "local_transport": ["公共交通", "步行", "出租车"],
        }

    return json.dumps(
        {
            "status": "success",
            "destination": destination,
            "data": data,
            "note": "本地模拟目的地数据库结果。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def simulate_weather(destination: str, date: str) -> str:
    """
    模拟天气查询。可能失败。
    """
    failure = maybe_fail("天气查询", WEATHER_FAIL_RATE)
    if failure:
        return json.dumps(
            {
                "status": "failed",
                "message": failure,
                "suggestion": "可稍后重试，或按季节常识准备雨具、防晒与轻便外套。",
            },
            ensure_ascii=False,
            indent=2,
        )

    return json.dumps(
        {
            "status": "success",
            "destination": destination,
            "date": date,
            "weather": random.choice(["晴", "多云", "阴", "小雨"]),
            "temperature": f"{random.randint(12, 30)}℃",
            "suggestion": random.choice(["适合步行游览", "建议携带雨具", "注意防晒", "适合室内外结合安排"]),
            "note": "这是模拟天气，不是真实天气。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def simulate_flight_booking(
    origin: str,
    destination: str,
    date: str,
    people: int = 1,
    cabin: str = "经济舱",
) -> str:
    """
    模拟机票查询与预订。可能失败。注意：这是模拟预订，不是真实订单。
    """
    failure = maybe_fail("机票预订", FLIGHT_FAIL_RATE)
    if failure:
        return json.dumps(
            {
                "status": "failed",
                "type": "flight",
                "origin": origin,
                "destination": destination,
                "date": date,
                "message": failure,
                "suggestion": "可以重试、换日期、换机场，或先保留交通建议不做模拟预订。",
            },
            ensure_ascii=False,
            indent=2,
        )

    price_per_person = random.randint(600, 2200)

    return json.dumps(
        {
            "status": "success",
            "type": "flight",
            "origin": origin,
            "destination": destination,
            "date": date,
            "people": people,
            "cabin": cabin,
            "airline": random.choice(["东方航空", "中国国航", "南方航空", "春秋航空"]),
            "departure_time": random.choice(["08:30", "11:20", "14:45", "19:10"]),
            "arrival_time": random.choice(["10:50", "13:40", "17:15", "21:30"]),
            "price_per_person": price_per_person,
            "total_price": price_per_person * people,
            "note": "这是本地模拟结果，并非真实机票订单。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def simulate_hotel_booking(
    destination: str,
    checkin_date: str,
    nights: int,
    people: int = 1,
    hotel_level: str = "中档",
    area_preference: str = "交通便利",
) -> str:
    """
    模拟酒店查询与预订。可能失败。注意：这是模拟预订，不是真实订单。
    """
    failure = maybe_fail("酒店预订", HOTEL_FAIL_RATE)
    if failure:
        return json.dumps(
            {
                "status": "failed",
                "type": "hotel",
                "destination": destination,
                "checkin_date": checkin_date,
                "message": failure,
                "suggestion": "可以重试、换区域、调整酒店档次，或只保留住宿区域建议。",
            },
            ensure_ascii=False,
            indent=2,
        )

    price_map = {
        "经济": (180, 350),
        "中档": (350, 700),
        "舒适": (700, 1200),
        "豪华": (1200, 2500),
    }
    low, high = price_map.get(hotel_level, (350, 700))
    price_per_night = random.randint(low, high)

    areas = DESTINATION_DB.get(destination, {}).get("hotel_areas", ["市中心", "交通枢纽附近"])

    return json.dumps(
        {
            "status": "success",
            "type": "hotel",
            "destination": destination,
            "checkin_date": checkin_date,
            "nights": nights,
            "people": people,
            "hotel_level": hotel_level,
            "area_preference": area_preference,
            "hotel_name": random.choice(["城市精选酒店", "湖畔假日酒店", "中心精品酒店", "旅行者之家"]),
            "area": random.choice(areas),
            "price_per_night": price_per_night,
            "total_price": price_per_night * nights,
            "note": "这是本地模拟结果，并非真实酒店订单。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def simulate_restaurant_booking(
    destination: str,
    date: str,
    people: int = 1,
    food_preference: str = "当地特色",
    meal_time: str = "晚餐",
) -> str:
    """
    模拟餐厅推荐与预订。可能失败。注意：这是模拟预订，不是真实订单。
    """
    failure = maybe_fail("餐厅预订", RESTAURANT_FAIL_RATE)
    if failure:
        return json.dumps(
            {
                "status": "failed",
                "type": "restaurant",
                "destination": destination,
                "date": date,
                "message": failure,
                "suggestion": "可以重试、换菜系、换用餐时间，或改成无需预订的餐饮建议。",
            },
            ensure_ascii=False,
            indent=2,
        )

    foods = DESTINATION_DB.get(destination, {}).get("foods", ["当地特色菜"])

    return json.dumps(
        {
            "status": "success",
            "type": "restaurant",
            "destination": destination,
            "date": date,
            "people": people,
            "restaurant_name": random.choice(["本地风味馆", "老街小馆", "城市食堂", "隐味料理"]),
            "recommended_food": random.choice(foods),
            "food_preference": food_preference,
            "meal_time": meal_time,
            "time": random.choice(["12:00", "12:30", "18:00", "18:30", "19:00", "19:30"]),
            "note": "这是本地模拟结果，并非真实餐厅订单。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def ask_user(question: str) -> str:
    """
    当信息缺失、工具连续失败、出现重要选择，或阶段完成需要用户确认时，向用户提问。
    用户回答会作为工具结果返回给 Agent，由 LLM 继续解析。
    """
    print("\n--- 当前节点：ask_user ---")
    print(question)
    reply = input("你：").strip()
    return reply


# =========================================================
# 4. LangGraph 状态
# =========================================================

Stage = Literal["need", "plan", "transport", "hotel", "dining", "final", "done"]


class TravelState(TypedDict, total=False):
    messages: List[Dict[str, str]]
    current_stage: Stage
    stage_results: Dict[str, str]
    last_stage_output: str
    user_confirmed: bool
    interaction_log: List[Dict[str, str]]


STAGES = ["need", "plan", "transport", "hotel", "dining", "final"]

STAGE_TITLES = {
    "need": "总体需求理解",
    "plan": "总体旅游规划",
    "transport": "交通建议及预定",
    "hotel": "住宿区域建议及预定",
    "dining": "餐饮建议及预定",
    "final": "完整旅行方案汇总",
}

STAGE_GOALS = {
    "need": """
你只负责“总体需求理解”。
目标：
- 理解用户要去哪里、从哪里出发、几个人、几天、预算、偏好、日期。
- 信息缺失时，调用 ask_user 询问用户补充。
- 不要写完整行程、交通、住宿、餐饮方案。
- 完成后输出本阶段结果，并请用户确认是否进入下一阶段。
""",
    "plan": """
你只负责“总体旅游规划”。
目标：
- 基于已有需求，调用目的地信息工具。
- 必要时查询模拟天气。
- 规划总体游玩节奏、景点组合、每日大致路线。
- 不要处理机票/酒店/餐厅预订。
- 完成后输出本阶段结果，并请用户确认是否进入下一阶段。
""",
    "transport": """
你只负责“交通建议及预定”。
目标：
- 自主判断从出发地到目的地的合理交通路径。
- 对京都这类目的地，可考虑杭州→大阪关西→京都。
- 调用机票模拟工具查询去程和返程。
- 如果航班时间不合理，要主动重规划。
- 如果工具失败，可以重试；连续失败或需要选择时调用 ask_user。
- 完成后输出本阶段结果，并请用户确认是否进入下一阶段。
""",
    "hotel": """
你只负责“住宿区域建议及预定”。
目标：
- 根据行程、预算和交通便利性推荐住宿区域。
- 调用酒店模拟工具。
- 如果失败，可以重试、换区域或调用 ask_user。
- 不要真实承诺已经预订，只能说明是模拟结果。
- 完成后输出本阶段结果，并请用户确认是否进入下一阶段。
""",
    "dining": """
你只负责“餐饮建议及预定”。
目标：
- 根据目的地特色、用户偏好和行程安排推荐餐饮。
- 调用餐厅模拟工具。
- 如果失败，可以重试、换类型或调用 ask_user。
- 不要真实承诺已经预订，只能说明是模拟结果。
- 完成后输出本阶段结果，并请用户确认是否进入最终汇总。
""",
    "final": """
你负责最终汇总。
目标：
- 汇总前面五个阶段的结果。
- 输出完整旅行方案。
- 最终方案必须只包含以下五个一级标题：
  1. 总体需求理解
  2. 总体旅游规划
  3. 交通建议及预定
  4. 住宿区域建议及预定
  5. 餐饮建议及预定
- 不要再调用工具，除非发现关键信息缺失必须问用户。
""",
}


# =========================================================
# 5. 模型与 Agent
# =========================================================

def build_model() -> ChatOpenRouter:
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("sk-or-v1-xxxx"):
        raise ValueError("请先在代码顶部填写 OPENROUTER_API_KEY。")

    return ChatOpenRouter(
        api_key=OPENROUTER_API_KEY,
        model=MODEL_NAME,
        temperature=0.7,
        max_tokens=4096,
    )


def build_stage_agent(stage: Stage):
    model = build_model()

    tools = [
        get_destination_info,
        simulate_weather,
        simulate_flight_booking,
        simulate_hotel_booking,
        simulate_restaurant_booking,
        ask_user,
    ]

    system_prompt = f"""
你是一个旅行规划 Agent。你需要像真实 Agent 一样：先说明当前思考，再根据情况调用工具，再根据工具结果继续规划。

当前阶段：{STAGE_TITLES[stage]}

阶段要求：
{STAGE_GOALS[stage]}

全局规则：
1. 你必须只完成当前阶段，不要一口气完成全部五个阶段。
2. 你可以根据情况自主调用工具。
3. 每次调用工具前，先用自然语言说明你为什么要调用这个工具。
4. 工具失败时，不要假装成功；可以重试、调整方案，必要时调用 ask_user。
5. 信息缺失时，不要用硬编码关键词判断，而是基于用户自然语言理解；必要时调用 ask_user。
6. 你可以和用户沟通，用户反馈会作为 ask_user 工具结果返回，你需要继续理解并执行。
7. 阶段结束时，请明确给出“本阶段结果”，并询问用户是否确认进入下一阶段。
8. 所有机票、酒店、餐厅、天气都是本地模拟结果，不是真实 API 结果。
9. 始终使用中文。
"""

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )


# =========================================================
# 6. 输出中间过程：只显示 model 文案，隐藏 tools
# =========================================================

def extract_text_from_message(msg: Any) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content)


def print_agent_chunk(chunk: Any) -> str:
    """
    只打印 model 节点的自然语言内容。
    不打印工具调用参数，不打印 tools 节点返回值。
    """
    collected_text = ""

    if not isinstance(chunk, dict):
        return collected_text

    for node_name, node_data in chunk.items():
        if node_name == "tools":
            continue

        if not isinstance(node_data, dict):
            continue

        messages = node_data.get("messages", [])

        for msg in messages:
            msg_type = getattr(msg, "type", "")

            if msg_type == "ai":
                content = extract_text_from_message(msg)
                if content.strip():
                    print("\n--- 当前节点：model ---")
                    print(content)
                    collected_text += content + "\n"

    return collected_text


# =========================================================
# 7. 阶段节点
# =========================================================

def make_stage_node(stage: Stage):
    def stage_node(state: TravelState) -> TravelState:
        print("\n" + "=" * 90)
        print(f"进入阶段：{STAGE_TITLES[stage]}")
        print("=" * 90)

        stage_agent = build_stage_agent(stage)
        stage_context = build_stage_context(state, stage)

        messages = state.get("messages", []) + [
            {"role": "user", "content": stage_context}
        ]

        stage_text = ""

        for chunk in stage_agent.stream(
            {"messages": messages},
            stream_mode="updates",
        ):
            stage_text += print_agent_chunk(chunk)

        stage_text = stage_text.strip()

        stage_results = {
            **state.get("stage_results", {}),
            STAGE_TITLES[stage]: stage_text,
        }

        return {
            **state,
            "messages": messages + [{"role": "assistant", "content": stage_text}],
            "stage_results": stage_results,
            "last_stage_output": stage_text,
            "current_stage": stage,
            "user_confirmed": False,
        }

    return stage_node


def build_stage_context(state: TravelState, stage: Stage) -> str:
    stage_results = state.get("stage_results", {})

    previous = "\n\n".join(
        [f"【{k}】\n{v}" for k, v in stage_results.items()]
    )

    if stage == "need":
        return """
现在开始第1阶段：总体需求理解。

用户原始需求在上文消息中。
你需要理解用户需求，必要时调用 ask_user 补充缺失信息。
完成后只输出“总体需求理解”，不要输出完整旅行方案。
"""

    if stage == "final":
        return f"""
现在开始最终汇总。

以下是前面阶段结果：
{previous}

请整理成完整旅行方案。
必须只包含五个一级标题：
1. 总体需求理解
2. 总体旅游规划
3. 交通建议及预定
4. 住宿区域建议及预定
5. 餐饮建议及预定
"""

    return f"""
现在开始阶段：{STAGE_TITLES[stage]}。

以下是此前阶段已经确认/生成的结果：
{previous}

请基于这些结果继续当前阶段。
只完成当前阶段，不要输出完整旅行方案。
阶段完成后请询问用户是否确认进入下一阶段。
"""


# =========================================================
# 8. 阶段间自然语言意图判断
# =========================================================

def classify_pause_intent(user_input: str, current_stage_title: str) -> str:
    """
    用 LLM 判断阶段完成后的用户输入意图：
    continue / revise / rerun / exit
    """
    model = build_model()

    prompt = f"""
你需要判断用户在一个旅行规划阶段完成后的回复意图。

当前阶段：{current_stage_title}

用户回复：
{user_input}

请只输出以下四个标签之一，不要输出其他内容：

continue：用户表示认可、满意、可以继续、进入下一阶段，或只是自然表达“可以”“挺好”“没问题”“就这样”“下一步”等。
revise：用户提出修改意见、补充信息、偏好调整、质疑当前方案，要求根据新信息调整当前阶段。
rerun：用户明确要求重新生成、重试、再跑一次，且没有给出具体修改方向。
exit：用户明确表示退出、结束、不做了。

判断规则：
- “可以，继续” => continue
- “看起来不错” => continue
- “挺好的，下一步吧” => continue
- “这个可以，不过酒店想便宜一点” => revise
- “我想改成3天” => revise
- “出发地改成上海” => revise
- “重新生成” => rerun
- “再跑一次” => rerun
- “退出” => exit
"""

    result = model.invoke(prompt).content.strip().lower()

    if "continue" in result:
        return "continue"
    if "rerun" in result:
        return "rerun"
    if "exit" in result:
        return "exit"
    return "revise"


# =========================================================
# 9. LangGraph 路由与暂停节点
# =========================================================

def next_stage(stage: Stage) -> Stage:
    idx = STAGES.index(stage)
    if idx + 1 >= len(STAGES):
        return "done"
    return STAGES[idx + 1]  # type: ignore


def route_after_stage(state: TravelState) -> str:
    stage = state.get("current_stage", "need")
    if stage == "final":
        return "done"
    return "pause"


def pause_node(state: TravelState) -> TravelState:
    current = state["current_stage"]

    print("\n" + "-" * 90)
    print(f"阶段《{STAGE_TITLES[current]}》已完成。")
    print("你可以自然回复确认进入下一阶段，提出修改意见，要求重试，或直接退出。")


    user_input = input("你：").strip()

    intent = classify_pause_intent(user_input, STAGE_TITLES[current])

    interaction_log = state.get("interaction_log", []) + [
        {
            "stage": STAGE_TITLES[current],
            "user_input": user_input,
            "classified_intent": intent,
        }
    ]

    if intent == "exit":
        return {
            **state,
            "current_stage": "done",
            "user_confirmed": False,
            "interaction_log": interaction_log,
            "messages": state.get("messages", []) + [
                {"role": "user", "content": "用户选择退出。"}
            ],
        }

    if intent == "continue":
        return {
            **state,
            "current_stage": next_stage(current),
            "user_confirmed": True,
            "interaction_log": interaction_log,
            "messages": state.get("messages", []) + [
                {
                    "role": "user",
                    "content": f"我确认阶段《{STAGE_TITLES[current]}》，请继续下一阶段。用户原话：{user_input}",
                }
            ],
        }

    if intent == "rerun":
        return {
            **state,
            "current_stage": current,
            "user_confirmed": False,
            "interaction_log": interaction_log,
            "messages": state.get("messages", []) + [
                {
                    "role": "user",
                    "content": f"请重新执行阶段《{STAGE_TITLES[current]}》，不要沿用上一版输出。用户原话：{user_input}",
                }
            ],
        }

    return {
        **state,
        "current_stage": current,
        "user_confirmed": False,
        "interaction_log": interaction_log,
        "messages": state.get("messages", []) + [
            {
                "role": "user",
                "content": f"我对阶段《{STAGE_TITLES[current]}》有以下修改意见或补充信息：{user_input}。请你理解后重新执行或调整该阶段。",
            }
        ],
    }


def route_after_pause(state: TravelState) -> str:
    stage = state.get("current_stage", "need")
    if stage == "done":
        return "done"
    return stage


def done_node(state: TravelState) -> TravelState:
    print("\n" + "=" * 90)
    print("流程结束。")
    print("=" * 90)

    log = state.get("interaction_log", [])
    if log:
        print("\n本次阶段交互记录：")
        for item in log:
            print(f"- 阶段：{item['stage']} | 用户输入：{item['user_input']} | 判断：{item['classified_intent']}")

    return state


def build_graph():
    graph = StateGraph(TravelState)

    for stage in STAGES:
        graph.add_node(stage, make_stage_node(stage))  # type: ignore

    graph.add_node("pause", pause_node)
    graph.add_node("done", done_node)

    graph.add_edge(START, "need")

    for stage in STAGES:
        graph.add_conditional_edges(
            stage,
            route_after_stage,
            {
                "pause": "pause",
                "done": "done",
            },
        )

    graph.add_conditional_edges(
        "pause",
        route_after_pause,
        {
            "need": "need",
            "plan": "plan",
            "transport": "transport",
            "hotel": "hotel",
            "dining": "dining",
            "final": "final",
            "done": "done",
        },
    )

    graph.add_edge("done", END)

    return graph.compile()


# =========================================================
# 10. 主程序
# =========================================================

def main():
    print("旅行规划 LangGraph Agent 已启动。")
    print("特点：五阶段执行 + 阶段内 Agent 自主工具调用 + 只显示 model 过程 + 阶段间自然语言意图判断")
    print("示例：我想从杭州去日本京都玩2天，2个人，预算10000元，5月25日出发。")
    print("-" * 90)

    user_request = input("请输入旅行需求：\n你：").strip()

    app = build_graph()

    initial_state: TravelState = {
        "messages": [{"role": "user", "content": user_request}],
        "current_stage": "need",
        "stage_results": {},
        "last_stage_output": "",
        "user_confirmed": False,
        "interaction_log": [],
    }

    app.invoke(initial_state)


if __name__ == "__main__":
    main()