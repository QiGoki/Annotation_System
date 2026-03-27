/**
 * 任务 API
 */
import request from '@/utils/request'
import type { Task, TaskAssign, TaskStatusUpdate } from '@/types/task'

/**
 * 获取任务列表
 */
export function getTaskList(params?: { project_id?: number; status?: string; assigned_to?: number; page?: number; page_size?: number }) {
  return request.get<Task[]>('/tasks', { params })
}

/**
 * 获取待办任务
 */
export function getPendingTasks() {
  return request.get<Task[]>('/tasks/pending')
}

/**
 * 获取任务详情
 */
export function getTaskDetail(taskId: number) {
  return request.get(`/tasks/${taskId}`)
}

/**
 * 分配任务
 */
export function assignTask(taskId: number, data: TaskAssign) {
  return request.put(`/tasks/${taskId}/assign`, data)
}

/**
 * 更新任务状态
 */
export function updateTaskStatus(taskId: number, data: TaskStatusUpdate) {
  return request.put(`/tasks/${taskId}/status`, data)
}

/**
 * 获取下一条任务
 */
export function getNextTask(taskId: number) {
  return request.get(`/tasks/${taskId}/next`)
}

/**
 * 保存标注
 */
export function saveAnnotation(taskId: number, data: { result_json: Record<string, any> }) {
  return request.post(`/tasks/${taskId}/annotate`, data)
}

/**
 * 提交标注
 */
export function submitAnnotation(taskId: number, data: { result_json: Record<string, any> }) {
  return request.post(`/tasks/${taskId}/submit`, data)
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
