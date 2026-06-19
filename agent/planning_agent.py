import json
import random
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict

from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from agent.llm_agent import _build_chat_model
from app.config import RUNTIME_CONFIG


Stage = Literal["need", "plan", "transport", "hotel", "dining", "final", "done"]


class PlanningGraphState(TypedDict, total=False):
    messages: List[Dict[str, str]]
    current_stage: Stage
    pending_next_stage: Stage
    stage_results: Dict[str, str]
    last_stage_output: str
    intermediate_outputs: List[str]
    user_confirmed: bool
    interaction_log: List[Dict[str, str]]
    done: bool


STAGES: List[Stage] = ["need", "plan", "transport", "hotel", "dining", "final"]

STAGE_TITLES = {
    "need": "总体需求理解",
    "plan": "总体旅游规划",
    "transport": "交通建议及预订",
    "hotel": "住宿区域建议及预订",
    "dining": "餐饮建议及预订",
    "final": "完整旅行方案汇总",
    "done": "流程结束",
}

STAGE_GOALS = {
    "need": """
你只负责“总体需求理解”。
目标：
- 理解用户要去哪里、从哪里出发、几个人、几天、预算、偏好、日期。
- 信息缺失时，调用 ask_user 工具提出需要用户补充的问题。
- 不要写完整行程、交通、住宿、餐饮方案。
- 完成后输出“本阶段结果”，并询问用户是否确认进入下一阶段。
""",
    "plan": """
你只负责“总体旅游规划”。
目标：
- 基于已确认需求，调用 get_destination_info 查询目的地信息。
- 必要时调用 query_weather 查询天气。
- 规划总体游玩节奏、景点组合、每日大致路线。
- 不要处理机票、酒店、餐厅预订。
- 完成后输出“本阶段结果”，并询问用户是否确认进入下一阶段。
""",
    "transport": """
你只负责“交通建议及预订”。
目标：
- 判断从出发地到目的地的合理交通路径。
- 对大阪/京都这类日本关西目的地，可优先考虑关西国际机场再衔接市内交通；对三亚这类海岛目的地，可优先考虑直飞三亚凤凰国际机场。
- 调用 query_flight_booking 查询去程和返程航班。
- 如果航班时间不合理，要主动调整建议。
- 如果工具失败，可以重试、调整方案，必要时调用 ask_user。
- 完成后输出“本阶段结果”，并询问用户是否确认进入下一阶段。
""",
    "hotel": """
你只负责“住宿区域建议及预订”。
目标：
- 根据行程、预算和交通便利性推荐住宿区域。
- 调用 query_hotel_booking 查询酒店。
- 如果工具失败，可以重试、换区域或调用 ask_user。
- 不要承诺已经产生外部平台订单。
- 完成后输出“本阶段结果”，并询问用户是否确认进入下一阶段。
""",
    "dining": """
你只负责“餐饮建议及预订”。
目标：
- 根据目的地特色、用户偏好和行程安排推荐餐饮。
- 调用 query_restaurant_booking 查询餐厅。
- 如果工具失败，可以重试、换类型或调用 ask_user。
- 不要承诺已经产生外部平台订单。
- 完成后输出“本阶段结果”，并询问用户是否确认进入最终汇总。
""",
    "final": """
你负责最终汇总。
目标：
- 汇总前面五个阶段的结果。
- 输出完整旅行方案。
- 最终方案必须只包含以下五个一级标题：
  1. 总体需求理解
  2. 总体旅游规划
  3. 交通建议及预订
  4. 住宿区域建议及预订
  5. 餐饮建议及预订
- 不要再调用工具，除非发现关键信息缺失必须问用户。
""",
}

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
    "三亚": {
        "country": "中国",
        "gateway_city": "三亚",
        "gateway_airport": "三亚凤凰国际机场",
        "attractions": ["亚龙湾", "蜈支洲岛", "天涯海角", "南山文化旅游区", "鹿回头", "第一市场"],
        "foods": ["海南椰子鸡", "清补凉", "文昌鸡", "海鲜火锅", "抱罗粉"],
        "hotel_areas": ["亚龙湾", "海棠湾", "三亚湾", "大东海"],
        "local_transport": ["打车", "公交", "景区巴士", "租车自驾"],
    },
    "大阪": {
        "country": "日本",
        "gateway_city": "大阪",
        "gateway_airport": "关西国际机场/大阪伊丹机场",
        "attractions": ["大阪城公园", "道顿堀", "心斋桥", "环球影城日本", "梅田蓝天大厦", "黑门市场"],
        "foods": ["章鱼烧", "大阪烧", "串炸", "拉面", "寿司"],
        "hotel_areas": ["难波", "心斋桥", "梅田", "天王寺"],
        "local_transport": ["地铁", "JR", "私铁", "步行", "出租车"],
    },
}

