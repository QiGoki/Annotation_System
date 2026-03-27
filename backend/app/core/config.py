"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "标注平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/annotation_platform"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".json", ".jsonl", ".jpg", ".jpeg", ".png"]

    # 初始管理员账号
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
