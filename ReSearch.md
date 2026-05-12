# 从零开发：独立资源推荐 Agent 功能设计文档

> 交付对象：Claude Code
>
> 目标：从零开发一个独立的“资源推荐 Agent”模块。用户输入自己的学习不足、学习目标、技术主题或问题描述后，系统自动搜索视频、文章、官方文档、博客、GitHub 项目等资源，并生成学习路径和练习任务。
>
> 说明：本方案不依赖“智能面试助手”背景，也不要求已有面试题、面试总结、面试记录等模块。它可以作为一个独立功能，也可以后续接入面试系统、学习平台、知识库系统或个人学习助手。

---

## 1. 功能目标

用户输入一个学习需求，例如：

```text
我对 Redis 缓存穿透、缓存击穿、缓存雪崩区分不清，想系统学习一下。
```

系统自动完成：

```text
用户学习需求
  ↓
提取学习主题 / 不足点
  ↓
标准化成技术知识点
  ↓
生成搜索关键词
  ↓
搜索视频、文章、博客、官方文档、GitHub 项目
  ↓
可选抓取网页正文
  ↓
评估资源质量
  ↓
生成学习路径
  ↓
生成练习题 / 复盘任务
  ↓
前端展示给用户
```

最终用户看到的是：

1. 系统识别出的学习主题；
2. 每个主题对应的推荐资源；
3. 推荐资源的类型、链接、摘要、推荐理由、难度；
4. 一条分阶段学习路径；
5. 针对学习主题生成的练习题和复盘任务；
6. 可选：收藏资源、标记已学习、重新生成资源。

---

## 2. 示例场景

用户输入：

```text
我最近学习 Java 后端，Redis 缓存穿透、缓存击穿、缓存雪崩总是分不清，布隆过滤器和分布式锁也说不明白，希望帮我找一些学习资料。
```

系统输出：

```json
{
  "topics": [
    {
      "raw_text": "Redis 缓存穿透、缓存击穿、缓存雪崩总是分不清",
      "normalized_topic": "Redis 缓存穿透、缓存击穿、缓存雪崩",
      "category": "Redis",
      "priority": "high"
    },
    {
      "raw_text": "布隆过滤器和分布式锁说不明白",
      "normalized_topic": "布隆过滤器与分布式锁在缓存保护中的应用",
      "category": "Redis",
      "priority": "medium"
    }
  ],
  "resources": [
    {
      "title": "Redis 缓存穿透、击穿、雪崩解决方案",
      "url": "https://example.com/redis-cache-problems",
      "resource_type": "article",
      "difficulty": "medium",
      "reason": "适合补齐缓存高并发问题的基础概念和常见解决方案"
    }
  ],
  "learning_path": {
    "title": "Redis 缓存高并发问题专项学习路径",
    "stages": [
      {
        "name": "概念补齐",
        "goal": "区分缓存穿透、击穿、雪崩的触发原因和解决方案"
      },
      {
        "name": "方案理解",
        "goal": "理解缓存空值、布隆过滤器、互斥锁、逻辑过期等方案"
      },
      {
        "name": "实践复盘",
        "goal": "能结合真实业务场景设计缓存保护方案"
      }
    ]
  },
  "practice_tasks": [
    {
      "question": "缓存穿透和缓存击穿有什么区别？请结合商品详情或优惠券查询场景说明。",
      "difficulty": "medium",
      "question_type": "scenario"
    }
  ]
}
```

---

## 3. 独立资源推荐 Agent 的定位

这个功能本质上是一个面向学习场景的 Agent，不绑定某个具体业务系统。

它可以服务于：

1. 学习平台：根据用户输入的学习目标推荐资料；
2. 面试准备工具：根据薄弱点推荐资料；
3. 企业培训系统：根据岗位能力模型推荐课程；
4. 个人知识助手：根据用户问题生成学习路线；
5. 编程辅助工具：根据技术栈推荐官方文档和实践项目。

核心能力包括：

1. **学习需求理解**：理解用户输入的自然语言学习需求；
2. **主题抽取**：提取用户想学习的知识点；
3. **主题标准化**：把口语化描述转换成标准技术主题；
4. **搜索规划**：为每个主题生成搜索 query；
5. **资源搜索**：搜索文章、视频、文档、博客、项目；
6. **网页抓取**：抓取高质量网页正文，转成 Markdown；
7. **官方文档补充**：针对框架、库、工具补充官方文档；
8. **资源评估**：按相关性、质量、难度、实用性打分；
9. **学习路径生成**：输出分阶段学习建议；
10. **练习任务生成**：生成复盘题、实践任务、面试题或小项目任务。

---

## 4. 技术选型

### 4.1 后端技术栈

推荐使用 Python 后端，方便接入 Agent、搜索 API、MCP 工具和大模型。

