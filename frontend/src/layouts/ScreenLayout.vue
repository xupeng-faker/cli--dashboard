<script setup lang="ts">
import { ref } from 'vue'
import { useScreenFit } from '@/composables/useScreenFit'

const screen = ref<HTMLElement | null>(null)
useScreenFit(screen)
</script>

<template>
  <div class="stage">
    <div ref="screen" class="screen">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.stage {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 50% 0%, #0c2744 0%, transparent 52%),
    #03070e;
}

.screen {
  width: 1920px;
  height: 1080px;
  position: absolute;
  transform-origin: left top;
  padding: 12px 20px 16px;
  display: flex;
  flex-direction: column;
  background-image:
    linear-gradient(rgba(62, 198, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(62, 198, 255, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
}
</style>
