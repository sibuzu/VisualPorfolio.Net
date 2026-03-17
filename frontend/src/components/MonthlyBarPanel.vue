<template>
  <section>
    <div class="range-row">
      <span class="label">類別：</span>
      <button
        v-for="opt in categoryOptions"
        :key="opt.value"
        class="range-btn"
        :class="{ active: category === opt.value }"
        @click="category = opt.value"
      >
        {{ opt.label }}
      </button>
    </div>
    <div class="range-row">
      <span class="label">範圍：</span>
      <button
        v-for="opt in rangeOptions"
        :key="opt.value"
        class="range-btn"
        :class="{ active: interval === opt.value }"
        @click="interval = opt.value"
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
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  Tooltip
} from 'chart.js'
import { storeToRefs } from 'pinia'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

Chart.register(CategoryScale, LinearScale, BarController, BarElement, Tooltip, Legend)

const chartRef = ref(null)
let chart = null
const store = usePortfolioStore()
const { analysis, equities } = storeToRefs(store)
const interval = ref(12)
const category = ref('profit_mdd')
const MAX_SEPARATE_STRATEGIES = 10
const PROFIT_COLOR = '#0000ff'
const MDD_COLOR = '#ff0000'

const categoryOptions = [
  { label: '獲利', value: 'profit' },
  { label: '獲利+MDD', value: 'profit_mdd' },
  { label: '獲利(個別)', value: 'profit_separate' }
]

const rangeOptions = [
  { label: '每年', value: 12 },
  { label: '每半年', value: 6 },
  { label: '每4月', value: 4 },
  { label: '每3月', value: 3 },
  { label: '每2月', value: 2 },
  { label: '每月', value: 1 }
]

function bucketKey(period, monthsPerBucket) {
  const [y, m] = period.split('/').map((x) => Number(x))
  const startMonth = Math.floor((m - 1) / monthsPerBucket) * monthsPerBucket + 1
  if (monthsPerBucket === 12) return `${y}`
  if (monthsPerBucket === 1) return `${y}/${String(startMonth).padStart(2, '0')}`
  return `${y}/${String(startMonth).padStart(2, '0')}-${String(startMonth + monthsPerBucket - 1).padStart(2, '0')}`
}

const bucketedRows = computed(() => {
  const src = analysis.value.monthly || []
  const mpb = interval.value
  const out = []
  const byKey = new Map()

  for (const row of src) {
    const key = bucketKey(row.period, mpb)
    if (!byKey.has(key)) {
      byKey.set(key, { period: key, profit: 0, mdd: 0 })
      out.push(byKey.get(key))
    }
    const rec = byKey.get(key)
    rec.profit += Number(row.profit || 0)
    rec.mdd = Math.max(rec.mdd, Number(row.mdd || 0))
  }
  return out
})

const separateBucketSeries = computed(() => {
  if (category.value !== 'profit_separate') return []
  const rows = analysis.value.position_analysis || []
  const periods = bucketedRows.value.map((r) => r.period)
  const bySiByPeriod = new Map()

  for (const row of rows) {
    const si = Number(row.strategy_index)
    const exitDate = String(row.exit || '').slice(0, 10)
    if (!exitDate) continue
    const monthPeriod = `${exitDate.slice(0, 4)}/${exitDate.slice(5, 7)}`
    const key = bucketKey(monthPeriod, interval.value)
    if (!bySiByPeriod.has(si)) bySiByPeriod.set(si, new Map())
    const m = bySiByPeriod.get(si)
    m.set(key, (m.get(key) || 0) + Number(row.pnl || 0))
  }

  const sortedSi = Array.from(bySiByPeriod.keys()).sort((a, b) => a - b).slice(0, MAX_SEPARATE_STRATEGIES)
  return sortedSi.map((si) => {
    const eq = equities.value[si]
    const name = String(eq?.name || eq?.filename || `策略${si + 1}`).replace(/\.[^.]+$/, '')
    const color = eq?.color || '#6b7280'
    const dataByPeriod = bySiByPeriod.get(si) || new Map()
    return {
      name,
      color,
      data: periods.map((p) => Number(dataByPeriod.get(p) || 0))
    }
  })
})

function render() {
  if (!chartRef.value) return

  let datasets = [
    {
      label: '獲利',
      data: bucketedRows.value.map((m) => m.profit),
      backgroundColor: PROFIT_COLOR
    }
  ]

  if (category.value === 'profit_mdd') {
    datasets = [
      {
        label: '獲利',
        data: bucketedRows.value.map((m) => m.profit),
        backgroundColor: PROFIT_COLOR
      },
      {
        label: 'MDD',
        data: bucketedRows.value.map((m) => m.mdd),
        backgroundColor: MDD_COLOR
      }
    ]
  } else if (category.value === 'profit_separate') {
    datasets = separateBucketSeries.value.map((s) => ({
      label: s.name,
      data: s.data,
      backgroundColor: s.color
    }))
  }

  const [yMin, yMax] = calcYRange(datasets)

  if (chart) {
    chart.destroy()
    chart = null
  }

  chart = new Chart(chartRef.value, {
    type: 'bar',
    data: {
      labels: bucketedRows.value.map((m) => m.period),
      datasets: datasets.map((ds) => ({
        ...ds,
        borderWidth: 0,
        categoryPercentage: 1,
        barPercentage: 1,
        barThickness: 'flex',
        maxBarThickness: 44
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
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
        }
      },
      scales: {
        x: {
          stacked: false,
          grid: {
            color: '#e5e7eb'
          },
          ticks: {
            color: '#4b5563'
          }
        },
        y: {
          stacked: false,
          min: yMin,
          max: yMax,
          grid: {
            color: '#d9e1e8'
          },
          ticks: {
            color: '#4b5563',
            callback(v) {
              return Math.round(Number(v || 0)).toLocaleString('en-US')
            }
          }
        }
      }
    }
  })
}

function calcYRange(datasets) {
  const vals = []
  for (const ds of datasets || []) {
    for (const v of ds.data || []) {
      const n = Number(v)
      if (Number.isFinite(n)) vals.push(n)
    }
  }
  if (!vals.length) return [0, 1]

  let min = Math.min(...vals)
  let max = Math.max(...vals)
  if (min === max) {
    const d = Math.max(1, Math.abs(min) * 0.1)
    return [Math.floor(min - d), Math.ceil(max + d)]
  }

  const pad = (max - min) * 0.08
  min -= pad
  max += pad
  return [Math.floor(min), Math.ceil(max)]
}

function onResize() {
  chart?.resize()
}

watch([() => analysis.value.monthly, () => analysis.value.position_analysis, () => equities.value, interval, category], async () => {
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
.range-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.label {
  color: var(--muted);
}
.range-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 8px;
  padding: 5px 10px;
  cursor: pointer;
}
.range-btn.active {
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