| 功能 | 技术选型 | 说明 |
|---|---|---|
| Web 框架 | FastAPI | 接口开发简单，支持异步，适合 Agent 后端 |
| ORM | SQLAlchemy 2.x | 数据库模型管理 |
| Migration | Alembic | 数据库迁移 |
| 数据库 | PostgreSQL / MySQL | 保存推荐任务、学习主题、资源、学习路径 |
| 缓存 | Redis | 保存任务状态、缓存搜索结果、限流 |
| 异步任务 | Celery + Redis / RQ / ARQ | 搜索和网页抓取耗时较长，建议异步执行 |
| Agent 编排 | LangGraph | 后期用于多步骤 Agent 流程编排 |
| LLM 调用 | OpenAI / Claude / DeepSeek / 通义千问 | 封装成统一 LLMClient |
| 搜索 | Tavily | 搜索文章、视频、博客、学习资料 |
| 网页抓取 | Firecrawl MCP / Firecrawl SDK | 抓取网页正文，转 Markdown 或结构化数据 |
| 技术文档 | Context7 MCP | 获取技术框架、库、工具的官方文档和代码示例 |
| 向量库 | Qdrant / Chroma / Milvus | 可选，后期沉淀本地资源库 |

### 4.2 前端技术栈

如果已有前端项目，优先复用现有栈。

推荐组合：

| 功能 | 技术选型 |
|---|---|
| 前端框架 | Vue 3 / React |
| UI 组件库 | Element Plus / Ant Design / shadcn/ui |
| 请求库 | Axios / Fetch |
| 状态管理 | Pinia / Zustand / Redux Toolkit |
| Markdown 渲染 | markdown-it / react-markdown |

---

## 5. Tavily、Firecrawl、Context7 的职责划分

这三个工具不要混用，它们职责不同。

| 工具 | 定位 | 在本项目中的作用 |
|---|---|---|
| Tavily | 搜索引擎 / AI Search API | 根据学习主题搜索全网资源，比如文章、视频、教程、博客 |
| Firecrawl | 网页抓取 / 内容清洗 | 对 Tavily 搜到的 URL 抓取正文，转成 Markdown，用于摘要和评分 |
| Context7 | 技术文档检索 | 查询框架、库、工具的官方文档和代码示例，比如 FastAPI、LangGraph、Redis、Spring |

推荐调用链：

```text
学习主题
  ↓
Tavily 搜索相关资源
  ↓
Firecrawl 抓取高质量网页正文
  ↓
Context7 补充官方技术文档
  ↓
LLM 评估资源质量
  ↓
生成学习路径和练习任务
```

第一版 MVP 可以只接 Tavily。

第二版再接 Firecrawl。

第三版再接 Context7。

---

## 6. 总体架构设计

```text
┌──────────────────────────────────────────────┐
│                  前端页面                      │
│                                              │
│  学习需求输入框                               │
│  推荐任务状态                                 │
│  学习主题展示                                 │
│  学习路径展示                                 │
│  资源卡片展示                                 │
│  练习任务展示                                 │
│  收藏 / 标记已学                              │
└───────────────────────┬──────────────────────┘
                        │ HTTP / SSE / WebSocket
                        ▼
┌──────────────────────────────────────────────┐
│                FastAPI Backend                │
│                                              │
│  recommendation API                           │
│  task service                                 │
│  topic service                                │
│  resource service                             │
│  learning path service                        │
│  practice task service                        │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│                Agent Workflow                 │
│                                              │
│  UserNeedAnalyzer                             │
│  TopicExtractor                               │
│  TopicNormalizer                              │
│  SearchPlanner                                │
│  ResourceSearcher                             │
│  PageScraper                                  │
│  DocsFetcher                                  │
│  ResourceEvaluator                            │
│  LearningPathGenerator                        │
│  PracticeTaskGenerator                        │
└───────────────┬──────────────────────────────┘
                │
        ┌───────┼────────┬───────────┐
        ▼       ▼        ▼           ▼
     Tavily  Firecrawl Context7      LLM

┌──────────────────────────────────────────────┐
│                  数据层                       │
│                                              │
│  users                                       │
│  recommendation_tasks                        │
│  learning_topics                             │
│  resources                                   │
│  learning_paths                              │
│  practice_tasks                              │
│  user_resource_progress                      │
└──────────────────────────────────────────────┘
```

---

## 7. 功能边界

### 7.1 MVP 必须实现

第一版必须完成最小闭环：

```text
用户输入学习需求
  ↓
LLM 抽取学习主题
  ↓
LLM 生成搜索关键词
  ↓
Tavily 搜索资源
  ↓
资源去重和初步评分
  ↓
LLM 生成学习路径
  ↓
LLM 生成练习任务
  ↓
前端展示
```

MVP 要求：

