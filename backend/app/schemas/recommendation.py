from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RecommendationTaskCreate(BaseModel):
    user_input: str = Field(..., description="用户输入的学习需求")
    max_topics: int = Field(default=5, description="最多提取的主题数量")
    max_resources_per_topic: int = Field(default=5, description="每个主题最多推荐的资源数量")
    include_video: bool = Field(default=True, description="是否包含视频资源")
    include_articles: bool = Field(default=True, description="是否包含文章资源")
    include_official_docs: bool = Field(default=True, description="是否包含官方文档")
    include_github: bool = Field(default=True, description="是否包含 GitHub 项目")
    include_practice_tasks: bool = Field(default=True, description="是否生成练习任务")


class RecommendationTaskResponse(BaseModel):
    task_id: int
    status: str

    class Config:
        from_attributes = True


class RecommendationTaskStatus(BaseModel):
    task_id: int
    status: str
    current_step: Optional[str] = None
    progress: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class LearningTopicSchema(BaseModel):
    id: int
    raw_text: str
    normalized_topic: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    reason: Optional[str] = None
    keywords: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ResourceSchema(BaseModel):
    id: int
    title: str
    url: str
    resource_type: Optional[str] = None
    summary: Optional[str] = None
    reason: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_minutes: Optional[int] = None
    final_score: Optional[float] = None

    class Config:
        from_attributes = True


class LearningPathStage(BaseModel):
    name: str
    goal: str
    resources: Optional[List[int]] = []
    tasks: Optional[List[str]] = []
    expected_output: Optional[str] = None


class LearningPathSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    stages: List[LearningPathStage]

    class Config:
        from_attributes = True


class PracticeTaskSchema(BaseModel):
    id: int
    task_text: str
    reference_answer: Optional[str] = None
    difficulty: Optional[str] = None
    task_type: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendationResult(BaseModel):
    task_id: int
    status: str
    topics: List[LearningTopicSchema]
    resources: List[ResourceSchema]
    learning_path: Optional[LearningPathSchema] = None
    practice_tasks: List[PracticeTaskSchema]
