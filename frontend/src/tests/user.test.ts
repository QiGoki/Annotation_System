/**
 * 用户 API 测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// 模拟 request
const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  },
}))

describe('User API', () => {
  let userApi: typeof import('@/api/user')

  beforeEach(async () => {
    // 清除 mocks
    vi.clearAllMocks()

    // 重新导入模块
    userApi = await import('@/api/user')
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should have correct API functions', () => {
    // 验证函数存在
    expect(userApi.login).toBeDefined()
    expect(userApi.getUserList).toBeDefined()
    expect(userApi.createUser).toBeDefined()
    expect(userApi.logout).toBeDefined()
  })

  it('login should call POST /auth/login', async () => {
    mockPost.mockResolvedValue({ data: { access_token: 'test-token' } })

    await userApi.login({ username: 'test', password: 'test123' })

    expect(mockPost).toHaveBeenCalledWith('/auth/login', {
      username: 'test',
      password: 'test123',
    })
  })

  it('getUserList should call GET /users', async () => {
    mockGet.mockResolvedValue({ data: [] })

    await userApi.getUserList({ page: 1, page_size: 20 })

    expect(mockGet).toHaveBeenCalledWith('/users', {
      params: { page: 1, page_size: 20 },
    })
  })

  it('createUser should call POST /auth/register', async () => {
    mockPost.mockResolvedValue({ data: {} })

    await userApi.createUser({
      username: 'newuser',
      password: 'password123',
      role: 'annotator',
    })

    expect(mockPost).toHaveBeenCalledWith('/auth/register', {
      username: 'newuser',
      password: 'password123',
      role: 'annotator',
    })
  })
})
