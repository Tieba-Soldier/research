"""Pydantic schemas for agent outputs"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class UserNeedAnalysisOutput(BaseModel):
    """用户需求分析输出"""
    user_level: str = Field(..., min_length=1, description="用户水平")
    learning_goal: str = Field(..., min_length=1, description="学习目标")
    time_constraint: str = Field(..., min_length=1, description="时间约束")
    preferred_format: str = Field(..., min_length=1, description="偏好格式")

    @validator('user_level', 'learning_goal', 'time_constraint', 'preferred_format')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class TopicItem(BaseModel):
    """单个主题"""
    raw_text: str = Field(..., min_length=1, description="原始主题文本")
    normalized_topic: str = Field(..., min_length=1, description="标准化主题")
    priority: int = Field(..., ge=1, le=10, description="优先级1-10")

    @validator('raw_text', 'normalized_topic')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Topic text cannot be empty')
        return v.strip()


class TopicExtractorOutput(BaseModel):
    """主题提取器输出"""
    topics: List[TopicItem] = Field(..., min_items=1, description="至少1个主题")

    @validator('topics')
    def validate_topics(cls, v):
        if not v:
            raise ValueError("topics cannot be empty")
        return v


class NormalizedTopic(BaseModel):
    """单个标准化主题"""
    original: str = Field(..., min_length=1, description="原始主题")
    normalized: str = Field(..., min_length=1, description="标准化后的主题")
    category: str = Field(..., description="主题分类")
    priority: str = Field(..., description="优先级")
    reason: str = Field(..., min_length=1, description="标准化原因")
    keywords: List[str] = Field(..., min_items=1, description="关键词列表")

    @validator('category')
    def validate_category(cls, v):
        allowed = ['programming', 'database', 'framework', 'algorithm', 'system-design', 'devops', 'frontend', 'backend', 'other']
        if v not in allowed:
            raise ValueError(f"category 必须是 {allowed} 之一")
        return v

    @validator('priority')
    def validate_priority(cls, v):
        allowed = ['low', 'medium', 'high']
        if v not in allowed:
            raise ValueError(f"priority 必须是 {allowed} 之一")
        return v

    @validator('keywords')
    def validate_keywords(cls, v):
        if any(not s.strip() for s in v):
            raise ValueError("关键词不能为空字符串")
        return v


class TopicNormalizerOutput(BaseModel):
    """主题标准化器输出"""
    normalized_topics: List[NormalizedTopic] = Field(..., min_items=1, description="标准化主题列表")


class ResourceEvaluatorOutput(BaseModel):
    """资源评估器输出"""
    title: str = Field(..., min_length=1, description="资源标题")
    url: str = Field(..., min_length=1, description="资源URL")
    summary: str = Field(..., min_length=1, description="资源摘要")
    reason: str = Field(..., min_length=1, description="推荐理由")
    quality_score: int = Field(..., ge=1, le=10, description="质量评分1-10")
    difficulty_level: str = Field(..., min_length=1, description="难度级别")

    @validator('title', 'url', 'summary', 'reason', 'difficulty_level')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class LearningStage(BaseModel):
    """学习阶段"""
    stage_number: int = Field(..., ge=1, description="阶段编号")
    stage_name: str = Field(..., min_length=1, description="阶段名称")
    description: str = Field(..., min_length=1, description="阶段描述")
    estimated_hours: int = Field(..., ge=1, description="预计学时")

    @validator('stage_name', 'description')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class LearningPathGeneratorOutput(BaseModel):
    """学习路径生成器输出"""
    stages: List[LearningStage] = Field(..., min_items=1, description="至少1个阶段")

    @validator('stages')
    def validate_stages(cls, v):
        if not v:
            raise ValueError("stages cannot be empty")
        return v


class PracticeTask(BaseModel):
    """练习任务"""
    task_text: str = Field(..., min_length=1, description="任务文本")
    difficulty: str = Field(..., min_length=1, description="难度")
    estimated_time: str = Field(..., min_length=1, description="预计时间")

    @validator('task_text', 'difficulty', 'estimated_time')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class PracticeTaskGeneratorOutput(BaseModel):
    """练习任务生成器输出"""
    tasks: List[PracticeTask] = Field(..., min_items=1, description="至少1个任务")

    @validator('tasks')
    def validate_tasks(cls, v):
        if not v:
            raise ValueError("tasks cannot be empty")
        return v


class SearchQuery(BaseModel):
    """搜索查询"""
    query: str = Field(..., min_length=1, description="搜索查询文本")
    topic: str = Field(..., min_length=1, description="关联主题")
    search_type: str = Field(..., description="搜索类型")
    priority: str = Field(..., description="优先级")

    @validator('search_type')
    def validate_search_type(cls, v):
        allowed = ['tutorial', 'practice', 'troubleshooting', 'best_practice', 'comparison']
        if v not in allowed:
            raise ValueError(f"search_type 必须是 {allowed} 之一")
        return v

    @validator('priority')
    def validate_priority(cls, v):
        allowed = ['high', 'medium', 'low']
        if v not in allowed:
            raise ValueError(f"priority 必须是 {allowed} 之一")
        return v


class SearchPlannerOutput(BaseModel):
    """搜索规划器输出"""
    search_queries: List[SearchQuery] = Field(..., min_items=6, description="搜索查询列表")
