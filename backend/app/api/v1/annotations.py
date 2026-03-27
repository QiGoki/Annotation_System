"""
标注 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.annotation import Annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate
from app.services.task_service import TaskService

router = APIRouter()


@router.post("/{task_id}/annotate")
def save_annotation(
    task_id: int,
    annotation_in: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存标注结果"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查是否已有标注
    annotation = db.query(Annotation).filter(Annotation.task_id == task_id).first()

    if annotation:
        # 更新现有标注
        annotation.result_json = annotation_in.result_json
        annotation.updated_at = datetime.utcnow()
    else:
        # 创建新标注
        annotation = Annotation(
            task_id=task_id,
            result_json=annotation_in.result_json,
            created_by=current_user.id
        )
        db.add(annotation)

    db.commit()
    return {"message": "保存成功"}


@router.post("/{task_id}/submit")
def submit_annotation(
    task_id: int,
    annotation_in: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交标注结果"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 保存或更新标注
    annotation = db.query(Annotation).filter(Annotation.task_id == task_id).first()

    if annotation:
        annotation.result_json = annotation_in.result_json
        annotation.updated_at = datetime.utcnow()
    else:
        annotation = Annotation(
            task_id=task_id,
            result_json=annotation_in.result_json,
            created_by=current_user.id
        )
        db.add(annotation)

    # 更新任务状态为 completed
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    db.commit()

    # 获取下一条任务
    next_task = TaskService.get_next_task(db, task_id)

    return {
        "message": "提交成功",
        "data": {
            "next_task_id": next_task.id if next_task else None
        }
    }
