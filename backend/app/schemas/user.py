"""
用户 Schema
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    role: str = Field(default="annotator", description="角色：admin | annotator")


class UserCreate(UserBase):
    """创建用户请求 Schema"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户请求 Schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应 Schema"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录请求 Schema"""
    username: str
    password: str


class Token(BaseModel):
    """Token 响应 Schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ChangePassword(BaseModel):
    """修改密码请求 Schema"""
    old_password: str
    new_password: str = Field(..., min_length=6)
