"""
任务服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime
import json

from ..models.task import Task
from ..models.annotation import Annotation
from ..schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """任务服务类"""

    @staticmethod
    def create_task(db: Session, project_id: int, data_source: dict) -> Task:
        """创建任务"""
        task = Task(
            project_id=project_id,
            data_source=data_source
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def batch_create_tasks(db: Session, project_id: int, data_sources: List[dict]) -> int:
        """批量创建任务"""
        tasks = [
            Task(project_id=project_id, data_source=ds)
            for ds in data_sources
        ]
        db.bulk_save_objects(tasks)
        db.commit()
        return len(tasks)

    @staticmethod
    def get_tasks(
        db: Session,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        assigned_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Task], int]:
        """获取任务列表"""
        query = db.query(Task)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(Task.status == status)
        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)

        total = query.count()
        tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
        return tasks, total

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """获取任务详情"""
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def update_task(db: Session, task_id: int, task_in: TaskUpdate) -> Task:
        """更新任务"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")

        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # 如果状态变为 completed，设置完成时间
        if task_in.status == "completed" and task.completed_at is None:
            task.completed_at = datetime.utcnow()

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def assign_task(db: Session, task_id: int, assigned_to: int) -> Task:
        """分配任务"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")

        task.assigned_to = assigned_to
        task.status = "pending"
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_pending_task_for_user(db: Session, user_id: int) -> Optional[Task]:
        """获取用户待办任务"""
        return db.query(Task).filter(
            Task.assigned_to == user_id,
            Task.status.in_(["pending", "doing"])
        ).first()

    @staticmethod
    def get_next_task(db: Session, current_task_id: int, project_id: Optional[int] = None) -> Optional[Task]:
        """获取下一条任务"""
        current_task = db.query(Task).filter(Task.id == current_task_id).first()
        if not current_task:
            return None

        query = db.query(Task).filter(
            Task.id > current_task_id,
            Task.project_id == current_task.project_id
        )
        if project_id:
            query = query.filter(Task.project_id == project_id)

        return query.order_by(Task.id).first()
