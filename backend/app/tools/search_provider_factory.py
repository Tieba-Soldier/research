"""
搜索Provider工厂
根据配置返回合适的搜索provider，支持fallback机制
"""
from typing import Optional
from app.core.config import settings
from app.core.exceptions import SearchException
from app.tools.tavily_tool import TavilyTool
from app.tools.bocha_tool import BochaTool
import logging

logger = logging.getLogger(__name__)


def get_search_provider(provider_name: Optional[str] = None):
    """
    获取搜索provider实例

    Args:
        provider_name: 指定provider名称，如果为None则使用配置中的默认值

    Returns:
        搜索provider实例

    Raises:
        SearchException: 当无法创建provider时
    """
    target_provider = provider_name or settings.SEARCH_PROVIDER

    try:
        if target_provider == "bocha":
            if settings.ENABLE_BOCHA and settings.BOCHA_API_KEY:
                logger.info("Using Bocha search provider")
                return BochaTool()
            else:
                logger.warning("Bocha not enabled or API key missing, trying fallback")
                return _get_fallback_provider()

        elif target_provider == "tavily":
            if settings.ENABLE_TAVILY and settings.TAVILY_API_KEY:
                logger.info("Using Tavily search provider")
                return TavilyTool()
            else:
                logger.warning("Tavily not enabled or API key missing, trying fallback")
                return _get_fallback_provider()

        else:
            logger.warning(f"Unknown provider: {target_provider}, using default")
            return _get_default_provider()

    except Exception as e:
        logger.error(f"Failed to create provider {target_provider}: {str(e)}")
        return _get_fallback_provider()


def _get_fallback_provider():
    """获取fallback provider"""
    fallback = settings.SEARCH_FALLBACK_PROVIDER

    if not fallback:
        logger.info("No fallback provider configured, using default")
        return _get_default_provider()

    try:
        if fallback == "tavily" and settings.ENABLE_TAVILY and settings.TAVILY_API_KEY:
            logger.info("Using Tavily as fallback provider")
            return TavilyTool()

        elif fallback == "bocha" and settings.ENABLE_BOCHA and settings.BOCHA_API_KEY:
            logger.info("Using Bocha as fallback provider")
            return BochaTool()

        else:
            logger.warning(f"Fallback provider {fallback} not available")
            return _get_default_provider()

    except Exception as e:
        logger.error(f"Failed to create fallback provider: {str(e)}")
        return _get_default_provider()


def _get_default_provider():
    """获取默认provider（优先级：Bocha > Tavily）"""
    # 优先尝试Bocha（国内优先）
    if settings.ENABLE_BOCHA and settings.BOCHA_API_KEY:
        try:
            logger.info("Using Bocha as default provider")
            return BochaTool()
        except Exception as e:
            logger.error(f"Failed to create Bocha: {str(e)}")

    # 其次尝试Tavily
    if settings.ENABLE_TAVILY and settings.TAVILY_API_KEY:
        try:
            logger.info("Using Tavily as default provider")
            return TavilyTool()
        except Exception as e:
            logger.error(f"Failed to create Tavily: {str(e)}")

    raise SearchException("No search provider available")


def get_primary_provider():
    """获取主搜索provider"""
    return get_search_provider(settings.SEARCH_PROVIDER)


def get_fallback_provider_instance():
    """获取fallback provider实例"""
    return _get_fallback_provider()