DESTINATION_WEATHER_PROFILES = {
    "京都": {
        "weather": ["晴", "多云", "小雨", "阴"],
        "temperature": (10, 28),
        "suggestions": ["适合寺社与街区步行", "建议携带折叠伞", "早晚温差较明显", "热门景点建议错峰"],
    },
    "北京": {
        "weather": ["晴", "多云", "阴", "小雨"],
        "temperature": (8, 32),
        "suggestions": ["注意防晒和补水", "长城行程建议预留体力", "博物馆建议提前预约", "适合地铁串联景点"],
    },
    "杭州": {
        "weather": ["晴", "多云", "小雨", "阵雨"],
        "temperature": (12, 30),
        "suggestions": ["西湖周边适合步行或骑行", "雨天可增加博物馆和茶馆安排", "建议携带雨具", "避开湖滨高峰时段"],
    },
    "三亚": {
        "weather": ["晴", "多云", "阵雨", "雷阵雨"],
        "temperature": (24, 34),
        "suggestions": ["注意防晒和补水", "海岛项目需关注风浪", "建议准备泳衣和防水袋", "午后可安排室内或酒店休整"],
    },
    "大阪": {
        "weather": ["晴", "多云", "小雨", "阴"],
        "temperature": (9, 29),
        "suggestions": ["适合地铁串联商圈与景点", "环球影城建议提前规划入园时间", "雨天可安排购物和室内展馆", "热门餐厅建议错峰"],
    },
}

DESTINATION_FLIGHT_OPTIONS = {
    "京都": {
        "airlines": ["日本航空", "全日空", "东方航空", "中国国航"],
        "arrival_times": ["11:50", "14:20", "18:35", "21:10"],
        "price_range": (1200, 3600),
    },
    "大阪": {
        "airlines": ["日本航空", "全日空", "东方航空", "中国国航", "春秋航空"],
        "arrival_times": ["11:40", "14:10", "18:20", "21:05"],
        "price_range": (1100, 3400),
    },
    "三亚": {
        "airlines": ["海南航空", "南方航空", "东方航空", "中国国航"],
        "arrival_times": ["10:55", "13:45", "17:20", "22:15"],
        "price_range": (700, 2600),
    },
}

DESTINATION_HOTEL_NAMES = {
    "京都": ["町家精品旅宿", "京都站前精选酒店", "鸭川河畔旅馆", "四条雅居酒店"],
    "北京": ["王府井精选酒店", "前门庭院酒店", "国贸商务酒店", "鼓楼文化客栈"],
    "杭州": ["湖畔假日酒店", "西湖雅居酒店", "钱江新城精选酒店", "武林城市酒店"],
    "三亚": ["亚龙湾海景度假酒店", "海棠湾亲海酒店", "三亚湾假日酒店", "大东海精品酒店"],
    "大阪": ["难波城市酒店", "心斋桥精品酒店", "梅田交通枢纽酒店", "天王寺舒适酒店"],
}

DESTINATION_RESTAURANT_NAMES = {
    "京都": ["祇园和味料理", "鸭川汤豆腐馆", "岚山茶寮", "京都町家食堂"],
    "北京": ["前门烤鸭店", "鼓楼涮肉馆", "老北京炸酱面馆", "胡同家常菜"],
    "杭州": ["湖滨杭帮菜馆", "龙井茶香餐厅", "河坊街小馆", "西溪风味馆"],
    "三亚": ["第一市场海鲜店", "椰林清补凉铺", "亚龙湾海鲜餐厅", "海南家常菜馆"],
    "大阪": ["道顿堀章鱼烧铺", "难波大阪烧店", "新世界串炸屋", "黑门市场食堂"],
}

