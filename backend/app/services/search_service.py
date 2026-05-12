from typing import List, Dict, Any
import asyncio
import logging
import time
from app.tools.search_provider_factory import get_primary_provider, get_fallback_provider_instance
from app.core.config import settings
from app.core.exceptions import SearchException
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务：负责搜索query生成、多Provider搜索、结果去重"""

    def __init__(self):
        self.primary_provider = get_primary_provider()
        self.fallback_provider = None
        self.cache = cache_service
        logger.info(f"SearchService initialized with provider: {self.primary_provider.get_provider_name()}")

    async def search_for_topics(
        self,
        topics: List[Dict[str, Any]],
        max_resources_per_topic: int = 5
    ) -> List[Dict[str, Any]]:
        """
        为多个主题并发搜索资源

        Args:
            topics: 主题列表，每个主题包含 id, normalized, keywords
            max_resources_per_topic: 每个主题最多返回的资源数

        Returns:
            资源列表，每个资源包含 topic_id, title, url, summary, source, resource_type
        """
        start_time = time.time()
        logger.info(f"Starting search for {len(topics)} topics")

        # 并发搜索所有主题
        search_tasks = [
            self._search_single_topic(topic, max_resources_per_topic)
            for topic in topics
        ]

        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 收集所有成功的结果
        all_resources = []
        failed_topics = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                topic_name = topics[i].get("normalized", "Unknown")
                logger.error(f"Search failed for topic '{topic_name}': {str(result)}")
                failed_topics.append(topic_name)
            else:
                all_resources.extend(result)

        # 去重
        unique_resources = self._deduplicate_resources(all_resources)

        duration = time.time() - start_time
        logger.info(
            f"Search completed in {duration:.2f}s: "
            f"{len(unique_resources)} unique resources from {len(topics)} topics "
            f"({len(failed_topics)} topics failed)"
        )

        return unique_resources

    async def _search_single_topic(
        self,
        topic: Dict[str, Any],
        max_resources: int
    ) -> List[Dict[str, Any]]:
        """搜索单个主题的资源"""
        topic_id = topic.get("id")
        normalized_topic = topic.get("normalized", "")
        keywords = topic.get("keywords", [])

        logger.info(f"Searching for topic: {normalized_topic}")

        # 生成搜索查询
        search_queries = self._generate_search_queries(normalized_topic, keywords)

        # 限制查询数量
        search_queries = search_queries[:settings.MAX_SEARCH_QUERIES_PER_TOPIC]

        resources = []

        for query in search_queries:
            try:
                # 获取provider名称用于缓存
                provider_name = self.primary_provider.get_provider_name()

                # 尝试从缓存获取
                cached_results = await self.cache.get_search_cache(
                    query,
                    provider=provider_name,
                    region=settings.SEARCH_REGION
                )

                if cached_results:
                    logger.info(f"Using cached results for query: {query} (provider: {provider_name})")
                    results = cached_results
                    actual_provider = provider_name  # 缓存命中，使用主provider名称
                else:
                    # 缓存未命中，调用API（带fallback）
                    results, actual_provider = await self._search_with_fallback(query, max_resources)

                    # 使用实际provider名称缓存结果
                    await self.cache.set_search_cache(
                        query,
                        results,
                        provider=actual_provider,
                        region=settings.SEARCH_REGION
                    )
                    logger.info(f"Found {len(results)} resources for query: {query} (provider: {actual_provider})")

                for result in results:
                    resources.append({
                        "topic_id": topic_id,
                        "title": result["title"],
                        "url": result["url"],
                        "summary": result["snippet"],
                        "source": result["source"],
                        "resource_type": self._infer_resource_type(result["url"], result["title"]),
                        "raw_score": result.get("score", 0.0),
                    })

            except SearchException as e:
                logger.warning(f"Search failed for query '{query}': {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error searching '{query}': {str(e)}")
                continue

        logger.info(f"Topic '{normalized_topic}' search completed: {len(resources)} resources")
        return resources

    def _generate_search_queries(
        self,
        normalized_topic: str,
        keywords: List[str]
    ) -> List[str]:
        """生成搜索查询，支持中文资源导向"""
        queries = []

        # 判断是否为国内搜索模式
        is_cn_mode = settings.SEARCH_REGION in ["cn", "hybrid"]

        # 主查询：标准化主题
        if normalized_topic:
            queries.append(normalized_topic)

            # 国内模式：添加中文导向查询
            if is_cn_mode:
                queries.extend(self._generate_cn_queries(normalized_topic))

        # 关键词查询
        for keyword in keywords[:3]:  # 最多3个关键词
            if keyword and keyword != normalized_topic:
                queries.append(keyword)

        # 如果没有查询，使用关键词组合
        if not queries and keywords:
            queries.append(" ".join(keywords[:2]))

        return queries

    def _generate_cn_queries(self, topic: str) -> List[str]:
        """
        为主题生成中文导向的搜索查询
        根据主题特征智能选择查询类型

        Args:
            topic: 标准化主题

        Returns:
            中文导向查询列表
        """
        cn_queries = []
        topic_lower = topic.lower()

        # 判断主题类型，优先生成最相关的查询
        is_framework = any(kw in topic_lower for kw in ['spring', 'django', 'react', 'vue', 'angular'])
        is_database = any(kw in topic_lower for kw in ['mysql', 'redis', 'mongodb', 'postgresql'])
        is_language = any(kw in topic_lower for kw in ['python', 'java', 'javascript', 'go', 'rust'])
        is_tool = any(kw in topic_lower for kw in ['docker', 'kubernetes', 'git', 'nginx'])

        # 基础查询：教程和文档（所有主题都需要）
        cn_queries.append(f"{topic} 教程")
        cn_queries.append(f"{topic} 中文文档")

        # 根据主题类型添加特定查询
        if is_framework or is_tool:
            # 框架和工具：优先实战和官方文档
            cn_queries.append(f"{topic} 实战")
            cn_queries.append(f"{topic} 官方文档")
        elif is_database:
            # 数据库：优先实战和优化
            cn_queries.append(f"{topic} 实战")
            cn_queries.append(f"{topic} 优化")
        elif is_language:
            # 编程语言：优先入门和进阶
            cn_queries.append(f"{topic} 入门")
            cn_queries.append(f"{topic} 进阶")
        else:
            # 其他主题：实战和平台导向
            cn_queries.append(f"{topic} 实战")
            cn_queries.append(f"{topic} B站")

        # 返回前4个查询（不再硬截断为3个）
        return cn_queries[:4]

    def _infer_resource_type(self, url: str, title: str) -> str:
        """推断资源类型，增强国内站点识别"""
        text = f"{url} {title}".lower()

        # 视频类
        if "youtube.com" in text or "youtu.be" in text or "bilibili.com" in text:
            return "video"

        # 代码仓库类
        if "github.com" in text or "gitee.com" in text:
            return "github"

        # 官方文档类
        if any(domain in text for domain in [
            "docs.",
            "documentation",
            "developer.mozilla.org",
            "cloud.tencent.com",
            "developer.aliyun.com",
            "huaweicloud.com",
            "volcengine.com"
        ]) or "官方文档" in title:
            return "official_doc"

        # 文章/博客类
        if any(keyword in text for keyword in [
            "blog",
            "juejin.cn",
            "csdn.net",
            "zhihu.com",
            "segmentfault.com",
            "infoq.cn"
        ]) or any(keyword in title for keyword in ["文章", "教程", "博客"]):
            return "article"

        return "article"

    def _deduplicate_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重资源（按URL）"""
        seen_urls = set()
        unique_resources = []

        for resource in resources:
            url = resource["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_resources.append(resource)

        logger.info(f"Deduplicated: {len(resources)} -> {len(unique_resources)} resources")
        return unique_resources

    async def _search_with_fallback(self, query: str, max_results: int) -> tuple[List[Dict[str, Any]], str]:
        """
        使用主provider搜索，失败时自动fallback到备用provider

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            (搜索结果列表, 实际使用的provider名称)
        """
        try:
            # 尝试使用主provider
            results = await self.primary_provider.search(query, max_results)
            provider_name = self.primary_provider.get_provider_name()
            logger.info(f"Primary provider ({provider_name}) search succeeded")
            return results, provider_name

        except Exception as e:
            logger.warning(
                f"Primary provider ({self.primary_provider.get_provider_name()}) failed: {str(e)}, "
                f"trying fallback"
            )

            # 初始化fallback provider（延迟加载）
            if not self.fallback_provider:
                try:
                    self.fallback_provider = get_fallback_provider_instance()
                    logger.info(f"Fallback provider initialized: {self.fallback_provider.get_provider_name()}")
                except Exception as fallback_init_error:
                    logger.error(f"Failed to initialize fallback provider: {str(fallback_init_error)}")
                    raise SearchException(f"Both primary and fallback provider initialization failed")

            # 尝试使用fallback provider
            try:
                results = await self.fallback_provider.search(query, max_results)
                provider_name = self.fallback_provider.get_provider_name()
                logger.info(f"Fallback provider ({provider_name}) search succeeded")
                return results, provider_name
            except Exception as fallback_error:
                logger.error(f"Fallback provider also failed: {str(fallback_error)}")
                raise SearchException(f"All search providers failed for query: {query}")

