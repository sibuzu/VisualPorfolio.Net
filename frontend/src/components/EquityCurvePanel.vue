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
    <div class="chart-wrap">
      <canvas ref="chartRef" class="chart"></canvas>
    </div>
  </section>
</template>

<script setup>
import {
  CategoryScale,
  Chart,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip
} from 'chart.js'
import { storeToRefs } from 'pinia'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

Chart.register(CategoryScale, LinearScale, LineController, LineElement, PointElement, Tooltip, Legend)

const drawdownBandsPlugin = {
  id: 'drawdownBands',
  beforeDatasetsDraw(chart, _args, pluginOptions) {
    const bands = pluginOptions?.bands || []
    if (!bands.length) return
    const xScale = chart.scales.x
    const yScale = chart.scales.y
    if (!xScale || !yScale) return

    const ctx = chart.ctx
    const top = yScale.top
    const bottom = yScale.bottom
    ctx.save()
    ctx.fillStyle = 'rgba(230, 90, 90, 0.10)'

    for (const band of bands) {
      const start = Number(band.start)
      const end = Number(band.end)
      if (!Number.isFinite(start) || !Number.isFinite(end)) continue
      const x1 = xScale.getPixelForValue(Math.max(0, start))
      const x2 = xScale.getPixelForValue(Math.max(0, end))
      const left = Math.min(x1, x2)
      const width = Math.max(1, Math.abs(x2 - x1))
      ctx.fillRect(left, top, width, bottom - top)
    }
    ctx.restore()
  }
}

const chartRef = ref(null)
let chart = null
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
const totalSeries = computed(() => analysis.value.equity_curve.map((r) => Number(r.profit || 0)))

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
      color: eq?.color || '#6b7280',
      data: []
    }
  })

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

  const selected = []
  if (mode.value === 'total' || mode.value === 'both') {
    selected.push({ name: '總獲利', color: '#6ba7d9', width: 2, data: totalSeries.value })
  }
  if (mode.value === 'separate' || mode.value === 'both') {
    selected.push(...separateSeries.value.map((s) => ({ name: s.name, color: s.color, width: 2, data: s.data })))
  }

  const sampled = downsampleSeries(dates.value, selected, MAX_POINTS)
  const bands = buildBands(sampled.sourceIdx)

  if (chart) {
    chart.destroy()
    chart = null
  }

  chart = new Chart(chartRef.value, {
    type: 'line',
    data: {
      labels: sampled.dates,
      datasets: sampled.series.map((s, idx) => ({
        label: s.name,
        data: s.data,
        borderColor: s.color,
        backgroundColor: s.color,
        borderWidth: s.width || 2,
        pointRadius: 0,
        pointHoverRadius: 3,
        tension: 0.15,
        fill: false,
        order: idx + 1
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      animation: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label(ctx) {
              const y = Number(ctx.parsed.y || 0)
              return `${ctx.dataset.label}: ${Math.round(y).toLocaleString('en-US')}`
            }
          }
        },
        drawdownBands: {
          bands
        }
      },
      scales: {
        x: {
          grid: {
            color: '#e5e7eb',
            lineWidth: 1
          },
          ticks: {
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 10,
            color: '#4b5563'
          }
        },
        y: {
          grid: {
            color: '#d9e1e8',
            lineWidth: 1
          },
          ticks: {
            color: '#4b5563',
            callback(v) {
              return Math.round(Number(v || 0)).toLocaleString('en-US')
            }
          }
        }
      }
    },
    plugins: [drawdownBandsPlugin]
  })
}

function legendName(eq, si) {
  const raw = String(eq?.name || eq?.filename || `策略${si + 1}`)
  return raw.replace(/\.[^.]+$/, '')
}

function downsampleSeries(sourceDates, sourceSeries, targetCount) {
  const n = sourceDates.length
  if (!n || n <= targetCount) {
    return {
      dates: sourceDates,
      sourceIdx: sourceDates.map((_, i) => i),
      series: sourceSeries
    }
  }
  if (targetCount <= 2) {
    const edgeSeries = sourceSeries.map((s) => ({
      ...s,
      data: [s.data?.[0] ?? 0, s.data?.[n - 1] ?? 0]
    }))
    return {
      dates: [sourceDates[0], sourceDates[n - 1]],
      sourceIdx: [0, n - 1],
      series: edgeSeries
    }
  }

  const interiorCount = targetCount - 2
  const interiorN = n - 2
  const bucketSize = interiorN / interiorCount
  const sampledDates = [sourceDates[0]]
  const sampledSourceIdx = [0]
  const sampledSeries = sourceSeries.map((s) => ({ ...s, data: [s.data?.[0] ?? 0] }))

  for (let i = 0; i < interiorCount; i++) {
    const start = 1 + Math.floor(i * bucketSize)
    const endBase = 1 + Math.floor((i + 1) * bucketSize)
    const end = Math.min(n - 1, endBase)
    const bucketEnd = end <= start ? Math.min(n - 1, start + 1) : end
    const srcIdx = bucketEnd - 1

    sampledDates.push(sourceDates[srcIdx])
    sampledSourceIdx.push(srcIdx)

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
  sampledSourceIdx.push(n - 1)
  for (let si = 0; si < sourceSeries.length; si++) {
    sampledSeries[si].data.push(sourceSeries[si].data?.[n - 1] ?? 0)
  }
  return { dates: sampledDates, sourceIdx: sampledSourceIdx, series: sampledSeries }
}

function buildBands(sampledSourceIdx) {
  const markers = analysis.value.mdd_markers || []
  if (!markers.length || !sampledSourceIdx.length) return []

  return markers
    .map((m) => {
      const startRaw = Math.max(0, Number(m.start_idx || 0))
      const endRaw = Math.max(startRaw, Number(m.end_idx2 ?? m.end_idx ?? startRaw))
      const start = sampledSourceIdx.findIndex((idx) => idx >= startRaw)
      let end = -1
      for (let i = sampledSourceIdx.length - 1; i >= 0; i--) {
        if (sampledSourceIdx[i] <= endRaw) {
          end = i
          break
        }
      }
      if (start < 0 || end < 0 || start > end) return null
      return { start, end }
    })
    .filter(Boolean)
}

function onResize() {
  chart?.resize()
}

watch([() => analysis.value.equity_curve, () => analysis.value.position_analysis, () => analysis.value.mdd_markers, () => equities.value, mode], async () => {
  await nextTick()
  render()
}, { deep: true })

onMounted(() => {
  render()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.destroy()
})
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
.chart-wrap {
  width: 100%;
  height: 420px;
}
.chart {
  width: 100%;
  height: 100%;
}
</style>
