from typing import Dict, Any
from pathlib import Path
import json
import logging
from app.tools.llm_client import LLMClient
from app.schemas.llm_outputs import ResourceEvaluationOutput
from app.utils.llm_fallback import LLMFallback

logger = logging.getLogger(__name__)


class ResourceEvaluator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "resource_evaluator.md"
        return prompt_path.read_text(encoding="utf-8")

    async def evaluate(self, resource: Dict[str, Any], user_context: str, task_id: int = None) -> Dict[str, Any]:
        """评估单个资源并返回统一结构。"""
        prompt = self.prompt_template.replace(
            "{{tavily_results}}",
            json.dumps([resource], ensure_ascii=False, indent=2)
        )
        prompt = prompt.replace("{{topic}}", user_context)

        # 兜底数据
        fallback_data = LLMFallback.resource_evaluation([resource], user_context)

        try:
            result = await self.llm_client.generate_json(
                prompt,
                schema=ResourceEvaluationOutput,
                fallback_data=fallback_data,
                node_name=f"ResourceEvaluator[task={task_id}]",
                timeout=30
            )
            logger.info(
                f"[task={task_id}] Resource evaluation successful: "
                f"{len(result.get('resources', []))} resources"
            )
            return self._normalize_evaluation(resource, result.get("resources", []))
        except Exception as e:
            logger.error(f"[task={task_id}] Resource evaluation failed: {e}, using fallback")
            return self._normalize_evaluation(resource, fallback_data.get("resources", []))

    def calculate_final_score(self, evaluated_resource: Dict[str, Any]) -> float:
        relevance_score = float(evaluated_resource.get("relevance_score", 0) or 0)
        quality_score = float(evaluated_resource.get("quality_score", 0) or 0)
        practical_score = float(evaluated_resource.get("practical_score", 0) or 0)
        return round(relevance_score * 0.45 + quality_score * 0.35 + practical_score * 0.20, 2)

    def _normalize_evaluation(
        self,
        resource: Dict[str, Any],
        evaluated_resources: Any
    ) -> Dict[str, Any]:
        evaluated = evaluated_resources[0] if evaluated_resources else {}
        title = str(evaluated.get("title") or resource.get("title") or "未命名资源").strip()
        url = str(evaluated.get("url") or resource.get("url") or "").strip()
        summary = str(
            evaluated.get("summary")
            or resource.get("summary")
            or f"{title}，适合作为当前学习主题的补充材料。"
        ).strip()
        reason = str(
            evaluated.get("reason")
            or f"该资源与当前学习需求高度相关，可作为 {title} 的入门或进阶材料。"
        ).strip()

        quality_score = self._to_score_100(evaluated.get("quality_score"), default=75.0)
        relevance_score = self._calculate_relevance_score(resource)
        practical_score = self._calculate_practical_score(resource)

        return {
            **resource,
            "title": title,
            "url": url,
            "summary": summary,
            "reason": reason,
            "difficulty": self._normalize_difficulty(evaluated.get("difficulty_level")),
            "estimated_minutes": self._estimate_minutes(resource),
            "relevance_score": relevance_score,
            "quality_score": quality_score,
            "practical_score": practical_score,
        }

    def _to_score_100(self, value: Any, default: float = 70.0) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return default

        if score <= 10:
            score *= 10
        return max(0.0, min(score, 100.0))

    def _calculate_relevance_score(self, resource: Dict[str, Any]) -> float:
        raw_score = resource.get("raw_score")
        if raw_score is None:
            return 75.0

        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            return 75.0

        if score <= 1:
            score *= 100
        return round(max(0.0, min(score, 100.0)), 2)

    def _calculate_practical_score(self, resource: Dict[str, Any]) -> float:
        resource_type = str(resource.get("resource_type") or "").lower()
        if resource_type == "github":
            return 92.0
        if resource_type == "official_doc":
            return 85.0
        if resource_type == "video":
            return 78.0
        return 80.0

    def _normalize_difficulty(self, difficulty_level: Any) -> str:
        difficulty = str(difficulty_level or "").strip().lower()
        if difficulty in {"入门", "简单", "basic", "easy"}:
            return "basic"
        if difficulty in {"高级", "困难", "advanced", "hard"}:
            return "advanced"
        return "medium"

    def _estimate_minutes(self, resource: Dict[str, Any]) -> int:
        resource_type = str(resource.get("resource_type") or "").lower()
        if resource_type == "video":
            return 45
        if resource_type == "github":
            return 60
        if resource_type == "official_doc":
            return 40
        return 30
