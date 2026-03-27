"""
项目 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ProjectBase(BaseModel):
    """项目基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    image_base_path: Optional[str] = Field(None, description="图片/数据基础路径")
    sample_json: Optional[dict] = Field(None, description="示例 JSON")
    config_json: dict = Field(..., description="标注组件配置 JSON")


class ProjectCreate(ProjectBase):
    """创建项目请求 Schema"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目请求 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config_json: Optional[dict] = None
    is_deleted: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """项目响应 Schema"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


class ProjectListItem(ProjectResponse):
    """项目列表项（包含统计信息）"""
    task_count: int = 0
    completed_count: int = 0


class ProjectStatistics(BaseModel):
    """项目统计信息"""
    total_tasks: int
    pending_tasks: int
    doing_tasks: int
    completed_tasks: int
    completion_rate: float
    daily_progress: list = []
