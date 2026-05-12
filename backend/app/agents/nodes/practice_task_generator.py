from typing import List, Dict, Any
from pathlib import Path
import json
import logging
from app.tools.llm_client import LLMClient
from app.schemas.llm_outputs import PracticeTaskOutput
from app.utils.llm_fallback import LLMFallback

logger = logging.getLogger(__name__)


class PracticeTaskGenerator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "practice_task_generator.md"
        return prompt_path.read_text(encoding="utf-8")

    async def generate(self, topics: List[Dict[str, Any]], task_id: int = None) -> List[Dict[str, Any]]:
        """生成练习任务"""
        topic_payload = [
            {
                "id": topic.get("id"),
                "topic": str(
                    topic.get("normalized")
                    or topic.get("normalized_topic")
                    or topic.get("original")
                    or topic.get("raw_text")
                    or ""
                ).strip(),
            }
            for topic in topics
        ]
        topic_payload = [topic for topic in topic_payload if topic["topic"]]

        prompt = self.prompt_template.replace(
            "{{topics}}",
            json.dumps(topic_payload, ensure_ascii=False, indent=2)
        )

        # 兜底数据
        fallback_data = LLMFallback.practice_tasks(
            topic_payload[0]["topic"] if topic_payload else "学习主题"
        )

        try:
            result = await self.llm_client.generate_json(
                prompt,
                schema=PracticeTaskOutput,
                fallback_data=fallback_data,
                node_name=f"PracticeTaskGenerator[task={task_id}]",
                timeout=30
            )
            logger.info(
                f"[task={task_id}] Practice tasks generated successfully: "
                f"{len(result.get('tasks', []))} tasks"
            )
            return self._normalize_tasks(topic_payload, result.get("tasks", []))
        except Exception as e:
            logger.error(f"[task={task_id}] Practice task generation failed: {e}, using fallback")
            return self._normalize_tasks(topic_payload, fallback_data.get("tasks", []))

    def _normalize_tasks(
        self,
        topics: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not topics:
            topics = [{"id": None, "topic": "学习主题"}]

        normalized_tasks = []
        for index, task in enumerate(tasks):
            topic = topics[index % len(topics)]
            topic_name = topic["topic"]
            task_text = str(task.get("task_text") or "").strip()
            if not task_text:
                continue

            normalized_tasks.append(
                {
                    "topic_id": topic.get("id"),
                    "task_text": task_text,
                    "reference_answer": (
                        f"请结合 {topic_name} 的推荐资源，总结关键概念、实现思路和常见坑点。"
                    ),
                    "difficulty": self._normalize_difficulty(task.get("difficulty")),
                    "task_type": self._infer_task_type(task_text),
                }
            )

        return normalized_tasks

    def _normalize_difficulty(self, difficulty: Any) -> str:
        value = str(difficulty or "").strip().lower()
        if value in {"简单", "basic", "easy"}:
            return "basic"
        if value in {"困难", "高级", "advanced", "hard"}:
            return "advanced"
        return "medium"

    def _infer_task_type(self, task_text: str) -> str:
        if any(keyword in task_text for keyword in ["实现", "编写", "代码", "项目"]):
            return "coding_task"
        if any(keyword in task_text for keyword in ["分析", "对比", "设计", "优化"]):
            return "analysis_question"
        return "concept_question"
