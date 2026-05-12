"""
搜索Provider抽象接口
定义统一的搜索接口和返回结构
"""
from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime


class SearchResult:
    """统一搜索结果结构"""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        score: float = 0.0,
        source: str = "",
        provider: str = "",
        language: Optional[str] = None,
        published_at: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.score = score
        self.source = source
        self.provider = provider
        self.language = language
        self.published_at = published_at
        self.raw = raw or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score,
            "source": self.source,
            "provider": self.provider,
            "language": self.language,
            "published_at": self.published_at,
            "raw": self.raw,
        }


class SearchProvider(Protocol):
    """搜索Provider协议接口"""

    async def search(
        self,
        query: str,
        max_results: int = 5,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索查询词
            max_results: 最大结果数
            timeout: 超时时间(秒)

        Returns:
            统一格式的搜索结果列表
        """
        ...

    def get_provider_name(self) -> str:
        """获取provider名称"""
        ...
