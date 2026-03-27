"""
数据导入工具
"""
from sqlalchemy.orm import Session
from typing import Iterator, List
import json

from ..models.project import Project
from ..services.task_service import TaskService


class ImportService:
    """数据导入服务"""

    @staticmethod
    def parse_jsonl(file_content: bytes) -> Iterator[dict]:
        """解析 JSONL 文件"""
        lines = file_content.decode('utf-8').strip().split('\n')
        for line in lines:
            if line.strip():
                yield json.loads(line)

    @staticmethod
    def parse_json(file_content: bytes) -> List[dict]:
        """解析 JSON 数组文件"""
        data = json.loads(file_content.decode('utf-8'))
        if isinstance(data, list):
            return data
        return [data]

    @staticmethod
    def import_data(db: Session, project_id: int, data_items: List[dict]) -> int:
        """导入数据到项目"""
        # 验证项目存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")

        # 批量创建任务
        count = TaskService.batch_create_tasks(db, project_id, data_items)
        return count
