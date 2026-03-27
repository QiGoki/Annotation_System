"""
任务领取服务
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..models.task import Task
from ..models.project_member import ProjectMember
from ..services.project_member_service import ProjectMemberService


class ClaimTaskService:
    """任务领取服务类"""

    @staticmethod
    def claim_task(db: Session, task_id: int, user_id: int) -> Task:
        """
        领取任务
        规则：
        1. 用户必须是项目成员
        2. 任务必须是 pending 状态（未领取）
        3. 领取后任务状态变为 doing
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")

        # 检查任务状态
        if task.status != "pending":
            if task.status == "doing":
                # 获取当前领取者信息
                current_assignee = db.query(Task).filter(Task.id == task_id).first()
                raise ValueError(f"任务已被领取，当前标注中")
            else:
                raise ValueError("任务已完成，无法领取")

        # 检查用户是否是项目成员
        is_member = ProjectMemberService.is_member(db, task.project_id, user_id)
        if not is_member:
            raise ValueError("您不是该项目成员，无法领取任务")

        # 领取任务
        task.assigned_to = user_id
        task.status = "doing"
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def release_task(db: Session, task_id: int, user_id: int) -> Task:
        """
        释放任务
        规则：
        1. 只有任务领取者或项目管理员可以释放
        2. 释放后任务状态变回 pending
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")

        # 检查是否是任务领取者
        if task.assigned_to != user_id:
            # 检查是否是项目管理员
            member = ProjectMemberService.get_member(db, task.project_id, user_id)
            if not member or member.role != "admin":
                raise ValueError("您无权释放此任务")

        # 释放任务
        task.assigned_to = None
        task.status = "pending"
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_available_tasks(db: Session, project_id: int, user_id: int) -> list:
        """
        获取用户可领取的任务列表
        规则：
        1. 用户必须是项目成员
        2. 任务状态为 pending（未领取）
        """
        # 检查用户是否是项目成员
        is_member = ProjectMemberService.is_member(db, project_id, user_id)
        if not is_member:
            return []

        # 获取未领取的任务
        tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "pending"
        ).order_by(Task.created_at.asc()).all()

        return tasks
