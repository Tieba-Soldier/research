from typing import List, Dict, Any
from app.core.config import settings
from app.core.exceptions import SearchException
from app.core.retry import api_retry
from app.tools.search_provider import SearchResult
import asyncio


class TavilyTool:
    def __init__(self):
        if not settings.TAVILY_API_KEY:
            raise SearchException("TAVILY_API_KEY not configured")
        self.api_key = settings.TAVILY_API_KEY

    def get_provider_name(self) -> str:
        """获取provider名称"""
        return "tavily"

    @api_retry
    async def search(self, query: str, max_results: int = 5, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        搜索资源
        返回统一格式的搜索结果
        """
        if not settings.ENABLE_TAVILY:
            return []

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.api_key)

            # 在线程池中运行同步调用，添加超时控制
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.search,
                    query=query,
                    max_results=max_results,
                    search_depth="basic",
                    include_answer=False,
                ),
                timeout=timeout
            )

            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    score=item.get("score", 0.0),
                    source=self._extract_domain(item.get("url", "")),
                    provider="tavily",
                    language=None,
                    published_at=item.get("published_date"),
                    raw=item,
                )
                results.append(result.to_dict())

            return results

        except asyncio.TimeoutError:
            raise SearchException(f"Tavily search timeout after {timeout}s for query: {query}")
        except Exception as e:
            raise SearchException(f"Tavily search failed: {str(e)}")

    def _extract_domain(self, url: str) -> str:
        """从 URL 中提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
