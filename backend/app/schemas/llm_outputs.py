"""
LLM输出的Pydantic Schema定义
确保所有关键字段不为空
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class UserNeedAnalysis(BaseModel):
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


class LearningTopic(BaseModel):
    """学习主题"""
    raw_text: str = Field(..., min_length=1, description="原始主题文本")
    normalized_topic: str = Field(..., min_length=1, description="标准化主题")
    priority: int = Field(..., ge=1, le=10, description="优先级1-10")

    @validator('raw_text', 'normalized_topic')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Topic text cannot be empty')
        return v.strip()


class LearningTopicOutput(BaseModel):
    """主题提取输出"""
    topics: List[LearningTopic] = Field(..., min_items=1, description="至少1个主题")


class ResourceEvaluation(BaseModel):
    """资源评估"""
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


class ResourceEvaluationOutput(BaseModel):
    """资源评估输出"""
    resources: List[ResourceEvaluation] = Field(..., description="评估后的资源列表")


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


class LearningPathOutput(BaseModel):
    """学习路径输出"""
    stages: List[LearningStage] = Field(..., min_items=1, description="至少1个阶段")


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


class PracticeTaskOutput(BaseModel):
    """练习任务输出"""
    tasks: List[PracticeTask] = Field(..., min_items=1, description="至少1个任务")
