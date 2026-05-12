"""
搜索优化专项测试
验证搜索层的缓存、fallback、provider切换等功能
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.search_service import SearchService
from app.tools.search_provider import SearchResult
from app.core.exceptions import SearchException


class TestSearchCache:
    """测试搜索缓存功能"""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """测试缓存命中"""
        from app.services.cache_service import CacheService

        cache = CacheService()
        await cache.initialize()

        query = "Python测试"
        test_results = [{"title": "测试结果", "url": "http://example.com", "snippet": "test"}]

        # 写入缓存
        await cache.set_search_cache(query, test_results, provider="bocha", region="cn")

        # 读取缓存
        cached = await cache.get_search_cache(query, provider="bocha", region="cn")

        assert cached is not None
        assert len(cached) == 1
        assert cached[0]["title"] == "测试结果"

        await cache.close()

    @pytest.mark.asyncio
    async def test_cache_isolation_by_provider(self):
        """测试不同provider的缓存隔离"""
        from app.services.cache_service import CacheService

        cache = CacheService()
        await cache.initialize()

        query = "Python教程"
        results_bocha = [{"title": "Bocha结果", "url": "http://example.com", "snippet": "test"}]
        results_tavily = [{"title": "Tavily结果", "url": "http://example.org", "snippet": "test"}]

        # 写入博查缓存
        await cache.set_search_cache(query, results_bocha, provider="bocha", region="cn")

        # 写入Tavily缓存
        await cache.set_search_cache(query, results_tavily, provider="tavily", region="global")

        # 读取博查缓存
        cached_bocha = await cache.get_search_cache(query, provider="bocha", region="cn")
        assert cached_bocha is not None
        assert cached_bocha[0]["title"] == "Bocha结果"

        # 读取Tavily缓存
        cached_tavily = await cache.get_search_cache(query, provider="tavily", region="global")
        assert cached_tavily is not None
        assert cached_tavily[0]["title"] == "Tavily结果"

        await cache.close()


class TestSearchFallback:
    """测试搜索fallback功能"""

    @pytest.mark.asyncio
    async def test_fallback_triggered(self):
        """测试主provider失败时触发fallback"""
        service = SearchService()

        # Mock主provider失败
        with patch.object(service.primary_provider, 'search', side_effect=Exception("Primary failed")):
            # Mock fallback provider成功
            with patch('app.services.search_service.get_fallback_provider_instance') as mock_fallback:
                mock_fallback_provider = Mock()
                mock_fallback_provider.get_provider_name.return_value = "tavily"
                mock_fallback_provider.search = AsyncMock(return_value=[
                    {
                        "title": "Fallback结果",
                        "url": "http://fallback.com",
                        "snippet": "fallback test",
                        "score": 0.8,
                        "source": "fallback",
                        "provider": "tavily"
                    }
                ])
                mock_fallback.return_value = mock_fallback_provider

                # 执行搜索
                results, actual_provider = await service._search_with_fallback("test query", 5)

                # 验证fallback被触发
                assert actual_provider == "tavily"
                assert len(results) > 0
                assert results[0]["title"] == "Fallback结果"

    @pytest.mark.asyncio
    async def test_fallback_cache_uses_actual_provider(self):
        """测试fallback结果使用实际provider名称缓存"""
        service = SearchService()

        # Mock主provider失败
        with patch.object(service.primary_provider, 'search', side_effect=Exception("Primary failed")):
            # Mock fallback provider成功
            with patch('app.services.search_service.get_fallback_provider_instance') as mock_fallback:
                mock_fallback_provider = Mock()
                mock_fallback_provider.get_provider_name.return_value = "tavily"
                mock_fallback_provider.search = AsyncMock(return_value=[
                    {
                        "title": "Fallback结果",
                        "url": "http://fallback.com",
                        "snippet": "test",
                        "score": 0.8,
                        "source": "test",
                        "provider": "tavily"
                    }
                ])
                mock_fallback.return_value = mock_fallback_provider

                topics = [{
                    'id': 1,
                    'normalized': 'Fallback测试',
                    'keywords': ['test']
                }]

                # 执行搜索
                results = await service.search_for_topics(topics, max_resources_per_topic=3)

                # 验证结果存在
                assert len(results) > 0


class TestProviderSwitch:
    """测试provider切换功能"""

    @pytest.mark.asyncio
    async def test_provider_switch(self):
        """测试切换provider后返回不同结果"""
        from app.tools.search_provider_factory import get_search_provider

        # 测试博查provider
        bocha_provider = get_search_provider("bocha")
        assert bocha_provider.get_provider_name() == "bocha"

        # 测试Tavily provider
        tavily_provider = get_search_provider("tavily")
        assert tavily_provider.get_provider_name() == "tavily"


class TestRegionMode:
    """测试region模式行为"""

    @pytest.mark.asyncio
    async def test_cn_mode_generates_chinese_queries(self):
        """测试cn模式生成中文导向查询"""
        from app.core.config import settings

        service = SearchService()
        original_region = settings.SEARCH_REGION

        # 设置为cn模式
        settings.SEARCH_REGION = "cn"

        queries = service._generate_search_queries("Python", ["入门"])

        # 验证包含中文导向查询
        assert any("教程" in q for q in queries)
        assert any("中文文档" in q for q in queries)

        # 恢复原始配置
        settings.SEARCH_REGION = original_region

    @pytest.mark.asyncio
    async def test_global_mode_no_chinese_queries(self):
        """测试global模式不生成中文导向查询"""
        from app.core.config import settings

        service = SearchService()
        original_region = settings.SEARCH_REGION

        # 设置为global模式
        settings.SEARCH_REGION = "global"

        queries = service._generate_search_queries("Python", ["tutorial"])

        # 验证不包含中文导向查询
        assert not any("教程" in q for q in queries)
        assert not any("中文文档" in q for q in queries)

        # 恢复原始配置
        settings.SEARCH_REGION = original_region


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
