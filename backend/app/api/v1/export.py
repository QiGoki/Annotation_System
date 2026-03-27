"""
数据导入导出 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import json
import io
import asyncio

from app.core.database import get_db
from app.core.deps import get_current_active_admin_user
from app.models.user import User
from app.models.project import Project
from app.schemas.task import TaskCreate
from app.utils.import_utils import ImportService
from app.services.export_service import ExportService

router = APIRouter()


@router.post("/import")
async def import_data(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """导入数据（JSON/JSONL 文件）"""
    try:
        content = await file.read()

        # 根据文件扩展名选择解析方式
        if file.filename and file.filename.endswith('.jsonl'):
            data_items = list(ImportService.parse_jsonl(content))
        else:
            data_items = ImportService.parse_json(content)

        count = ImportService.import_data(db, project_id, data_items)
        return {"message": f"成功导入{count}条数据，创建{count}个任务"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="文件格式错误，请上传有效的 JSON/JSONL 文件")


@router.post("/import-urls")
def import_urls(
    project_id: int,
    items: list,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """通过 URL 列表导入数据"""
    try:
        count = ImportService.import_data(db, project_id, items)
        return {"message": f"成功导入{count}条数据，创建{count}个任务"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export")
def export_data(
    project_id: int,
    status: str = Query("completed", description="导出的任务状态"),
    format: str = Query("jsonl", description="导出格式：json/jsonl"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """导出标注结果"""
    try:
        if format == "jsonl":
            content = ExportService.export_jsonl(db, project_id, status)
            return StreamingResponse(
                io.BytesIO(content.encode('utf-8')),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename=export_{project_id}.jsonl"}
            )
        elif format == "json":
            content = ExportService.export_json(db, project_id, status)
            return StreamingResponse(
                io.BytesIO(json.dumps(content, ensure_ascii=False).encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=export_{project_id}.json"}
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
