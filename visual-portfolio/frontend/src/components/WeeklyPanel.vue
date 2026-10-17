<template>
  <section>
    <h3>每週獲利</h3>
    <div ref="chartRef" class="chart"></div>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { storeToRefs } from 'pinia'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const chartRef = ref(null)
let chart
const { analysis } = storeToRefs(usePortfolioStore())

function render() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['每週獲利', 'MDD', '累積獲利'] },
    xAxis: { type: 'category', data: analysis.value.weekly.map((w) => w.period) },
    yAxis: [{ type: 'value' }, { type: 'value' }],
    series: [
      { name: '每週獲利', type: 'bar', data: analysis.value.weekly.map((w) => w.profit), yAxisIndex: 0 },
      { name: 'MDD', type: 'bar', data: analysis.value.weekly.map((w) => w.mdd || 0), yAxisIndex: 0 },
      { name: '累積獲利', type: 'line', data: analysis.value.weekly.map((w) => w.cumulative), yAxisIndex: 1, smooth: true }
    ]
  })
}

watch(() => analysis.value.weekly, async () => {
  await nextTick()
  render()
})

onMounted(render)
onBeforeUnmount(() => chart?.dispose())
</script>

<style scoped>
.chart {
  width: 100%;
  height: 420px;
}
</style>
