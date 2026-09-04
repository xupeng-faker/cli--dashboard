export interface KpiValue {
  value: number
  prev: number
  change_pct: number | null
  compare_label?: string
  hint?: string
}

export interface TimeRangeMeta {
  start: string
  end: string
  granularity: 'hour' | 'day' | 'week' | 'month'
}

export interface MetricRow {
  name?: string
  total_calls: number
  unique_users: number
  success_count: number
  failure_count: number
  success_rate: number
  avg_duration_ms: number
  avg_api_duration_ms: number
  p50_duration_ms: number
  p95_duration_ms: number
}

export interface TrendPoint {
  bucket: string
  calls: number
  users: number
  success_rate: number
  avg_duration_ms: number
  avg_api_duration_ms: number
}

export interface CommandRow extends MetricRow {
  domain: string
  platform: string
  command: string
  command_name: string
}

export interface UserRow extends MetricRow {
  user_id: string
  user_cn_name: string
  org_dept_name4: string | null
  org_dept_name5: string | null
  last_seen: string
}

export interface NamedMetric extends MetricRow {
  name: string
}

export interface OverviewPayload {
  data_source: 'mock' | 'gaussdb'
  range: TimeRangeMeta
  kpis: {
    total_calls: KpiValue
    mau: KpiValue
    month_calls: KpiValue
    success_rate: KpiValue
    avg_duration_ms: KpiValue
    p95_duration_ms: KpiValue
  }
  trend: TrendPoint[]
  result_dist: NamedMetric[]
  domain_dist: NamedMetric[]
  platform_dist: NamedMetric[]
  input_source_dist: NamedMetric[]
  dept5_dist: NamedMetric[]
  top_commands: CommandRow[]
}

export interface CommandsPayload {
  data_source: 'mock' | 'gaussdb'
  range: TimeRangeMeta
  commands: CommandRow[]
  cli_versions: NamedMetric[]
  output_formats: NamedMetric[]
  input_sources: NamedMetric[]
  domains: NamedMetric[]
}

export interface UsersPayload {
  data_source: 'mock' | 'gaussdb'
  range: TimeRangeMeta
  users: UserRow[]
  departments: NamedMetric[]
  environments: NamedMetric[]
  trend: TrendPoint[]
}

export interface QualityPayload {
  data_source: 'mock' | 'gaussdb'
  range: TimeRangeMeta
  metrics: MetricRow
  trend: TrendPoint[]
  error_categories: NamedMetric[]
  error_codes: NamedMetric[]
  slow_commands: CommandRow[]
  duration_histogram: { name: string; total_calls: number }[]
}

export interface CommandEvent {
  id: number
  event_id: string
  event_time: string
  cli_version: string
  domain: string
  platform: string | null
  command: string
  command_name: string
  duration_ms: number
  api_duration_ms: number | null
  api_calls: Array<Record<string, unknown>> | null
  input_source: string
  output_format: string | null
  result: string
  exit_code: number
  environment: string
  error_category: string | null
  error_code: string | null
  args_detail: Record<string, unknown>
  user_id: string
  user_cn_name: string
  user_long_id: string
  org_dept_code4: string | null
  org_dept_name4: string | null
  org_dept_code5: string | null
  org_dept_name5: string | null
  org_dept_code6: string | null
  org_dept_name6: string | null
}

export interface EventsPayload {
  data_source: 'mock' | 'gaussdb'
  range: TimeRangeMeta
  items: CommandEvent[]
  total: number
  limit: number
  offset: number
}

export interface FilterOptions {
  data_source: 'mock' | 'gaussdb'
  domains: string[]
  platforms: string[]
  environments: string[]
  results: string[]
  command_names: string[]
  input_sources: string[]
  cli_versions: string[]
}

export interface DashboardQuery {
  start: string
  end: string
  domain?: string
  platform?: string
  environment?: string
  result?: string
  command_name?: string
  user_id?: string
  input_source?: string
  keyword?: string
}
