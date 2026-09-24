/**
 * Axios 统一网络请求与拦截器封装存根
 * 
 * 职责:
 *  - 注入全局 X-Trace-Id 请求头
 *  - 注入 Bearer Access Token
 *  - 401 状态码无感调用 refresh_token 换签重试机制存根
 *  - 统一业务错误弹窗提示
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

service.interceptors.request.use(
  (config) => {
    // 注入 TraceID 与 Token 存根
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    // 401 自动无感续签存根
    return Promise.reject(error)
  }
)

export default service
