"""
任务模型
表名：tasks
"""
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    data_source = Column(JSON, nullable=False)  # 数据源：图片 URL/路径 或 文本内容
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending/doing/completed
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_to])
    annotation = relationship("Annotation", back_populates="task", uselist=False, cascade="all, delete-orphan")
