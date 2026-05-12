"""
博查搜索工具
接入博查Search API作为国内主搜索源
"""
from typing import List, Dict, Any
import httpx
import asyncio
from app.core.config import settings
from app.core.exceptions import SearchException
from app.core.retry import api_retry
from app.tools.search_provider import SearchResult


class BochaTool:
    def __init__(self):
        if not settings.BOCHA_API_KEY:
            raise SearchException("BOCHA_API_KEY not configured")
        self.api_key = settings.BOCHA_API_KEY
        self.base_url = "https://api.bochaai.com/v1/web-search"

    def get_provider_name(self) -> str:
        """获取provider名称"""
        return "bocha"

    @api_retry
    async def search(self, query: str, max_results: int = 5, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        使用博查API搜索资源
        返回统一格式的搜索结果
        """
        if not settings.ENABLE_BOCHA:
            return []

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "freshness": "noLimit",
                        "summary": True,
                        "count": max_results,
                    },
                )

                if response.status_code != 200:
                    raise SearchException(
                        f"Bocha API error: {response.status_code} - {response.text}"
                    )

                data = response.json()
                results = []

                # 解析博查返回结果 - 数据在 data.webPages.value 中
                web_pages = data.get("data", {}).get("webPages", {}).get("value", [])

                for item in web_pages:
                    result = SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("summary", item.get("snippet", "")),
                        score=0.8,  # 博查不返回score，给个默认值
                        source=item.get("siteName", self._extract_domain(item.get("url", ""))),
                        provider="bocha",
                        language=self._detect_language(item.get("name", "")),
                        published_at=item.get("datePublished"),
                        raw=item,
                    )
                    results.append(result.to_dict())

                return results

        except httpx.TimeoutException:
            raise SearchException(f"Bocha search timeout after {timeout}s for query: {query}")
        except httpx.HTTPError as e:
            raise SearchException(f"Bocha HTTP error: {str(e)}")
        except Exception as e:
            raise SearchException(f"Bocha search failed: {str(e)}")

    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

    def _detect_language(self, text: str) -> str:
        """简单检测文本语言"""
        if not text:
            return "unknown"

        # 简单判断：如果包含中文字符则为中文
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return "zh"

        return "en"
