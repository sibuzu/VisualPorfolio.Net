<script setup>
import { computed } from 'vue'

const props = defineProps({
  section: { type: Object, required: true },
  symbol: { type: String, default: '' },
  compound: { type: Boolean, default: false }
})
const summary = computed(() => props.section.summary || {})
const number = (value, digits = 2) => Number(value || 0).toLocaleString('en-US', { maximumFractionDigits: digits })
const money = value => {
  const amount = Math.round(Number(value || 0))
  return `${amount < 0 ? '-' : ''}$${number(Math.abs(amount), 0)}`
}
const percent = value => `${Number(value || 0).toFixed(2)}%`
function days(start, end) {
  if (!start || !end) return null
  return Math.max(0, Math.round((Date.parse(end.slice(0, 10)) - Date.parse(start.slice(0, 10))) / 86400000))
}
const dateSuffix = computed(() => summary.value.start_date && summary.value.end_date
  ? `(${summary.value.start_date.replaceAll('-', '/')} - ${summary.value.end_date.replaceAll('-', '/')})` : '')
const cards = computed(() => {
  const s = summary.value
  const duration = days(s.start_date, s.end_date)
  const years = duration == null ? 0 : (duration + 1) / 365.25
  const annualProfit = years ? s.net_profit / years : 0
  if (props.compound) {
    const multiple = s.initial_capital > 0 ? `${(s.final_capital / s.initial_capital).toFixed(2)}X` : '—'
    return [
      { label: 'Symbol', value: props.symbol || '—' },
      { label: '期間', value: `${years.toFixed(2)} years` },
      { label: '初始資金', value: money(s.initial_capital) },
      { label: '最終資金', value: money(s.final_capital) },
      { label: '獲利倍數', value: multiple },
      { label: '年化獲利', value: percent(s.annual_return_pct) }
    ]
  }
  return [
    { label: 'Symbol', value: props.symbol || '—' },
    { label: '期間', value: `${years.toFixed(2)} years` },
    { label: '交易成本', value: s.trade_cost ?? '—' },
    { label: '總獲利', value: money(s.net_profit) },
    { label: '年獲利', value: money(annualProfit) },
    { label: 'MDD', value: money(s.max_drawdown) },
    { label: '總獲利/MDD', value: number(s.profit_over_mdd) },
    { label: '年獲利/MDD', value: number(s.max_drawdown ? annualProfit / s.max_drawdown : 0) },
    { label: 'Sharpe Ratio', value: number(s.sharpe_ratio) },
    { label: 'Sortino Ratio', value: number(s.sortino_ratio) },
    { label: '獲利因子', value: number(s.profit_factor) },
    { label: '交易次數', value: number(s.trade_count, 0) },
    { label: '贏錢次數', value: number(s.winning_count, 0) },
    { label: '輸錢次數', value: number(s.losing_count, 0) },
    { label: '贏錢機率', value: `${Number(s.win_rate_pct || 0).toFixed(2)}%` }
  ]
})
</script>

<template>
  <section class="summary-panel">
    <h3>Summary <span class="summary-date">{{ dateSuffix }}</span></h3>
    <div class="cards" :class="{ 'cards-compound': compound }"><div v-for="item in cards" :key="item.label" class="card"><div class="label">{{ item.label }}</div><div class="value">{{ item.value }}</div></div></div>
    <h3>MDD</h3>
    <div class="table-scroll">
      <table class="grid">
        <thead><tr><th>#</th><th v-if="compound">MDD(%)</th><th>{{ compound ? 'MDD($)' : 'MDD' }}</th><th>日期</th><th>低點天數</th><th>回升天數</th></tr></thead>
        <tbody>
          <tr v-for="(row, index) in section.drawdowns" :key="index">
            <td>{{ index + 1 }}</td>
            <td v-if="compound">{{ percent(row.percent) }}</td>
            <td>{{ compound ? money(row.amount) : number(row.amount, 0) }}</td>
            <td>{{ row.started_at?.slice(0, 10) }} ~ {{ row.bottomed_at?.slice(0, 10) }}</td>
            <td>{{ days(row.started_at, row.bottomed_at) }}</td>
            <td>{{ days(row.started_at, row.recovered_at) ?? '—' }}</td>
          </tr>
          <tr v-if="!section.drawdowns?.length"><td :colspan="compound ? 6 : 5" class="no-data">此區間沒有回撤</td></tr>
        </tbody>
      </table>
    </div>
    <template v-for="period in [{ key: 'annual', title: 'Annual Profits' }, { key: 'monthly', title: 'Month Profits' }]" :key="period.key">
      <h3>{{ period.title }}</h3>
      <div class="table-scroll">
        <table class="grid">
          <thead><tr><th>Date</th><th v-if="compound">Profit(%)</th><th>{{ compound ? 'Profit($)' : 'Profit' }}</th><th v-if="compound">MDD(%)</th><th>{{ compound ? 'MDD($)' : 'MDD' }}</th></tr></thead>
          <tbody>
            <tr v-for="row in section.periods?.[period.key] || []" :key="row.period" :class="row.profit >= 0 ? 'row-profit' : 'row-loss'">
              <td>{{ row.period }}</td>
              <td v-if="compound">{{ percent(row.return_pct) }}</td>
              <td>{{ compound ? money(row.profit) : number(row.profit, 0) }}</td>
              <td v-if="compound">{{ percent(row.mdd_pct) }}</td>
              <td>{{ compound ? money(row.mdd) : number(row.mdd, 0) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<style scoped>
/* Visual Portfolio SummaryPanel layout and styles. */
.cards { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin-bottom: 14px; }
.cards.cards-compound { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.card { border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; position: relative; }
.label { color: var(--muted); font-size: 13px; }
.value { font-size: 18px; font-weight: 700; overflow-wrap: anywhere; }
.grid { width: 100%; border-collapse: collapse; margin-bottom: 14px; font-size: 16px; }
.grid th, .grid td { border: 1px solid var(--line); padding: 8px; text-align: right; }
.grid th:first-child, .grid td:first-child { text-align: left; }
h3 { margin: 8px 0; font-size: 1.17em; }
.summary-date { font-size: 0.8em; color: #4b5563; font-weight: 500; }
.row-profit { color: #1d4ed8; }
.row-loss { color: #b00020; }
@media (max-width: 1400px) { .cards { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@media (max-width: 1100px) { .cards { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 800px) { .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .cards { grid-template-columns: 1fr; } }
@media (max-width: 800px) { .cards.cards-compound { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .cards.cards-compound { grid-template-columns: 1fr; } }
@media print { .card, tr { break-inside: avoid; } }
</style>
