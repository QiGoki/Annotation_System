"""
项目服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime
from ..models.project import Project
from ..models.task import Task
from ..schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """项目服务类"""

    @staticmethod
    def create_project(db: Session, project_in: ProjectCreate, created_by: int) -> Project:
        """创建项目"""
        project = Project(
            name=project_in.name,
            description=project_in.description,
            image_base_path=project_in.image_base_path,
            sample_json=project_in.sample_json,
            config_json=project_in.config_json,
            created_by=created_by
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_projects(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Tuple[List[Project], int]:
        """获取项目列表"""
        query = db.query(Project).filter(Project.is_deleted == False)
        if keyword:
            query = query.filter(Project.name.contains(keyword))
        if created_by:
            query = query.filter(Project.created_by == created_by)

        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
        return projects, total

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """获取项目详情"""
        return db.query(Project).filter(
            Project.id == project_id,
            Project.is_deleted == False
        ).first()

    @staticmethod
    def update_project(db: Session, project_id: int, project_in: ProjectUpdate) -> Project:
        """更新项目"""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.is_deleted == False
        ).first()
        if not project:
            raise ValueError("项目不存在")

        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """删除项目（软删除）"""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.is_deleted == False
        ).first()
        if not project:
            raise ValueError("项目不存在")

        project.is_deleted = True
        project.updated_at = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def get_project_statistics(db: Session, project_id: int) -> dict:
        """获取项目统计信息"""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.is_deleted == False
        ).first()
        if not project:
            raise ValueError("项目不存在")

        # 统计任务数
        total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
        pending_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "pending"
        ).count()
        doing_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "doing"
        ).count()
        completed_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "completed"
        ).count()

        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0

        return {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "doing_tasks": doing_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "daily_progress": []  # 可以后续实现每日进度统计
        }
