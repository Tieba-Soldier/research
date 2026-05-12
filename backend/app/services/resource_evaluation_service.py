from typing import List, Dict, Any
import asyncio
import logging
import time
from app.agents.nodes.resource_evaluator import ResourceEvaluator
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class ResourceEvaluationService:
    """资源评估服务：负责资源评分和推荐理由生成"""

    def __init__(self):
        self.evaluator = ResourceEvaluator()
        self.cache = cache_service

    async def evaluate_resources(
        self,
        resources: List[Dict[str, Any]],
        user_context: str
    ) -> List[Dict[str, Any]]:
        """
        批量评估资源

        Args:
            resources: 资源列表
            user_context: 用户学习上下文

        Returns:
            评估后的资源列表，包含评分和推荐理由
        """
        start_time = time.time()
        logger.info(f"Starting evaluation for {len(resources)} resources")

        # 并发评估所有资源
        evaluation_tasks = [
            self._evaluate_single_resource(resource, user_context)
            for resource in resources
        ]

        results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

        # 收集结果
        evaluated_resources = []
        failed_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Evaluation failed for resource {resources[i].get('url', '')}: {str(result)}")
                # 使用默认评分作为降级
                evaluated_resources.append(self._create_default_evaluation(resources[i]))
                failed_count += 1
            else:
                evaluated_resources.append(result)

        duration = time.time() - start_time
        logger.info(
            f"Evaluation completed in {duration:.2f}s: "
            f"{len(evaluated_resources)} resources evaluated "
            f"({failed_count} used default scores)"
        )

        return evaluated_resources

    async def _evaluate_single_resource(
        self,
        resource: Dict[str, Any],
        user_context: str
    ) -> Dict[str, Any]:
        """评估单个资源"""
        url = resource.get("url", "")

        try:
            # 尝试从缓存获取
            cached_evaluation = await self.cache.get_resource_evaluation_cache(url)

            if cached_evaluation:
                logger.info(f"Using cached evaluation for: {url}")
                # 合并原始资源数据
                return {**resource, **cached_evaluation}

            # 缓存未命中，调用评估
            evaluated = await self.evaluator.evaluate(resource, user_context)

            # 计算最终得分
            final_score = self.evaluator.calculate_final_score(evaluated)
            evaluated["final_score"] = final_score

            # 缓存评估结果（只缓存评估相关字段）
            cache_data = {
                "summary": evaluated.get("summary"),
                "reason": evaluated.get("reason"),
                "difficulty": evaluated.get("difficulty"),
                "estimated_minutes": evaluated.get("estimated_minutes"),
                "relevance_score": evaluated.get("relevance_score"),
                "quality_score": evaluated.get("quality_score"),
                "practical_score": evaluated.get("practical_score"),
                "final_score": final_score
            }
            await self.cache.set_resource_evaluation_cache(url, cache_data)

            return evaluated

        except Exception as e:
            logger.error(f"Failed to evaluate resource {url}: {str(e)}")
            raise

    def _create_default_evaluation(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认评估结果（降级方案）"""
        return {
            **resource,
            "summary": resource.get("summary", "暂无摘要"),
            "reason": "该资源与学习主题相关，建议查看",
            "difficulty": "medium",
            "estimated_minutes": 30,
            "relevance_score": 70.0,
            "quality_score": 70.0,
            "practical_score": 70.0,
            "final_score": 70.0
        }
