# ReSearch — 智能学习资源推荐 Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org/)

> 输入你的学习需求，AI 自动搜索、评估全球学习资源，为你生成个性化学习路径和练习任务。

## 目录

- [这是什么](#这是什么)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [Agent 工作流](#agent-工作流)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [路线图](#路线图)

## 这是什么

你对某个技术一知半解，比如"Redis 缓存穿透、缓存击穿、缓存雪崩总是分不清"，把这段话告诉 ReSearch：

1. **分析需求** — 理解你想学什么
2. **提取主题** — 识别出「缓存穿透」「缓存击穿」「缓存雪崩」「布隆过滤器」「分布式锁」
3. **全网搜索** — 调用 Tavily 搜索视频、文章、官方文档、GitHub 项目
4. **评估质量** — LLM 对每项资源打分、写推荐理由
5. **生成路径** — 三阶段学习路径（入门 → 实战 → 进阶）
6. **生成练习** — 针对性的练习题和复盘任务

你得到的不只是一堆链接，而是一份结构化的学习方案。

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI（异步） |
| **数据库** | PostgreSQL + SQLAlchemy 2.x + Alembic |
| **LLM** | OpenAI / Anthropic / DeepSeek / SiliconFlow 可切换 |
| **搜索引擎** | Tavily API（支持 Bocha 国内搜索作为备选） |
| **缓存** | Redis |
| **前端** | Vue 3 + Element Plus + Vite + Axios |

## 快速开始

### 前提条件

- Python 3.10+ / Node.js 18+ / PostgreSQL 14+
- [Tavily API Key](https://tavily.com/)（必需）
- 至少一个 LLM API Key（OpenAI / Anthropic / DeepSeek / SiliconFlow 四选一）

### 后端

```bash
cd backend

# 创建虚拟环境（可选但推荐）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env       # 编辑 .env 填入你的 API Key
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger 文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000，输入你的学习需求即可。

## API 概览

### 创建推荐任务

```http
POST /api/recommendations
Content-Type: application/json

{
  "user_input": "我想系统学习 Redis 缓存穿透、布隆过滤器和分布式锁",
  "max_topics": 5,
  "max_resources_per_topic": 5,
  "include_video": true,
  "include_articles": true,
  "include_official_docs": true,
  "include_github": true,
  "include_practice_tasks": true
}
```

### 查询任务状态

```http
GET /api/recommendations/tasks/{task_id}
```

状态流转：`PENDING → ANALYZING_USER_NEED → EXTRACTING_TOPICS → NORMALIZING_TOPICS → SEARCHING_RESOURCES → EVALUATING_RESOURCES → GENERATING_LEARNING_PATH → GENERATING_PRACTICE_TASKS → COMPLETED`

### 获取推荐结果

```http
GET /api/recommendations/tasks/{task_id}/result
```

返回学习主题、资源列表（含评分和推荐理由）、三阶段学习路径、练习任务。

### 资源操作

```http
POST /api/resources/{resource_id}/mark-studied   # 标记已学习
POST /api/resources/{resource_id}/favorite       # 收藏
```

## Agent 工作流

```
用户输入
  ↓  UserNeedAnalyzer        分析学习需求，识别薄弱点
  ↓  TopicExtractor          提取具体学习主题
  ↓  TopicNormalizer         将模糊主题标准化为技术知识点
  ↓  SearchService           Tavily 多维度资源搜索
  ↓  ResourceEvaluator       LLM 评估资源质量 + 生成推荐理由
  ↓  LearningPathGenerator  生成「基础 → 实战 → 进阶」三阶段路径
  ↓  PracticeTaskGenerator  生成针对性练习与复盘任务
  ↓                         结果持久化到 PostgreSQL
```

每个节点独立封装，可单独调试、替换或扩展。

## 项目结构

```
research/
├── backend/
│   ├── app/
│   │   ├── agents/nodes/     # 6 个 Agent 节点（需求分析 → 练习生成）
│   │   ├── agents/prompts/   # 各节点的 LLM Prompt 模板
│   │   ├── services/         # 业务逻辑（推荐、搜索、评估、缓存等）
│   │   ├── tools/            # 外部工具封装（Tavily、Bocha、LLM Client）
│   │   ├── models/           # SQLAlchemy 数据模型（6 张表）
│   │   ├── schemas/          # Pydantic 请求/响应模式
│   │   ├── api/routes/       # FastAPI 路由
│   │   ├── core/             # 配置、异常、重试、校验
│   │   └── main.py           # 应用入口
│   ├── alembic/              # 数据库迁移脚本
│   ├── tests/                # E2E 测试 + 搜索优化测试
│   └── docs/                 # 架构、优化、Token 消耗等文档
├── frontend/
│   └── src/
│       ├── components/       # ResourceCard、LearningPath、PracticeTask
│       ├── pages/            # RecommendationPage
│       └── api/              # Axios 封装
└── ReSearch.md               # 完整设计文档
```

## 配置说明

```env
# LLM Provider（四选一）
LLM_PROVIDER=openai       # openai | anthropic | deepseek | siliconflow
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx
SILICONFLOW_API_KEY=sk-xxx

# 搜索引擎
TAVILY_API_KEY=tvly-xxx

# 功能开关
ENABLE_TAVILY=true
ENABLE_FIRECRAWL=false    # 二期启用：网页正文抓取
ENABLE_CONTEXT7=false     # 三期启用：官方文档精准检索

# 推荐参数
MAX_TOPICS_PER_REQUEST=5
MAX_RESOURCES_PER_TOPIC=5
MAX_SEARCH_QUERIES_PER_TOPIC=5
```

完整的 `.env.example` 见 `backend/.env.example`。

## 路线图

### ✅ 已完成
- 用户输入 → 任务创建 → 状态轮询 → 结果展示（全链路闭环）
- 6 节点 Agent 工作流
- Tavily 多类型资源搜索 + 质量评估
- 三阶段学习路径 + 练习任务生成
- 搜索失败降级、LLM 调用重试
- 历史结果持久化（刷新页面不丢失）

### 🚧 规划中
- Firecrawl 网页正文抓取，摘要更精准
- Context7 官方文档精准检索
- LangGraph 工作流编排
- 学习进度追踪 + 二次测验
- 资源收藏 + 标记已学

## License

MIT