1. 能理解用户输入的学习需求；
2. 能从学习需求中提取具体技术主题；
3. 能根据主题搜索资源；
4. 能保存推荐任务和推荐结果；
5. 能展示资源卡片；
6. 能生成三阶段学习路径；
7. 能生成练习任务；
8. 搜索失败时不能导致系统崩溃。

### 7.2 第二版增强

1. 接入 Firecrawl，抓取网页正文；
2. 根据网页正文重新生成摘要和推荐理由；
3. 提升资源评分准确度；
4. 支持官方文档、GitHub 项目、视频资源分类。

### 7.3 第三版增强

1. 接入 Context7，获取官方技术文档；
2. 引入 LangGraph 编排完整 Agent 流程；
3. 支持学习进度记录；
4. 支持根据已学资源生成二次测验；
5. 支持长期能力画像。

---

## 8. 前后端职责划分

### 8.1 前端负责

前端只负责交互和展示，不负责 Agent 逻辑。

前端功能：

1. 提供学习需求输入框；
2. 提供推荐配置选项，例如是否包含视频、官方文档、GitHub 项目；
3. 展示推荐任务进度；
4. 展示学习主题列表；
5. 展示学习路径；
6. 展示推荐资源卡片；
7. 展示练习任务；
8. 支持收藏资源；
9. 支持标记资源已学习；
10. 支持重新生成推荐结果。

### 8.2 后端负责

后端负责核心业务逻辑。

后端功能：

1. 接收用户学习需求；
2. 创建推荐任务；
3. 调用 LLM 分析学习需求；
4. 抽取学习主题；
5. 标准化技术主题；
6. 调用 Tavily 搜索资源；
7. 可选调用 Firecrawl 抓取网页正文；
8. 可选调用 Context7 获取官方文档；
9. 对资源去重、评分、排序；
10. 生成学习路径；
11. 生成练习任务；
12. 保存结果；
13. 提供前端查询接口。

---

## 9. 后端目录结构设计

建议新增或调整为以下结构：

```text
backend/
  app/
    main.py

    core/
      config.py
      logging.py
      exceptions.py
      response.py

    db/
      base.py
      session.py

    models/
      user.py
      recommendation_task.py
      learning_topic.py
      resource.py
      learning_path.py
      practice_task.py
      user_resource_progress.py

    schemas/
      recommendation.py
      learning_topic.py
      resource.py
      learning_path.py
      practice_task.py

    api/
      routes/
        recommendation.py
        resource.py
        learning_path.py
        practice_task.py

    services/
      recommendation_service.py
      topic_service.py
      resource_service.py
      learning_path_service.py
      practice_task_service.py

    agents/
      state.py
      graph.py
      nodes/
        user_need_analyzer.py
        topic_extractor.py
        topic_normalizer.py
        search_planner.py
        resource_searcher.py
        page_scraper.py
        docs_fetcher.py
        resource_evaluator.py
        learning_path_generator.py
        practice_task_generator.py

    tools/
      llm_client.py
      tavily_tool.py
      firecrawl_tool.py
      context7_tool.py
      web_tool_base.py

    prompts/
      user_need_analyzer.md
      topic_extractor.md
      topic_normalizer.md
      search_planner.md
      resource_evaluator.md
      learning_path_generator.md
      practice_task_generator.md

    tasks/
      recommendation_tasks.py

    utils/
      json_parser.py
      text_cleaner.py
      url_utils.py
      score_utils.py
```

---

## 10. 数据库设计

### 10.1 recommendation_tasks

保存资源推荐任务。

