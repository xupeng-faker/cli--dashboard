import { onMounted, onUnmounted, ref } from 'vue'

function pad(value: number) {
  return String(value).padStart(2, '0')
}

export function useClock() {
  const text = ref('')

  function tick() {
    const now = new Date()
    text.value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
  }

  let timer = 0
  onMounted(() => {
    tick()
    timer = window.setInterval(tick, 1000)
  })
  onUnmounted(() => window.clearInterval(timer))

  return { text }
}
