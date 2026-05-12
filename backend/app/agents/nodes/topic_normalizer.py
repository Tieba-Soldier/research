from typing import List, Dict, Any
from pathlib import Path
import json
import logging
from app.tools.llm_client import LLMClient
from app.agents.schemas import TopicNormalizerOutput

logger = logging.getLogger(__name__)


class TopicNormalizer:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "topic_normalizer.md"
        return prompt_path.read_text(encoding="utf-8")

    async def normalize(self, topics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """标准化学习主题"""
        # 从 TopicExtractor 输出中提取主题列表
        source_topics = topics_data.get("topics", [])
        normalized_source_topics = [
            self._normalize_source_topic(topic)
            for topic in source_topics
        ]
        normalized_source_topics = [topic for topic in normalized_source_topics if topic["normalized"]]
        main_topic = topics_data.get("main_topic", "") or (
            normalized_source_topics[0]["normalized"] if normalized_source_topics else ""
        )

        prompt = self.prompt_template.replace(
            "{{topics}}",
            json.dumps(
                {"topics": normalized_source_topics, "main_topic": main_topic},
                ensure_ascii=False,
                indent=2
            )
        )

        # 兜底数据：如果 LLM 失败，返回基本的标准化主题
        fallback_data = {
            "normalized_topics": normalized_source_topics
        }

        try:
            result = await self.llm_client.generate_json(
                prompt,
                schema=TopicNormalizerOutput,
                fallback_data=fallback_data
            )
            logger.info(f"Topic normalization successful: {len(result.get('normalized_topics', []))} topics")
            normalized_topics = result.get("normalized_topics", [])
            merged_topics = [
                self._merge_topic_defaults(topic)
                for topic in normalized_topics
            ]
            return [topic for topic in merged_topics if topic.get("normalized")]
        except Exception as e:
            logger.error(f"Topic normalization failed: {e}, using fallback")
            return fallback_data["normalized_topics"]

    def _normalize_source_topic(self, topic: Any) -> Dict[str, Any]:
        """把提取阶段的主题统一成服务层使用的字段。"""
        if isinstance(topic, str):
            original = topic.strip()
            normalized = original
            priority_value = None
        else:
            original = str(topic.get("original") or topic.get("raw_text") or "").strip()
            normalized = str(topic.get("normalized") or topic.get("normalized_topic") or original).strip()
            priority_value = topic.get("priority")

        return {
            "original": original or normalized,
            "normalized": normalized or original,
            "category": "other",
            "priority": self._normalize_priority(priority_value),
            "reason": "自动标准化主题",
            "keywords": [normalized or original] if (normalized or original) else [],
        }

    def _merge_topic_defaults(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        merged = {
            "original": str(topic.get("original") or topic.get("raw_text") or "").strip(),
            "normalized": str(topic.get("normalized") or topic.get("normalized_topic") or "").strip(),
            "category": str(topic.get("category") or "other").strip() or "other",
            "priority": self._normalize_priority(topic.get("priority")),
            "reason": str(topic.get("reason") or "自动标准化主题").strip() or "自动标准化主题",
            "keywords": [
                str(keyword).strip()
                for keyword in topic.get("keywords", [])
                if str(keyword).strip()
            ],
        }

        if not merged["original"]:
            merged["original"] = merged["normalized"]
        if not merged["normalized"]:
            merged["normalized"] = merged["original"]
        if not merged["keywords"] and merged["normalized"]:
            merged["keywords"] = [merged["normalized"]]
        return merged

    def _normalize_priority(self, value: Any) -> str:
        if isinstance(value, int):
            if value >= 8:
                return "high"
            if value >= 4:
                return "medium"
            return "low"

        normalized = str(value or "").strip().lower()
        if normalized in {"high", "medium", "low"}:
            return normalized
        return "medium"
