# TrustAgent 实验系统

TrustAgent 是一个基于 FastAPI、Gradio、LangChain / LangGraph 的可信智能体实验平台。系统面向多任务人机交互实验，当前支持账号登录、后台任务配置、聊天任务、问答任务、规划任务，以及实验数据保存与导出。

## 功能概览

### 账号与后台管理

系统采用账号模式登录。管理员可以在后台页面中创建账号、设置密码、查看账号信息，并为账号分配不同类型的实验任务。

主要入口：

```text
/login    用户登录
/profile  用户个人信息页
/admin    后台管理
```

后台当前包含：

- 账号管理
- 用户数据记录查看与导出
- 聊天任务配置
- 问答任务配置
- 规划任务配置

用户登录后进入个人信息页，可以查看和修改姓名、手机号等信息，并根据剩余任务次数进入对应实验。

### 聊天任务

聊天任务用于研究不同 LLM 输出风格配置下的用户交互体验。

当前包含 8 个聊天主题：

- 国际局势与信息焦虑
- AI 与未来工作的变化
- 长期忙碌与休息负罪感
- 社交压力与边界感
- 兴趣坚持与自我怀疑
- 数字生活与注意力分散
- 生活选择与未来规划
- 亲密关系与情感困惑

聊天输出风格由 3 个特征维度组成，每个维度 2 个水平：

- 社会情感表达：理性导向型 / 感性导向型
- 认知透明表达：低透明度 / 高透明度
- 对话立场对齐：用户立场型 / 独立客观型

后台支持两种聊天任务分配方式：

- 批量分配：将 8 个主题与 8 种风格组合随机一对一匹配，为用户生成 8 次聊天任务。
- 单独分配：管理员手动选择 1 个主题和 3 个维度水平，为用户增加 1 次聊天任务。

聊天任务流程：

- 用户进入任务后看到本次聊天主题说明。
- 用户与 LLM 进行 8 轮对话。
- 每 2 轮弹出一次 1-7 分信任评分。
- 最后一轮评分后结束实验并保存记录。
- 保存后自动返回个人信息页。

聊天页面：

```text
/chat
```

### 问答任务

问答任务基于阅读材料和题库进行二选一判断实验。

题目数据来自：

```text
data/data.json
```

当前题库特点：

- 不再按 block 分组。
- 每题为二选一。
- 当前题目数量为 15。
- 部分题目有标准答案。
- 部分题目为模糊决策题，没有唯一标准答案，每个选项都有对应反馈说明。

问答任务配置页面支持管理员为用户分配问答任务，并指定 LLM 初始答案的目标准确率：

- 60%
- 80%

问答任务流程：

- 用户进入页面后先阅读材料。
- 点击“开始实验”后正式开始第一题。
- 系统根据后台配置生成 LLM 的初始答案序列。
- LLM 第一次回答必须按照初始化答案输出。
- 用户选择自己的答案并点击确认。
- 如果题目有标准答案，则公布正确/错误反馈。
- 如果是模糊决策题，则展示所选选项对应的反馈说明。
- 用户进行 1-7 分信任评分。
- 点击“评分并进入下一题”进入下一题。
- 第 15 题评分后结束实验、保存数据并返回个人信息页。

问答页面：

```text
/qa
```

### 规划任务

规划任务是一个阶段式旅行规划 Agent，用于模拟更复杂的多阶段智能体协作过程。

当前规划主题：

```text
旅行
```

规划任务使用 LangChain tool 和 LangGraph 风格的阶段式状态管理。Agent 会围绕旅行需求逐步推进，当前阶段包括：

1. 总体需求理解
2. 总体旅游规划
3. 交通建议及预订
4. 住宿区域建议及预订
5. 餐饮建议及预订
6. 完整旅行方案汇总

规划任务特点：

- 每个阶段只处理当前阶段目标。
- 阶段完成后询问用户是否确认进入下一阶段。
- 用户确认阶段后弹出 1-7 分阶段评分。
- 评分完成后才进入下一阶段。
- 阶段确认采用保守逻辑，避免将普通追问误判为“进入下一阶段”。
- 规划 Agent 使用工具模拟目的地查询、天气查询、机票查询、酒店查询、餐厅查询等过程。
- 中间过程会以特殊样式展示，增强 Agent 推进过程的可见性。
- 最终阶段评分后保存实验数据并返回个人信息页。

