<template>
  <section>
    <h3>Summary</h3>
    <div class="cards">
      <div v-for="item in summaryItems" :key="item.key" class="card">
        <div class="label">{{ item.label }}</div>
        <div class="value">{{ item.value }}</div>
      </div>
    </div>

    <h3>MDD</h3>
    <table class="grid">
      <thead>
        <tr>
          <th>#</th>
          <th>MDD</th>
          <th>日期</th>
          <th>低點天數</th>
          <th>回升天數</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in mddRows" :key="`mdd-${r.no}`">
          <td>{{ r.no }}</td>
          <td>{{ num(r.mdd) }}</td>
          <td>{{ r.period }}</td>
          <td>{{ r.lowDays }}</td>
          <td>{{ r.recoverDays }}</td>
        </tr>
      </tbody>
    </table>

    <h3>Annual Profits</h3>
    <table class="grid">
      <thead>
        <tr>
          <th>Date</th>
          <th>Profit</th>
          <th>MDD</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in annualRows" :key="`a-${r.date}`">
          <td>{{ r.date }}</td>
          <td>{{ num(r.profit) }}</td>
          <td>{{ num(r.mdd) }}</td>
        </tr>
      </tbody>
    </table>

    <h3>Month Profits</h3>
    <table class="grid">
      <thead>
        <tr>
          <th>Date</th>
          <th>Profit</th>
          <th>MDD</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in monthRows" :key="`m-${r.date}`">
          <td>{{ r.date }}</td>
          <td>{{ num(r.profit) }}</td>
          <td>{{ num(r.mdd) }}</td>
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

const summaryItems = computed(() => {
  const s = analysis.value.summary || {}
  return [
    { key: 'period', label: '期間', value: s.period || '-' },
    { key: 'net_profit', label: '總獲利', value: num(s.net_profit) },
    { key: 'mdd', label: 'MDD', value: num(s.mdd) },
    { key: 'profit_factor', label: '獲利因子', value: num(s.profit_factor) },
    { key: 'trade_count', label: '總交易次數', value: num0(s.trade_count) },
    { key: 'win_prob', label: '贏錢機率', value: pct(s.win_prob) },
    { key: 'avg_win', label: '平均每次贏錢', value: num(s.avg_win) },
    { key: 'avg_loss', label: '平均每次輸錢', value: num(s.avg_loss) },
    { key: 'sharpe', label: 'Sharpe Ratio', value: num(s.sharpe) },
    { key: 'sortino', label: 'Sortino Ratio', value: num(s.sortino) },
    { key: 'sqn', label: 'SQN', value: num(s.sqn) },
  ]
})

const mddRows = computed(() =>
  (analysis.value.mdd_markers || []).map((m, i) => {
    const curve = analysis.value.equity_curve || []
    const start = curve[m.start_idx]?.date || '-'
    const trough = curve[m.end_idx]?.date || '-'
    const recover = curve[m.end_idx2]?.date || '-'
    const lowDays = diffDays(start, trough)
    const recoverDays = diffDays(start, recover)
    return {
      no: i + 1,
      mdd: Math.abs(Number(m.value || 0)),
      period: `${start} ~ ${trough}`,
      lowDays,
      recoverDays,
    }
  })
)

const annualRows = computed(() =>
  (analysis.value.annual || []).map((r) => ({
    date: String(r.period || ''),
    profit: Number(r.profit || 0),
    mdd: Number(r.mdd || 0),
  }))
)

const monthRows = computed(() =>
  (analysis.value.monthly || []).map((r) => ({
    date: String(r.period || ''),
    profit: Number(r.profit || 0),
    mdd: Number(r.mdd || 0),
  }))
)

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

function diffDays(start, end) {
  if (!start || !end || start === '-' || end === '-') return '-'
  const s = new Date(start)
  const e = new Date(end)
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return '-'
  return Math.max(0, Math.round((e - s) / 86400000))
}
</script>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 8px;
  margin-bottom: 14px;
}
.card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 10px;
}
.label {
  color: var(--muted);
  font-size: 13px;
}
.value {
  font-size: 18px;
  font-weight: 700;
}
.grid {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 14px;
}
.grid th,
.grid td {
  border: 1px solid var(--line);
  padding: 8px;
  text-align: right;
}
.grid th:first-child,
.grid td:first-child {
  text-align: left;
}
h3 {
  margin: 8px 0;
}
</style>
