import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { DashboardQuery, FilterOptions } from '@/types/dashboard'
import { get_filter_options } from '@/api/dashboard'

export type RangePreset = 'month' | '3m' | '12m' | 'all'

function start_of_month(date = new Date()): Date {
  const start = new Date(date)
  start.setDate(1)
  start.setHours(0, 0, 0, 0)
  return start
}

function add_months(date: Date, months: number): Date {
  const next = new Date(date)
  next.setMonth(next.getMonth() + months)
  return next
}

function format_date(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function range_of(preset: RangePreset): [Date, Date] {
  const end = new Date()
  if (preset === 'month') return [start_of_month(end), end]
  if (preset === '3m') return [add_months(end, -3), end]
  if (preset === '12m') return [add_months(end, -12), end]
  return [new Date(2020, 0, 1), end]
}

export const useFilterStore = defineStore('filters', () => {
  const preset = ref<RangePreset>('all')
  const date_range = ref<[Date, Date]>(range_of('all'))
  const options = ref<FilterOptions>({
    data_source: 'mock',
    domains: [],
    platforms: [],
    environments: [],
    results: [],
    command_names: [],
    input_sources: [],
    cli_versions: [],
  })

  const query = computed<DashboardQuery>(() => ({
    start: date_range.value[0].toISOString(),
    end: date_range.value[1].toISOString(),
  }))

  const query_key = computed(() => JSON.stringify(query.value))

  const range_label = computed(() => `${format_date(date_range.value[0])}  ~  ${format_date(date_range.value[1])}`)

  async function load_options() {
    options.value = await get_filter_options(query.value)
  }

  function apply_preset(next: RangePreset) {
    preset.value = next
    date_range.value = range_of(next)
  }

  return {
    preset,
    date_range,
    options,
    query,
    query_key,
    range_label,
    load_options,
    apply_preset,
  }
})
