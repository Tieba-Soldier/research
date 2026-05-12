# Resource Recommendation Agent - Backend

智能学习资源推荐系统后端服务。

## 功能特性

- 自动分析用户学习需求
- 提取和标准化学习主题
- 使用 Tavily 搜索相关学习资源
- 智能评估资源质量
- 生成三阶段学习路径
- 生成针对性练习任务

## 技术栈

- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- Tavily API
- OpenAI/Anthropic/DeepSeek/SiliconFlow

## 安装

```bash
cd backend
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

必须配置的环境变量：
- `DATABASE_URL`: PostgreSQL 数据库连接
- `TAVILY_API_KEY`: Tavily 搜索 API Key
- `LLM_PROVIDER`: LLM 提供商 (openai/anthropic/deepseek/siliconflow)
- 对应的 LLM API Key (根据 LLM_PROVIDER 选择)

## LLM 提供商配置

支持以下 LLM 提供商：

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
```

### Anthropic (Claude)
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
```

### DeepSeek
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx
```

### SiliconFlow (硅基流动) - 推荐国内用户使用
```env
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=sk-xxx
```

详细配置说明请查看 [docs/SILICONFLOW.md](docs/SILICONFLOW.md)

## 数据库迁移

```bash
# 执行迁移
alembic upgrade head
```

## 运行

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要 API

### 创建推荐任务
```
POST /api/recommendations
```

### 查询任务状态
```
GET /api/recommendations/tasks/{task_id}
```

### 获取推荐结果
```
GET /api/recommendations/tasks/{task_id}/result
```

### 标记资源已学习
```
POST /api/resources/{resource_id}/mark-studied
```

### 收藏资源
```
POST /api/resources/{resource_id}/favorite
```
