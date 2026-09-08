import type { EChartsOption } from 'echarts'

const MUTED = '#7ea3b8'
const LINE = 'rgba(62, 198, 255, 0.18)'
const PALETTE = ['#3ec6ff', '#3ddea0', '#f5c14a', '#ff6b6b', '#7b8cff', '#5eead4']

const tooltip = {
  trigger: 'axis' as const,
  backgroundColor: 'rgba(6, 18, 32, 0.92)',
  borderColor: 'rgba(62, 198, 255, 0.35)',
  textStyle: { color: '#d6e8f5', fontSize: 12 },
}

export function bar_option(labels: string[], values: number[], axis_name: string): EChartsOption {
  return {
    color: PALETTE,
    tooltip,
    grid: { left: 44, right: 12, top: 28, bottom: 28 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: MUTED, fontSize: 11, rotate: labels.some((item) => item.length > 8) ? 20 : 0 },
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: axis_name,
      nameTextStyle: { color: MUTED },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: LINE, type: 'dashed' } },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barMaxWidth: 18,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#5ee1ff' },
              { offset: 1, color: '#1a6fa3' },
            ],
          },
        },
      },
    ],
  }
}

export function hbar_option(labels: string[], values: number[], label_width = 118): EChartsOption {
  return {
    color: PALETTE,
    tooltip: { ...tooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: label_width + 12, right: 36, top: 8, bottom: 8 },
    xAxis: {
      type: 'value',
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: LINE, type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLabel: { color: '#b7d4e6', fontSize: 11, width: label_width, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barWidth: 10,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#134e72' },
              { offset: 1, color: '#3ec6ff' },
            ],
          },
        },
      },
    ],
  }
}

export function pie_option(items: { name: string; value: number }[]): EChartsOption {
  return {
    color: PALETTE,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: tooltip.backgroundColor, borderColor: tooltip.borderColor, textStyle: tooltip.textStyle },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'middle',
      textStyle: { color: MUTED, fontSize: 11, width: 92, overflow: 'truncate' },
      itemWidth: 10,
      itemHeight: 10,
    },
    series: [
      {
        type: 'pie',
        radius: ['48%', '70%'],
        center: ['36%', '50%'],
        itemStyle: { borderColor: '#071422', borderWidth: 2 },
        label: { show: false },
        data: items,
      },
    ],
  }
}

function value_axis(name: string, show_split: boolean) {
  return {
    type: 'value' as const,
    min: 0,
    name,
    nameTextStyle: { color: MUTED },
    axisLabel: { color: MUTED },
    axisLine: { show: true, lineStyle: { color: LINE } },
    splitLine: show_split ? { lineStyle: { color: LINE, type: 'dashed' as const } } : { show: false },
  }
}

export function line_option(
  labels: string[],
  series: { name: string; data: number[]; yAxisIndex?: number }[],
  y_names: [string, string?],
): EChartsOption {
  const dual = Boolean(y_names[1])
  const from_origin = labels.length > 0
  const axis_labels = from_origin ? ['', ...labels] : labels
  const axis_series = from_origin ? series.map((item) => ({ ...item, data: [0, ...item.data] })) : series
  return {
    color: PALETTE,
    tooltip: {
      ...tooltip,
      formatter(params: unknown) {
        const items = Array.isArray(params) ? params : [params]
        const first = items[0] as { axisValue?: string; marker?: string; seriesName?: string; value?: number } | undefined
        if (!first || first.axisValue === '') {
          return ''
        }
        const lines = items.map((item) => {
          const point = item as { marker?: string; seriesName?: string; value?: number }
          return `${point.marker || ''}${point.seriesName}  ${point.value ?? '-'}`
        })
        return `${first.axisValue}<br/>${lines.join('<br/>')}`
      },
    },
    legend: { top: 0, textStyle: { color: MUTED }, icon: 'circle', itemWidth: 8 },
    grid: { left: 48, right: dual ? 48 : 16, top: 36, bottom: 28 },
    xAxis: {
      type: 'category',
      data: axis_labels,
      boundaryGap: false,
      axisLabel: { color: MUTED, fontSize: 11 },
      axisLine: { onZero: true, lineStyle: { color: LINE } },
      axisTick: { show: false },
    },
    yAxis: dual ? [value_axis(y_names[0], true), value_axis(y_names[1] || '', false)] : value_axis(y_names[0], true),
    series: axis_series.map((item, index) => ({
      type: 'line',
      name: item.name,
      data: item.data,
      yAxisIndex: item.yAxisIndex || 0,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2 },
      areaStyle:
        index === 0
          ? {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(62, 198, 255, 0.28)' },
                  { offset: 1, color: 'rgba(62, 198, 255, 0.02)' },
                ],
              },
            }
          : undefined,
    })),
  }
}
