"""
项目成员管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_admin_user
from app.models.user import User
from app.models.project import Project
from app.services.project_member_service import ProjectMemberService
from app.services.project_service import ProjectService


router = APIRouter()


class MemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    role: str
    joined_at: str


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: str = "member"


class ProjectMemberUpdate(BaseModel):
    role: str


@router.get("/{project_id}/members", response_model=List[MemberResponse])
def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目成员列表（仅项目成员可访问）"""
    # 检查权限：只有项目成员可以查看成员列表
    is_member = ProjectMemberService.is_member(db, project_id, current_user.id)
    if not is_member:
        # 管理员可以查看所有项目
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权访问该项目")

    members = ProjectMemberService.get_project_members(db, project_id)

    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "username": user.username if user else "未知",
            "role": m.role,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None
        })
    return result


@router.post("/{project_id}/members")
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """添加项目成员（仅管理员）"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 只有项目创建者或系统管理员可以添加成员
        if project.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权添加成员")

        member = ProjectMemberService.add_member(
            db,
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role
        )
        return {"message": "添加成员成功", "member_id": member.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """移除项目成员（仅管理员）"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 只有项目创建者或系统管理员可以移除成员
        if project.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权移除成员")

        ProjectMemberService.remove_member(db, project_id, user_id)
        return {"message": "移除成员成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}/members/{user_id}/role")
def update_member_role(
    project_id: int,
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    """更新成员角色（仅管理员）"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 只有项目创建者或系统管理员可以更新角色
        if project.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权更新角色")

        member = ProjectMemberService.update_member_role(db, project_id, user_id, role)
        return {"message": "更新角色成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-projects", response_model=List[dict])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我参与的项目列表"""
    projects = ProjectMemberService.get_user_projects(db, current_user.id)

    # 也包含创建的项目
    created_projects = db.query(Project).filter(
        Project.created_by == current_user.id,
        Project.is_deleted == False
    ).all()

    # 合并去重
    all_project_ids = set([p.id for p in projects] + [p.id for p in created_projects])
    all_projects = db.query(Project).filter(Project.id.in_(all_project_ids)).all()

    result = []
    for proj in all_projects:
        # 统计任务数
        from app.models.task import Task
        total_tasks = db.query(Task).filter(Task.project_id == proj.id).count()
        pending_tasks = db.query(Task).filter(
            Task.project_id == proj.id,
            Task.status == "pending"
        ).count()

        result.append({
            "id": proj.id,
            "name": proj.name,
            "description": proj.description,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "role": "owner" if proj.created_by == current_user.id else "member"
        })

    return result