FLIGHT_FAIL_RATE = 0.25
HOTEL_FAIL_RATE = 0.25
RESTAURANT_FAIL_RATE = 0.30
WEATHER_FAIL_RATE = 0.10


def initial_state() -> Dict[str, Any]:
    return {
        "messages": [],
        "current_stage": "need",
        "pending_next_stage": "",
        "stage_results": {},
        "last_stage_output": "",
        "intermediate_outputs": [],
        "user_confirmed": False,
        "awaiting_user_info": False,
        "interaction_log": [],
        "done": False,
    }


def maybe_fail(action: str, fail_rate: float) -> Optional[str]:
    if random.random() < fail_rate:
        return f"{action}失败：供应商接口暂时不可用、库存不足或网络波动。"
    return None


@tool
def get_destination_info(destination: str) -> str:
    """
    查询目的地基础旅行信息，包括国家、入口城市、景点、美食、住宿区域和本地交通。
    本工具返回当前系统可用的目的地资料。
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
            "note": "当前系统目的地资料。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def query_weather(destination: str, date: str) -> str:
    """
    查询天气信息。可能失败。
    """
    failure = maybe_fail("天气查询", WEATHER_FAIL_RATE)
    if failure:
        return json.dumps(
            {
                "status": "failed",
                "message": failure,
                "suggestion": "可以稍后重试，或按季节常识准备雨具、防晒与轻便外套。",
            },
            ensure_ascii=False,
            indent=2,
        )

    return json.dumps(
        {
            "status": "success",
            "destination": destination,
            "date": date,
            "weather": random.choice(DESTINATION_WEATHER_PROFILES.get(destination, {}).get("weather", ["晴", "多云", "阴", "小雨"])),
            "temperature": f"{random.randint(*DESTINATION_WEATHER_PROFILES.get(destination, {}).get('temperature', (12, 30)))}℃",
            "suggestion": random.choice(DESTINATION_WEATHER_PROFILES.get(destination, {}).get("suggestions", ["适合步行游览", "建议携带雨具", "注意防晒", "适合室内外结合安排"])),
            "note": "当前系统天气查询结果。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def query_flight_booking(
    origin: str,
    destination: str,
    date: str,
    people: int = 1,
    cabin: str = "经济舱",
) -> str:
    """
    查询机票信息。可能失败。注意：不要承诺已经产生外部平台订单。
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
                "suggestion": "可以重试、换日期、换机场，或先保留交通建议。",
            },
            ensure_ascii=False,
            indent=2,
        )

    flight_options = DESTINATION_FLIGHT_OPTIONS.get(destination, {})
    price_low, price_high = flight_options.get("price_range", (600, 2200))
    price_per_person = random.randint(price_low, price_high)
    return json.dumps(
        {
            "status": "success",
            "type": "flight",
            "origin": origin,
            "destination": destination,
            "date": date,
            "people": people,
            "cabin": cabin,
            "airline": random.choice(flight_options.get("airlines", ["东方航空", "中国国航", "南方航空", "春秋航空"])),
            "departure_time": random.choice(["08:30", "11:20", "14:45", "19:10"]),
            "arrival_time": random.choice(flight_options.get("arrival_times", ["10:50", "13:40", "17:15", "21:30"])),
            "price_per_person": price_per_person,
            "total_price": price_per_person * people,
            "note": "当前系统机票查询结果。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def query_hotel_booking(
    destination: str,
    checkin_date: str,
    nights: int,
    people: int = 1,
    hotel_level: str = "中档",
    area_preference: str = "交通便利",
) -> str:
    """
    查询酒店信息。可能失败。注意：不要承诺已经产生外部平台订单。
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
            "hotel_name": random.choice(DESTINATION_HOTEL_NAMES.get(destination, ["城市精选酒店", "湖畔假日酒店", "中心精品酒店", "旅行者之家"])),
            "area": random.choice(areas),
            "price_per_night": price_per_night,
            "total_price": price_per_night * nights,
            "note": "当前系统酒店查询结果。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def query_restaurant_booking(
    destination: str,
    date: str,
    people: int = 1,
    food_preference: str = "当地特色",
    meal_time: str = "晚餐",
) -> str:
    """
    查询餐厅信息。可能失败。注意：不要承诺已经产生外部平台订单。
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
            "restaurant_name": random.choice(DESTINATION_RESTAURANT_NAMES.get(destination, ["本地风味馆", "老街小馆", "城市食堂", "隐味料理"])),
            "recommended_food": random.choice(foods),
            "food_preference": food_preference,
            "meal_time": meal_time,
            "time": random.choice(["12:00", "12:30", "18:00", "18:30", "19:00", "19:30"]),
            "note": "当前系统餐厅查询结果。",
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def ask_user(question: str) -> str:
    """
    当信息缺失、工具连续失败、出现重要选择，或阶段完成需要用户确认时，向用户提问。
    Web 页面中本工具不会阻塞等待输入，只会返回需要用户补充的问题。
    """
    return json.dumps(
        {
            "status": "need_user_input",
            "question": question,
            "instruction": "请在本阶段结果中明确展示这个问题，并等待用户下一轮输入。",
        },
        ensure_ascii=False,
        indent=2,
    )


def build_model():
    return _build_chat_model(
        temperature=float(RUNTIME_CONFIG["temperature"]),
        max_tokens=max(4096, int(RUNTIME_CONFIG["max_tokens"])),
    )


def build_stage_agent(stage: Stage):
    tools = [
        get_destination_info,
        query_weather,
        query_flight_booking,
        query_hotel_booking,
        query_restaurant_booking,
        ask_user,
    ]

    system_prompt = f"""
你是一个旅行规划 Agent。你需要先用自然语言说明当前处理步骤，再根据情况调用工具，再根据工具结果继续规划。

当前阶段：{STAGE_TITLES[stage]}

阶段要求：
{STAGE_GOALS[stage]}

全局规则：
1. 你必须只完成当前阶段，不要一口气完成全部五个阶段。
2. 你可以根据情况自主调用工具。
3. 每次调用工具前，先用自然语言说明你为什么要调用这个工具。
4. 工具失败时，不要假装成功；可以重试、调整方案，必要时调用 ask_user。
5. 信息缺失时，不要硬编码猜测；必要时调用 ask_user。
6. ask_user 不会在工具内部等待用户输入；你必须把问题写到阶段结果里，等待用户下一轮回复。
7. 阶段结束时，请明确给出“本阶段结果”，并询问用户是否确认进入下一阶段。
8. 机票、酒店、餐厅、天气查询结果来自当前系统数据；不要向用户承诺已经产生外部平台订单。
9. 始终使用简体中文。
10. 不要输出隐藏推理或内部链式思考，只输出可以给用户查看的处理过程、工具使用说明和阶段结果。
11. 不要在每个阶段开头完整复述目的地、日期、人数、预算、偏好等基础信息；除非这些信息刚被用户修改，否则只引用当前阶段必须用到的关键信息。
12. 中间过程要短，每次工具调用前后的说明控制在 1-2 句话内；把详细内容集中放到“本阶段结果”中。
"""

    return create_agent(
        model=build_model(),
        tools=tools,
        system_prompt=system_prompt,
    )


def extract_text_from_message(msg: Any) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content)


