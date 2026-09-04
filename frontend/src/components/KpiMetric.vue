<script setup lang="ts">
import { computed } from 'vue'
import type { KpiValue } from '@/types/dashboard'
import { format_change } from '@/utils/format'

const props = defineProps<{
  label: string
  display: string
  kpi: KpiValue
  invert?: boolean
}>()

const delta_class = computed(() => {
  if (props.kpi.hint || props.kpi.change_pct === null || props.kpi.change_pct === 0) return 'flat'
  const up = props.kpi.change_pct > 0
  if (props.invert) return up ? 'down' : 'up'
  return up ? 'up' : 'down'
})

const delta_text = computed(() => {
  if (props.kpi.hint) return props.kpi.hint
  return format_change(props.kpi.change_pct, props.kpi.compare_label)
})
</script>

<template>
  <article class="kpi">
    <div class="label">{{ label }}</div>
    <div class="value">{{ display }}</div>
    <div class="delta" :class="delta_class">{{ delta_text }}</div>
  </article>
</template>

<style scoped>
.kpi {
  height: 100%;
  padding: 14px 16px 12px;
  background: rgba(8, 28, 48, 0.55);
  border: 1px solid rgba(62, 198, 255, 0.2);
}

.label {
  color: var(--muted);
  font-size: 13px;
  letter-spacing: 0.12em;
}

.value {
  margin: 8px 0 6px;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  color: #f3fbff;
}

.delta {
  font-size: 12px;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

.flat {
  color: var(--muted);
}
</style>
