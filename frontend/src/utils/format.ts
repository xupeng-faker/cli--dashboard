export function format_number(value: number): string {
  return Math.round(value).toLocaleString('zh-CN')
}

export function format_decimal(value: number, digits = 1): string {
  return value.toLocaleString('zh-CN', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

export function format_pct(value: number): string {
  return `${format_decimal(value, 1)}%`
}

export function format_duration(ms: number): string {
  if (!Number.isFinite(ms)) return '-'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${Math.round(ms)}ms`
}

export function format_time(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function format_bucket(value: string, granularity: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n: number) => String(n).padStart(2, '0')
  if (granularity === 'month') return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`
  const month = `${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  if (granularity === 'hour') return `${month} ${pad(date.getHours())}:00`
  return month
}

export function format_change(value: number | null, label = '较上周期'): string {
  if (value === null || Number.isNaN(value)) return `${label} —`
  const prefix = value > 0 ? '+' : ''
  return `${label} ${prefix}${value.toFixed(1)}%`
}

export const RESULT_LABELS: Record<string, string> = {
  success: '成功',
  failure: '失败',
  usage_error: '用法错误',
  interrupted: '中断',
}

export const INPUT_SOURCE_LABELS: Record<string, string> = {
  windows: 'Windows',
  darwin: 'macOS',
  linux: 'Linux',
}

export const ERROR_CATEGORY_LABELS: Record<string, string> = {
  network: '网络',
  auth: '鉴权',
  validation: '参数校验',
  business: '业务',
  unknown: '未知',
}

export function label_of(map: Record<string, string>, key: string): string {
  return map[key] || key
}
