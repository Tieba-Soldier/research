from typing import Optional, Dict, Any, List, Union, Type
import json
import re
import logging
import asyncio
from pydantic import BaseModel, ValidationError
from app.core.config import settings
from app.core.exceptions import LLMException, JSONParseException
from app.utils.llm_json_parser import LLMJsonParser, LLMJsonParseError

logger = logging.getLogger(__name__)

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 30


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise LLMException("OPENAI_API_KEY not configured")
            return settings.OPENAI_API_KEY
        elif self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise LLMException("ANTHROPIC_API_KEY not configured")
            return settings.ANTHROPIC_API_KEY
        elif self.provider == "deepseek":
            if not settings.DEEPSEEK_API_KEY:
                raise LLMException("DEEPSEEK_API_KEY not configured")
            return settings.DEEPSEEK_API_KEY
        elif self.provider == "siliconflow":
            if not settings.SILICONFLOW_API_KEY:
                raise LLMException("SILICONFLOW_API_KEY not configured")
            return settings.SILICONFLOW_API_KEY
        elif self.provider == "dashscope":
            if not settings.DASHSCOPE_API_KEY:
                raise LLMException("DASHSCOPE_API_KEY not configured")
            return settings.DASHSCOPE_API_KEY
        else:
            raise LLMException(f"Unsupported LLM provider: {self.provider}")

    async def generate_text(self, prompt: str) -> str:
        """生成普通文本"""
        try:
            if self.provider == "openai":
                return await self._generate_openai_text(prompt)
            elif self.provider == "anthropic":
                return await self._generate_anthropic_text(prompt)
            elif self.provider == "deepseek":
                return await self._generate_deepseek_text(prompt)
            elif self.provider == "siliconflow":
                return await self._generate_siliconflow_text(prompt)
            elif self.provider == "dashscope":
                return await self._generate_dashscope_text(prompt)
        except Exception as e:
            raise LLMException(f"LLM generation failed: {str(e)}")

    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        fallback_data: Optional[Dict[str, Any]] = None,
        node_name: str = "unknown",
        timeout: int = DEFAULT_TIMEOUT
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        生成 JSON 并解析，支持 Schema 校验和兜底逻辑

        Args:
            prompt: 提示词
            schema: Pydantic Schema 类，用于校验输出
            fallback_data: 兜底数据，当解析失败时返回
            node_name: 节点名称，用于日志
            timeout: 超时时间（秒）

        Returns:
            解析后的 JSON 数据
        """
        logger.info(f"[{node_name}] Starting LLM call with timeout={timeout}s")

        # 在 prompt 中强调 JSON 格式要求
        json_prompt = f"""{prompt}

