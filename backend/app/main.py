"""
标注平台 - FastAPI 主应用
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import Base, engine
from .core.config import settings
from .api.v1 import auth, users, projects, tasks, annotations, export, project_members

# 创建数据库表（测试环境除外）
if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="多模态混合标注低代码平台",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目管理"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务管理"])
app.include_router(annotations.router, prefix="/api/v1/annotations", tags=["标注执行"])
app.include_router(export.router, prefix="/api/v1/export", tags=["数据导出"])
app.include_router(project_members.router, prefix="/api/v1/project-members", tags=["项目成员"])


@app.get("/")
def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "多模态混合标注低代码平台"
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "healthy"}
