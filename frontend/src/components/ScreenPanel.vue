<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <section class="panel">
    <header class="head">
      <span class="mark" />
      <h3>{{ title }}</h3>
      <div class="action">
        <slot name="action" />
      </div>
    </header>
    <div class="body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.panel {
  position: relative;
  height: 100%;
  min-height: 0;
  background: var(--panel);
  border: 1px solid rgba(62, 198, 255, 0.22);
  display: flex;
  flex-direction: column;
}

.panel::before,
.panel::after {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  border-color: var(--accent);
  border-style: solid;
  pointer-events: none;
}

.panel::before {
  top: -1px;
  left: -1px;
  border-width: 2px 0 0 2px;
}

.panel::after {
  right: -1px;
  bottom: -1px;
  border-width: 0 2px 2px 0;
}

.head {
  height: 36px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(62, 198, 255, 0.16);
}

.mark {
  width: 8px;
  height: 8px;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
}

h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.action {
  margin-left: auto;
}

.body {
  flex: 1;
  min-height: 0;
  padding: 8px 10px 10px;
  display: flex;
}

.body > :deep(*) {
  flex: 1;
  min-height: 0;
  min-width: 0;
}
</style>
