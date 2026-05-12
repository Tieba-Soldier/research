from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.recommendation import (
    RecommendationTaskCreate,
    RecommendationTaskResponse,
    RecommendationTaskStatus,
    RecommendationResult,
)
from app.services.recommendation_service_v2 import RecommendationService
from app.core.response import success_response, error_response
from app.core.exceptions import TaskNotFoundException

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("", response_model=dict)
async def create_recommendation_task(
    request: RecommendationTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """创建资源推荐任务"""
    try:
        service = RecommendationService(db)
        task_id = await service.create_task(request.user_input)

        # 在后台执行推荐流程 - 使用独立的数据库会话
        async def run_recommendation():
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as bg_db:
                bg_service = RecommendationService(bg_db)
                await bg_service.execute_recommendation(task_id)

        background_tasks.add_task(run_recommendation)

        return success_response(
            data={"task_id": task_id, "status": "PENDING"},
            message="资源推荐任务已创建"
        )
    except Exception as e:
        return error_response(message=str(e), code=500)


@router.get("/tasks/{task_id}", response_model=dict)
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询任务状态"""
    try:
        service = RecommendationService(db)
        task = await service.get_task(task_id)

        return success_response(
            data={
                "task_id": task.id,
                "status": task.status,
                "current_step": task.current_step,
                "progress": task.progress,
                "error_message": task.error_message,
            }
        )
    except TaskNotFoundException as e:
        return error_response(message=str(e), code=404)
    except Exception as e:
        return error_response(message=str(e), code=500)


@router.get("/tasks/{task_id}/result", response_model=dict)
async def get_recommendation_result(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """查询推荐结果"""
    try:
        service = RecommendationService(db)
        result = await service.get_recommendation_result(task_id)

        return success_response(data=result)
    except TaskNotFoundException as e:
        return error_response(message=str(e), code=404)
    except Exception as e:
        return error_response(message=str(e), code=500)
