"""
项目 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from io import BytesIO
from pathlib import Path
import json
import re
import mimetypes
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_admin_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.annotation import Annotation
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListItem, ProjectStatistics
from app.schemas.task import TaskResponse
from app.services.project_service import ProjectService

router = APIRouter()


class FieldExtractConfig(BaseModel):
    """字段提取配置"""
    key: str = Field(..., description="输出字段名")
    path: Optional[str] = Field(None, description="JSON Path，如 $.image.url")
    regex: Optional[str] = Field(None, description="正则表达式，如 \"id=(\\d+)\"")


class ExtractRequest(BaseModel):
    """提取请求"""
    json_str: str = Field(..., description="示例 JSON 字符串")
    fields: List[FieldExtractConfig] = Field(default_factory=list, description="字段提取配置列表")


def infer_type(value: Any) -> str:
    """推断 JSON 值的类型"""
    if isinstance(value, str):
        return "string"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    elif value is None:
        return "null"
    return "string"


def parse_json_path(path: str) -> List[Any]:
    """解析 JSON Path 字符串为路径列表

    支持：
    - $.a.b.c - 嵌套访问
    - $.items[0] - 数组索引
    - $.items[*] - 所有数组元素
    - a.b.c - 省略 $ 的简写（自动添加）
    - a[0].b - 数组开头（自动添加 $）
    """
    # 自动添加 $ 前缀
    if not path.startswith('$'):
        path = '$' + path

    parts = []
    remaining = path[1:]  # 去掉 $

    while remaining:
        if remaining.startswith('.'):
            # 对象属性访问 .a
            match = re.match(r'\.([a-zA-Z_][a-zA-Z0-9_]*)', remaining)
            if match:
                parts.append(match.group(1))
                remaining = remaining[len(match.group(0)):]
            else:
                raise ValueError(f"无效的 JSON Path: {path}")
        elif remaining.startswith('['):
            # 数组索引 [0] 或 [*]
            match = re.match(r'\[(\d+|\*)\]', remaining)
            if match:
                idx = match.group(1)
                parts.append(int(idx) if idx != '*' else '*')
                remaining = remaining[len(match.group(0)):]
            else:
                raise ValueError(f"无效的 JSON Path: {path}")
        else:
            # 处理开头的属性名（没有 . 前缀）
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)', remaining)
            if match:
                parts.append(match.group(1))
                remaining = remaining[len(match.group(0)):]
            else:
                raise ValueError(f"无效的 JSON Path: {path}")

    return parts


def extract_by_path(data: Any, path_parts: List[Any]) -> Any:
    """根据解析后的路径提取数据"""
    current = data

    for part in path_parts:
        if current is None:
            return None

        if isinstance(part, int):
            # 数组索引
            if isinstance(current, list) and 0 <= part < len(current):
                current = current[part]
            else:
                return None
        elif part == '*':
            # 所有数组元素
            if isinstance(current, list):
                current = current  # 返回整个数组
            else:
                return None
        elif isinstance(part, str):
            # 对象属性
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

    return current


def extract_value(data: Any, path: Optional[str], regex: Optional[str]) -> Any:
    """根据 path 和 regex 提取值

    处理逻辑：
    1. 只有 path: 直接提取
    2. 只有 regex: 全文匹配
    3. path + regex: 先提取 path 的值，再用正则匹配
    """
    result = None

    # Step 1: 使用 path 提取
    if path:
        try:
            path_parts = parse_json_path(path)
            result = extract_by_path(data, path_parts)
        except ValueError:
            return None
    else:
        # 没有 path 时使用整个 JSON
        result = data

    # Step 2: 使用 regex 提取
    if regex and result is not None:
        # 将结果转为字符串进行正则匹配
        if isinstance(result, (dict, list)):
            str_value = json.dumps(result, ensure_ascii=False)
        else:
            str_value = str(result)

        matches = re.findall(regex, str_value)
        if matches:
            # 如果有捕获组，返回捕获组；否则返回整个匹配
            if isinstance(matches[0], tuple):
                return list(matches[0]) if len(matches[0]) > 1 else list(matches)
            else:
                return list(matches)

    return result


@router.post("/parse-json")
def parse_json_fields(
    request: ExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解析示例 JSON，提取字段值

    输入：
    {
        "json_str": "{...}",
        "fields": [
            {"key": "image_url", "path": "$.image.url"},
            {"key": "first_type", "path": "$.annotations[0].type"},
            {"key": "all_types", "path": "$.annotations", "regex": '"type":\\s*"(\\w+)"'}
        ]
    }

    输出：
    {
        "fields": [
            {"key": "image_url", "type": "string", "value": "/img/001.jpg"},
            {"key": "first_type", "type": "string", "value": "person"},
            {"key": "all_types", "type": "array", "value": ["person", "car"]}
        ]
    }
    """
    try:
        parsed = json.loads(request.json_str)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 格式错误：{str(e)}")

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="JSON 根节点必须是对象")

    fields = []
    for field_config in request.fields:
        value = extract_value(parsed, field_config.path, field_config.regex)
        fields.append({
            "key": field_config.key,
            "type": infer_type(value),
            "value": value,
            "path": field_config.path,
            "regex": field_config.regex
        })

    return {"fields": fields}


