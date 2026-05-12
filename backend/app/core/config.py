from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_ENV: str = "dev"
    APP_NAME: str = "resource-recommendation-agent"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    SILICONFLOW_API_KEY: Optional[str] = None
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_MODEL: str = "qwen-max"

    # Search - Unified Configuration
    SEARCH_PROVIDER: str = "tavily"  # tavily | bocha | zhipu
    SEARCH_REGION: str = "global"  # global | cn | hybrid
    SEARCH_FALLBACK_PROVIDER: Optional[str] = None
    SEARCH_TIMEOUT_SECONDS: int = 30

    # Search Providers
    TAVILY_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None
    BOCHA_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None

    # Feature Flags
    ENABLE_TAVILY: bool = True
    ENABLE_FIRECRAWL: bool = False
    ENABLE_BOCHA: bool = False
    ENABLE_ZHIPU_SEARCH: bool = False
    ENABLE_CONTEXT7: bool = False
    ENABLE_VIDEO_SEARCH: bool = True
    ENABLE_GITHUB_SEARCH: bool = True

    # Recommendation Config
    MAX_TOPICS_PER_REQUEST: int = 5
    MAX_RESOURCES_PER_TOPIC: int = 5
    MAX_SEARCH_QUERIES_PER_TOPIC: int = 5
    MAX_SCRAPE_PAGES_PER_TOPIC: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
