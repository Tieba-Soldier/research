from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stages = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
