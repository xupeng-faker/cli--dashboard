<script setup lang="ts">
import { useFilterStore, type RangePreset } from '@/stores/filters'

const filters = useFilterStore()

const presets: { label: string; id: RangePreset }[] = [
  { label: '本月', id: 'month' },
  { label: '近 3 月', id: '3m' },
  { label: '近 12 月', id: '12m' },
  { label: '全部', id: 'all' },
]
</script>

<template>
  <header class="header">
    <div class="side">
      <div class="kicker">STAT WINDOW</div>
      <div class="clock">{{ filters.range_label }}</div>
    </div>
    <div class="title-wrap">
      <div class="wing" />
      <div class="title">
        <div class="en">CORETOOLCLI USAGE</div>
        <h1>CoreToolCLI 使用概览</h1>
      </div>
      <div class="wing right" />
    </div>
    <div class="side right">
      <div class="presets">
        <button
          v-for="item in presets"
          :key="item.id"
          type="button"
          :class="{ active: filters.preset === item.id }"
          @click="filters.apply_preset(item.id)"
        >
          {{ item.label }}
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  height: 86px;
  flex: none;
  display: grid;
  grid-template-columns: 300px 1fr 420px;
  align-items: center;
}

.side .kicker {
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.18em;
}

.clock {
  margin-top: 4px;
  font-size: 18px;
  letter-spacing: 0.06em;
  font-variant-numeric: tabular-nums;
}

.right {
  text-align: right;
}

.title-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.wing {
  width: 160px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent));
  position: relative;
}

.wing.right {
  background: linear-gradient(90deg, var(--accent), transparent);
}

.wing::after {
  content: '';
  position: absolute;
  right: 0;
  top: -4px;
  width: 10px;
  height: 10px;
  border: 2px solid var(--accent);
  transform: rotate(45deg);
}

.wing.right::after {
  right: auto;
  left: 0;
}

.title {
  text-align: center;
}

.en {
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.28em;
}

h1 {
  margin: 4px 0 0;
  font-size: 30px;
  font-weight: 650;
  letter-spacing: 0.18em;
}

.presets {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.presets button {
  background: transparent;
  color: var(--muted);
  border: 1px solid rgba(62, 198, 255, 0.28);
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12px;
}

.presets button.active {
  color: #061018;
  background: var(--accent);
  border-color: var(--accent);
}
</style>
