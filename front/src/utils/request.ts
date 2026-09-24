/**
 * Axios 统一网络请求与拦截器封装
 * 
 * 职责:
 *  - 注入全局 X-Trace-Id 请求头 (RedLine 4: 全链路穿透)
 *  - 注入 Bearer Access Token
 *  - 401 状态码无感调用 refresh_token 换签重试机制 (RedLine 3)
 *  - 统一业务异常与网络错误处理
 */

import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

interface CustomRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback)
}

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

export const generateTraceId = (): string => {
  return `trace-kg-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`
}

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 注入 TraceID
    if (!config.headers['X-Trace-Id']) {
      config.headers['X-Trace-Id'] = generateTraceId()
    }

    // 注入 Access Token
    const accessToken = localStorage.getItem('access_token')
    if (accessToken && !config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${accessToken}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config as CustomRequestConfig | undefined

    // 401 自动无感续签机制
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_context')
        if (window.location.pathname !== '/login') {
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`
        }
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            if (originalRequest.headers) {
              originalRequest.headers['Authorization'] = `Bearer ${newToken}`
            }
            resolve(service(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const refreshResponse = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${refreshToken}`,
              'X-Trace-Id': generateTraceId()
            }
          }
        )

        const newTokenData = refreshResponse.data?.data
        const newAccessToken = newTokenData?.access_token

        if (newAccessToken) {
          localStorage.setItem('access_token', newAccessToken)
          if (newTokenData.refresh_token) {
            localStorage.setItem('refresh_token', newTokenData.refresh_token)
          }

          if (originalRequest.headers) {
            originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
          }

          onRefreshed(newAccessToken)
          return service(originalRequest)
        } else {
          throw new Error('Refresh token invalid response')
        }
      } catch (refreshErr) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_context')
        if (window.location.pathname !== '/login') {
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`
        }
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default service
