"""
任务 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class TaskBase(BaseModel):
    """任务基础 Schema"""
    data_source: dict = Field(..., description="数据源：图片 URL/路径 或 文本内容")


class TaskCreate(TaskBase):
    """创建任务请求 Schema"""
    project_id: int


class TaskUpdate(BaseModel):
    """更新任务请求 Schema"""
    status: Optional[str] = Field(None, description="任务状态：pending/doing/completed")
    assigned_to: Optional[int] = Field(None, description="分配给的用户 ID")


class TaskResponse(TaskBase):
    """任务响应 Schema"""
    id: int
    project_id: int
    status: str
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListItem(TaskResponse):
    """任务列表项（包含项目信息）"""
    project_name: Optional[str] = None


class TaskWithAnnotation(TaskResponse):
    """包含标注结果的任务详情"""
    project_name: str
    project_config: dict
    annotation: Optional["AnnotationResponse"] = None


class TaskAssign(BaseModel):
    """分配任务请求 Schema"""
    assigned_to: int


class TaskStatusUpdate(BaseModel):
    """更新任务状态请求 Schema"""
    status: str = Field(..., description="任务状态：pending/doing/completed")


# 前向引用
from .annotation import AnnotationResponse
TaskWithAnnotation.model_rebuild()
