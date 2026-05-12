# 启动项目指南

## 重要提示

在启动项目前，你需要配置以下内容：

### 1. 配置数据库

项目需要 PostgreSQL 数据库。请确保：
- PostgreSQL 已安装并运行
- 创建数据库：`CREATE DATABASE resource_agent;`
- 在 `.env` 文件中配置正确的数据库连接

### 2. 配置 API Keys

在 `backend/.env` 文件中配置以下 API Keys：

**必需配置**：
- `TAVILY_API_KEY` - Tavily 搜索 API（获取：https://tavily.com）
- LLM API Key（四选一）：
  - `OPENAI_API_KEY` - OpenAI API
  - `ANTHROPIC_API_KEY` - Anthropic Claude API
  - `DEEPSEEK_API_KEY` - DeepSeek API
  - `SILICONFLOW_API_KEY` - 硅基流动 API（推荐国内用户）

### 3. 执行数据库迁移

```bash
cd backend
.venv/Scripts/alembic upgrade head
```

### 4. 启动后端服务

```bash
cd backend
.venv/Scripts/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 6. 启动前端服务

```bash
cd frontend
npm run dev
```

## 访问地址

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

## 当前状态

✅ 后端虚拟环境已创建 (`.venv`)
✅ 后端依赖已安装
⚠️ 需要配置 `.env` 文件
⚠️ 需要配置数据库
⚠️ 需要执行数据库迁移
⚠️ 需要安装前端依赖
