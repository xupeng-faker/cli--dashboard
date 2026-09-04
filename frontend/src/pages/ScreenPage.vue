<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ChartBox from '@/components/ChartBox.vue'
import KpiMetric from '@/components/KpiMetric.vue'
import RankList from '@/components/RankList.vue'
import ScreenHeader from '@/components/ScreenHeader.vue'
import ScreenPanel from '@/components/ScreenPanel.vue'
import ScreenLayout from '@/layouts/ScreenLayout.vue'
import { get_overview, get_quality, get_users } from '@/api/dashboard'
import { useFilterStore } from '@/stores/filters'
import type { OverviewPayload, QualityPayload, UsersPayload } from '@/types/dashboard'
import { bar_option, hbar_option, line_option, pie_option } from '@/utils/charts'
import {
  ERROR_CATEGORY_LABELS,
  RESULT_LABELS,
  format_bucket,
  format_duration,
  format_number,
  format_pct,
  label_of,
} from '@/utils/format'

const filters = useFilterStore()
const overview = ref<OverviewPayload | null>(null)
const quality = ref<QualityPayload | null>(null)
const users = ref<UsersPayload | null>(null)

async function load() {
  const query = filters.query
  try {
    const [ov, q, u] = await Promise.all([get_overview(query), get_quality(query), get_users(query)])
    overview.value = ov
    quality.value = q
    users.value = u
    filters.options.data_source = ov.data_source
  } catch {
    return
  }
}

watch(() => filters.query_key, load, { immediate: true })

const kpis = computed(() => overview.value?.kpis)
const user_series_name = computed(() => (overview.value?.range.granularity === 'month' ? '月活用户' : '活跃用户'))

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

const dept5_option = computed(() =>
  pie_option(
    (overview.value?.dept5_dist || []).map((item) => ({
      name: item.name,
      value: item.total_calls,
    })),
  ),
)

const platform_option = computed(() =>
  bar_option(
    (overview.value?.platform_dist || []).map((item) => item.name),
    (overview.value?.platform_dist || []).map((item) => item.total_calls),
    '调用量',
  ),
)

const command_option = computed(() =>
  hbar_option(
    (overview.value?.top_commands || []).slice(0, 8).map((item) => item.command_name + ' / ' + item.domain),
    (overview.value?.top_commands || []).slice(0, 8).map((item) => item.total_calls),
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

const duration_option = computed(() =>
  bar_option(
    (quality.value?.duration_histogram || []).map((item) => item.name),
    (quality.value?.duration_histogram || []).map((item) => item.total_calls),
    '调用量',
  ),
)

const user_items = computed(() =>
  (users.value?.users || []).slice(0, 8).map((item) => ({
    title: `${item.user_cn_name}  ${item.user_id}`,
    meta: item.org_dept_name4 || '',
    value: format_number(item.total_calls),
  })),
)
</script>

<template>
  <ScreenLayout>
    <ScreenHeader />
    <div class="kpis" v-if="kpis">
      <KpiMetric label="累计调用" :display="format_number(kpis.total_calls.value)" :kpi="kpis.total_calls" />
      <KpiMetric label="月活用户" :display="format_number(kpis.mau.value)" :kpi="kpis.mau" />
      <KpiMetric label="本月调用" :display="format_number(kpis.month_calls.value)" :kpi="kpis.month_calls" />
      <KpiMetric label="成功率" :display="format_pct(kpis.success_rate.value)" :kpi="kpis.success_rate" />
      <KpiMetric label="平均耗时" :display="format_duration(kpis.avg_duration_ms.value)" :kpi="kpis.avg_duration_ms" invert />
      <KpiMetric label="P95 耗时" :display="format_duration(kpis.p95_duration_ms.value)" :kpi="kpis.p95_duration_ms" invert />
    </div>

    <div class="grid">
      <div class="col">
        <ScreenPanel title="执行结果">
          <ChartBox :option="result_option" />
        </ScreenPanel>
        <ScreenPanel title="5级各部门调用分布">
          <ChartBox :option="dept5_option" />
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
        <ScreenPanel title="错误分类">
          <ChartBox :option="error_option" />
        </ScreenPanel>
        <ScreenPanel title="耗时分布">
          <ChartBox :option="duration_option" />
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
</style>
