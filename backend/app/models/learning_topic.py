from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class LearningTopic(Base):
    __tablename__ = "learning_topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    raw_text = Column(Text, nullable=False)
    normalized_topic = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
