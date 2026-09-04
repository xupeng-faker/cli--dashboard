import axios, { type AxiosError } from 'axios'

const API_PREFIX = '/cli_api'

function get_api_base_url(): string {
  const base = import.meta.env.VITE_API_BASE_URL
  if (typeof base === 'string' && base.trim()) {
    return base.replace(/\/+$/, '')
  }
  return ''
}

export const http = axios.create({
  baseURL: `${get_api_base_url()}${API_PREFIX}`,
  timeout: 20000,
})

export function is_http_error(err: unknown): err is AxiosError {
  return axios.isAxiosError(err)
}
