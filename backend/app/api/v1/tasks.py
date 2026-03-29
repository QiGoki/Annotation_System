"""
任务 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_admin_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.annotation import Annotation
from app.schemas.task import TaskResponse, TaskListItem, TaskAssign, TaskStatusUpdate, TaskUpdate
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.services.claim_task_service import ClaimTaskService

router = APIRouter()


class AnnotateRequest(BaseModel):
    """标注请求"""
    result_json: dict


@router.get("", response_model=List[dict])
def get_task_list(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表（支持按项目、状态等筛选）"""
    tasks, total = TaskService.get_tasks(
        db,
        project_id=project_id,
        status=status,
        assigned_to=assigned_to,
        skip=skip,
        limit=limit
    )

    result = []
    for task in tasks:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        task_dict = TaskListItem.model_validate(task).model_dump()
        task_dict["project_name"] = project.name if project else None
        result.append(task_dict)

    return result


@router.get("/pending", response_model=List[TaskListItem])
def get_pending_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户待标注任务"""
    tasks, _ = TaskService.get_tasks(
        db,
        assigned_to=current_user.id,
        status="pending",
        skip=0,
        limit=100
    )

    result = []
    for task in tasks:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        task_dict = TaskListItem.model_validate(task).model_dump()
        task_dict["project_name"] = project.name if project else None
        result.append(task_dict)

    return result


@router.get("/{task_id}", response_model=dict)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情（用于标注执行）"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    project = db.query(Project).filter(Project.id == task.project_id).first()
    annotation = db.query(Annotation).filter(Annotation.task_id == task_id).first()

    return {
        "id": task.id,
        "project_id": task.project_id,
        "project_name": project.name if project else None,
        "project_config": project.config_json if project else None,
        "data_source": task.data_source,
        "status": task.status,
        "annotation": {
            "id": annotation.id,
            "result_json": annotation.result_json,
            "created_at": annotation.created_at
        } if annotation else None
    }


@router.put("/{task_id}/assign")
def assign_task(
    task_id: int,
    assign_data: TaskAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """分配任务（仅管理员）"""
    try:
        task = TaskService.assign_task(db, task_id, assign_data.assigned_to)
        return {"message": "任务分配成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{task_id}/status")
def update_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务状态"""
    try:
        task = TaskService.update_task(db, task_id, TaskUpdate(status=status_data.status))
        return {"message": "任务状态已更新"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{task_id}/next")
def get_next_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取下一条任务"""
    next_task = TaskService.get_next_task(db, task_id)
    if next_task:
        return {"task_id": next_task.id, "has_next": True}
    return {"task_id": None, "has_next": False}


@router.post("/{task_id}/annotate")
def annotate_task(
    task_id: int,
    data: AnnotateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存标注结果"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查是否有现有标注
    annotation = db.query(Annotation).filter(Annotation.task_id == task_id).first()

    if annotation:
        # 更新现有标注
        annotation.result_json = data.result_json
        annotation.updated_at = datetime.utcnow()
    else:
        # 创建新标注
        annotation = Annotation(
            task_id=task_id,
            result_json=data.result_json,
            created_by=current_user.id
        )
        db.add(annotation)

    db.commit()

    return {"code": 200, "message": "保存成功"}


@router.post("/{task_id}/submit")
def submit_task(
    task_id: int,
    data: AnnotateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交标注结果"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查是否有现有标注
    annotation = db.query(Annotation).filter(Annotation.task_id == task_id).first()

    if annotation:
        # 更新现有标注
        annotation.result_json = data.result_json
        annotation.updated_at = datetime.utcnow()
    else:
        # 创建新标注
        annotation = Annotation(
            task_id=task_id,
            result_json=data.result_json,
            created_by=current_user.id
        )
        db.add(annotation)

    # 更新任务状态为 completed
    task.status = "completed"
    task.updated_at = datetime.utcnow()

    db.commit()

    # 获取下一条任务
    next_task = TaskService.get_next_task(db, task_id)

    return {
        "code": 200,
        "message": "提交成功",
        "data": {
            "next_task_id": next_task.id if next_task else None
        }
    }


@router.post("/{task_id}/claim")
def claim_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """领取任务"""
    try:
        task = ClaimTaskService.claim_task(db, task_id, current_user.id)
        return {
            "code": 200,
            "message": "领取成功",
            "data": {
                "task_id": task.id,
                "status": task.status,
                "assigned_to": task.assigned_to
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/release")
def release_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """释放任务"""
    try:
        task = ClaimTaskService.release_task(db, task_id, current_user.id)
        return {
            "code": 200,
            "message": "释放成功",
            "data": {
                "task_id": task.id,
                "status": task.status,
                "assigned_to": None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
