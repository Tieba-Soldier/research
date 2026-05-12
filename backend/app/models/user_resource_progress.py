from sqlalchemy import Column, BigInteger, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class UserResourceProgress(Base):
    __tablename__ = "user_resource_progress"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    studied = Column(Boolean, default=False)
    favorite = Column(Boolean, default=False)
    studied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
