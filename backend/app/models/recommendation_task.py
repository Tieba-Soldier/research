from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class RecommendationTask(Base):
    __tablename__ = "recommendation_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    user_input = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    current_step = Column(String(255), nullable=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
