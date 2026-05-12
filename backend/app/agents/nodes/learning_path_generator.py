from typing import Dict, Any, List
from pathlib import Path
import json
import logging
from app.tools.llm_client import LLMClient
from app.schemas.llm_outputs import LearningPathOutput
from app.utils.llm_fallback import LLMFallback

logger = logging.getLogger(__name__)


class LearningPathGenerator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "learning_path_generator.md"
        return prompt_path.read_text(encoding="utf-8")

    async def generate(
        self,
        topics: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        task_id: int = None
    ) -> Dict[str, Any]:
        """生成学习路径"""
        topic_names = [
            str(
                topic.get("normalized")
                or topic.get("normalized_topic")
                or topic.get("original")
                or topic.get("raw_text")
                or ""
            ).strip()
            for topic in topics
        ]
        topic_names = [topic for topic in topic_names if topic]
        selected_resources = [
            {
                "id": resource.get("id"),
                "title": resource.get("title"),
                "difficulty": resource.get("difficulty"),
                "url": resource.get("url"),
            }
            for resource in resources[:6]
        ]

        logger.info(
            f"[task={task_id}] Starting learning path generation "
            f"with {len(topic_names)} topics and {len(selected_resources)} resources"
        )

        prompt = self.prompt_template.replace(
            "{{topics}}",
            json.dumps(
                {"topics": topic_names, "resources": selected_resources},
                ensure_ascii=False,
                indent=2
            )
        )

        # 兜底数据
        fallback_data = LLMFallback.learning_path(topic_names, selected_resources)

        try:
            result = await self.llm_client.generate_json(
                prompt,
                schema=LearningPathOutput,
                fallback_data=fallback_data,
                node_name=f"LearningPathGenerator[task={task_id}]",
                timeout=30
            )
            stages = result.get("stages", [])
            logger.info(
                f"[task={task_id}] Learning path generated successfully: "
                f"{len(stages)} stages"
            )
            return self._build_learning_path(topic_names, selected_resources, stages)
        except Exception as e:
            logger.error(f"[task={task_id}] Learning path generation failed: {e}, using fallback")
            return fallback_data

    def _build_learning_path(
        self,
        topics: List[str],
        resources: List[Dict[str, Any]],
        stages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not stages:
            return LLMFallback.learning_path(topics, resources)

        topic_str = "、".join(topics[:3]) if topics else "学习主题"
        enriched_stages = []

        for index, stage in enumerate(stages):
            stage_resources = resources[index::len(stages)] if resources else []
            resource_ids = [
                resource.get("id")
                for resource in stage_resources
                if resource.get("id") is not None
            ]
            stage_name = str(stage.get("stage_name") or f"阶段{index + 1}").strip()
            description = str(stage.get("description") or f"围绕{topic_str}完成{stage_name}学习").strip()
            estimated_hours = int(stage.get("estimated_hours") or 4)
            step_title = stage_name

            enriched_stages.append(
                {
                    "stage_number": int(stage.get("stage_number") or (index + 1)),
                    "stage_name": stage_name,
                    "description": description,
                    "estimated_hours": estimated_hours,
                    "steps": [
                        {
                            "step_number": 1,
                            "title": step_title,
                            "description": description,
                            "learning_goals": [description],
                            "resource_ids": resource_ids,
                            "estimated_minutes": estimated_hours * 60,
                        }
                    ],
                    "name": stage_name,
                    "goal": description,
                    "resources": resource_ids,
                    "tasks": [
                        resource.get("title", f"{stage_name}学习任务")
                        for resource in stage_resources[:3]
                    ] or [f"围绕{stage_name}完成学习与整理"],
                    "expected_output": f"完成 {stage_name} 阶段的总结、笔记或小练习",
                }
            )

        return {
            "path_name": f"{topic_str}学习路径",
            "description": f"根据学习主题和资源推荐生成的阶段化学习路径。",
            "stages": enriched_stages,
        }
