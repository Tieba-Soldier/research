from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class PracticeTask(Base):
    __tablename__ = "practice_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    topic_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=True)
    task_text = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=True)
    task_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
