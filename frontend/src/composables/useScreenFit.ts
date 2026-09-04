import { onMounted, onUnmounted, type Ref } from 'vue'

const DESIGN_WIDTH = 1920
const DESIGN_HEIGHT = 1080

export function useScreenFit(screen: Ref<HTMLElement | null>) {
  function resize() {
    const el = screen.value
    if (!el) return
    const scale = Math.min(window.innerWidth / DESIGN_WIDTH, window.innerHeight / DESIGN_HEIGHT)
    el.style.transform = `scale(${scale})`
    el.style.left = `${(window.innerWidth - DESIGN_WIDTH * scale) / 2}px`
    el.style.top = `${(window.innerHeight - DESIGN_HEIGHT * scale) / 2}px`
  }

  onMounted(() => {
    resize()
    window.addEventListener('resize', resize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
  })
}
