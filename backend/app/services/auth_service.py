"""
认证服务
"""
from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User
from ..schemas.user import UserCreate
from ..core.security import get_password_hash, verify_password


class AuthService:
    """认证服务类"""

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """创建用户"""
        user = User(
            username=user_in.username,
            password_hash=get_password_hash(user_in.password),
            role=user_in.role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        return db.query(User).filter(User.id == user_id).first()
