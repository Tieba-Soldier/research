from typing import List, Dict, Any
from pathlib import Path
import logging
from app.tools.llm_client import LLMClient
from app.schemas.llm_outputs import LearningTopicOutput
from app.utils.llm_fallback import LLMFallback

logger = logging.getLogger(__name__)


class TopicExtractor:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "topic_extractor.md"
        return prompt_path.read_text(encoding="utf-8")

    async def extract(self, user_input: str, task_id: int = None) -> Dict[str, Any]:
        """从用户输入中提取学习主题"""
        prompt = self.prompt_template.replace("{{user_input}}", user_input)

        # 兜底数据
        fallback_data = LLMFallback.topic_extraction(user_input)

        try:
            result = await self.llm_client.generate_json(
                prompt,
                schema=LearningTopicOutput,
                fallback_data=fallback_data,
                node_name=f"TopicExtractor[task={task_id}]",
                timeout=30
            )
            logger.info(f"[task={task_id}] Topic extraction successful: {len(result.get('topics', []))} topics")
            return result
        except Exception as e:
            logger.error(f"[task={task_id}] Topic extraction failed: {e}, using fallback")
            return fallback_data