规划页面：

```text
/plan
```

## 技术架构

项目主要目录结构：

```text
TrustAgent/
├── agent/
│   ├── llm_agent.py          # LLM 调用封装
│   ├── planning_agent.py     # 规划任务 Agent 和工具逻辑
│   └── plan.py               # 规划任务早期独立测试脚本
├── app/
│   ├── main.py               # FastAPI + Gradio 挂载入口
│   ├── config.py             # 全局配置
│   ├── styles.py             # Gradio 页面样式
│   ├── pages/
│   │   ├── login_page.py     # 登录页
│   │   ├── profile_page.py   # 用户个人信息页
│   │   ├── admin_page.py     # 后台管理页
│   │   ├── chat_page.py      # 聊天任务页
│   │   ├── qa_page.py        # 问答任务页
│   │   └── planning_page.py  # 规划任务页
│   └── services/
│       ├── account_service.py     # 账号、任务配置、任务领取
│       ├── auth_service.py        # 登录认证
│       ├── data_service.py        # 问答题库读取
│       ├── experiment_service.py  # 聊天与问答任务核心逻辑
│       ├── planning_service.py    # 规划页面渲染与状态推进
│       ├── user_data_service.py   # 实验数据保存与导出
│       └── key_service.py         # SQLite 连接与时间工具
├── data/
│   ├── data.json             # 问答任务题库
│   └── data.db               # SQLite 数据库
├── requirements.txt
├── environment.yml
└── README.md
```

### 页面路由

系统启动后挂载以下 Gradio 页面：

| 路由 | 功能 |
|---|---|
| `/` | 自动跳转到 `/login` |
| `/login` | 登录页 |
| `/profile` | 用户个人信息页 |
| `/chat` | 聊天任务页 |
| `/qa` | 问答任务页 |
| `/plan` | 规划任务页 |
| `/admin` | 后台管理页 |
| `/exports/{filename}` | 数据导出下载 |

## LLM 配置

LLM 调用封装在：

```text
agent/llm_agent.py
```

系统会自动读取项目根目录下的 `.env` 文件。

