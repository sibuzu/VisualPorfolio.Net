<template>
  <section>
    <h3>逐年獲利</h3>
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
const { analysis } = storeToRefs(usePortfolioStore())
const interval = ref(1)

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

function render() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['獲利', 'MDD'] },
    xAxis: { type: 'category', data: bucketedRows.value.map((m) => m.period) },
    yAxis: { type: 'value' },
    series: [
      { name: '獲利', type: 'bar', data: bucketedRows.value.map((m) => m.profit) },
      { name: 'MDD', type: 'bar', data: bucketedRows.value.map((m) => m.mdd) }
    ]
  })
}

watch([() => analysis.value.monthly, interval], async () => {
  await nextTick()
  render()
})

onMounted(render)
onBeforeUnmount(() => chart?.dispose())
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
.chart {
  width: 100%;
  height: 420px;
}
</style>
