from typing import List, Dict, Any


class FirecrawlTool:
    """Firecrawl 网页抓取工具（第一版预留接口）"""

    def __init__(self):
        pass

    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        抓取网页正文
        返回字段：
        - title: 标题
        - url: URL
        - markdown: Markdown 格式正文
        - metadata: 元数据
        """
        # 第一版暂不实现，返回空结果
        return {
            "title": "",
            "url": url,
            "markdown": "",
            "metadata": {},
        }
