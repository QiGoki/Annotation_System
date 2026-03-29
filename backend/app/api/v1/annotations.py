"""
标注 API 路由

注意：标注相关的核心操作（保存、提交）已移至 tasks.py，
此文件保留用于未来扩展其他标注相关功能。
"""
from fastapi import APIRouter

router = APIRouter()

# 标注保存和提交端点已统一到 tasks.py 中
# 前端调用路径：POST /tasks/{task_id}/annotate 和 POST /tasks/{task_id}/submit
