from typing import List, Dict, Any
from app.agents.nodes.user_need_analyzer import UserNeedAnalyzer
from app.agents.nodes.topic_extractor import TopicExtractor
from app.agents.nodes.topic_normalizer import TopicNormalizer
import logging
import time

logger = logging.getLogger(__name__)


class TopicService:
    """主题服务：负责用户需求分析、主题提取、主题标准化"""

    def __init__(self):
        self.user_need_analyzer = UserNeedAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.topic_normalizer = TopicNormalizer()

    async def analyze_and_extract_topics(
        self,
        user_input: str,
        max_topics: int = 5
    ) -> Dict[str, Any]:
        """
        分析用户需求并提取标准化主题

        Returns:
            {
                "user_need": {...},
                "topics": [
                    {
                        "original": "原始主题",
                        "normalized": "标准化主题",
                        "category": "分类",
                        "priority": "优先级",
                        "reason": "原因",
                        "keywords": ["关键词1", "关键词2"]
                    }
                ]
            }
        """
        start_time = time.time()

        try:
            # 1. 分析用户需求
            logger.info(f"Analyzing user need: {user_input[:50]}...")
            need_start = time.time()
            user_need = await self.user_need_analyzer.analyze(user_input)
            need_duration = time.time() - need_start
            logger.info(f"User need analysis completed in {need_duration:.2f}s")

            # 2. 提取主题
            logger.info("Extracting topics...")
            extract_start = time.time()
            topics_data = await self.topic_extractor.extract(user_input)
            extract_duration = time.time() - extract_start
            logger.info(
                f"Extracted {len(topics_data.get('topics', []))} topics in {extract_duration:.2f}s"
            )

            # 3. 标准化主题
            logger.info("Normalizing topics...")
            normalize_start = time.time()
            normalized_topics = await self.topic_normalizer.normalize(topics_data)
            normalize_duration = time.time() - normalize_start
            logger.info(f"Normalized {len(normalized_topics)} topics in {normalize_duration:.2f}s")

            # 限制主题数量
            normalized_topics = normalized_topics[:max_topics]

            total_duration = time.time() - start_time
            logger.info(
                f"Topic service completed in {total_duration:.2f}s "
                f"(analyze: {need_duration:.2f}s, extract: {extract_duration:.2f}s, "
                f"normalize: {normalize_duration:.2f}s)"
            )

            return {
                "user_need": user_need,
                "topics": normalized_topics,
                "metrics": {
                    "total_duration": total_duration,
                    "analyze_duration": need_duration,
                    "extract_duration": extract_duration,
                    "normalize_duration": normalize_duration,
                    "topic_count": len(normalized_topics)
                }
            }

        except Exception as e:
            logger.error(f"Topic service failed: {str(e)}", exc_info=True)
            raise
