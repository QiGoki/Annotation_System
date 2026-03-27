"""
数据导出服务
"""
from sqlalchemy.orm import Session
from typing import List
import json

from ..models.task import Task
from ..models.project import Project
from ..models.user import User
from ..models.annotation import Annotation


class ExportService:
    """数据导出服务"""

    @staticmethod
    def export_jsonl(db: Session, project_id: int, status: str = "completed") -> str:
        """导出为 JSONL 格式"""
        tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == status
        ).all()

        lines = []
        for task in tasks:
            annotation = db.query(Annotation).filter(Annotation.task_id == task.id).first()
            annotator = db.query(User).filter(User.id == annotation.created_by).first() if annotation else None

            export_data = {
                "task_id": task.id,
                "data": task.data_source,
                "result": annotation.result_json if annotation else None,
                "annotated_by": annotator.username if annotator else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
            lines.append(json.dumps(export_data, ensure_ascii=False))

        return '\n'.join(lines)

    @staticmethod
    def export_json(db: Session, project_id: int, status: str = "completed") -> dict:
        """导出为 JSON 格式"""
        tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == status
        ).all()

        result = []
        for task in tasks:
            annotation = db.query(Annotation).filter(Annotation.task_id == task.id).first()
            annotator = db.query(User).filter(User.id == annotation.created_by).first() if annotation else None

            export_data = {
                "task_id": task.id,
                "data": task.data_source,
                "result": annotation.result_json if annotation else None,
                "annotated_by": annotator.username if annotator else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
            result.append(export_data)

        return {"data": result}