def summarize_tool_result(msg: Any) -> str:
    tool_name = str(getattr(msg, "name", "") or "").strip()
    content = extract_text_from_message(msg).strip()
    if not content:
        return ""

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return f"工具返回结果：{content}"

    status = str(payload.get("status") or "").strip()
    if status == "failed":
        message = str(payload.get("message") or "查询失败。").strip()
        suggestion = str(payload.get("suggestion") or "").strip()
        if suggestion:
            return f"查询失败：{message}\n调整方向：{suggestion}"
        return f"查询失败：{message}"

    if status == "need_user_input":
        question = str(payload.get("question") or "").strip()
        return f"需要用户补充信息：{question}" if question else "需要用户补充信息。"

    if status != "success":
        return ""

    result_type = str(payload.get("type") or "").strip()
    if tool_name == "get_destination_info":
        destination = str(payload.get("destination") or "").strip()
        data = payload.get("data") or {}
        attractions = "、".join(list(data.get("attractions") or [])[:4])
        foods = "、".join(list(data.get("foods") or [])[:3])
        return f"已获取{destination or '目的地'}资料：可参考景点包括{attractions or '若干景点'}；特色餐饮包括{foods or '当地餐饮'}。"

    if tool_name == "query_weather":
        weather = str(payload.get("weather") or "").strip()
        temperature = str(payload.get("temperature") or "").strip()
        suggestion = str(payload.get("suggestion") or "").strip()
        return f"已获取天气信息：{weather}，{temperature}。{suggestion}"

    if result_type == "flight":
        airline = str(payload.get("airline") or "").strip()
        departure = str(payload.get("departure_time") or "").strip()
        arrival = str(payload.get("arrival_time") or "").strip()
        total_price = str(payload.get("total_price") or "").strip()
        return f"已获取航班信息：{airline}，{departure}-{arrival}，总价约 {total_price} 元。"

    if result_type == "hotel":
        hotel_name = str(payload.get("hotel_name") or "").strip()
        area = str(payload.get("area") or "").strip()
        total_price = str(payload.get("total_price") or "").strip()
        return f"已获取酒店信息：{hotel_name}，位置在{area}，总价约 {total_price} 元。"

    if result_type == "restaurant":
        restaurant_name = str(payload.get("restaurant_name") or "").strip()
        food = str(payload.get("recommended_food") or "").strip()
        time = str(payload.get("time") or "").strip()
        return f"已获取餐厅信息：{restaurant_name}，推荐{food}，可选时间 {time}。"

    return "工具查询完成，已获得可用于本阶段规划的信息。"


