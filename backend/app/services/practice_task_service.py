from typing import List, Dict, Any
import logging
import time
from app.agents.nodes.practice_task_generator import PracticeTaskGenerator

logger = logging.getLogger(__name__)


class PracticeTaskService:
    """练习任务服务：负责练习任务生成"""

    def __init__(self):
        self.generator = PracticeTaskGenerator()

    async def generate_practice_tasks(
        self,
        topics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        生成练习任务

        Args:
            topics: 主题列表

        Returns:
            练习任务列表
        """
        start_time = time.time()
        logger.info(f"Generating practice tasks for {len(topics)} topics")

        try:
            practice_tasks = await self.generator.generate(topics)

            duration = time.time() - start_time
            logger.info(f"Generated {len(practice_tasks)} practice tasks in {duration:.2f}s")

            return practice_tasks

        except Exception as e:
            logger.error(f"Practice task generation failed: {str(e)}", exc_info=True)
            # 使用兜底任务
            logger.warning("Using fallback practice tasks")
            return self._create_fallback_tasks(topics)

    def _create_fallback_tasks(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """创建兜底练习任务"""
        fallback_tasks = []

        for topic in topics:
            topic_id = topic.get("id")
            normalized = (
                topic.get("normalized")
                or topic.get("normalized_topic")
                or topic.get("raw_text")
                or "该主题"
            )

            # 为每个主题生成3个基础任务
            fallback_tasks.extend([
                {
                    "topic_id": topic_id,
                    "task_text": f"请简述{normalized}的核心概念和主要应用场景",
                    "reference_answer": f"请根据学习资源总结{normalized}的定义、特点和使用场景",
                    "difficulty": "basic",
                    "task_type": "concept_question"
                },
                {
                    "topic_id": topic_id,
                    "task_text": f"请实现一个使用{normalized}的简单示例",
                    "reference_answer": f"参考学习资源中的示例代码，实现一个基础功能",
                    "difficulty": "medium",
                    "task_type": "coding_task"
                },
                {
                    "topic_id": topic_id,
                    "task_text": f"请分析在实际项目中使用{normalized}时需要注意哪些问题",
                    "reference_answer": f"结合学习资源，总结最佳实践和常见陷阱",
                    "difficulty": "medium",
                    "task_type": "analysis_question"
                }
            ])

        logger.info(f"Created {len(fallback_tasks)} fallback practice tasks")
        return fallback_tasks
