# Resource Recommendation Agent

智能学习资源推荐系统 - 从零实现的独立资源推荐 Agent 功能。

## 项目简介

用户输入学习需求、技术薄弱点、学习目标或问题描述后，系统自动：
1. 分析学习需求
2. 提取和标准化学习主题
3. 使用 Tavily 搜索相关资源（视频、文章、官方文档、GitHub 项目）
4. 智能评估资源质量
5. 生成三阶段学习路径
6. 生成针对性练习任务

## 技术架构

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL + SQLAlchemy 2.x
- **迁移**: Alembic
- **LLM**: OpenAI / Anthropic / DeepSeek / SiliconFlow
- **搜索**: Tavily API
- **异步**: asyncio

### 前端
- **框架**: Vue 3
- **UI 组件**: Element Plus
- **构建工具**: Vite
- **HTTP 客户端**: Axios

## 项目结构

```
research/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── exceptions.py  # 异常定义
│   │   │   └── response.py    # 响应封装
│   │   ├── db/                # 数据库
│   │   │   ├── base.py        # Base 模型
│   │   │   └── session.py     # 会话管理
│   │   ├── models/            # 数据库模型
│   │   │   ├── recommendation_task.py
│   │   │   ├── learning_topic.py
│   │   │   ├── resource.py
│   │   │   ├── learning_path.py
│   │   │   ├── practice_task.py
│   │   │   └── user_resource_progress.py
│   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── recommendation.py
│   │   │   └── resource.py
│   │   ├── api/               # API 路由
│   │   │   └── routes/
│   │   │       ├── recommendation.py
│   │   │       └── resource.py
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── recommendation_service.py
│   │   │   └── resource_search_service.py
│   │   ├── agents/            # Agent 节点
│   │   │   └── nodes/
│   │   │       ├── user_need_analyzer.py
│   │   │       ├── topic_extractor.py
│   │   │       ├── topic_normalizer.py
│   │   │       ├── resource_evaluator.py
│   │   │       ├── learning_path_generator.py
│   │   │       └── practice_task_generator.py
│   │   ├── tools/             # 工具封装
│   │   │   ├── llm_client.py
│   │   │   ├── tavily_tool.py
│   │   │   ├── firecrawl_tool.py (预留)
│   │   │   └── context7_tool.py (预留)
│   │   ├── prompts/           # LLM Prompts
│   │   │   ├── user_need_analyzer.md
│   │   │   ├── topic_extractor.md
│   │   │   ├── topic_normalizer.md
│   │   │   ├── resource_evaluator.md
│   │   │   ├── learning_path_generator.md
│   │   │   └── practice_task_generator.md
│   │   └── main.py            # 应用入口
│   ├── alembic/               # 数据库迁移
│   │   └── versions/
│   │       └── 001_initial_migration.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   │   ├── ResourceCard.vue
│   │   │   ├── LearningPath.vue
│   │   │   └── PracticeTask.vue
│   │   ├── pages/             # 页面
│   │   │   └── RecommendationPage.vue
│   │   ├── api/               # API 调用
│   │   │   └── index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── README.md
│
└── ReSearch.md                 # 设计文档
```

## 快速开始

### 1. 环境准备

**必需**:
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

**API Keys**:
- Tavily API Key (必需)
- OpenAI / Anthropic / DeepSeek / SiliconFlow API Key (四选一)

### 2. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入真实配置

# 执行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档: http://localhost:8000/docs

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问: http://localhost:3000

## 核心功能

### 1. 创建推荐任务

**API**: `POST /api/recommendations`

**请求示例**:
```json
{
  "user_input": "我想学习 Redis 缓存穿透、缓存击穿、缓存雪崩，还有布隆过滤器和分布式锁。",
  "max_topics": 5,
  "max_resources_per_topic": 5,
  "include_video": true,
  "include_articles": true,
  "include_official_docs": true,
  "include_github": true,
  "include_practice_tasks": true
}
```

### 2. 查询任务状态

**API**: `GET /api/recommendations/tasks/{task_id}`

