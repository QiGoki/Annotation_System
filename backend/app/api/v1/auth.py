"""
认证 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.core.deps import get_current_user, get_current_active_admin_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse, ChangePassword
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """注册新用户（仅管理员）"""
    # 检查用户名是否已存在
    existing_user = AuthService.get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    return AuthService.create_user(db, user_in)


@router.post("/login", response_model=Token)
def login(request: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = AuthService.authenticate(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # JWT 是无状态的，登出只需要前端删除 token
    return {"message": "登出成功"}


@router.post("/change-password")
def change_password(
    request: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()

    return {"message": "密码修改成功"}
