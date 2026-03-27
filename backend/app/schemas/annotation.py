"""
标注结果 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class AnnotationBase(BaseModel):
    """标注结果基础 Schema"""
    result_json: dict = Field(..., description="标注结果 JSON")


class AnnotationCreate(AnnotationBase):
    """创建标注结果请求 Schema"""
    task_id: int


class AnnotationResponse(AnnotationBase):
    """标注结果响应 Schema"""
    id: int
    task_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationUpdate(BaseModel):
    """更新标注结果请求 Schema"""
    result_json: dict
