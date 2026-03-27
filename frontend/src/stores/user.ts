/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login, logout } from '@/api/user'
import type { User, LoginParams } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const user = ref<User | null>(null)

  /**
   * 登录
   */
  const loginAction = async (params: LoginParams) => {
    const res = await login(params)
    token.value = res.access_token
    user.value = res.user
    // 存储 token 到 localStorage
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
  }

  /**
   * 登出
   */
  const logoutAction = async () => {
    try {
      await logout()
    } catch (e) {
      // 忽略错误
    } finally {
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  /**
   * 初始化用户状态（从 localStorage 恢复）
   */
  const initUser = () => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    if (storedToken && storedUser) {
      token.value = storedToken
      user.value = JSON.parse(storedUser)
    }
  }

  return {
    token,
    user,
    login: loginAction,
    logout: logoutAction,
    initUser,
  }
})
