import axios from 'axios'
import type { ApiError } from '../types'
export const api = axios.create({baseURL:'/api',timeout:15000})
api.interceptors.request.use(config => {
  const token = sessionStorage.getItem('lichu_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use(response => response, error => {
  if (axios.isAxiosError(error) && error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
    sessionStorage.removeItem('lichu_token')
    window.dispatchEvent(new Event('lichu:unauthorized'))
  }
  return Promise.reject(error)
})
export function errorOf(error:unknown):ApiError {
  if (axios.isAxiosError<ApiError>(error) && error.response?.data?.message) return error.response.data
  return {code:'NETWORK_ERROR',message:'서버에 연결할 수 없습니다. 연결 상태를 확인하고 다시 시도해주세요.',fields:{}}
}
