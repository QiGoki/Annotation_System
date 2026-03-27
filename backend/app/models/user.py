"""
用户模型
表名：users
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="annotator", index=True)  # 'admin' | 'annotator'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    created_projects = relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assigned_to")
    created_annotations = relationship("Annotation", back_populates="creator", foreign_keys="Annotation.created_by")
    project_members = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
