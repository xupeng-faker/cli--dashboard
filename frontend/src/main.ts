import { createPinia } from 'pinia'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { createApp } from 'vue'

import App from './App.vue'
import { router } from './router'
import './styles/global.css'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
