"""
项目模型
表名：projects
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_base_path = Column(String(500), nullable=True)  # 图片/数据基础路径
    sample_json = Column(JSON, nullable=True)  # 示例 JSON（用于解析字段）
    config_json = Column(JSON, nullable=False)  # 标注组件配置
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # 关联关系
    creator = relationship("User", back_populates="created_projects", foreign_keys=[created_by])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
