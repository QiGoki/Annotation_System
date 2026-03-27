/**
 * 用户类型定义
 */
export interface User {
  id: number
  username: string
  role: 'admin' | 'annotator'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  role: 'admin' | 'annotator'
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}
