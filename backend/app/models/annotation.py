"""
标注结果模型
表名：annotations
"""
from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), unique=True, nullable=False, index=True)
    result_json = Column(JSON, nullable=False)  # 标注结果
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    task = relationship("Task", back_populates="annotation")
    creator = relationship("User", back_populates="created_annotations", foreign_keys=[created_by])
