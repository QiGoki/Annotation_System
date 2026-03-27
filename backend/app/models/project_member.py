"""
项目成员关联表
实现项目与用户的多对多关系（含角色）
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default="member")  # admin: 管理员，member: 普通成员
    joined_at = Column(DateTime, default=datetime.utcnow)

    # 唯一约束：同一用户不能重复加入同一项目
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )

    # 关联关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_members")