def collect_agent_chunk(chunk: Any, seen_message_keys: set) -> str:
    collected_text = ""
    if not isinstance(chunk, dict):
        return collected_text

    for node_name, node_data in chunk.items():
        if not isinstance(node_data, dict):
            continue

        for msg in node_data.get("messages", []) or []:
            msg_type = getattr(msg, "type", "")
            if msg_type == "ai":
                content = extract_text_from_message(msg).strip()
            elif msg_type == "tool":
                content = summarize_tool_result(msg).strip()
            else:
                continue
            if not content:
                continue

            msg_id = getattr(msg, "id", None)
            key = msg_id or f"{msg_type}:{content}"
            if key in seen_message_keys:
                continue
            seen_message_keys.add(key)
            collected_text += content + "\n\n"

    return collected_text


def build_stage_context(state: Dict[str, Any], stage: Stage, user_input: str) -> str:
    stage_results = state.get("stage_results", {}) or {}
    previous = "\n\n".join([f"【{key}】\n{value}" for key, value in stage_results.items()])
    messages = state.get("messages", []) or []
    original_need = messages[0]["content"] if messages else user_input

    if stage == "need":
        return f"""
现在开始第 1 阶段：总体需求理解。

用户原始需求：
{original_need}

用户本轮输入：
{user_input}

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
3. 交通建议及预订
4. 住宿区域建议及预订
5. 餐饮建议及预订
"""

    return f"""
现在开始阶段：{STAGE_TITLES[stage]}。

用户原始需求：
{original_need}

用户本轮输入：
{user_input}

以下是此前阶段已经确认或生成的结果：
{previous or "暂无。"}

请基于这些结果继续当前阶段。
只完成当前阶段，不要输出完整旅行方案。
不要完整复述此前阶段的基础信息，只在必要处简短引用。
阶段完成后请询问用户是否确认进入下一阶段。
"""


