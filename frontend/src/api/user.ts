/**
 * 用户 API
 */
import request from '@/utils/request'
import type { User, LoginParams, TokenResponse } from '@/types/user'

/**
 * 用户登录
 */
export function login(data: LoginParams) {
  return request.post<TokenResponse>('/auth/login', data)
}

/**
 * 用户登出
 */
export function logout() {
  return request.post('/auth/logout')
}

/**
 * 修改密码
 */
export function changePassword(data: { old_password: string; new_password: string }) {
  return request.post('/auth/change-password', data)
}

/**
 * 获取用户列表
 */
export function getUserList(params?: { page?: number; page_size?: number; role?: string; keyword?: string }) {
  return request.get<User[]>('/users', { params })
}

/**
 * 获取用户详情
 */
export function getUserDetail(userId: number) {
  return request.get<User>(`/users/${userId}`)
}

/**
 * 创建用户
 */
export function createUser(data: { username: string; password: string; role: string }) {
  return request.post<User>('/auth/register', data)
}

/**
 * 更新用户状态
 */
export function updateUserStatus(userId: number, is_active: boolean) {
  return request.put<User>(`/users/${userId}/status`, null, { params: { is_active } })
}

/**
 * 删除用户
 */
export function deleteUser(userId: number) {
  return request.delete(`/users/${userId}`)
}
