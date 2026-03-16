<template>
  <section>
    <div class="mode-row">
      <span class="label">類別：</span>
      <button
        v-for="opt in modeOptions"
        :key="opt.value"
        class="mode-btn"
        :class="{ active: mode === opt.value }"
        @click="mode = opt.value"
      >
        {{ opt.label }}
      </button>
    </div>
    <div ref="chartRef" class="chart"></div>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { storeToRefs } from 'pinia'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const chartRef = ref(null)
let chart
const store = usePortfolioStore()
const { analysis, equities } = storeToRefs(store)
const mode = ref('total')
const MAX_POINTS = 2000
const MAX_SEPARATE_SERIES = 20
const modeOptions = [
  { label: '總獲利', value: 'total' },
  { label: '個別獲利', value: 'separate' },
  { label: '總獲利+個別獲利', value: 'both' }
]

const dates = computed(() => analysis.value.equity_curve.map((r) => r.date))
const totalSeries = computed(() => analysis.value.equity_curve.map((r) => r.profit))

const separateSeries = computed(() => {
  const rows = analysis.value.position_analysis || []
  if (!rows.length) return []

  const tradedSet = new Set(rows.map((r) => Number(r.strategy_index)))
  const strategyIndices = equities.value
    .map((_, i) => i)
    .filter((i) => tradedSet.has(i))
    .slice(0, MAX_SEPARATE_SERIES)

  const acc = new Map(strategyIndices.map((si) => [si, 0]))
  const out = strategyIndices.map((si) => {
    const eq = equities.value[si]
    return {
      name: legendName(eq, si),
      type: 'line',
      smooth: true,
      lineStyle: { color: eq?.color || undefined },
      itemStyle: { color: eq?.color || undefined },
      data: []
    }
  })

  // Keep per-strategy curve aligned to trade sequence (same axis length as total curve).
  for (const row of rows) {
    const hitSi = Number(row.strategy_index)
    const pnl = Number(row.pnl || 0)
    if (acc.has(hitSi)) {
      acc.set(hitSi, (acc.get(hitSi) || 0) + pnl)
    }
    for (let i = 0; i < strategyIndices.length; i++) {
      const si = strategyIndices[i]
      out[i].data.push(acc.get(si) || 0)
    }
  }
  return out
})

function render() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const selected = []
  if (mode.value === 'total' || mode.value === 'both') {
    selected.push({ name: '總獲利', type: 'line', data: totalSeries.value, smooth: true, lineStyle: { width: 3 } })
  }
  if (mode.value === 'separate' || mode.value === 'both') {
    selected.push(...separateSeries.value)
  }
  const sampled = downsampleSeries(dates.value, selected, MAX_POINTS)
  const series = sampled.series

  chart.setOption(
    {
      tooltip: { trigger: 'axis' },
      legend: { data: series.map((s) => s.name) },
      xAxis: { type: 'category', data: sampled.dates },
      yAxis: { type: 'value' },
      series
    },
    { notMerge: true }
  )
}

function legendName(eq, si) {
  const raw = String(eq?.name || eq?.filename || `策略${si + 1}`)
  return raw.replace(/\.[^.]+$/, '')
}

function downsampleSeries(sourceDates, sourceSeries, targetCount) {
  const n = sourceDates.length
  if (!n || n <= targetCount) {
    return { dates: sourceDates, series: sourceSeries }
  }
  if (targetCount <= 2) {
    const edgeSeries = sourceSeries.map((s) => ({
      ...s,
      data: [s.data?.[0] ?? 0, s.data?.[n - 1] ?? 0]
    }))
    return { dates: [sourceDates[0], sourceDates[n - 1]], series: edgeSeries }
  }

  const interiorCount = targetCount - 2
  const interiorN = n - 2
  const bucketSize = interiorN / interiorCount
  const sampledDates = [sourceDates[0]]
  const sampledSeries = sourceSeries.map((s) => ({ ...s, data: [s.data?.[0] ?? 0] }))

  for (let i = 0; i < interiorCount; i++) {
    const start = 1 + Math.floor(i * bucketSize)
    const endBase = 1 + Math.floor((i + 1) * bucketSize)
    const end = Math.min(n - 1, endBase)
    const bucketEnd = end <= start ? Math.min(n - 1, start + 1) : end

    sampledDates.push(sourceDates[bucketEnd - 1])

    for (let si = 0; si < sourceSeries.length; si++) {
      let sum = 0
      let count = 0
      const arr = sourceSeries[si].data || []
      for (let j = start; j < bucketEnd; j++) {
        const v = Number(arr[j])
        if (Number.isFinite(v)) {
          sum += v
          count++
        }
      }
      sampledSeries[si].data.push(count > 0 ? sum / count : 0)
    }
  }

  sampledDates.push(sourceDates[n - 1])
  for (let si = 0; si < sourceSeries.length; si++) {
    sampledSeries[si].data.push(sourceSeries[si].data?.[n - 1] ?? 0)
  }
  return { dates: sampledDates, series: sampledSeries }
}

watch([() => analysis.value.equity_curve, () => analysis.value.position_analysis, () => equities.value, mode], async () => {
  await nextTick()
  render()
}, { deep: true })

onMounted(render)
onBeforeUnmount(() => chart?.dispose())
</script>

<style scoped>
.mode-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.label {
  color: var(--muted);
}
.mode-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 8px;
  padding: 5px 10px;
  cursor: pointer;
}
.mode-btn.active {
  border-color: var(--accent);
  color: var(--accent);
}
.chart {
  width: 100%;
  height: 420px;
}
</style>
