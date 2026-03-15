<template>
  <section>
    <div class="period-tabs">
      <button
        v-for="opt in periodOptions"
        :key="opt.value"
        class="period-btn"
        :class="{ active: period === opt.value }"
        @click="period = opt.value"
      >
        {{ opt.label }}
      </button>
    </div>

    <table class="summary-table">
      <thead>
        <tr>
          <th>勝</th>
          <th>負</th>
          <th>總次數</th>
          <th>勝率</th>
          <th>總贏</th>
          <th>總輸</th>
          <th>平均贏</th>
          <th>平均輸</th>
          <th>平均贏輸比</th>
          <th>全部贏輸比</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ row.wins }}</td>
          <td>{{ row.losses }}</td>
          <td>{{ row.total }}</td>
          <td>{{ pct(row.win_prob) }}</td>
          <td>{{ num(row.total_win) }}</td>
          <td>{{ num(row.total_loss) }}</td>
          <td>{{ num(row.avg_win) }}</td>
          <td>{{ num(row.avg_loss) }}</td>
          <td>{{ num(row.avg_win_loss_ratio) }}</td>
          <td>{{ num(row.total_win_loss_ratio) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed } from 'vue'
import { ref } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const { analysis } = storeToRefs(usePortfolioStore())
const period = ref('day')
const periodOptions = [
  { label: '日', value: 'day' },
  { label: '週', value: 'week' },
  { label: '月', value: 'month' },
  { label: '年', value: 'year' }
]

const rowMap = computed(() => {
  const wl = analysis.value.win_loss || {}
  return {
    day: wl.day || {},
    week: wl.week || {},
    month: wl.month || {},
    year: wl.year || {}
  }
})
const row = computed(() => rowMap.value[period.value] || {})

function num(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function pct(v) {
  const n = Number(v || 0) * 100
  return `${n.toFixed(2)}%`
}
</script>

<style scoped>
.period-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.period-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 8px;
  padding: 5px 10px;
  cursor: pointer;
}
.period-btn.active {
  border-color: var(--accent);
  color: var(--accent);
}
.summary-table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  text-align: right;
}
</style>
