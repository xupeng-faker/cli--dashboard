<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ChartBox from '@/components/ChartBox.vue'
import KpiMetric from '@/components/KpiMetric.vue'
import RankList from '@/components/RankList.vue'
import ScreenHeader from '@/components/ScreenHeader.vue'
import ScreenPanel from '@/components/ScreenPanel.vue'
import ScreenLayout from '@/layouts/ScreenLayout.vue'
import { get_departments, get_overview, get_quality, get_users } from '@/api/dashboard'
import { useFilterStore } from '@/stores/filters'
import type { NamedMetric, OverviewPayload, QualityPayload, UsersPayload } from '@/types/dashboard'
import { bar_option, hbar_option, line_option, pie_option } from '@/utils/charts'
import {
  ERROR_CATEGORY_LABELS,
  RESULT_LABELS,
  format_bucket,
  format_number,
  label_of,
} from '@/utils/format'

const filters = useFilterStore()
const overview = ref<OverviewPayload | null>(null)
const quality = ref<QualityPayload | null>(null)
const users = ref<UsersPayload | null>(null)
const department_level = ref<4 | 5 | 6>(4)
const selected_dept4 = ref<string | null>(null)
const selected_dept5 = ref<string | null>(null)
const department_rows = ref<NamedMetric[]>([])
const loading = ref(true)
let load_seq = 0

function has_display_name(name: unknown): name is string {
  if (typeof name !== 'string') return false
  const text = name.trim()
  if (!text) return false
  const normalized = text.toLowerCase()
  return normalized !== 'unknown' && text !== '未知' && text !== '未填写部门'
}

async function load() {
  const seq = ++load_seq
  loading.value = true
  const query = filters.query
  try {
    const [ov, q, u] = await Promise.all([get_overview(query), get_quality(query), get_users(query)])
    if (seq !== load_seq) return
    overview.value = ov
    quality.value = q
    users.value = u
    department_level.value = 4
    selected_dept4.value = null
    selected_dept5.value = null
    department_rows.value = ov.dept4_dist
    filters.options.data_source = ov.data_source
  } catch {
    return
  } finally {
    if (seq === load_seq) loading.value = false
  }
}

watch(() => filters.query_key, load, { immediate: true })

const kpis = computed(() => overview.value?.kpis)
const trend_cumulative = computed(() => Boolean(overview.value?.range.cumulative))
const user_series_name = computed(() => {
  if (trend_cumulative.value) return '累计用户'
  return overview.value?.range.granularity === 'month' ? '月活用户' : '活跃用户'
})
const call_series_name = computed(() => (trend_cumulative.value ? '累计调用' : '调用量'))
const trend_title = computed(() => {
  if (trend_cumulative.value) {
    return overview.value?.range.granularity === 'month' ? '按月累增' : '按日累增'
  }
  return `调用量与${user_series_name.value}`
})
const department_title = computed(() => {
  if (department_level.value === 4) return '部门调用分布（点击下钻）'
  if (department_level.value === 5) return `${selected_dept4.value} · 5级部门`
  return `${selected_dept5.value} · 6级部门`
})

const trend_option = computed(() => {
  const rows = overview.value?.trend || []
  const start = rows.findIndex((item) => item.calls > 0)
  const visible = start < 0 ? rows : rows.slice(start)
  const granularity = overview.value?.range.granularity || 'month'
  return line_option(
    visible.map((item) => format_bucket(item.bucket, granularity)),
    [
      { name: call_series_name.value, data: visible.map((item) => item.calls) },
      { name: user_series_name.value, data: visible.map((item) => item.users), yAxisIndex: 1 },
    ],
    [call_series_name.value, user_series_name.value],
  )
})

const result_option = computed(() =>
  pie_option(
    (overview.value?.result_dist || []).map((item) => ({
      name: label_of(RESULT_LABELS, item.name),
      value: item.total_calls,
    })),
  ),
)

const department_option = computed(() =>
  pie_option(
    department_rows.value
      .filter((item) => has_display_name(item.name))
      .map((item) => ({
        name: item.name,
        value: item.total_calls,
      })),
  ),
)

async function show_department_level(level: 5 | 6, dept4: string, dept5?: string) {
  try {
    const response = await get_departments(filters.query, level, dept4, dept5)
    department_level.value = level
    selected_dept4.value = dept4
    selected_dept5.value = dept5 || null
    department_rows.value = response.departments
  } catch {
    return
  }
}

function drill_department(params: { name?: string }) {
  const name = params.name
  if (!has_display_name(name)) return
  if (department_level.value === 4) {
    void show_department_level(5, name)
  } else if (department_level.value === 5 && selected_dept4.value) {
    void show_department_level(6, selected_dept4.value, name)
  }
}