任务状态流转:
```
PENDING → ANALYZING_USER_NEED → EXTRACTING_TOPICS → 
NORMALIZING_TOPICS → SEARCHING_RESOURCES → 
EVALUATING_RESOURCES → GENERATING_LEARNING_PATH → 
GENERATING_PRACTICE_TASKS → COMPLETED
```

### 3. 获取推荐结果

**API**: `GET /api/recommendations/tasks/{task_id}/result`

返回:
- 学习主题列表
- 推荐资源列表（带评分和推荐理由）
- 三阶段学习路径
- 练习任务列表

### 4. 资源管理

- 标记已学习: `POST /api/resources/{resource_id}/mark-studied`
- 收藏资源: `POST /api/resources/{resource_id}/favorite`

## Agent 工作流

```
用户输入
  ↓
UserNeedAnalyzer (分析学习需求)
  ↓
TopicExtractor (提取学习主题)
  ↓
TopicNormalizer (标准化主题)
  ↓
ResourceSearchService (Tavily 搜索资源)
  ↓
ResourceEvaluator (评估资源质量)
  ↓
LearningPathGenerator (生成学习路径)
  ↓
PracticeTaskGenerator (生成练习任务)
  ↓
保存结果到数据库
```

## 数据库模型

### recommendation_tasks
推荐任务表，记录任务状态和进度。

### learning_topics
学习主题表，存储提取和标准化后的学习主题。

### resources
资源表，存储搜索到的学习资源及评分。

### learning_paths
学习路径表，存储生成的三阶段学习路径。

### practice_tasks
练习任务表，存储生成的练习题和复盘任务。

### user_resource_progress
用户学习进度表，记录已学习和收藏状态。

## 配置说明

### 环境变量

```env
# LLM 配置
LLM_PROVIDER=openai              # openai / anthropic / deepseek / siliconflow
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx
SILICONFLOW_API_KEY=sk-xxx       # 硅基流动 API Key
DASHSCOPE_API_KEY=sk-xxx
# 搜索配置
TAVILY_API_KEY=tvly-xxx

# 功能开关
ENABLE_TAVILY=true
ENABLE_FIRECRAWL=false           # 第一版暂不启用
ENABLE_CONTEXT7=false            # 第一版暂不启用

# 推荐配置
MAX_TOPICS_PER_REQUEST=5         # 每次最多提取主题数
MAX_RESOURCES_PER_TOPIC=5        # 每个主题最多推荐资源数
MAX_SEARCH_QUERIES_PER_TOPIC=5   # 每个主题最多搜索查询数
```

## MVP 验收标准

✅ 用户可以输入学习需求  
✅ 系统创建推荐任务并返回 task_id  
✅ 前端可以轮询查询任务状态  
✅ 系统能从用户输入中提取学习主题  
✅ 系统能使用 Tavily 搜索资源  
✅ 推荐结果保存到数据库  
✅ 前端展示资源卡片  
✅ 前端展示三阶段学习路径  
✅ 前端展示练习任务  
✅ 外部搜索失败时任务不崩溃  
✅ 用户刷新页面后可以查看历史结果  

## 后续增强

### 第二版
- 接入 Firecrawl 抓取网页正文
- 根据正文生成更准确的摘要和推荐理由
- 提升资源评分准确度

### 第三版
- 接入 Context7 获取官方技术文档
- 引入 LangGraph 编排完整 Agent 流程
- 支持学习进度跟踪
- 支持根据已学资源生成二次测验

## 注意事项

1. **API Key 安全**: 所有 API Key 必须配置在 `.env` 文件中，不要提交到代码仓库
2. **搜索限流**: Tavily API 有调用限制，注意控制搜索频率
3. **LLM 成本**: 每次推荐会调用多次 LLM，注意成本控制
4. **异常处理**: 外部 API 调用失败时有降级策略，不会导致整体任务失败
5. **数据隐私**: 搜索关键词中不包含用户隐私信息

## 开发者

本项目由 Claude Code 根据 ReSearch.md 设计文档从零实现。

## License

MIT