def build_completed_stage_state(
    state: Dict[str, Any],
    stage: Stage,
    user_input: str,
    stage_text_parts: List[str],
) -> Dict[str, Any]:
    stage_text = "\n\n".join(part.strip() for part in stage_text_parts if part.strip()).strip()
    if not stage_text:
        stage_text = "本阶段没有生成可展示内容。"

    awaiting_user_info = any("需要用户补充信息" in part for part in stage_text_parts)
    stage_results = dict(state.get("stage_results", {}) or {})
    if not awaiting_user_info:
        stage_results[STAGE_TITLES[stage]] = stage_text
    visible_messages = state.get("messages", []) + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": stage_text},
    ]

    return {
        **state,
        "messages": visible_messages,
        "stage_results": stage_results,
        "last_stage_output": stage_text,
        "intermediate_outputs": stage_text_parts,
        "current_stage": stage,
        "user_confirmed": False,
        "awaiting_user_info": awaiting_user_info,
        "done": stage == "final" and not awaiting_user_info,
    }


def iter_stage_text_parts(state: Dict[str, Any], stage: Stage, user_input: str):
    stage_agent = build_stage_agent(stage)
    stage_context = build_stage_context(state, stage, user_input)
    messages = state.get("messages", []) + [{"role": "user", "content": stage_context}]
    seen_message_keys: set = set()

    for chunk in stage_agent.stream({"messages": messages}, stream_mode="updates"):
        text = collect_agent_chunk(chunk, seen_message_keys)
        if text.strip():
            yield text.strip()


def stream_stage(state: Dict[str, Any], user_input: str):
    state = dict(state or initial_state())
    stage: Stage = state.get("current_stage", "need")
    clean_user_input = str(user_input or "").strip()
    if stage == "done" or state.get("done"):
        yield {
            "type": "final",
            "state": state,
            "output": "规划流程已经结束。",
            "intermediate_outputs": [],
        }
        return

    stage_text_parts: List[str] = []
    for text in iter_stage_text_parts(state, stage, clean_user_input):
        stage_text_parts.append(text)
        yield {
            "type": "partial",
            "state": state,
            "output": "\n\n".join(stage_text_parts),
            "intermediate_outputs": list(stage_text_parts),
        }

    next_state = build_completed_stage_state(state, stage, clean_user_input, stage_text_parts)
    yield {
        "type": "final",
        "state": next_state,
        "output": str(next_state.get("last_stage_output") or ""),
        "intermediate_outputs": list(stage_text_parts),
    }


def make_stage_node(stage: Stage):
    def stage_node(state: PlanningGraphState) -> PlanningGraphState:
        stage_text_parts = list(iter_stage_text_parts(state, stage, state.get("latest_user_input", "")))
        return build_completed_stage_state(state, stage, state.get("latest_user_input", ""), stage_text_parts)

    return stage_node


def build_one_stage_graph(stage: Stage):
    graph = StateGraph(PlanningGraphState)
    graph.add_node(stage, make_stage_node(stage))  # type: ignore[arg-type]
    graph.add_edge(START, stage)
    graph.add_edge(stage, END)
    return graph.compile()


def run_stage(state: Dict[str, Any], user_input: str) -> Tuple[Dict[str, Any], str]:
    final_event = None
    for event in stream_stage(state, user_input):
        final_event = event

    if not final_event:
        state = dict(state or initial_state())
        return state, ""

    next_state = dict(final_event.get("state") or state or initial_state())
    return next_state, str(final_event.get("output") or "").strip()


def build_intent_model_prompt(user_input: str, current_stage_title: str) -> str:
    return f"""
你需要判断用户在一个旅行规划阶段完成后的回复意图。

当前阶段：{current_stage_title}

用户回复：
{user_input}

请只输出以下四个标签之一，不要输出其他内容：

continue：用户明确表示当前阶段已经确认，并希望进入下一阶段。
revise：用户提出修改意见、补充信息、偏好调整、质疑当前方案，要求根据新信息调整当前阶段。
rerun：用户明确要求重新生成、重试、再跑一次，且没有给出具体修改方向。
exit：用户明确表示退出、结束、不做了。

额外判定规则：
1. 只有用户明确表达“当前阶段可以结束/确认，并进入下一阶段”时，才输出 continue。
2. 如果用户只是说“好的”“可以”“没问题”，但同时提出问题、追问细节、补充条件、表达疑问、要求继续解释或调整偏好，必须输出 revise。
3. 如果用户仍在和 Agent 讨论当前阶段，不要输出 continue。
4. 宁可保守输出 revise，也不要过早输出 continue。
"""


