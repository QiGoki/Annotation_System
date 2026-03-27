/**
 * 项目 API
 */
import request from '@/utils/request'
import type { Project, ProjectCreate, ProjectStatistics } from '@/types/project'

/**
 * 获取项目列表
 */
export function getProjectList(params?: { page?: number; page_size?: number; keyword?: string }) {
  return request.get<Project[]>('/projects', { params })
}

/**
 * 获取项目详情
 */
export function getProjectDetail(projectId: number) {
  return request.get<Project>(`/projects/${projectId}`)
}

/**
 * 创建项目
 */
export function createProject(data: ProjectCreate) {
  return request.post<Project>('/projects', data)
}

/**
 * 更新项目
 */
export function updateProject(projectId: number, data: Partial<ProjectCreate>) {
  return request.put<Project>(`/projects/${projectId}`, data)
}

/**
 * 删除项目
 */
export function deleteProject(projectId: number) {
  return request.delete(`/projects/${projectId}`)
}

/**
 * 获取项目统计信息
 */
export function getProjectStatistics(projectId: number) {
  return request.get<ProjectStatistics>(`/projects/${projectId}/statistics`)
}

/**
 * 保存标注页面配置
 */
export function saveAnnotationPageConfig(projectId: number, config: any) {
  return request.post(`/projects/${projectId}/annotation-config`, config)
}

/**
 * 获取标注页面配置
 */
export function getAnnotationPageConfig(projectId: number) {
  return request.get<any>(`/projects/${projectId}/annotation-config`)
}
