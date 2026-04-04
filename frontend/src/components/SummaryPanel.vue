<template>
  <section>
    <h3>
      Summary
      <span v-if="summaryDateSuffix" class="summary-date">{{ summaryDateSuffix }}</span>
    </h3>
    <div class="cards">
      <div v-for="item in summaryCards" :key="item.label" class="card" :class="{ 'card-editable': item.editable }">
        <button
          v-if="item.editable"
          type="button"
          class="card-edit-btn"
          title="編輯 Sharpe 設定"
          aria-label="編輯 Sharpe 設定"
          @click="editSharpeConfig"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm17.71-10.04a1.003 1.003 0 0 0 0-1.42l-2.5-2.5a1.003 1.003 0 0 0-1.42 0L14.71 5.37l3.75 3.75 2.25-2.25z"/>
          </svg>
        </button>
        <div class="label">{{ item.label }}</div>
        <div class="value">{{ item.value }}</div>
      </div>
    </div>
    <dialog ref="sharpeDialogRef" class="sharpe-dialog">
      <form method="dialog" class="sharpe-form" @submit.prevent="confirmSharpeDialog">
        <h4>Sharpe 設定</h4>
        <label class="sharpe-field">
          <span>本金（萬元）</span>
          <input v-model="sharpeDraftCapitalWan" type="number" step="0.01" min="0" />
        </label>
        <label class="sharpe-field">
          <span>無風險利率（年化 %）</span>
          <input v-model="sharpeDraftRiskFreeRate" type="number" step="0.01" />
        </label>
        <div class="sharpe-actions">
          <button type="button" @click="closeSharpeDialog">取消</button>
          <button type="submit">確定</button>
        </div>
      </form>
    </dialog>

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
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '../stores/portfolio'

const props = defineProps({
  readonly: { type: Boolean, default: false }
})

const route = useRoute()
const portfolioStore = usePortfolioStore()
const { analysis } = storeToRefs(portfolioStore)
const sharpeDialogRef = ref(null)
const sharpeDraftCapitalWan = ref('')
const sharpeDraftRiskFreeRate = ref('')
const summary = computed(() => analysis.value.summary || {})
const trades = computed(() => analysis.value.position_analysis || [])
const realTrades = computed(() =>
  trades.value.filter((t) => Math.abs(Number(t?.trade_amount || 0)) > 0)
)
const periodDates = computed(() => parsePeriod(summary.value.period))
const periodYears = computed(() => {
  const { start, end } = periodDates.value
  if (!start || !end) return 0
  return ((end - start) / 86400000 + 1) / 365.25
})

const derived = computed(() => {
  const netProfit = Number(summary.value.net_profit || 0)
  const mdd = Math.abs(Number(summary.value.mdd || 0))
  const tradeCount = Number(summary.value.trade_count || realTrades.value.length || 0)
  const winCount = realTrades.value.filter((t) => Number(t.pnl || 0) > 0).length
  const lossCount = tradeCount - winCount
  const winAmount = realTrades.value
    .filter((t) => Number(t.pnl || 0) > 0)
    .reduce((s, t) => s + Number(t.pnl || 0), 0)
  const lossAmount = realTrades.value
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
  { label: '交易次數', value: num0(derived.value.tradeCount) },
  { label: '總獲利', value: moneyInt(derived.value.netProfit) },
  { label: '年獲利', value: moneyInt(derived.value.yearProfit) },
  { label: 'MDD', value: moneyInt(derived.value.mdd) },
  { label: '總獲利/MDD', value: ratio(derived.value.pmr) },
  { label: '年獲利/MDD', value: ratio(derived.value.ypmr) },
  { label: 'Sharpe Ratio', value: ratio(summary.value.sharpe), editable: true },
  { label: 'Sortino Ratio', value: ratio(summary.value.sortino) },
  { label: '獲利因子', value: ratio(derived.value.profitFactor) },
  { label: '贏錢總金額', value: moneyInt(derived.value.winAmount) },
  { label: '輸錢總金額', value: moneyInt(derived.value.lossAmount) },
  { label: '贏錢次數', value: num0(derived.value.winCount) },
  { label: '輸錢次數', value: num0(derived.value.lossCount) },
  { label: '贏錢機率', value: `${derived.value.winProb.toFixed(2)}%` },
].filter(Boolean))

