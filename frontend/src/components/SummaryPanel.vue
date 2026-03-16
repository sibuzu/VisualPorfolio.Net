<template>
  <section>
    <h3>Summary</h3>
    <div class="cards">
      <div v-for="item in summaryCards" :key="item.label" class="card">
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
          <td>{{ numInt(r.mdd) }}</td>
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
        <tr
          v-for="r in annualRows"
          :key="`a-${r.date}`"
          :class="r.profit >= 0 ? 'row-profit' : 'row-loss'"
        >
          <td>{{ r.date }}</td>
          <td>{{ numInt(r.profit) }}</td>
          <td>{{ numInt(r.mdd) }}</td>
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
        <tr
          v-for="r in monthRows"
          :key="`m-${r.date}`"
          :class="r.profit >= 0 ? 'row-profit' : 'row-loss'"
        >
          <td>{{ r.date }}</td>
          <td>{{ numInt(r.profit) }}</td>
          <td>{{ numInt(r.mdd) }}</td>
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
const summary = computed(() => analysis.value.summary || {})
const trades = computed(() => analysis.value.position_analysis || [])
const periodDates = computed(() => parsePeriod(summary.value.period))
const periodYears = computed(() => {
  const { start, end } = periodDates.value
  if (!start || !end) return 0
  return ((end - start) / 86400000 + 1) / 365.25
})

const derived = computed(() => {
  const netProfit = Number(summary.value.net_profit || 0)
  const mdd = Math.abs(Number(summary.value.mdd || 0))
  const tradeCount = Number(summary.value.trade_count || trades.value.length || 0)
  const winCount = trades.value.filter((t) => Number(t.pnl || 0) > 0).length
  const lossCount = tradeCount - winCount
  const winAmount = trades.value
    .filter((t) => Number(t.pnl || 0) > 0)
    .reduce((s, t) => s + Number(t.pnl || 0), 0)
  const lossAmount = trades.value
    .filter((t) => Number(t.pnl || 0) <= 0)
    .reduce((s, t) => s + Number(t.pnl || 0), 0)
  const yearProfit = periodYears.value > 0 ? netProfit / periodYears.value : 0
  const pmr = mdd > 0 ? netProfit / mdd : 0
  const ypmr = mdd > 0 ? yearProfit / mdd : 0
  const avgNet = tradeCount > 0 ? netProfit / tradeCount : 0
  const avgWin = winCount > 0 ? winAmount / winCount : 0
  const avgLoss = lossCount > 0 ? lossAmount / lossCount : 0
  const profitFactor = lossAmount === 0 ? 100 : -winAmount / lossAmount
  const winProb = tradeCount > 0 ? (winCount / tradeCount) * 100 : 0
  return {
    netProfit,
    mdd,
    tradeCount,
    winCount,
    lossCount,
    winAmount,
    lossAmount,
    yearProfit,
    pmr,
    ypmr,
    avgNet,
    avgWin,
    avgLoss,
    profitFactor,
    winProb,
  }
})

const summaryCards = computed(() => [
  { label: '期間', value: `${periodYears.value.toFixed(2)} years` },
  { label: '交易日期', value: tradeDateRange(periodDates.value.start, periodDates.value.end) },
  { label: '總獲利', value: moneyInt(derived.value.netProfit) },
  { label: '年獲利', value: moneyInt(derived.value.yearProfit) },
  { label: 'MDD', value: moneyInt(derived.value.mdd) },
  { label: '總獲利/MDD', value: ratio(derived.value.pmr) },
  { label: '年獲利/MDD', value: ratio(derived.value.ypmr) },
  { label: '交易次數', value: num0(derived.value.tradeCount) },
  { label: '贏錢次數', value: num0(derived.value.winCount) },
  { label: '輸錢次數', value: num0(derived.value.lossCount) },
  { label: '贏錢機率', value: `${derived.value.winProb.toFixed(2)}%` },
  { label: '贏錢總金額', value: moneyInt(derived.value.winAmount) },
  { label: '輸錢總金額', value: moneyInt(derived.value.lossAmount) },
  { label: '平均每次輸贏', value: moneyInt(derived.value.avgNet) },
  { label: '平均每次贏錢', value: moneyInt(derived.value.avgWin) },
  { label: '平均每次輸錢', value: moneyInt(derived.value.avgLoss) },
  { label: '獲利因子', value: ratio(derived.value.profitFactor) },
  { label: 'Sharpe Ratio', value: ratio(summary.value.sharpe) },
  { label: 'Sortino Ratio', value: ratio(summary.value.sortino) },
].filter(Boolean))

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

function numInt(v) {
  const n = Math.round(Number(v || 0))
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
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

function parsePeriod(periodText) {
  const parts = String(periodText || '').split('~').map((x) => x.trim())
  const start = parts[0] ? new Date(parts[0]) : null
  const end = parts[1] ? new Date(parts[1]) : null
  return {
    start: start && !Number.isNaN(start.getTime()) ? start : null,
    end: end && !Number.isNaN(end.getTime()) ? end : null,
  }
}

function fmtDateSlash(d) {
  if (!d) return '-'
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

function tradeDateRange(start, end) {
  if (!start || !end) return summary.value.period || '-'
  return `${fmtDateSlash(start)} - ${fmtDateSlash(end)}`
}

function moneyInt(v) {
  const n = Math.round(Number(v || 0))
  return `$ ${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

function ratio(v) {
  const n = Number(v || 0)
  return n.toFixed(2).replace(/\.?0+$/, '')
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
.row-profit {
  color: #1d4ed8;
}
.row-loss {
  color: #b00020;
}
</style>
