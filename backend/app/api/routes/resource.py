from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user_resource_progress import UserResourceProgress
from app.schemas.resource import MarkStudiedRequest, FavoriteRequest
from app.core.response import success_response, error_response

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/{resource_id}/mark-studied", response_model=dict)
async def mark_resource_studied(
    resource_id: int,
    request: MarkStudiedRequest,
    db: AsyncSession = Depends(get_db),
):
    """标记资源已学习"""
    try:
        # 这里简化处理，实际应该从认证中获取 user_id
        user_id = 1

        # 查找或创建进度记录
        result = await db.execute(
            select(UserResourceProgress).where(
                UserResourceProgress.user_id == user_id,
                UserResourceProgress.resource_id == resource_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.studied = request.studied
        else:
            progress = UserResourceProgress(
                user_id=user_id,
                resource_id=resource_id,
                studied=request.studied,
            )
            db.add(progress)

        await db.commit()

        return success_response(message="标记成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@router.post("/{resource_id}/favorite", response_model=dict)
async def favorite_resource(
    resource_id: int,
    request: FavoriteRequest,
    db: AsyncSession = Depends(get_db),
):
    """收藏资源"""
    try:
        user_id = 1

        result = await db.execute(
            select(UserResourceProgress).where(
                UserResourceProgress.user_id == user_id,
                UserResourceProgress.resource_id == resource_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.favorite = request.favorite
        else:
            progress = UserResourceProgress(
                user_id=user_id,
                resource_id=resource_id,
                favorite=request.favorite,
            )
            db.add(progress)

        await db.commit()

        return success_response(message="收藏成功")
    except Exception as e:
        return error_response(message=str(e), code=500)
