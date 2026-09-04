<script setup lang="ts">
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'
import { computed } from 'vue'

const props = defineProps<{
  option: EChartsOption
}>()

const chart_key = computed(() => JSON.stringify(props.option.series ?? []))
</script>

<template>
  <VChart :key="chart_key" class="chart" :option="option" autoresize />
</template>

<style scoped>
.chart {
  width: 100%;
  height: 100%;
}
</style>