const summaryDateSuffix = computed(() => {
  const txt = tradeDateRange(periodDates.value.start, periodDates.value.end)
  return txt && txt !== '-' ? `(${txt})` : ''
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

async function editSharpeConfig() {
  const currentCapital = Number(portfolioStore.sharpeConfig?.capital || 1000000)
  const currentRf = Number(portfolioStore.sharpeConfig?.risk_free_rate || 0)
  sharpeDraftCapitalWan.value = String(currentCapital / 10000)
  sharpeDraftRiskFreeRate.value = String(currentRf)
  sharpeDialogRef.value?.showModal()
}

function closeSharpeDialog() {
  sharpeDialogRef.value?.close()
}

async function confirmSharpeDialog() {
  const capitalWan = Number(String(sharpeDraftCapitalWan.value || '').replace(/,/g, '').trim())
  const riskFreeRate = Number(String(sharpeDraftRiskFreeRate.value || '').replace(/,/g, '').trim())
  if (!Number.isFinite(capitalWan) || capitalWan <= 0) {
    alert('本金（萬元）必須是大於 0 的數字')
    return
  }
  if (!Number.isFinite(riskFreeRate)) {
    alert('無風險利率必須是數字')
    return
  }

  const capital = capitalWan * 10000
  const prevCapital = Number(portfolioStore.sharpeConfig?.capital || 1000000)
  const prevRf = Number(portfolioStore.sharpeConfig?.risk_free_rate || 0)
  const changed = Math.abs(capital - prevCapital) > 1e-9 || Math.abs(riskFreeRate - prevRf) > 1e-9
  if (!changed) {
    closeSharpeDialog()
    return
  }

  portfolioStore.setSharpeConfig({
    capital,
    risk_free_rate: riskFreeRate
  })

  recalcSharpeOnly(capital, riskFreeRate)

  if (!props.readonly) {
    try {
      await portfolioStore.saveGseaGroup(route.params.projectId)
    } catch (e) {
      alert(e?.message || '儲存 Sharpe 設定失敗')
    }
  }

  closeSharpeDialog()
}

function recalcSharpeOnly(capital, riskFreeRate) {
  const rows = analysis.value.position_analysis || []
  if (!rows.length) {
    portfolioStore.analysis.summary = {
      ...(portfolioStore.analysis.summary || {}),
      sharpe: 0
    }
    return
  }

  const dayPnl = new Map()
  const dates = []
  for (const r of rows) {
    const d = String(r?.exit || '').slice(0, 10)
    if (!d) continue
    const pnl = Number(r?.pnl || 0)
    dayPnl.set(d, Number(dayPnl.get(d) || 0) + pnl)
    dates.push(d)
  }
  if (!dates.length || dayPnl.size === 0) {
    portfolioStore.analysis.summary = {
      ...(portfolioStore.analysis.summary || {}),
      sharpe: 0
    }
    return
  }

  dates.sort()
  const start = new Date(dates[0])
  const end = new Date(dates[dates.length - 1])
  const years = Math.max(((end - start) / 86400000 + 1) / 365.25, 1e-9)
  const ep = Array.from(dayPnl.values())
  const n = years > 0 ? ep.length / years : ep.length
  const rf = n > 0 ? (riskFreeRate * 0.01) / n : 0
  const usedCapital = capital > 0 ? capital : 1000000
  const adjusted = ep.map((x) => (x / usedCapital) - rf)
  const mean = adjusted.length ? adjusted.reduce((a, b) => a + b, 0) / adjusted.length : 0
  const std = stdPop(adjusted)
  const sharpe = std > 0 && n > 0 ? (Math.sqrt(n) * mean) / std : 0

  portfolioStore.analysis.summary = {
    ...(portfolioStore.analysis.summary || {}),
    sharpe: round6(sharpe)
  }
}

function stdPop(values) {
  if (!values.length) return 0
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const variance = values.reduce((s, x) => s + (x - mean) * (x - mean), 0) / values.length
  return Math.sqrt(variance)
}

function round6(v) {
  return Math.round(Number(v || 0) * 1e6) / 1e6
}
</script>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 14px;
}
.card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 10px;
  position: relative;
}
.card-editable {
  padding-right: 34px;
}
.card-edit-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #6b7280;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.card-edit-btn svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
}
.card-edit-btn:hover,
.card-edit-btn:focus-visible {
  color: var(--accent);
  background: #eef2ff;
}
.sharpe-dialog {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0;
  max-width: 420px;
  width: calc(100% - 24px);
}
.sharpe-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
}
.sharpe-form h4 {
  margin: 0 0 2px;
}
.sharpe-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}
.sharpe-field input {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 6px 8px;
}
.sharpe-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 2px;
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
.summary-date {
  font-size: 0.8em;
  color: #4b5563;
  font-weight: 500;
}
.row-profit {
  color: #1d4ed8;
}
.row-loss {
  color: #b00020;
}
@media (max-width: 1400px) {
  .cards {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
@media (max-width: 1100px) {
  .cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 800px) {
  .cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 520px) {
  .cards {
    grid-template-columns: 1fr;
  }
}
</style>
