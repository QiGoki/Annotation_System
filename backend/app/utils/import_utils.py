"""
数据导入工具
"""
from sqlalchemy.orm import Session
from typing import Iterator, List
import json
import os

from ..models.project import Project
from ..models.task import Task


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
    def import_data(db: Session, project_id: int, data_items: List[dict], filename: str = None) -> int:
        """导入数据到项目

        一个文件创建一个 Task，data_items 存储整个数据数组
        """
        # 验证项目存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")

        # 生成任务名称
        if filename:
            # 去除扩展名作为任务名称
            task_name = os.path.splitext(filename)[0]
        else:
            task_name = f"任务_{project_id}"

        # 创建一个 Task，存储所有数据
        task = Task(
            project_id=project_id,
            name=task_name,
            data_source=data_items  # 存储整个数据数组
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        return len(data_items)  # 返回数据条数
