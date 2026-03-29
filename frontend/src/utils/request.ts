import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'

const baseURL = '/api/v1'

// 简单的消息提示函数
const showMessage = (message: string, type: 'error' | 'success' | 'warning' = 'error') => {
  // 创建消息元素
  const container = document.createElement('div')
  container.className = `global-message global-message-${type}`
  container.textContent = message
  document.body.appendChild(container)

  // 3秒后自动移除
  setTimeout(() => {
    container.remove()
  }, 3000)
}

class Request {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
    })

    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        const userStore = useUserStore()
        if (userStore.token) {
          config.headers.Authorization = `Bearer ${userStore.token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response.data
      },
      (error) => {
        if (error.response) {
          const { status, data } = error.response
          if (status === 401) {
            // Token 过期，跳转登录
            const userStore = useUserStore()
            userStore.logout()
            window.location.href = '/login'
          } else {
            showMessage(data?.detail || '请求失败', 'error')
          }
        } else {
          showMessage('网络错误', 'error')
        }
        return Promise.reject(error)
      }
    )
  }

  public get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.get(url, config)
  }

  public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.post(url, data, config)
  }

  public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.put(url, data, config)
  }

  public delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.delete(url, config)
  }
}

export const request = new Request()
export default request