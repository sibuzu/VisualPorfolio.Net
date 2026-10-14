<template>
  <section>
    <h3>年度獲利</h3>
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
    legend: { data: ['獲利', 'MDD'] },
    xAxis: { type: 'category', data: analysis.value.annual.map((m) => m.period) },
    yAxis: { type: 'value' },
    series: [
      { name: '獲利', type: 'bar', data: analysis.value.annual.map((m) => m.profit) },
      { name: 'MDD', type: 'bar', data: analysis.value.annual.map((m) => m.mdd) }
    ]
  })
}

watch(() => analysis.value.annual, async () => {
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