@router.post("/auto-discover")
def auto_discover_fields(
    request: ExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动发现 JSON 中的字段（保留原有功能）

    输入：{"json_str": "{...}"}
    输出：{"fields": [{"key": "...", "type": "..."}, ...]}
    """
    try:
        parsed = json.loads(request.json_str)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 格式错误：{str(e)}")

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="JSON 根节点必须是对象")

    fields = []
    for key, value in parsed.items():
        fields.append({
            "key": key,
            "type": infer_type(value),
            "nullable": value is None
        })

    return {"fields": fields}


@router.post("", response_model=ProjectResponse)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可创建项目")
    return ProjectService.create_project(db, project_in, current_user.id)


@router.get("", response_model=List[ProjectListItem])
def get_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="项目名称关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""
    skip = (page - 1) * page_size
    projects, total = ProjectService.get_projects(
        db, skip=skip, limit=page_size, keyword=keyword,
        created_by=None if current_user.role == "admin" else current_user.id
    )

    # 填充统计信息
    result = []
    for project in projects:
        task_count = db.query(Task).filter(Task.project_id == project.id).count()
        completed_count = db.query(Task).filter(
            Task.project_id == project.id,
            Task.status == "completed"
        ).count()
        project_dict = ProjectListItem.model_validate(project).model_dump()
        project_dict["task_count"] = task_count
        project_dict["completed_count"] = completed_count
        result.append(project_dict)

    return result


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情"""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """更新项目（仅管理员）"""
    try:
        project = ProjectService.update_project(db, project_id, project_in)
        return project
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """删除项目（仅管理员）"""
    try:
        ProjectService.delete_project(db, project_id)
        return {"message": "项目已删除"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
def get_project_statistics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目统计信息"""
    try:
        stats = ProjectService.get_project_statistics(db, project_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/annotation-config")
def get_annotation_page_config(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标注页面配置"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 返回 config_json，如果没有则返回空配置
    return project.config_json if project.config_json else {"modules": []}


@router.post("/{project_id}/annotation-config")
def save_annotation_page_config(
    project_id: int,
    config: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存标注页面配置"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查权限：仅创建者或管理员可修改
    if current_user.role != "admin" and project.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改此项目配置")

    # 更新配置
    project.config_json = config
    db.commit()
    db.refresh(project)

    return {"message": "配置已保存", "config": config}


@router.get("/{project_id}/images/{image_path:path}")
def get_project_image(
    project_id: int,
    image_path: str,
    db: Session = Depends(get_db)
):
    """获取项目图片（代理接口）

    根据 project.image_base_path + image_path 读取图片文件
    注意：此接口不需要认证，用于前端 <img> 标签直接访问
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.image_base_path:
        raise HTTPException(status_code=400, detail="项目未配置图片根目录")

    # 构建完整路径
    full_path = Path(project.image_base_path) / image_path

    # 调试输出
    print(f"[图片代理] project_id={project_id}")
    print(f"[图片代理] image_base_path={project.image_base_path}")
    print(f"[图片代理] image_path={image_path}")
    print(f"[图片代理] full_path={full_path}")
    print(f"[图片代理] full_path.exists()={full_path.exists()}")

    # 安全检查：确保路径在 image_base_path 内（防止目录遍历攻击）
    try:
        full_path = full_path.resolve()
        base_path = Path(project.image_base_path).resolve()
        print(f"[图片代理] resolved full_path={full_path}")
        print(f"[图片代理] resolved base_path={base_path}")
        if not str(full_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="非法路径")
    except Exception:
        raise HTTPException(status_code=400, detail="无效的路径")

    # 检查文件是否存在
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="不是有效文件")

    # 获取 MIME 类型
    mime_type, _ = mimetypes.guess_type(str(full_path))
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "application/octet-stream"

    # 读取文件
    try:
        with open(full_path, "rb") as f:
            content = f.read()
        return Response(content=content, media_type=mime_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
