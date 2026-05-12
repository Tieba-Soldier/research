from typing import Dict, Any
from pathlib import Path
import logging
from app.tools.llm_client import LLMClient
from app.schemas.llm_outputs import UserNeedAnalysis
from app.utils.llm_fallback import LLMFallback

logger = logging.getLogger(__name__)


class UserNeedAnalyzer:
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "user_need_analyzer.md"
        return prompt_path.read_text(encoding="utf-8")

    async def analyze(self, user_input: str, task_id: int = None) -> Dict[str, Any]:
        """分析用户学习需求"""
        prompt = self.prompt_template.replace("{{user_input}}", user_input)

        # 兜底数据
        fallback_data = LLMFallback.user_need_analysis(user_input)

        try:
            result = await self.llm_client.generate_json(
                prompt,
                schema=UserNeedAnalysis,
                fallback_data=fallback_data,
                node_name=f"UserNeedAnalyzer[task={task_id}]",
                timeout=30
            )
            logger.info(f"[task={task_id}] User need analysis successful")
            return result
        except Exception as e:
            logger.error(f"[task={task_id}] User need analysis failed: {e}, using fallback")
            return fallback_data
