"""
项目成员服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models.project_member import ProjectMember
from ..models.project import Project
from ..models.user import User


class ProjectMemberService:
    """项目成员服务类"""

    @staticmethod
    def add_member(db: Session, project_id: int, user_id: int, role: str = "member") -> ProjectMember:
        """添加项目成员"""
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")

        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 检查是否已是成员
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        if existing:
            raise ValueError("该用户已是项目成员")

        # 创建成员关系
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, project_id: int, user_id: int) -> bool:
        """移除项目成员"""
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        if not member:
            raise ValueError("该用户不是项目成员")

        db.delete(member)
        db.commit()
        return True

    @staticmethod
    def update_member_role(db: Session, project_id: int, user_id: int, role: str) -> ProjectMember:
        """更新成员角色"""
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        if not member:
            raise ValueError("该用户不是项目成员")

        member.role = role
        member.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def get_project_members(db: Session, project_id: int) -> List[ProjectMember]:
        """获取项目所有成员"""
        return db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

    @staticmethod
    def get_user_projects(db: Session, user_id: int) -> List[Project]:
        """获取用户参与的所有项目"""
        members = db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id
        ).all()
        project_ids = [m.project_id for m in members]
        return db.query(Project).filter(Project.id.in_(project_ids)).all()

    @staticmethod
    def is_member(db: Session, project_id: int, user_id: int) -> bool:
        """检查用户是否是项目成员"""
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        return member is not None

    @staticmethod
    def get_member(db: Session, project_id: int, user_id: int) -> Optional[ProjectMember]:
        """获取项目成员信息"""
        return db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
