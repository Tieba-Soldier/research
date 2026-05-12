from typing import List, Dict, Any


class Context7Tool:
    """Context7 官方文档检索工具（第一版预留接口）"""

    def __init__(self):
        pass

    async def fetch_docs(self, library_name: str, topic: str) -> List[Dict[str, Any]]:
        """
        获取官方技术文档
        返回字段：
        - title: 标题
        - content: 内容
        - url: URL
        - library: 库名称
        - topic: 主题
        """
        # 第一版暂不实现，返回空列表
        return []
