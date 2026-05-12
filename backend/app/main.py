from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import recommendation, resource

app = FastAPI(
    title="Resource Recommendation Agent",
    description="智能学习资源推荐系统",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(recommendation.router)
app.include_router(resource.router)


@app.get("/")
async def root():
    return {"message": "Resource Recommendation Agent API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