def classify_pause_intent(user_input: str, current_stage_title: str = "") -> str:
    text = str(user_input or "").strip()
    lowered = text.lower()
    if any(keyword in lowered for keyword in ["exit", "stop"]) or any(keyword in text for keyword in ["退出", "结束", "不做了", "停止"]):
        return "exit"
    if any(keyword in text for keyword in ["重来", "重新", "重跑", "再跑一次"]):
        return "rerun"
    explicit_continue_phrases = [
        "确认进入下一阶段",
        "进入下一阶段",
        "继续下一阶段",
        "可以进入下一阶段",
        "进入下一步",
        "继续下一步",
        "这个阶段可以了",
        "本阶段可以了",
        "这一阶段可以了",
        "当前阶段可以了",
        "确认这个阶段",
        "确认本阶段",
        "确认当前阶段",
    ]
    explicit_continue_lower = [
        "continue to next stage",
        "next stage",
        "go next",
        "proceed",
    ]
    if any(phrase in text for phrase in explicit_continue_phrases) or any(phrase in lowered for phrase in explicit_continue_lower):
        return "continue"

    try:
        model = build_model()
        result = model.invoke(build_intent_model_prompt(text, current_stage_title)).content.strip().lower()
        if "continue" in result:
            return "continue"
        if "rerun" in result:
            return "rerun"
        if "exit" in result:
            return "exit"
    except Exception:
        pass
    return "revise"


def next_stage(stage: Stage) -> Stage:
    if stage == "done":
        return "done"
    index = STAGES.index(stage)
    if index + 1 >= len(STAGES):
        return "done"
    return STAGES[index + 1]


def handle_feedback(state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    state = dict(state or initial_state())
    stage: Stage = state.get("current_stage", "need")
    intent = classify_pause_intent(user_input, STAGE_TITLES.get(stage, stage))
    interaction_log = list(state.get("interaction_log", []) or [])
    interaction_log.append(
        {
            "stage": STAGE_TITLES.get(stage, stage),
            "user_input": user_input,
            "classified_intent": intent,
        }
    )

    messages = list(state.get("messages", []) or [])
    if intent == "exit":
        messages.append({"role": "user", "content": "用户选择退出。"})
        return {
            **state,
            "current_stage": "done",
            "pending_next_stage": "",
            "done": True,
            "interaction_log": interaction_log,
            "messages": messages,
        }

    if intent == "continue":
        messages.append(
            {
                "role": "user",
                "content": f"我确认阶段《{STAGE_TITLES.get(stage, stage)}》，请继续下一阶段。用户原话：{user_input}",
            }
        )
        return {
            **state,
            "current_stage": stage,
            "pending_next_stage": next_stage(stage),
            "user_confirmed": True,
            "awaiting_user_info": False,
            "interaction_log": interaction_log,
            "messages": messages,
        }

    if intent == "rerun":
        messages.append(
            {
                "role": "user",
                "content": f"请重新执行阶段《{STAGE_TITLES.get(stage, stage)}》，不要沿用上一版输出。用户原话：{user_input}",
            }
        )
        return {
            **state,
            "current_stage": stage,
            "pending_next_stage": "",
            "user_confirmed": False,
            "awaiting_user_info": False,
            "interaction_log": interaction_log,
            "messages": messages,
        }

    messages.append(
        {
            "role": "user",
            "content": f"我对阶段《{STAGE_TITLES.get(stage, stage)}》有以下修改意见或补充信息：{user_input}。请理解后重新执行或调整该阶段。",
        }
    )
    return {
        **state,
        "current_stage": stage,
        "pending_next_stage": "",
        "user_confirmed": False,
        "awaiting_user_info": False,
        "interaction_log": interaction_log,
        "messages": messages,
    }
