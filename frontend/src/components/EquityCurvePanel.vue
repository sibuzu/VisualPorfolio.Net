<template>
  <section>
    <h3>Equity Curve</h3>
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
  const x = analysis.value.equity_curve.map((r) => r.date)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['Profit', 'Drawdown'] },
    xAxis: { type: 'category', data: x },
    yAxis: { type: 'value' },
    series: [
      { name: 'Profit', type: 'line', data: analysis.value.equity_curve.map((r) => r.profit), smooth: true },
      { name: 'Drawdown', type: 'line', data: analysis.value.equity_curve.map((r) => r.drawdown), smooth: true }
    ]
  })
}

watch(() => analysis.value.equity_curve, async () => {
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
