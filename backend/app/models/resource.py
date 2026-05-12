from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    topic_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=True)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    resource_type = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=True)
    estimated_minutes = Column(Integer, nullable=True)
    relevance_score = Column(Numeric(5, 2), nullable=True)
    quality_score = Column(Numeric(5, 2), nullable=True)
    practical_score = Column(Numeric(5, 2), nullable=True)
    final_score = Column(Numeric(5, 2), nullable=True)
    content_markdown = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
