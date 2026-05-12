"""
统一的LLM JSON输出解析器
处理markdown代码块、控制字符、格式错误等问题
"""
import json
import re
import logging
from typing import Any, Dict
from json_repair import repair_json

logger = logging.getLogger(__name__)


class LLMJsonParseError(Exception):
    """LLM JSON解析失败异常"""
    pass


class LLMJsonParser:
    """统一的LLM JSON解析器"""

    @staticmethod
    def parse(raw_output: str, node_name: str = "unknown") -> Dict[str, Any]:
        """
        解析LLM输出的JSON

        Args:
            raw_output: LLM原始输出
            node_name: 节点名称，用于日志

        Returns:
            解析后的字典

        Raises:
            LLMJsonParseError: 解析失败
        """
        if not raw_output or not raw_output.strip():
            logger.error(f"[{node_name}] Empty output")
            raise LLMJsonParseError("Empty output from LLM")

        # 记录原始输出前500字符
        logger.info(f"[{node_name}] Raw output preview: {raw_output[:500]}")

        try:
            # 步骤1: 去除markdown代码块
            cleaned = LLMJsonParser._remove_markdown_blocks(raw_output)

            # 步骤2: 清理控制字符
            cleaned = LLMJsonParser._clean_control_chars(cleaned)

            # 步骤3: 提取JSON部分
            cleaned = LLMJsonParser._extract_json(cleaned)

            # 步骤4: 尝试直接解析
            try:
                result = json.loads(cleaned)
                logger.info(f"[{node_name}] JSON parsed successfully")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"[{node_name}] Direct parse failed: {str(e)}, trying repair")

                # 步骤5: 使用json-repair修复
                try:
                    repaired = repair_json(cleaned)
                    result = json.loads(repaired)
                    logger.info(f"[{node_name}] JSON repaired and parsed successfully")
                    return result
                except Exception as repair_error:
                    logger.error(f"[{node_name}] Repair failed: {str(repair_error)}")
                    raise LLMJsonParseError(f"JSON repair failed: {str(repair_error)}")

        except LLMJsonParseError:
            raise
        except Exception as e:
            logger.error(f"[{node_name}] Unexpected error: {str(e)}")
            raise LLMJsonParseError(f"Unexpected parsing error: {str(e)}")

    @staticmethod
    def _remove_markdown_blocks(text: str) -> str:
        """去除markdown代码块标记"""
        # 去除 ```json ... ``` 或 ``` ... ```
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        return text.strip()

    @staticmethod
    def _clean_control_chars(text: str) -> str:
        """清理控制字符，保留必要的空白字符"""
        # 保留 \n \r \t，移除其他控制字符
        cleaned = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        return cleaned

    @staticmethod
    def _extract_json(text: str) -> str:
        """提取JSON部分，去除前后的解释文字"""
        text = text.strip()

        # 查找第一个 { 或 [
        start_brace = text.find('{')
        start_bracket = text.find('[')

        if start_brace == -1 and start_bracket == -1:
            return text

        if start_brace == -1:
            start = start_bracket
        elif start_bracket == -1:
            start = start_brace
        else:
            start = min(start_brace, start_bracket)

        # 查找最后一个 } 或 ]
        end_brace = text.rfind('}')
        end_bracket = text.rfind(']')

        if end_brace == -1 and end_bracket == -1:
            return text[start:]

        end = max(end_brace, end_bracket)

        return text[start:end+1]
