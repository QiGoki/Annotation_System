/**
 * 项目成员管理 API
 */
import request from '@/utils/request'

export interface ProjectMember {
  id: number
  user_id: number
  username: string
  role: 'admin' | 'member'
  joined_at: string
}

export interface MyProject {
  id: number
  name: string
  description: string
  total_tasks: number
  pending_tasks: number
  role: 'owner' | 'member'
}

/**
 * 获取我的项目列表
 */
export function getMyProjects() {
  return request.get<MyProject[]>('/project-members/my-projects')
}

/**
 * 获取项目成员列表
 */
export function getProjectMembers(projectId: number) {
  return request.get<ProjectMember[]>(`/project-members/${projectId}/members`)
}

/**
 * 添加项目成员
 */
export function addProjectMember(projectId: number, userId: number, role: string = 'member') {
  return request.post(`/project-members/${projectId}/members`, { user_id: userId, role })
}

/**
 * 移除项目成员
 */
export function removeProjectMember(projectId: number, userId: number) {
  return request.delete(`/project-members/${projectId}/members/${userId}`)
}

/**
 * 更新成员角色
 */
export function updateMemberRole(projectId: number, userId: number, role: string) {
  return request.put(`/project-members/${projectId}/members/${userId}/role`, null, { params: { role } })
}

/**
 * 领取任务
 */
export function claimTask(taskId: number) {
  return request.post(`/tasks/${taskId}/claim`)
}

/**
 * 释放任务
 */
export function releaseTask(taskId: number) {
  return request.post(`/tasks/${taskId}/release`)
}