```sql
CREATE TABLE recommendation_tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    user_input TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_step VARCHAR(255),
    progress INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

状态枚举：

```text
PENDING
ANALYZING_USER_NEED
EXTRACTING_TOPICS
NORMALIZING_TOPICS
SEARCHING_RESOURCES
SCRAPING_PAGES
FETCHING_DOCS
EVALUATING_RESOURCES
GENERATING_LEARNING_PATH
GENERATING_PRACTICE_TASKS
COMPLETED
FAILED
```

### 10.2 learning_topics

保存从用户输入中抽取出的学习主题。

```sql
CREATE TABLE learning_topics (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    user_id BIGINT,
    raw_text TEXT NOT NULL,
    normalized_topic VARCHAR(255),
    category VARCHAR(100),
    priority VARCHAR(50),
    reason TEXT,
    keywords JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

字段说明：

| 字段 | 说明 |
|---|---|
| raw_text | 用户原始表达中的学习问题 |
| normalized_topic | 标准化后的技术主题 |
| category | 技术分类，例如 Redis、MySQL、Spring、Docker |
| priority | 优先级：low / medium / high |
| reason | 为什么需要学习该主题 |
| keywords | 搜索关键词 |

### 10.3 resources

保存推荐资源。

```sql
CREATE TABLE resources (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    topic_id BIGINT,
    user_id BIGINT,
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    source VARCHAR(100),
    resource_type VARCHAR(50),
    summary TEXT,
    reason TEXT,
    difficulty VARCHAR(50),
    estimated_minutes INT,
    relevance_score NUMERIC(5,2),
    quality_score NUMERIC(5,2),
    practical_score NUMERIC(5,2),
    final_score NUMERIC(5,2),
    content_markdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

资源类型：

```text
video
article
doc
official_doc
github
course
qa
```

### 10.4 learning_paths

保存学习路径。

```sql
CREATE TABLE learning_paths (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    user_id BIGINT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    stages JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 10.5 practice_tasks

保存练习任务。

```sql
CREATE TABLE practice_tasks (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    topic_id BIGINT,
    user_id BIGINT,
    task_text TEXT NOT NULL,
    reference_answer TEXT,
    difficulty VARCHAR(50),
    task_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

任务类型：

```text
concept_question
comparison_question
scenario_question
coding_task
summary_task
project_task
interview_question
```

### 10.6 user_resource_progress

保存用户学习进度。

```sql
CREATE TABLE user_resource_progress (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    resource_id BIGINT NOT NULL,
    studied BOOLEAN DEFAULT FALSE,
    favorite BOOLEAN DEFAULT FALSE,
    studied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 11. API 设计

### 11.1 创建资源推荐任务

```http
POST /api/recommendations
```

请求：

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

响应：

```json
{
  "code": 0,
  "message": "资源推荐任务已创建",
  "data": {
    "task_id": 1001,
    "status": "PENDING"
  }
}
```

### 11.2 查询任务状态

```http
GET /api/recommendations/tasks/{task_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1001,
    "status": "SEARCHING_RESOURCES",
    "current_step": "正在搜索 Redis 缓存击穿相关资源",
    "progress": 45,
    "error_message": null
  }
}
```

### 11.3 查询推荐结果

```http
GET /api/recommendations/tasks/{task_id}/result
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1001,
    "status": "COMPLETED",
    "topics": [],
    "resources": [],
    "learning_path": {},
    "practice_tasks": []
  }
}
```

### 11.4 重新生成某个主题的资源

```http
POST /api/recommendations/tasks/{task_id}/topics/{topic_id}/regenerate
```

### 11.5 标记资源已学习

```http
POST /api/resources/{resource_id}/mark-studied
```

请求：

```json
{
  "studied": true
}
```

### 11.6 收藏资源

```http
POST /api/resources/{resource_id}/favorite
```

请求：

```json
{
  "favorite": true
}
```

---

## 12. Agent 工作流设计

### 12.1 Agent 状态对象

```python
from typing import TypedDict, List, Dict, Any, Optional

class ResourceRecommendationAgentState(TypedDict):
    user_id: Optional[int]
    task_id: int
    user_input: str

    user_need_summary: Optional[str]
    topics: List[Dict[str, Any]]
    normalized_topics: List[Dict[str, Any]]
    search_queries: List[Dict[str, Any]]
    raw_search_results: List[Dict[str, Any]]
    scraped_pages: List[Dict[str, Any]]
    official_docs: List[Dict[str, Any]]
    evaluated_resources: List[Dict[str, Any]]
    learning_path: Optional[Dict[str, Any]]
    practice_tasks: List[Dict[str, Any]]

    current_step: str
    progress: int
    errors: List[str]
```

### 12.2 工作流节点

```text
START
  ↓
analyze_user_need
  ↓
extract_topics
  ↓
normalize_topics
  ↓
build_search_queries
  ↓
search_resources
  ↓
filter_and_deduplicate
  ↓
scrape_pages 可选
  ↓
fetch_official_docs 可选
  ↓
evaluate_resources
  ↓
generate_learning_path
  ↓
generate_practice_tasks
  ↓
save_result
  ↓
END
```

### 12.3 节点说明

| 节点 | 职责 |
|---|---|
| analyze_user_need | 理解用户输入的学习目标和当前困惑 |
| extract_topics | 从用户输入中抽取学习主题 |
| normalize_topics | 把主题标准化成可搜索技术主题 |
| build_search_queries | 为每个主题生成搜索 query |
| search_resources | 调用 Tavily 搜索资源 |
| filter_and_deduplicate | 过滤无效结果，按 URL 和标题去重 |
| scrape_pages | 可选，用 Firecrawl 抓取网页正文 |
| fetch_official_docs | 可选，用 Context7 获取官方技术文档 |
| evaluate_resources | 资源评分、排序、生成推荐理由 |
| generate_learning_path | 生成三阶段学习路径 |
| generate_practice_tasks | 生成练习题、总结任务、实践任务 |
| save_result | 保存所有结果到数据库 |

---

## 13. Prompt 设计

### 13.1 user_need_analyzer.md

```text
你是一个学习需求分析助手。

请分析用户输入的学习需求，判断用户想学习什么、当前困惑是什么、学习目标是什么。

要求：
1. 不要添加用户没有表达的个人隐私信息。
2. 只关注学习主题、技术方向、知识不足、实践目标。
3. 输出 JSON，不要输出解释。

字段：
- learning_goal：用户的学习目标
- current_problem：用户当前遇到的问题
- target_level：basic / medium / advanced / unknown
- preferred_resource_types：video / article / official_doc / github / course / unknown

用户输入：
{{user_input}}
```

### 13.2 topic_extractor.md

```text
你是一个技术学习主题抽取器。

请从用户输入中提取具体、可学习、可搜索的技术主题。

要求：
1. 只提取可学习、可搜索、可复盘的技术知识点。
2. 不要提取泛泛而谈的问题，例如“我学得不好”。
3. 如果用户表达比较口语化，请转换成具体技术主题。
4. 每个主题必须具体，例如“Redis 缓存击穿解决方案”。
5. 输出 JSON 数组，不要输出解释。

字段：
- raw_text：用户原始表达中的问题
- category：技术分类，例如 Redis、MySQL、Spring、JVM、Docker
- priority：low / medium / high
- reason：为什么需要学习该主题

用户输入：
{{user_input}}
```

### 13.3 topic_normalizer.md

```text
你是一个技术知识点标准化助手。

请把用户的学习主题转换成适合搜索和学习的标准技术主题。

要求：
1. normalized_topic 要简洁明确。
2. keywords 用于后续搜索。
3. category 表示所属技术领域。
4. search_intent 表示搜索目的，例如“基础学习”“项目实践”“官方文档学习”“面试复习”。
5. 输出 JSON 数组。

学习主题：
{{topics}}
```

### 13.4 search_planner.md

```text
你是一个学习资源搜索规划器。

请根据标准技术主题生成搜索 query。

要求：
1. 每个主题生成 3 到 5 个 query。
2. query 要覆盖：博客文章、视频教程、官方文档、项目实践。
3. 中文技术主题优先生成中文 query，同时可以补充英文 query。
4. query 不要包含用户隐私信息。
5. 输出 JSON。

标准主题：
{{normalized_topics}}
```

### 13.5 resource_evaluator.md

```text
你是一个学习资源评估器。

请根据用户的学习主题，对搜索到的资源进行评分。

评分维度：
1. relevance_score：和学习主题的相关性，0 到 100。
2. quality_score：资源质量，0 到 100。
3. practical_score：是否适合实践或复盘，0 到 100。
4. difficulty：basic / medium / advanced。
5. reason：为什么推荐。

请剔除明显不相关、广告、低质量采集内容。
输出 JSON 数组。

学习主题：
{{topics}}

资源列表：
{{resources}}
```

### 13.6 learning_path_generator.md

```text
你是一个技术学习路径规划师。

请根据用户的学习主题和推荐资源，生成一个三阶段学习路径。

固定三阶段：
1. 概念补齐
2. 实践理解
3. 复盘巩固

每个阶段包含：
- name
- goal
- resources
- tasks
- expected_output

要求：
1. 学习路径必须和用户学习主题强相关。
2. 不要生成空泛建议。
3. 尽量结合真实业务场景或实践任务。
4. 输出 JSON。

学习主题：
{{topics}}

推荐资源：
{{resources}}
```

### 13.7 practice_task_generator.md

```text
你是一个技术学习教练。

请根据用户的学习主题生成练习任务。

要求：
1. 每个主题生成 3 到 5 个任务。
2. 任务类型包括：概念解释题、对比分析题、场景题、代码练习、总结任务、小项目任务。
3. 每个任务包含 task_text、task_type、difficulty、reference_answer。
4. 任务要适合学习复盘，不要太泛。
5. 输出 JSON 数组。

学习主题：
{{topics}}
```

---

## 14. 工具封装设计

### 14.1 LLMClient

所有 LLM 调用统一走 `LLMClient`，不要在业务代码里直接调用具体模型 API。

```python
class LLMClient:
    async def generate_json(self, prompt: str, schema_hint: str | None = None) -> dict | list:
        """调用 LLM，并解析 JSON。解析失败时自动修复或重试。"""
        pass

    async def generate_text(self, prompt: str) -> str:
        """普通文本生成。"""
        pass
```

### 14.2 TavilyTool

```python
class TavilyTool:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        返回字段：
        - title
        - url
        - snippet
        - score
        - source
        """
        pass
```

### 14.3 FirecrawlTool

```python
class FirecrawlTool:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def scrape(self, url: str) -> dict:
        """
        返回字段：
        - title
        - url
        - markdown
        - metadata
        """
        pass
```

### 14.4 Context7Tool

```python
class Context7Tool:
    async def fetch_docs(self, library_name: str, topic: str) -> list[dict]:
        """
        返回字段：
        - title
        - content
        - url
        - library
        - topic
        """
        pass
```

第一版可以只预留 Context7Tool，不实现真实调用。

---

## 15. 资源类型识别

可以先使用规则判断。

```python
def infer_resource_type(url: str, title: str) -> str:
    text = f"{url} {title}".lower()

    if "youtube.com" in text or "youtu.be" in text or "bilibili.com" in text:
        return "video"
    if "github.com" in text:
        return "github"
    if "docs." in text or "documentation" in text or "官方文档" in title:
        return "official_doc"
    if "blog" in text or "文章" in title or "教程" in title:
        return "article"
    return "article"
```

后期可以交给 LLM 判断。

---

## 16. 资源评分规则

推荐评分：

```text
final_score = relevance_score * 0.4
            + quality_score * 0.25
            + practical_score * 0.2
            + difficulty_score * 0.1
            + freshness_score * 0.05
```

评分维度：

| 维度 | 权重 | 说明 |
|---|---:|---|
| relevance_score | 40% | 是否和学习主题强相关 |
| quality_score | 25% | 来源质量、内容完整度 |
| practical_score | 20% | 是否适合实践和复盘 |
| difficulty_score | 10% | 是否匹配用户水平 |
| freshness_score | 5% | 内容是否较新 |

过滤规则：

1. URL 重复去重；
2. 标题相似度过高去重；
3. 明显广告页过滤；
4. 低质量采集站降权；
5. 官方文档、GitHub、知名技术社区加权；
6. 每个主题最多保留 5 个资源。

---

## 17. 前端页面设计

### 17.1 资源推荐首页

页面结构：

```text
资源推荐 Agent
├── 学习需求输入框
│   └── 例如：我想学习 Redis 缓存穿透、缓存击穿、布隆过滤器和分布式锁
├── 推荐配置
│   ├── 包含视频
│   ├── 包含文章
│   ├── 包含官方文档
│   ├── 包含 GitHub 项目
│   └── 生成练习任务
└── 按钮：生成资源推荐
```

### 17.2 任务状态展示

```text
正在生成资源推荐...
当前步骤：正在搜索 Redis 缓存击穿相关资源
进度：45%
```

可以使用轮询：

```text
每 2 秒请求 GET /api/recommendations/tasks/{task_id}
```

后期可以改成 SSE 或 WebSocket。

### 17.3 推荐结果页

```text
学习资源推荐
├── 识别出的学习主题
├── 三阶段学习路径
├── 推荐资源
│   ├── 视频资源
│   ├── 技术文章
│   ├── 官方文档
│   └── GitHub 示例
└── 练习任务
```

### 17.4 资源卡片字段

```typescript
type ResourceCard = {
  id: number
  title: string
  url: string
  resourceType: 'video' | 'article' | 'doc' | 'official_doc' | 'github'
  summary: string
  reason: string
  difficulty: 'basic' | 'medium' | 'advanced'
  estimatedMinutes: number
  finalScore: number
  studied: boolean
  favorite: boolean
}
```

---

## 18. MVP 开发步骤

### Step 1：创建数据库模型

实现：

1. `RecommendationTask`
2. `LearningTopic`
3. `Resource`
4. `LearningPath`
5. `PracticeTask`
6. `UserResourceProgress`

要求：

1. 使用 SQLAlchemy 2.x；
2. 补充 Pydantic Schema；
3. 生成 Alembic migration；
4. 如果没有用户系统，`user_id` 可以暂时允许为空。

### Step 2：实现推荐任务 API

接口：

1. `POST /api/recommendations`
2. `GET /api/recommendations/tasks/{task_id}`
3. `GET /api/recommendations/tasks/{task_id}/result`

要求：

1. 创建任务后立即返回 task_id；
2. 后台异步执行推荐流程；
3. 任务状态可查询；
4. 异常时写入 `error_message`。

### Step 3：实现 LLMClient

要求：

1. 支持读取环境变量中的 API Key；
2. 支持 `generate_text`；
3. 支持 `generate_json`；
4. JSON 解析失败时自动重试一次；
5. 所有 prompt 从 `prompts/` 目录读取。

### Step 4：实现 UserNeedAnalyzer

输入：

```text
user_input
```

输出：

```json
{
  "learning_goal": "系统学习 Redis 缓存高并发问题",
  "current_problem": "区分不清缓存穿透、击穿、雪崩，不理解布隆过滤器和分布式锁",
  "target_level": "medium",
  "preferred_resource_types": ["article", "video", "official_doc"]
}
```

### Step 5：实现 TopicExtractor

输入：

```text
user_input
```

输出：

```json
[
  {
    "raw_text": "Redis 缓存穿透、缓存击穿、缓存雪崩区分不清",
    "category": "Redis",
    "priority": "high",
    "reason": "这是 Redis 高并发缓存设计中的核心知识点"
  }
]
```

要求：

1. 调用 LLM；
2. 解析 JSON；
3. 保存到 `learning_topics` 表。

### Step 6：实现 TopicNormalizer

要求：

1. 将 `raw_text` 转换为 `normalized_topic`；
2. 生成关键词；
3. 保存回 `learning_topics.normalized_topic` 和 `learning_topics.keywords`。

示例：

```json
{
  "raw_text": "缓存击穿解决方案回答不完整",
  "normalized_topic": "Redis 缓存击穿解决方案",
  "keywords": ["Redis", "缓存击穿", "热点 Key", "分布式锁", "逻辑过期"]
}
```

### Step 7：实现 SearchPlanner

根据每个 `normalized_topic` 生成搜索 query。

示例：

```json
{
  "topic": "Redis 缓存击穿解决方案",
  "queries": [
    "Redis 缓存击穿 解决方案 教程",
    "Redis 热点 Key 分布式锁 逻辑过期",
    "Redis 缓存穿透 缓存击穿 缓存雪崩 区别",
    "Redis cache breakdown hot key mutex lock"
  ]
}
```

### Step 8：实现 TavilyTool

要求：

1. 从环境变量读取 `TAVILY_API_KEY`；
2. 提供 `async search(query, max_results)`；
3. 返回统一结构；
4. 处理超时、空结果和异常。

### Step 9：实现 ResourceSearchService

流程：

```text
learning_topics
  ↓
search queries
  ↓
Tavily search
  ↓
合并结果
  ↓
URL 去重
  ↓
资源类型识别
  ↓
保存 resources
```

### Step 10：实现 ResourceEvaluator

要求：

1. 对资源进行评分；
2. 生成推荐理由；
3. 每个主题最多保留 5 个资源；
4. 更新 `resources` 表的分数字段。

### Step 11：实现 LearningPathGenerator

生成固定三阶段学习路径：

```text
第一阶段：概念补齐
第二阶段：实践理解
第三阶段：复盘巩固
```

保存到 `learning_paths` 表。

### Step 12：实现 PracticeTaskGenerator

要求：

1. 每个主题生成 3 到 5 个练习任务；
2. 包含参考答案或参考思路；
3. 保存到 `practice_tasks` 表。

### Step 13：前端页面开发

新增：

1. 资源推荐首页；
2. 推荐任务状态组件；
3. 推荐结果页；
4. 资源卡片组件；
5. 学习路径组件；
6. 练习任务组件；
7. 收藏和标记已学按钮。

---

## 19. 第二版开发步骤：Firecrawl 增强

在 MVP 跑通后接入 Firecrawl。

新增流程：

```text
Tavily 搜索结果
  ↓
筛选 Top N URL
  ↓
Firecrawl 抓取正文
  ↓
正文摘要
  ↓
重新评估资源质量
```

实现要求：

1. 每个主题最多抓取 3 个页面；
2. 抓取失败不影响主流程；
3. 抓取正文保存到 `resources.content_markdown`；
4. 使用正文生成更准确的 `summary` 和 `reason`。

---

## 20. 第三版开发步骤：Context7 增强

适合技术框架或库相关主题。

例如：

```text
FastAPI
LangGraph
Spring Boot
Spring Security
Redis
Redisson
MyBatis
Vue
React
Docker
Kubernetes
```

流程：

```text
normalized_topic
  ↓
判断是否是框架 / 库 / 工具
  ↓
Context7 获取官方文档
  ↓
加入 official_doc 资源
  ↓
参与学习路径生成
```

第一版可以先预留接口：

```python
class Context7Tool:
    async def fetch_docs(self, library_name: str, topic: str) -> list[dict]:
        return []
```

---

## 21. 错误处理和降级策略

| 失败点 | 降级方案 |
|---|---|
| LLM 分析用户需求失败 | 重试一次；仍失败则返回任务失败 |
| LLM 输出 JSON 解析失败 | 用 JSON 修复 prompt 重试 |
| Tavily 搜索失败 | 换 query 重试；仍失败则只生成学习路径和练习任务 |
| Firecrawl 抓取失败 | 使用 Tavily snippet 作为摘要 |
| Context7 不可用 | 跳过官方文档补充 |
| 某个主题无资源 | 标记为空资源，但继续处理其他主题 |
| 整体任务失败 | 保存 FAILED 状态和错误信息，前端允许重新生成 |

---

## 22. 环境变量

```env
# App
APP_ENV=dev
APP_NAME=resource-recommendation-agent

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/resource_agent

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
DEEPSEEK_API_KEY=xxx

# Search
TAVILY_API_KEY=xxx
FIRECRAWL_API_KEY=xxx

# Feature Flags
ENABLE_TAVILY=true
ENABLE_FIRECRAWL=false
ENABLE_CONTEXT7=false
ENABLE_VIDEO_SEARCH=true
ENABLE_GITHUB_SEARCH=true

# Recommendation Config
MAX_TOPICS_PER_REQUEST=5
MAX_RESOURCES_PER_TOPIC=5
MAX_SEARCH_QUERIES_PER_TOPIC=5
MAX_SCRAPE_PAGES_PER_TOPIC=3
```

---

## 23. 安全注意事项

1. 搜索 query 中不要包含用户姓名、手机号、学校、公司、简历隐私等信息。
2. 只把技术知识点和学习目标用于搜索。
3. 外部网页内容不能直接作为系统指令使用，防止提示词注入。
4. 不要复制大段网页内容，只做摘要和链接推荐。
5. 对搜索结果来源进行展示，不要伪造资源来源。
6. 外部 API 调用必须设置超时和异常处理。
7. API Key 只能放在环境变量里，不能写死在代码中。

---

## 24. 测试用例

### 24.1 学习主题抽取测试

输入：

```text
我对 Redis 缓存穿透和缓存击穿区分不清，对布隆过滤器解释不完整，Spring 事务传播机制只知道 REQUIRED，不了解 REQUIRES_NEW。
```

期望输出：

```json
[
  {
    "normalized_topic": "Redis 缓存穿透与缓存击穿",
    "category": "Redis"
  },
  {
    "normalized_topic": "布隆过滤器原理与误判率",
    "category": "Redis"
  },
  {
    "normalized_topic": "Spring 事务传播机制",
    "category": "Spring"
  }
]
```

### 24.2 搜索测试

输入：

```text
Redis 缓存击穿解决方案
```

期望：

1. 至少返回 3 个资源；
2. 每个资源有 title、url、resource_type；
3. URL 不重复；
4. 推荐理由不为空。

### 24.3 学习路径测试

输入：

```text
Spring 事务传播机制掌握不清
```

期望输出包含：

```text
1. 概念补齐：理解 7 种事务传播行为
2. 实践理解：结合订单或优惠券业务说明事务边界
3. 复盘巩固：回答 REQUIRED 和 REQUIRES_NEW 的区别
```

---

## 25. 给 Claude Code 的开发指令

把下面这段直接发给 Claude Code：

```text
你是我的全栈开发助手。请你根据当前项目结构，从零实现一个独立的“资源推荐 Agent”功能。

功能背景：
这个功能不依赖面试助手，也不依赖面试总结。用户直接输入自己的学习需求、技术薄弱点、学习目标或问题描述，系统自动搜索相关视频、文章、官方文档、博客、GitHub 项目等资源，并生成学习路径和练习任务。

请优先实现 MVP：
1. 接收用户输入的学习需求 user_input；
2. 从 user_input 中抽取学习主题；
3. 把学习主题标准化成技术主题；
4. 使用 Tavily 搜索相关资源；
5. 对资源去重、评分、保存；
6. 生成三阶段学习路径；
7. 生成练习任务；
8. 提供 FastAPI 接口；
9. 前端展示学习主题、资源卡片、学习路径和练习任务。

开发要求：
- 后端使用 Python + FastAPI；
- 数据库使用 SQLAlchemy 2.x；
- Migration 使用 Alembic；
- LLM 调用封装成 LLMClient；
- Tavily、Firecrawl、Context7 都封装成独立工具类；
- 第一版只需要真实实现 Tavily，Firecrawl 和 Context7 可以先预留接口；
- 所有 Prompt 放到 prompts 目录；
- LLM 输出必须做 JSON 解析和异常处理；
- 外部工具调用失败时要有降级策略；
- 后端分层清晰：model、schema、route、service、agent、tool；
- 前端只负责展示和交互，不写复杂 Agent 逻辑。

请按以下顺序开发：
1. 阅读当前项目结构；
2. 新增数据库模型和 migration；
3. 新增 Pydantic schema；
4. 实现 LLMClient；
5. 实现 TavilyTool；
6. 实现 UserNeedAnalyzer；
7. 实现 TopicExtractor；
8. 实现 TopicNormalizer；
9. 实现 ResourceSearchService；
10. 实现 ResourceEvaluator；
11. 实现 LearningPathGenerator；
12. 实现 PracticeTaskGenerator；
13. 实现 recommendation API routes；
14. 实现前端页面和组件；
15. 补充单元测试和异常处理。

请不要一次性把所有代码写在一个文件里，要按照模块拆分。每完成一个模块，请说明修改了哪些文件、实现了什么功能、下一步应该做什么。
```

---

## 26. 最小版本验收标准

MVP 完成后需要满足：

1. 用户可以在资源推荐页面输入学习需求；
2. 后端会创建推荐任务并返回 task_id；
3. 前端可以查询任务状态；
4. 系统可以从用户输入中提取具体技术学习主题；
5. 系统可以使用 Tavily 搜索资源；
6. 推荐结果会保存到数据库；
7. 前端可以展示资源卡片；
8. 前端可以展示三阶段学习路径；
9. 前端可以展示练习任务；
10. 外部搜索失败时，任务不会直接崩溃；
11. 用户刷新页面后，仍然可以看到历史推荐结果。

