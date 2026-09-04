<script setup lang="ts">
defineProps<{
  items: { title: string; meta: string; value: string }[]
}>()
</script>

<template>
  <ol class="rank">
    <li v-for="(item, index) in items" :key="item.title + index">
      <span class="idx">{{ String(index + 1).padStart(2, '0') }}</span>
      <div class="copy">
        <div class="title">{{ item.title }}</div>
        <div class="meta">{{ item.meta }}</div>
      </div>
      <span class="value">{{ item.value }}</span>
    </li>
  </ol>
</template>

<style scoped>
.rank {
  list-style: none;
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

li {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  gap: 8px;
  align-items: center;
  height: 12.5%;
  border-bottom: 1px solid rgba(62, 198, 255, 0.08);
}

.idx {
  color: var(--accent);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta {
  color: var(--muted);
  font-size: 11px;
}

.value {
  font-variant-numeric: tabular-nums;
  color: #f3fbff;
}
</style>
