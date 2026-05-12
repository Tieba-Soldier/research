from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recommendation_task import RecommendationTask
from app.models.learning_topic import LearningTopic
from app.models.resource import Resource
from app.models.learning_path import LearningPath
from app.models.practice_task import PracticeTask
from app.agents.nodes.user_need_analyzer import UserNeedAnalyzer
from app.agents.nodes.topic_extractor import TopicExtractor
from app.agents.nodes.topic_normalizer import TopicNormalizer
from app.agents.nodes.resource_evaluator import ResourceEvaluator
from app.agents.nodes.learning_path_generator import LearningPathGenerator
from app.agents.nodes.practice_task_generator import PracticeTaskGenerator
from app.services.search_service import SearchService
from app.core.config import settings
from app.core.exceptions import TaskNotFoundException


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_need_analyzer = UserNeedAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.topic_normalizer = TopicNormalizer()
        self.search_service = SearchService()
        self.resource_evaluator = ResourceEvaluator()
        self.learning_path_generator = LearningPathGenerator()
        self.practice_task_generator = PracticeTaskGenerator()

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

    async def update_task_status(self, task_id: int, status: str, current_step: str = None, progress: int = None):
        """更新任务状态"""
        task = await self.get_task(task_id)
        task.status = status
        if current_step:
            task.current_step = current_step
        if progress is not None:
            task.progress = progress
        await self.db.commit()

    async def execute_recommendation(self, task_id: int):
        """执行推荐流程"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            task = await self.get_task(task_id)
            logger.info(f"Starting recommendation for task {task_id}")

            # 1. 分析用户需求
            await self.update_task_status(task_id, "ANALYZING_USER_NEED", "正在分析学习需求", 10)
            logger.info(f"Analyzing user need for task {task_id}")
            user_need = await self.user_need_analyzer.analyze(task.user_input, task_id)
            logger.info(f"User need analysis completed: {user_need}")

            # 2. 提取学习主题
            await self.update_task_status(task_id, "EXTRACTING_TOPICS", "正在提取学习主题", 20)
            topics_data = await self.topic_extractor.extract(task.user_input, task_id)
            logger.info(f"Topics extracted: {topics_data}")

            # 提取 topics 列表
            topics_list = topics_data.get("topics", [])
            if not topics_list:
                raise Exception("No topics extracted")

            logger.info(f"Extracted {len(topics_list)} topics")

            # 3. 保存学习主题（直接使用提取的主题）
            saved_topics = []
            for topic in topics_list[:settings.MAX_TOPICS_PER_REQUEST]:
                raw_text = topic.get("raw_text", "")
                normalized_topic = topic.get("normalized_topic", "")

                if not raw_text or not normalized_topic:
                    logger.warning(f"Skipping topic with empty fields: {topic}")
                    continue

                db_topic = LearningTopic(
                    task_id=task_id,
                    user_id=task.user_id,
                    raw_text=raw_text,
                    normalized_topic=normalized_topic,
                    category="other",
                    priority="medium",
                    reason="从用户输入中提取",
                    keywords=[normalized_topic],
                )
                self.db.add(db_topic)
                await self.db.flush()
                saved_topics.append(normalized_topic)

            await self.db.commit()

            if not saved_topics:
                raise Exception("No valid topics to save")

            # 5. 搜索资源
            await self.update_task_status(task_id, "SEARCHING_RESOURCES", "正在搜索学习资源", 40)

            # 构建主题列表用于搜索
            topics_for_search = []
            for i, topic in enumerate(saved_topics[:3]):  # 最多处理前3个主题
                topics_for_search.append({
                    'id': i + 1,
                    'normalized': topic,
                    'keywords': [topic]
                })

            # 使用新的SearchService批量搜索
            search_results = await self.search_service.search_for_topics(
                topics_for_search,
                max_resources_per_topic=settings.MAX_RESOURCES_PER_TOPIC
            )
            logger.info(f"Found {len(search_results)} total resources from search")

            # 按主题分组评估资源
            all_evaluated_resources = []
            for topic in saved_topics[:3]:
                # 筛选属于当前主题的资源
                topic_resources = [r for r in search_results if r.get('topic_id') and
                                   topics_for_search[r['topic_id']-1]['normalized'] == topic]

                if topic_resources:
                    try:
                        # 评估资源
                        evaluated = await self.resource_evaluator.evaluate(topic_resources, topic, task_id)
                        resources_list = evaluated.get("resources", [])

                        # 为每个资源添加 topic 信息
                        for res in resources_list:
                            res["topic"] = topic

                        all_evaluated_resources.extend(resources_list)
                        logger.info(f"Evaluated {len(resources_list)} resources for topic: {topic}")
                    except Exception as e:
                        logger.error(f"Failed to evaluate resources for topic {topic}: {e}")
                        continue

            logger.info(f"Total evaluated resources: {len(all_evaluated_resources)}")

            # 7. 保存资源
            await self.update_task_status(task_id, "SAVING_RESOURCES", "正在保存资源", 60)
            saved_resources = []
            for resource in all_evaluated_resources[:20]:  # 最多保存20个资源
                if not resource.get("title") or not resource.get("url"):
                    logger.warning(f"Skipping resource with empty title or url: {resource}")
                    continue

                quality_score = resource.get("quality_score", 7)

                db_resource = Resource(
                    task_id=task_id,
                    topic_id=None,
                    user_id=task.user_id,
                    title=resource.get("title", ""),
                    url=resource.get("url", ""),
                    source="tavily",
                    resource_type="article",
                    summary=resource.get("summary", ""),
                    reason=resource.get("reason", ""),
                    difficulty=resource.get("difficulty_level", "中等"),
                    estimated_minutes=30,
                    relevance_score=quality_score * 10,
                    quality_score=quality_score * 10,
                    practical_score=quality_score * 10,
                    final_score=quality_score * 10,
                )
                self.db.add(db_resource)
                await self.db.flush()
                saved_resources.append(db_resource)

            await self.db.commit()
            logger.info(f"Saved {len(saved_resources)} resources")

            # 8. 生成学习路径
            await self.update_task_status(task_id, "GENERATING_LEARNING_PATH", "正在生成学习路径", 75)
            learning_path_data = await self.learning_path_generator.generate(saved_topics, task_id)

            stages = learning_path_data.get("stages", [])
            if not stages:
                raise Exception("No learning path stages generated")

            db_learning_path = LearningPath(
                task_id=task_id,
                user_id=task.user_id,
                title=f"{saved_topics[0] if saved_topics else '学习'}路径",
                description=f"系统为您生成的{', '.join(saved_topics[:3])}学习路径",
                stages=stages,
            )
            self.db.add(db_learning_path)
            await self.db.commit()
            logger.info(f"Learning path saved with {len(stages)} stages")

            # 9. 生成练习任务
            await self.update_task_status(task_id, "GENERATING_PRACTICE_TASKS", "正在生成练习任务", 90)
            practice_tasks_data = await self.practice_task_generator.generate(saved_topics, task_id)

            tasks_list = practice_tasks_data.get("tasks", [])
            for practice_task in tasks_list:
                task_text = practice_task.get("task_text", "")
                if not task_text:
                    logger.warning(f"Skipping practice task with empty task_text: {practice_task}")
                    continue

                db_practice_task = PracticeTask(
                    task_id=task_id,
                    topic_id=None,
                    user_id=task.user_id,
                    task_text=task_text,
                    reference_answer="",
                    difficulty=practice_task.get("difficulty", "中等"),
                    task_type="concept_question",
                )
                self.db.add(db_practice_task)

            await self.db.commit()
            logger.info(f"Saved {len(tasks_list)} practice tasks")

            # 10. 完成
            await self.update_task_status(task_id, "COMPLETED", "推荐完成", 100)

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