function back_department() {
  if (department_level.value === 6 && selected_dept4.value) {
    void show_department_level(5, selected_dept4.value)
    return
  }
  department_level.value = 4
  selected_dept4.value = null
  selected_dept5.value = null
  department_rows.value = overview.value?.dept4_dist || []
}

const platform_rows = computed(() =>
  (overview.value?.platform_dist || []).filter((item) => has_display_name(item.name)),
)

const platform_option = computed(() =>
  hbar_option(
    platform_rows.value.map((item) => item.name),
    platform_rows.value.map((item) => item.total_calls),
    78,
  ),
)

const command_option = computed(() =>
  hbar_option(
    (overview.value?.top_commands || []).slice(0, 8).map((item) => item.command),
    (overview.value?.top_commands || []).slice(0, 8).map((item) => item.total_calls),
    280,
  ),
)

const error_option = computed(() =>
  pie_option(
    (quality.value?.error_categories || []).map((item) => ({
      name: label_of(ERROR_CATEGORY_LABELS, item.name),
      value: item.total_calls,
    })),
  ),
)

const domain_rows = computed(() =>
  (overview.value?.domain_dist || []).filter((item) => has_display_name(item.name)),
)

const domain_option = computed(() =>
  bar_option(
    domain_rows.value.map((item) => item.name),
    domain_rows.value.map((item) => item.total_calls),
    '调用量',
  ),
)

const user_items = computed(() =>
  (users.value?.users || []).slice(0, 8).map((item) => ({
    title: `${item.user_cn_name}  ${item.user_id}`,
    value: format_number(item.total_calls),
  })),
)
</script>

<template>
  <ScreenLayout>
    <ScreenHeader />
    <div class="body">
      <div v-if="loading" class="loading-mask">
        <div class="spinner" />
        <span>数据加载中</span>
      </div>
      <div class="kpis" v-if="kpis">
        <KpiMetric label="累计调用" :display="format_number(kpis.total_calls.value)" :kpi="kpis.total_calls" />
        <KpiMetric label="累计用户" :display="format_number(kpis.total_users.value)" :kpi="kpis.total_users" />
        <KpiMetric label="月活用户" :display="format_number(kpis.mau.value)" :kpi="kpis.mau" />
        <KpiMetric label="本月新增用户" :display="format_number(kpis.new_users.value)" :kpi="kpis.new_users" />
        <KpiMetric label="本月调用" :display="format_number(kpis.month_calls.value)" :kpi="kpis.month_calls" />
        <KpiMetric
          label="本月人均调用"
          :display="format_number(kpis.avg_calls_per_user.value)"
          :kpi="kpis.avg_calls_per_user"
        />
      </div>

      <div class="grid">
      <div class="col">
        <ScreenPanel title="执行结果">
          <ChartBox :option="result_option" />
        </ScreenPanel>
        <ScreenPanel title="错误分类">
          <ChartBox :option="error_option" />
        </ScreenPanel>
        <ScreenPanel title="平台调用量">
          <ChartBox :option="platform_option" />
        </ScreenPanel>
      </div>

      <div class="col center">
        <ScreenPanel :title="trend_title">
          <ChartBox :option="trend_option" />
        </ScreenPanel>
        <ScreenPanel title="热门指令">
          <ChartBox :option="command_option" />
        </ScreenPanel>
      </div>

      <div class="col">
        <ScreenPanel title="领域调用分布">
          <ChartBox :option="domain_option" />
        </ScreenPanel>
        <ScreenPanel :title="department_title">
          <template #action>
            <button v-if="department_level > 4" class="back-button" type="button" @click="back_department">
              返回上级
            </button>
          </template>
          <ChartBox :option="department_option" @click="drill_department" />
        </ScreenPanel>
        <ScreenPanel title="用户调用 TOP">
          <RankList :items="user_items" />
        </ScreenPanel>
      </div>
    </div>
    </div>
  </ScreenLayout>
</template>

<style scoped>
.body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  position: relative;
}

.loading-mask {
  position: absolute;
  inset: 0;
  z-index: 8;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background: rgba(3, 10, 20, 0.72);
  color: var(--accent);
  font-size: 13px;
  letter-spacing: 0.22em;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(62, 198, 255, 0.18);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.kpis {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  height: 108px;
  flex: none;
  margin-bottom: 12px;
}

.grid {
  display: grid;
  grid-template-columns: 420px 1fr 420px;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.col {
  display: grid;
  grid-template-rows: 1fr 1fr 1fr;
  gap: 12px;
  min-height: 0;
}

.center {
  grid-template-rows: 1.15fr 0.85fr;
}

.back-button {
  padding: 2px 8px;
  color: var(--accent);
  font: inherit;
  font-size: 12px;
  background: rgba(62, 198, 255, 0.08);
  border: 1px solid rgba(62, 198, 255, 0.3);
  cursor: pointer;
}
</style>
