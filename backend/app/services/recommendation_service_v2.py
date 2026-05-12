from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import time

from app.models.recommendation_task import RecommendationTask
from app.models.learning_topic import LearningTopic
from app.models.resource import Resource
from app.models.learning_path import LearningPath
from app.models.practice_task import PracticeTask

from app.services.topic_service import TopicService
from app.services.search_service import SearchService
from app.services.resource_evaluation_service import ResourceEvaluationService
from app.services.learning_path_service import LearningPathService
from app.services.practice_task_service import PracticeTaskService
from app.services.cache_service import cache_service

from app.core.config import settings
from app.core.exceptions import TaskNotFoundException
from app.core.validator import ResultValidator

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐服务：负责主流程编排"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.topic_service = TopicService()
        self.search_service = SearchService()
        self.evaluation_service = ResourceEvaluationService()
        self.learning_path_service = LearningPathService()
        self.practice_task_service = PracticeTaskService()

    async def create_task(self, user_input: str, user_id: Optional[int] = None) -> int:
        """创建推荐任务"""
        task = RecommendationTask(
            user_id=user_id,
            user_input=user_input,
            status="PENDING",
            progress=0,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        logger.info(f"Created task {task.id} for user_input: {user_input[:50]}...")
        return task.id

    async def get_task(self, task_id: int) -> RecommendationTask:
        """获取任务"""
        result = await self.db.execute(
            select(RecommendationTask).where(RecommendationTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise TaskNotFoundException(task_id)
        return task

    async def update_task_status(
        self,
        task_id: int,
        status: str,
        current_step: str = None,
        progress: int = None
    ):
        """更新任务状态"""
        task = await self.get_task(task_id)
        task.status = status
        if current_step:
            task.current_step = current_step
        if progress is not None:
            task.progress = progress
        await self.db.commit()
        logger.info(f"Task {task_id} status updated: {status} ({progress}%)")

    async def execute_recommendation(self, task_id: int):
        """执行推荐流程（主编排逻辑）"""
        overall_start = time.time()

        # 性能统计
        metrics = {
            "llm_calls": 0,
            "tavily_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        logger.info(f"=" * 60)
        logger.info(f"Starting recommendation workflow for task {task_id}")
        logger.info(f"=" * 60)

        try:
            # 初始化缓存
            await cache_service.initialize()

            task = await self.get_task(task_id)

            # ========== 阶段1: 主题分析 ==========
            await self.update_task_status(
                task_id, "ANALYZING_USER_NEED", "正在分析学习需求", 10
            )

            topic_start = time.time()
            topic_result = await self.topic_service.analyze_and_extract_topics(
                user_input=task.user_input,
                max_topics=settings.MAX_TOPICS_PER_REQUEST
            )
            topic_duration = time.time() - topic_start

            topics = topic_result["topics"]
            metrics["llm_calls"] += 3  # analyze + extract + normalize
            logger.info(f"[METRICS] topic_extraction_duration={topic_duration:.2f}s topics_count={len(topics)}")

            # 保存主题到数据库
            await self.update_task_status(
                task_id, "SAVING_TOPICS", "正在保存学习主题", 25
            )

            saved_topics = await self._save_topics(task_id, task.user_id, topics)

            # ========== 阶段2: 资源搜索 ==========
            await self.update_task_status(
                task_id, "SEARCHING_RESOURCES", "正在搜索学习资源", 35
            )

            search_start = time.time()
            raw_resources = await self.search_service.search_for_topics(
                topics=saved_topics,
                max_resources_per_topic=settings.MAX_RESOURCES_PER_TOPIC
            )
            search_duration = time.time() - search_start

            # 估算Tavily调用次数（每个主题最多MAX_SEARCH_QUERIES_PER_TOPIC次）
            estimated_tavily_calls = len(saved_topics) * min(3, settings.MAX_SEARCH_QUERIES_PER_TOPIC)
            metrics["tavily_calls"] += estimated_tavily_calls
            logger.info(f"[METRICS] search_duration={search_duration:.2f}s resources_found={len(raw_resources)} tavily_calls={estimated_tavily_calls}")

            # ========== 阶段3: 资源评估 ==========
            await self.update_task_status(
                task_id, "EVALUATING_RESOURCES", "正在评估资源质量", 50
            )

            eval_start = time.time()
            user_context = self._build_user_context(task.user_input, topics)
            evaluated_resources = await self.evaluation_service.evaluate_resources(
                resources=raw_resources,
                user_context=user_context
            )
            eval_duration = time.time() - eval_start

            metrics["llm_calls"] += len(raw_resources)  # 每个资源一次LLM调用
            logger.info(f"[METRICS] evaluation_duration={eval_duration:.2f}s resources_evaluated={len(evaluated_resources)} llm_calls={len(raw_resources)}")

            # 保存资源到数据库
            await self.update_task_status(
                task_id, "SAVING_RESOURCES", "正在保存资源", 65
            )

            saved_resources = await self._save_resources(
                task_id, task.user_id, evaluated_resources
            )

            # ========== 阶段4: 生成学习路径 ==========
            await self.update_task_status(
                task_id, "GENERATING_LEARNING_PATH", "正在生成学习路径", 75
            )

            path_start = time.time()
            learning_path_data = await self.learning_path_service.generate_learning_path(
                topics=saved_topics,
                resources=[{"id": r.id, "title": r.title, "url": r.url, "difficulty": r.difficulty} for r in saved_resources]
            )
            path_duration = time.time() - path_start

            metrics["llm_calls"] += 1
            logger.info(f"[METRICS] learning_path_duration={path_duration:.2f}s stages_count={len(learning_path_data.get('stages', []))}")

            await self._save_learning_path(task_id, task.user_id, learning_path_data)

            # ========== 阶段5: 生成练习任务 ==========
            await self.update_task_status(
                task_id, "GENERATING_PRACTICE_TASKS", "正在生成练习任务", 85
            )

            practice_start = time.time()
            practice_tasks = await self.practice_task_service.generate_practice_tasks(
                topics=saved_topics
            )
            practice_duration = time.time() - practice_start

            metrics["llm_calls"] += 1
            logger.info(f"[METRICS] practice_tasks_duration={practice_duration:.2f}s tasks_count={len(practice_tasks)}")

            await self._save_practice_tasks(task_id, task.user_id, practice_tasks)

            # ========== 质量验证 ==========
            logger.info("Validating result quality...")
            validation_result = ResultValidator.validate_all(
                topics=saved_topics,
                resources=[{
                    "title": r.title,
                    "url": r.url,
                    "summary": r.summary,
                    "reason": r.reason,
                    "final_score": r.final_score
                } for r in saved_resources],
                learning_path=learning_path_data,
                practice_tasks=practice_tasks
            )

            logger.info(f"[VALIDATION] is_valid={validation_result['is_valid']} total_issues={validation_result['total_issues']}")
            if not validation_result['is_valid']:
                logger.warning(f"[VALIDATION] Quality issues found: {validation_result['issues'][:3]}")

            # ========== 完成 ==========
            await self.update_task_status(task_id, "COMPLETED", "推荐完成", 100)

            overall_duration = time.time() - overall_start

            logger.info(f"=" * 60)
            logger.info(f"[METRICS] FINAL SUMMARY for task {task_id}")
            logger.info(f"[METRICS] total_duration={overall_duration:.2f}s")
            logger.info(f"[METRICS] topic_extraction={topic_duration:.2f}s search={search_duration:.2f}s evaluation={eval_duration:.2f}s path={path_duration:.2f}s practice={practice_duration:.2f}s")
            logger.info(f"[METRICS] topics={len(saved_topics)} resources={len(saved_resources)} practice_tasks={len(practice_tasks)}")
            logger.info(f"[METRICS] llm_calls={metrics['llm_calls']} tavily_calls={metrics['tavily_calls']}")
            logger.info(f"=" * 60)

        except Exception as e:
            logger.error(f"Recommendation failed for task {task_id}: {str(e)}", exc_info=True)
            try:
                await self.update_task_status(task_id, "FAILED", f"推荐失败: {str(e)}", 0)
                task = await self.get_task(task_id)
                task.error_message = str(e)
                await self.db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update task status: {str(update_error)}")
            raise

    async def _save_topics(
        self,
        task_id: int,
        user_id: Optional[int],
        topics: list
    ) -> list:
        """保存主题到数据库"""
        saved_topics = []

        for topic in topics:
            original = (
                topic.get("original")
                or topic.get("raw_text")
                or topic.get("normalized")
                or topic.get("normalized_topic")
                or ""
            )
            normalized = (
                topic.get("normalized")
                or topic.get("normalized_topic")
                or original
            )
            db_topic = LearningTopic(
                task_id=task_id,
                user_id=user_id,
                raw_text=original,
                normalized_topic=normalized,
                category=topic.get("category", ""),
                priority=topic.get("priority", "medium"),
                reason=topic.get("reason", ""),
                keywords=topic.get("keywords", []),
            )
            self.db.add(db_topic)
            await self.db.flush()
            saved_topics.append(
                {
                    "id": db_topic.id,
                    "original": original,
                    "normalized": normalized,
                    "category": topic.get("category", ""),
                    "priority": topic.get("priority", "medium"),
                    "reason": topic.get("reason", ""),
                    "keywords": topic.get("keywords", []),
                }
            )

        await self.db.commit()
        return saved_topics

    async def _save_resources(
        self,
        task_id: int,
        user_id: Optional[int],
        resources: list
    ) -> list:
        """批量保存资源到数据库"""
        saved_resources = []

        # 批量插入
        for resource in resources:
            db_resource = Resource(
                task_id=task_id,
                topic_id=resource.get("topic_id"),
                user_id=user_id,
                title=resource.get("title", ""),
                url=resource.get("url", ""),
                source=resource.get("source", ""),
                resource_type=resource.get("resource_type", "article"),
                summary=resource.get("summary", ""),
                reason=resource.get("reason", ""),
                difficulty=resource.get("difficulty", "medium"),
                estimated_minutes=resource.get("estimated_minutes"),
                relevance_score=resource.get("relevance_score", 0),
                quality_score=resource.get("quality_score", 0),
                practical_score=resource.get("practical_score", 0),
                final_score=resource.get("final_score", 0),
            )
            self.db.add(db_resource)
            saved_resources.append(db_resource)

        await self.db.commit()

        # 刷新以获取ID
        for resource in saved_resources:
            await self.db.refresh(resource)

        return saved_resources

    async def _save_learning_path(
        self,
        task_id: int,
        user_id: Optional[int],
        learning_path_data: dict
    ):
        """保存学习路径"""
        db_learning_path = LearningPath(
            task_id=task_id,
            user_id=user_id,
            title=learning_path_data.get("path_name", "学习路径"),
            description=learning_path_data.get("description", ""),
            stages=learning_path_data.get("stages", []),
        )
        self.db.add(db_learning_path)
        await self.db.commit()

    async def _save_practice_tasks(
        self,
        task_id: int,
        user_id: Optional[int],
        practice_tasks: list
    ):
        """保存练习任务"""
        for practice_task in practice_tasks:
            db_practice_task = PracticeTask(
                task_id=task_id,
                topic_id=practice_task.get("topic_id"),
                user_id=user_id,
                task_text=practice_task.get("task_text", ""),
                reference_answer=practice_task.get("reference_answer", ""),
                difficulty=practice_task.get("difficulty", "medium"),
                task_type=practice_task.get("task_type", "concept_question"),
            )
            self.db.add(db_practice_task)

        await self.db.commit()

    def _build_user_context(self, user_input: str, topics: list) -> str:
        """构建用户上下文"""
        topic_names = [
            t.get("normalized") or t.get("normalized_topic") or ""
            for t in topics
            if (t.get("normalized") or t.get("normalized_topic"))
        ]
        return f"用户学习需求：{user_input}\n学习主题：{', '.join(topic_names)}"

    async def get_recommendation_result(self, task_id: int) -> Dict[str, Any]:
        """获取推荐结果"""
        task = await self.get_task(task_id)

        # 获取学习主题
        topics_result = await self.db.execute(
            select(LearningTopic).where(LearningTopic.task_id == task_id)
        )
        topics = topics_result.scalars().all()

        # 获取资源
        resources_result = await self.db.execute(
            select(Resource).where(Resource.task_id == task_id).order_by(Resource.final_score.desc())
        )
        resources = resources_result.scalars().all()

        # 获取学习路径
        learning_path_result = await self.db.execute(
            select(LearningPath).where(LearningPath.task_id == task_id)
        )
        learning_path = learning_path_result.scalar_one_or_none()

        # 获取练习任务
        practice_tasks_result = await self.db.execute(
            select(PracticeTask).where(PracticeTask.task_id == task_id)
        )
        practice_tasks = practice_tasks_result.scalars().all()

        return {
            "task_id": task.id,
            "status": task.status,
            "topics": [
                {
                    "id": t.id,
                    "raw_text": t.raw_text,
                    "normalized_topic": t.normalized_topic,
                    "category": t.category,
                    "priority": t.priority,
                    "reason": t.reason,
                    "keywords": t.keywords,
                }
                for t in topics
            ],
            "resources": [
                {
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "source": r.source,
                    "resource_type": r.resource_type,
                    "summary": r.summary,
                    "reason": r.reason,
                    "difficulty": r.difficulty,
                    "estimated_minutes": r.estimated_minutes,
                    "relevance_score": float(r.relevance_score) if r.relevance_score else 0,
                    "quality_score": float(r.quality_score) if r.quality_score else 0,
                    "practical_score": float(r.practical_score) if r.practical_score else 0,
                    "final_score": float(r.final_score) if r.final_score else 0,
                }
                for r in resources
            ],
            "learning_path": {
                "id": learning_path.id,
                "title": learning_path.title,
                "description": learning_path.description,
                "stages": learning_path.stages,
            } if learning_path else None,
            "practice_tasks": [
                {
                    "id": p.id,
                    "task_text": p.task_text,
                    "reference_answer": p.reference_answer,
                    "difficulty": p.difficulty,
                    "task_type": p.task_type,
                }
                for p in practice_tasks
            ],
        }