CRITICAL OUTPUT REQUIREMENTS:
1. Output ONLY valid JSON - no other text
2. NO markdown code blocks (no ```json or ```)
3. NO explanations before or after JSON
4. Start directly with {{ or [
5. All fields must have non-empty values
6. Use proper JSON syntax with double quotes

Example format:
{{"field1": "value1", "field2": "value2"}}"""

        # 第一次尝试（带超时）
        try:
            text = await asyncio.wait_for(
                self.generate_text(json_prompt),
                timeout=timeout
            )
            logger.info(f"[{node_name}] LLM response received, length={len(text)}")

            # 使用统一解析器
            parsed_data = LLMJsonParser.parse(text, node_name)
            logger.info(f"[{node_name}] JSON parsed successfully")

            # 如果提供了 Schema，进行校验
            if schema:
                try:
                    validated = schema(**parsed_data)
                    logger.info(f"[{node_name}] Schema validation passed")
                    return validated.dict()
                except ValidationError as e:
                    logger.warning(f"[{node_name}] Schema validation failed: {e}")
                    # 校验失败，尝试修复
                    return await self._retry_with_fix(text, schema, fallback_data, node_name, timeout)

            return parsed_data

        except asyncio.TimeoutError:
            logger.error(f"[{node_name}] LLM call timeout after {timeout}s")
            if fallback_data:
                logger.info(f"[{node_name}] Using fallback data due to timeout")
                return fallback_data
            raise LLMException(f"LLM call timeout after {timeout}s")

        except LLMJsonParseError as e:
            logger.warning(f"[{node_name}] First JSON parse failed: {e}")
            # 第一次解析失败，尝试修复
            return await self._retry_with_fix(text if 'text' in locals() else "", schema, fallback_data, node_name, timeout)

    async def _retry_with_fix(
        self,
        original_text: str,
        schema: Optional[Type[BaseModel]] = None,
        fallback_data: Optional[Dict[str, Any]] = None,
        node_name: str = "unknown",
        timeout: int = DEFAULT_TIMEOUT
    ) -> Union[Dict[str, Any], List[Any]]:
        """重试并修复 JSON"""
        logger.info(f"[{node_name}] Attempting to fix JSON with repair prompt")

        try:
            # 构造修复 prompt
            fix_prompt = f"""The following text should be valid JSON but failed to parse or validate:

{original_text[:1000]}

Please fix it and return ONLY valid JSON. Requirements:
1. No markdown code blocks
2. No explanation text
3. All fields must be non-empty
4. Use proper JSON syntax
5. Start directly with {{ or [

Return the fixed JSON now:"""

            text = await asyncio.wait_for(
                self.generate_text(fix_prompt),
                timeout=timeout
            )
            logger.info(f"[{node_name}] Repair response received, length={len(text)}")

            # 使用统一解析器
            parsed_data = LLMJsonParser.parse(text, node_name)
            logger.info(f"[{node_name}] Repaired JSON parsed successfully")

            # 如果提供了 Schema，再次校验
            if schema:
                try:
                    validated = schema(**parsed_data)
                    logger.info(f"[{node_name}] Schema validation passed after repair")
                    return validated.dict()
                except ValidationError as e:
                    logger.error(f"[{node_name}] Schema validation failed after retry: {e}")
                    # 校验仍然失败，使用兜底数据
                    if fallback_data:
                        logger.info(f"[{node_name}] Using fallback data after validation failure")
                        return fallback_data
                    raise JSONParseException(f"Schema validation failed: {e}")

            return parsed_data

        except asyncio.TimeoutError:
            logger.error(f"[{node_name}] Repair attempt timeout after {timeout}s")
            if fallback_data:
                logger.info(f"[{node_name}] Using fallback data after repair timeout")
                return fallback_data
            raise LLMException(f"Repair timeout after {timeout}s")

        except Exception as e:
            logger.error(f"[{node_name}] JSON fix failed: {e}")
            # 修复失败，使用兜底数据
            if fallback_data:
                logger.info(f"[{node_name}] Using fallback data after fix failure")
                return fallback_data
            raise JSONParseException(f"Failed to parse JSON after retry: {str(e)}")

    async def _generate_openai_text(self, prompt: str) -> str:
        """调用 OpenAI API"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMException(f"OpenAI API error: {str(e)}")

    async def _generate_anthropic_text(self, prompt: str) -> str:
        """调用 Anthropic API"""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)

            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            raise LLMException(f"Anthropic API error: {str(e)}")

    async def _generate_deepseek_text(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )

            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMException(f"DeepSeek API error: {str(e)}")

    async def _generate_siliconflow_text(self, prompt: str) -> str:
        """调用硅基流动 API"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            from openai import AsyncOpenAI
            import httpx

            logger.info(f"Calling SiliconFlow API with prompt length: {len(prompt)}")

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.siliconflow.cn/v1",
                timeout=httpx.Timeout(60.0, connect=10.0),
                max_retries=2
            )

            response = await client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            logger.info(f"SiliconFlow API response received, length: {len(response.choices[0].message.content)}")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"SiliconFlow API error: {str(e)}", exc_info=True)
            raise LLMException(f"SiliconFlow API error: {str(e)}")

    async def _generate_dashscope_text(self, prompt: str) -> str:
        """调用阿里云百炼 API"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            import httpx

            logger.info(f"Calling DashScope API with prompt length: {len(prompt)}")

            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": settings.DASHSCOPE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info(f"DashScope API response received, length: {len(content)}")
                return content
        except Exception as e:
            logger.error(f"DashScope API error: {str(e)}", exc_info=True)
            raise LLMException(f"DashScope API error: {str(e)}")
