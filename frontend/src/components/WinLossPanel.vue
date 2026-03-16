<template>
  <section>
    <table class="summary-table">
      <thead>
        <tr>
          <th>項目</th>
          <th>日</th>
          <th>週</th>
          <th>月</th>
          <th>年</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.key">
          <td>{{ r.label }}</td>
          <td>{{ r.day }}</td>
          <td>{{ r.week }}</td>
          <td>{{ r.month }}</td>
          <td>{{ r.year }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const { analysis } = storeToRefs(usePortfolioStore())
const wl = computed(() => {
  const wl = analysis.value.win_loss || {}
  return {
    day: wl.day || {},
    week: wl.week || {},
    month: wl.month || {},
    year: wl.year || {}
  }
})

function byPeriod(fn) {
  const src = wl.value
  return {
    day: fn(src.day || {}),
    week: fn(src.week || {}),
    month: fn(src.month || {}),
    year: fn(src.year || {})
  }
}

const rows = computed(() => {
  const total = byPeriod((r) => num0(r.total))
  const wins = byPeriod((r) => num0(r.wins))
  const losses = byPeriod((r) => num0(r.losses))
  const winProb = byPeriod((r) => pct(r.win_prob))
  const avgWin = byPeriod((r) => num0(r.avg_win))
  const avgLoss = byPeriod((r) => num0(r.avg_loss))
  const maxWin = byPeriod((r) => num0(r.max_win))
  const maxLoss = byPeriod((r) => num0(r.max_loss))
  const avgRatio = byPeriod((r) => num(r.avg_win_loss_ratio))
  const totalRatio = byPeriod((r) => num(r.total_win_loss_ratio))
  return [
    { key: 'total', label: '總次數', ...total },
    { key: 'wins', label: '贏錢次數', ...wins },
    { key: 'losses', label: '輸錢次數', ...losses },
    { key: 'win_prob', label: '贏錢機率', ...winProb },
    { key: 'avg_win', label: '平均每次贏錢', ...avgWin },
    { key: 'avg_loss', label: '平均每次輸錢', ...avgLoss },
    { key: 'max_win', label: '最大贏錢', ...maxWin },
    { key: 'max_loss', label: '最大輸錢', ...maxLoss },
    { key: 'avg_ratio', label: '每次贏輸比', ...avgRatio },
    { key: 'total_ratio', label: '全部贏輸比', ...totalRatio }
  ]
})

function num(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function num0(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function pct(v) {
  const n = Number(v || 0) * 100
  return `${n.toFixed(2)}%`
}
</script>

<style scoped>
.summary-table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  text-align: right;
}
th:first-child,
td:first-child {
  text-align: left;
}
</style>
