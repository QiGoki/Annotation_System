/**
 * API 响应类型
 */
export interface ApiResponse<T = any> {
  code: number
  data: T
  message?: string
}

/**
 * 分页响应类型
 */
export interface PageResponse<T = any> {
  total: number
  page: number
  page_size: number
  items: T[]
}