### OpenRouter

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=openrouter/auto
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### DeepSeek

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key
TRUSTAGENT_LLM_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### OpenAI Compatible

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
TRUSTAGENT_LLM_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
```

通用运行参数位于：

```text
app/config.py
```

主要包括：

```python
RUNTIME_CONFIG = {
    "system_prompt": "...",
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "openai/gpt-5.4",
}
```

实际调用模型优先读取 `.env` 中的 provider 和 model 配置。

## 数据存储

系统使用 SQLite 存储账号、任务配置和实验记录。

默认数据库路径：

```text
data/data.db
```

主要数据表包括：

- `experiment_accounts`
- `chat_task_configs`
- `qa_task_configs`
- `experiment_records`

实验记录统一保存到 `experiment_records` 表中，具体任务数据以 JSON 字符串形式保存在 `transcript_json` 字段。

### 聊天任务记录结构

聊天任务保存内容主要包括：

```json
{
  "metadata": {
    "account_id": "1",
    "experiment_key": "password",
    "subject_name": "张三",
    "task_name": "聊天",
    "chat_config_id": "1",
    "chat_topic": "AI 与未来工作的变化",
    "chat_user_instruction": "...",
    "emotional_valence_level": "感性导向型",
    "transparency_level": "高透明度",
    "stance_strategy_level": "独立客观型",
    "trust_scores": [
      {
        "turn_index": 2,
        "rating": "5",
        "rating_timestamp": "..."
      }
    ],
    "started_at": "...",
    "ended_at": "..."
  },
  "runtime_config": {
    "system_prompt": "...",
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "...",
    "provider": "...",
    "base_url": "..."
  },
  "custom_chat_records": []
}
```

### 问答任务记录结构

问答任务保存内容主要包括：

```json
{
  "metadata": {
    "account_id": "1",
    "experiment_key": "password",
    "subject_name": "张三",
    "task_name": "问答",
    "qa_config_id": "1",
    "qa_target_accuracy": "0.8",
    "started_at": "...",
    "ended_at": "..."
  },
  "runtime_config": {
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "...",
    "provider": "...",
    "base_url": "..."
  },
  "answer_plan": {
    "target_accuracy": 0.8,
    "answers": {}
  },
  "qa_records": [],
  "qa_chat_history": []
}
```

### 规划任务记录结构

规划任务保存内容主要包括：

```json
{
  "metadata": {
    "account_id": "1",
    "experiment_key": "password",
    "subject_name": "张三",
    "task_name": "规划",
    "planning_topic": "旅行",
    "started_at": "...",
    "ended_at": "..."
  },
  "runtime_config": {
    "temperature": 0.7,
    "max_tokens": 1024,
    "model": "...",
    "provider": "...",
    "base_url": "..."
  },
  "planning_state": {},
  "planning_records": []
}
```

## 数据导出

后台用户数据记录页面支持按账号和任务类型查看记录，并导出数据。

支持按任务类型筛选：

- 全部任务
- 聊天
- 问答
- 规划

导出逻辑：

- 每条实验记录导出为一个独立 JSON 文件。
- 同一用户或同一筛选条件下的多条记录会打包为 ZIP。
- ZIP 文件生成在服务器端 `data/exports/` 目录下。
- 浏览器通过 `/exports/{filename}` 下载。

## 安装与运行

### 1. 创建 Conda 环境

```bash
conda env create -f environment.yml
conda activate TrustAgent
```

或使用 pip：

```bash
pip install -r requirements.txt
```

### 2. 配置 `.env`

在项目根目录创建 `.env`，例如：

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=openrouter/auto
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 3. 启动系统

```bash
python app/main.py
```

默认启动地址：

```text
http://127.0.0.1:6006
```

登录页：

```text
http://127.0.0.1:6006/login
```

后台管理页：

```text
http://127.0.0.1:6006/admin
```

## 使用流程

### 管理员流程

1. 进入 `/admin`。
2. 在账号管理中创建账号并设置密码。
3. 在聊天、问答或规划配置页面为账号分配任务。
4. 用户完成实验后，在用户数据记录页面查看或导出数据。

### 用户流程

1. 进入 `/login`。
2. 输入账号和密码登录。
3. 进入个人信息页。
4. 查看或修改姓名、手机号等信息。
5. 根据剩余次数进入聊天、问答或规划任务。
6. 完成任务后系统保存数据并返回个人信息页。

## 注意事项

- 当前数据库文件为 `data/data.db`，如需重新初始化系统数据，可以在备份后删除该文件，再重新启动系统。
- `.env` 中必须配置对应 provider 的 API Key，否则 LLM 调用会失败。
- 问答任务依赖 `data/data.json`，题库结构变化后需要同步检查 `app/services/data_service.py`。
- 规划任务中的工具查询为系统内置数据和随机失败模拟，不会产生真实外部订单。
- 后台删除账号时，应同步清理该账号相关任务配置和实验记录。
- 多用户部署时需要特别注意账号上下文隔离，当前页面通过 query 参数中的 `account_id` 传递用户身份。

## 开发说明

### 任务页面

- 聊天页面：`app/pages/chat_page.py`
- 问答页面：`app/pages/qa_page.py`
- 规划页面：`app/pages/planning_page.py`

### 任务服务

- 聊天与问答核心逻辑：`app/services/experiment_service.py`
- 规划任务页面逻辑：`app/services/planning_service.py`
- 规划 Agent：`agent/planning_agent.py`
- LLM 调用封装：`agent/llm_agent.py`

### 样式

统一样式主要位于：

```text
app/styles.py
```

### 数据服务

- 账号与任务配置：`app/services/account_service.py`
- 实验记录保存与导出：`app/services/user_data_service.py`
- 问答题库读取：`app/services/data_service.py`
