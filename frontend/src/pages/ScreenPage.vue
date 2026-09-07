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

async function load() {
  const query = filters.query
  try {
    const [ov, q, u] = await Promise.all([get_overview(query), get_quality(query), get_users(query)])
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
  }
}

watch(() => filters.query_key, load, { immediate: true })

const kpis = computed(() => overview.value?.kpis)
const user_series_name = computed(() => (overview.value?.range.granularity === 'month' ? '月活用户' : '活跃用户'))
const department_title = computed(() => {
  if (department_level.value === 4) return '部门调用分布（点击下钻）'
  if (department_level.value === 5) return `${selected_dept4.value} · 5级部门`
  return `${selected_dept5.value} · 6级部门`
})

const trend_option = computed(() => {
  const rows = overview.value?.trend || []
  const granularity = overview.value?.range.granularity || 'month'
  return line_option(
    rows.map((item) => format_bucket(item.bucket, granularity)),
    [
      { name: '调用量', data: rows.map((item) => item.calls) },
      { name: user_series_name.value, data: rows.map((item) => item.users), yAxisIndex: 1 },
    ],
    ['调用量', user_series_name.value],
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
    department_rows.value.map((item) => ({
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
  if (!name || name === '未填写部门') return
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

const platform_option = computed(() =>
  bar_option(
    (overview.value?.platform_dist || []).map((item) => item.name),
    (overview.value?.platform_dist || []).map((item) => item.total_calls),
    '调用量',
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

const domain_option = computed(() =>
  bar_option(
    (overview.value?.domain_dist || []).map((item) => item.name),
    (overview.value?.domain_dist || []).map((item) => item.total_calls),
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
        <ScreenPanel :title="`调用量与${user_series_name}`">
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
  </ScreenLayout>
</template>

<style scoped>
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
