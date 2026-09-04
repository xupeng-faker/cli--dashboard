import { onMounted, onUnmounted } from 'vue'

export function usePolling(load: () => void, interval_ms = 30000) {
  let timer = 0

  onMounted(() => {
    load()
    timer = window.setInterval(load, interval_ms)
  })

  onUnmounted(() => window.clearInterval(timer))
}
