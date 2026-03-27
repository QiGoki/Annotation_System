"""
用户管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_admin_user
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


class PasswordChange(BaseModel):
    """密码修改请求"""
    old_password: str
    new_password: str


class AdminPasswordChange(BaseModel):
    """管理员重置密码请求"""
    new_password: str


@router.post("", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """创建用户（仅管理员）"""
    try:
        user = UserService.create_user(db, user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[UserResponse])
def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="角色"),
    keyword: Optional[str] = Query(None, description="用户名关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """获取用户列表（仅管理员）"""
    skip = (page - 1) * page_size
    users = UserService.get_users(db, skip=skip, limit=page_size, role=role, keyword=keyword)
    return users


@router.get("/total")
def get_users_total(
    role: Optional[str] = Query(None, description="角色"),
    keyword: Optional[str] = Query(None, description="用户名关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """获取用户总数（仅管理员）"""
    total = UserService.get_users_total(db, role=role, keyword=keyword)
    return {"total": total}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """获取用户详情（仅管理员）"""
    user = UserService.get_users(db, skip=0, limit=1)
    user = next((u for u in user if u.id == user_id), None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """启用/禁用用户（仅管理员）"""
    user_in = UserUpdate(is_active=is_active)
    try:
        user = UserService.update_user(db, user_id, user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """删除用户（仅管理员）"""
    try:
        UserService.delete_user(db, user_id)
        return {"message": "用户已删除"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改当前用户密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    # 更新密码
    user_in = UserUpdate(password_hash=get_password_hash(password_data.new_password))
    try:
        user = UserService.update_user(db, current_user.id, user_in)
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    password_data: AdminPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """管理员重置用户密码"""
    try:
        user_in = UserUpdate(password_hash=get_password_hash(password_data.new_password))
        user = UserService.update_user(db, user_id, user_in)
        return {"message": "密码已重置"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
