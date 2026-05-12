import hashlib
import json
import logging
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis缓存服务"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False

    async def initialize(self):
        """初始化Redis连接"""
        if self._initialized:
            return

        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # 测试连接
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {str(e)}. Cache will be disabled.")
            self.redis_client = None
            self._initialized = False

    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False

    def _generate_key(self, prefix: str, data: str) -> str:
        """生成缓存key（使用hash避免key过长）"""
        hash_value = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{hash_value}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._initialized or not self.redis_client:
            return None

        try:
            import time
            start = time.time()
            value = await self.redis_client.get(key)
            duration = time.time() - start

            if value:
                ttl = await self.redis_client.ttl(key)
                logger.info(f"cache_hit=true cache_key={key} ttl={ttl}s read_time={duration*1000:.2f}ms")
                return json.loads(value)
            logger.info(f"cache_hit=false cache_key={key} read_time={duration*1000:.2f}ms")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        if not self._initialized or not self.redis_client:
            return

        try:
            import time
            start = time.time()
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            duration = time.time() - start
            logger.info(f"cache_set cache_key={key} ttl={ttl}s write_time={duration*1000:.2f}ms")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")

    async def get_search_cache(self, query: str, provider: str = "", region: str = "") -> Optional[list]:
        """获取搜索结果缓存"""
        cache_key = f"{provider}|{region}|{query}"
        key = self._generate_key("search", cache_key)
        return await self.get(key)

    async def set_search_cache(self, query: str, results: list, ttl: int = 3600, provider: str = "", region: str = ""):
        """设置搜索结果缓存（默认1小时）"""
        cache_key = f"{provider}|{region}|{query}"
        key = self._generate_key("search", cache_key)
        await self.set(key, results, ttl)

    async def get_topic_cache(self, user_input: str, topic: str) -> Optional[dict]:
        """获取主题标准化缓存"""
        cache_key = f"{user_input}|{topic}"
        key = self._generate_key("topic", cache_key)
        return await self.get(key)

    async def set_topic_cache(self, user_input: str, topic: str, normalized: dict, ttl: int = 7200):
        """设置主题标准化缓存（默认2小时）"""
        cache_key = f"{user_input}|{topic}"
        key = self._generate_key("topic", cache_key)
        await self.set(key, normalized, ttl)

    async def get_resource_evaluation_cache(self, url: str) -> Optional[dict]:
        """获取资源评估缓存"""
        key = self._generate_key("eval", url)
        return await self.get(key)

    async def set_resource_evaluation_cache(self, url: str, evaluation: dict, ttl: int = 86400):
        """设置资源评估缓存（默认24小时）"""
        key = self._generate_key("eval", url)
        await self.set(key, evaluation, ttl)


# 全局缓存实例
cache_service = CacheService()
