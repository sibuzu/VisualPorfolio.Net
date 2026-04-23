<template>
  <section>
    <div class="head-row">
      <h3 class="head-title">
        <span>動態複利</span>
        <button type="button" class="help-btn" title="Help" aria-label="Help" @click="openHelp">
          <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24" aria-hidden="true">
            <path d="M0 0h24v24H0z" fill="none"/>
            <path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z"/>
          </svg>
        </button>
      </h3>
    </div>

    <div class="config-cards">
      <div class="config-card" v-for="row in configRows" :key="row.key">
        <button
          v-if="row.editable"
          type="button"
          class="edit-btn"
          title="編輯"
          aria-label="編輯"
          @click="startEdit(row)"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z"/>
          </svg>
        </button>
        <div class="label">{{ row.label }}</div>
        <div v-if="editingKey === row.key" class="edit-row">
          <input
            ref="editInputRef"
            v-model="draftValue"
            class="edit-input"
            type="text"
            @keydown.enter.prevent="saveEdit(row)"
            @keyup.esc="cancelEdit"
            @blur="cancelEdit"
          />
        </div>
        <div v-else class="val">{{ row.value }}</div>
      </div>
    </div>
    <p v-if="configError" class="error">{{ configError }}</p>
    <p v-if="portfolioStore.loading || portfolioStore.updatingConfig" class="busy">更新計算中...</p>

    <table class="grid">
      <colgroup>
        <col style="width: 28%" />
        <col style="width: 36%" />
        <col style="width: 36%" />
      </colgroup>
      <thead>
        <tr>
          <th>項目</th>
          <th>每週調整</th>
          <th>每月調整</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>初始淨值(萬)</td>
          <td>{{ wanIntText(weekly.initial_net_value) }}</td>
          <td>{{ wanIntText(monthly.initial_net_value) }}</td>
        </tr>
        <tr>
          <td>最終淨值(萬)</td>
          <td>{{ wanIntText(weekly.final_net_value) }}</td>
          <td>{{ wanIntText(monthly.final_net_value) }}</td>
        </tr>
        <tr>
          <td>獲利倍數</td>
          <td>{{ ratio(weekly.profit_multiple) }}</td>
          <td>{{ ratio(monthly.profit_multiple) }}</td>
        </tr>
        <tr>
          <td>CAGR(%)</td>
          <td>{{ pct(weekly.cagr_pct) }}</td>
          <td>{{ pct(monthly.cagr_pct) }}</td>
        </tr>
        <tr>
          <td>MDD(%)</td>
          <td>{{ pct(weekly.mdd_pct) }}</td>
          <td>{{ pct(monthly.mdd_pct) }}</td>
        </tr>
        <tr>
          <td>MDD(萬)</td>
          <td>{{ wanIntText(weekly.mdd_amount) }}</td>
          <td>{{ wanIntText(monthly.mdd_amount) }}</td>
        </tr>
        <tr>
          <td>MDD%日期</td>
          <td>{{ dateText(weekly.mdd_pct_date) }}</td>
          <td>{{ dateText(monthly.mdd_pct_date) }}</td>
        </tr>
        <tr>
          <td>MDD萬日期</td>
          <td>{{ dateText(weekly.mdd_amount_date) }}</td>
          <td>{{ dateText(monthly.mdd_amount_date) }}</td>
        </tr>
        <tr>
          <td>高點回撤調整次數</td>
          <td>{{ int0(weekly.rollback_adjust_count) }}</td>
          <td>{{ int0(monthly.rollback_adjust_count) }}</td>
        </tr>
        <tr>
          <td>達到最大倍數規模日期</td>
          <td>{{ maxScaleDate(weekly) }}</td>
          <td>{{ maxScaleDate(monthly) }}</td>
        </tr>
      </tbody>
    </table>

    <h4>Dynamic MDD Equity Curve - Weekly vs Monthly Rebalance</h4>
    <div ref="curveChartRef" class="curve-chart"></div>
    <p class="curve-summary">
      Final Weekly: {{ moneyText(weekly.final_net_value) }}
      &nbsp;&nbsp; Final Monthly: {{ moneyText(monthly.final_net_value) }}
      &nbsp;&nbsp; Difference (M-W): {{ moneyText((monthly.final_net_value || 0) - (weekly.final_net_value || 0)) }}
    </p>

    <dialog ref="helpDialogRef" class="help-dialog">
      <form method="dialog" class="help-form">
        <h4>動態複利規則</h4>
        <pre class="help-lines">
  1. 一開始用 {{ percentText(draft.initial_ratio) }}，初始MDD風險控制為 {{ wanIntText(draft.initial_capital * draft.initial_ratio) }} 萬。
  2. 累積獲利 &gt; {{ wanIntText(draft.add_threshold_profit) }} 萬，下一期切到 {{ percentText(draft.add_ratio) }}。
  3. 切到 {{ percentText(draft.add_ratio) }} 後，只要從高點回撤 &gt; {{ rollbackThresholdHelpText() }}，下一期切回 {{ percentText(draft.initial_ratio) }}。
  4. 切回 {{ percentText(draft.initial_ratio) }} 後，只要淨值再創新高，下一期再切回 {{ percentText(draft.add_ratio) }}。
  5. MDD風險控制 {{ wanIntText(draft.max_multiple * draft.initial_capital * draft.initial_ratio) }} 萬封頂，最大為 {{ compactNum(draft.max_multiple) }}倍初始MDD風險控制。
        </pre>
        <div class="help-actions">
          <button type="submit">關閉</button>
        </div>
      </form>
    </dialog>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { storeToRefs } from 'pinia'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '../stores/portfolio'

const props = defineProps({
  readonly: { type: Boolean, default: false }
})

const route = useRoute()
const portfolioStore = usePortfolioStore()
const { analysis } = storeToRefs(portfolioStore)
const helpDialogRef = ref(null)
const curveChartRef = ref(null)
let curveChart
const editingKey = ref('')
const draftValue = ref('')
const configError = ref('')
const committingByEnter = ref(false)
const editInputRef = ref(null)

const draft = ref({
  initial_capital: 80000000,
  initial_ratio: 0.1,
  add_threshold_profit: 100000000,
  add_ratio: 0.15,
  rollback_amount: 20000000,
  rollback_percent: 0,
  max_multiple: 10
})

watch(
  () => portfolioStore.dynamicCompoundingConfig,
  (cfg) => {
    draft.value = {
      initial_capital: Number(cfg?.initial_capital || 80000000),
      initial_ratio: Number(cfg?.initial_ratio || 0.1),
      add_threshold_profit: Number(cfg?.add_threshold_profit || 100000000),
      add_ratio: Number(cfg?.add_ratio || 0.15),
      rollback_amount: Number(cfg?.rollback_amount || 20000000),
      rollback_percent: Number(cfg?.rollback_percent || 0),
      max_multiple: Number(cfg?.max_multiple || 10)
    }
  },
  { immediate: true, deep: true }
)

const refMdd = computed(() => wanIntText(Number(analysis.value?.summary?.mdd || 0)))
const weekly = computed(() => analysis.value?.dynamic_compounding?.weekly || {})
const monthly = computed(() => analysis.value?.dynamic_compounding?.monthly || {})

const configRows = computed(() => [
  { key: 'initial_capital', label: '初始資金(萬)', value: wanIntText(draft.value.initial_capital), editable: true, kind: 'amount' },
  { key: 'mdd_ref', label: 'MDD（萬）', value: refMdd.value, editable: false, kind: 'readonly' },
  { key: 'initial_ratio', label: '初始比例', value: ratio(draft.value.initial_ratio), editable: true, kind: 'ratio' },
  { key: 'add_threshold_profit', label: '獲利達加碼(萬)', value: wanIntText(draft.value.add_threshold_profit), editable: true, kind: 'amount' },
  { key: 'add_ratio', label: '加碼比例', value: ratio(draft.value.add_ratio), editable: true, kind: 'ratio' },
  { key: 'rollback_amount', label: '回徹金額(萬, %)', value: rollbackDisplayText(), editable: true, kind: 'rollback' },
  { key: 'max_multiple', label: '最大倍數', value: ratio(draft.value.max_multiple), editable: true, kind: 'ratio' }
])

function startEdit(row) {
  if (!row.editable) return
  configError.value = ''
  editingKey.value = row.key
  const current = draft.value[row.key]
  if (row.kind === 'amount') {
    draftValue.value = String(toWanInt(current))
  } else if (row.kind === 'rollback') {
    draftValue.value = rollbackEditText()
  } else {
    draftValue.value = String(current ?? '')
  }
  nextTick(() => {
    const el = editInputRef.value
    if (el && typeof el.focus === 'function') {
      el.focus()
      if (typeof el.select === 'function') el.select()
    }
  })
}

async function saveEdit(row) {
  committingByEnter.value = true
  const raw = String(draftValue.value || '').replace(/,/g, '').trim()
  const nextDraft = { ...draft.value }
  if (row.kind === 'rollback') {
    const parsed = parseRollbackInput(raw)
    if (!parsed.ok) {
      configError.value = parsed.error
      committingByEnter.value = false
      return
    }
    nextDraft.rollback_amount = parsed.rollback_amount
    nextDraft.rollback_percent = parsed.rollback_percent
  } else {
    const n = Number(raw)
    if (!Number.isFinite(n)) {
      configError.value = '請輸入有效數值'
      committingByEnter.value = false
      return
    }
    if (row.kind === 'amount') {
      nextDraft[row.key] = Math.round(n) * 10000
    } else {
      nextDraft[row.key] = n
    }
  }

  configError.value = ''
  editingKey.value = ''
  draftValue.value = ''
  draft.value = nextDraft

  try {
    portfolioStore.setDynamicCompoundingConfig(nextDraft)
    if (props.readonly) {
      await portfolioStore.analyze(route.params.projectId)
    } else {
      await portfolioStore.persistAndAnalyze(route.params.projectId)
    }
  } catch (e) {
    configError.value = e.message || '更新動態複利設定失敗'
  } finally {
    nextTick(() => {
      committingByEnter.value = false
    })
  }
}

function cancelEdit() {
  if (committingByEnter.value) return
  editingKey.value = ''
  draftValue.value = ''
}

function openHelp() {
  helpDialogRef.value?.showModal()
}

function rollbackDisplayText() {
  const pct = Number(draft.value.rollback_percent || 0)
  if (pct > 0) return percentText(pct)
  return wanIntText(draft.value.rollback_amount)
}

function rollbackEditText() {
  const pct = Number(draft.value.rollback_percent || 0)
  if (pct > 0) return `${compactNum(pct * 100)}%`
  return String(toWanInt(draft.value.rollback_amount))
}

function rollbackThresholdHelpText() {
  const pct = Number(draft.value.rollback_percent || 0)
  if (pct > 0) return `${percentText(pct)}（相對高點）`
  return `${wanIntText(draft.value.rollback_amount)} 萬`
}

function parseRollbackInput(raw) {
  const text = String(raw || '').trim()
  const hasPercent = /%\s*$/.test(text)
  const numberText = hasPercent ? text.replace(/%\s*$/, '').trim() : text
  const n = Number(numberText)
  if (!Number.isFinite(n) || n < 0) {
    return { ok: false, error: '請輸入有效數值' }
  }
  if (hasPercent) {
    return {
      ok: true,
      rollback_amount: Number(draft.value.rollback_amount || 0),
      rollback_percent: n / 100
    }
  }
  return {
    ok: true,
    rollback_amount: Math.round(n) * 10000,
    rollback_percent: 0
  }
}

function toWanInt(v) {
  return Math.round(Number(v || 0) / 10000)
}

function wanIntText(v) {
  const n = toWanInt(v)
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function ratio(v) {
  return Number(v || 0).toFixed(2)
}

function pct(v) {
  return Number(v || 0).toFixed(2)
}

function percentText(v) {
  return `${compactNum(Number(v || 0) * 100)}%`
}

function compactNum(v) {
  const s = Number(v || 0).toFixed(2)
  return s.replace(/\.?0+$/, '')
}

function int0(v) {
  return Math.round(Number(v || 0)).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function moneyText(v) {
  return Math.round(Number(v || 0)).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function dateText(v) {
  const s = String(v || '').trim()
  return s || '未達成'
}

function maxScaleDate(row) {
  return row?.reach_max_multiple_date || row?.reach_10x_date || '未達成'
}

function renderCurveChart() {
  if (!curveChartRef.value) return
  if (!curveChart) curveChart = echarts.init(curveChartRef.value)

  const weeklyCurve = Array.isArray(weekly.value?.curve) ? weekly.value.curve : []
  const monthlyCurve = Array.isArray(monthly.value?.curve) ? monthly.value.curve : []
  const toWan = (n) => Number(n || 0) / 10000

  curveChart.setOption(
    {
      backgroundColor: '#f3f3f3',
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v) => `${Math.round(Number(v || 0)).toLocaleString('en-US')} 萬`
      },
      legend: {
        show: true,
        top: 10,
        left: 22,
        data: ['Weekly Rebalance', 'Monthly Rebalance'],
        textStyle: {
          fontSize: 14
        }
      },
      grid: {
        left: 72,
        right: 22,
        top: 56,
        bottom: 42
      },
      xAxis: {
        type: 'time',
        splitLine: { show: true, lineStyle: { color: '#dddddd' } },
        axisLine: { lineStyle: { color: '#666' } },
        axisLabel: { color: '#555' }
      },
      yAxis: {
        type: 'value',
        name: '淨值(萬)',
        splitLine: { show: true, lineStyle: { color: '#dddddd' } },
        axisLine: { lineStyle: { color: '#666' } },
        axisLabel: {
          color: '#555',
          formatter: (v) => Math.round(Number(v || 0)).toLocaleString('en-US')
        }
      },
      series: [
        {
          name: 'Weekly Rebalance',
          type: 'line',
          smooth: false,
          showSymbol: false,
          lineStyle: { width: 1.5, color: '#1f77b4' },
          data: weeklyCurve.map((p) => [p.date, toWan(p.net_value)])
        },
        {
          name: 'Monthly Rebalance',
          type: 'line',
          smooth: false,
          showSymbol: false,
          lineStyle: { width: 1.5, color: '#ff7f0e' },
          data: monthlyCurve.map((p) => [p.date, toWan(p.net_value)])
        }
      ]
    },
    { notMerge: true }
  )
}

watch(
  [weekly, monthly],
  async () => {
    await nextTick()
    renderCurveChart()
  },
  { deep: true }
)

onMounted(() => {
  renderCurveChart()
})

onBeforeUnmount(() => {
  curveChart?.dispose()
  curveChart = null
})
</script>

<style scoped>
.head-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.head-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}
.config-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}
.config-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  position: relative;
}
.edit-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border: 0;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  padding: 0;
}
.edit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.edit-btn:hover:not(:disabled) {
  color: var(--accent);
}
.edit-btn svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}
.edit-row {
  margin-top: 4px;
  display: block;
}
.edit-input {
  width: 120px;
  padding: 4px 6px;
  border: 1px solid var(--line);
  border-radius: 6px;
}
.help-btn {
  border: 0;
  background: transparent;
  border-radius: 999px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
}
.help-btn:hover {
  background: rgba(0, 0, 0, 0.06);
}
.help-btn svg {
  width: 22px;
  height: 22px;
  fill: currentColor;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field input {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 10px;
}
.busy {
  color: var(--muted);
  margin: 4px 0 12px;
}
.label {
  color: var(--muted);
  font-size: 13px;
}
.val {
  font-size: 20px;
  font-weight: 700;
}
.grid {
  width: 100%;
  border-collapse: collapse;
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
.curve-chart {
  width: 100%;
  height: 420px;
  margin-top: 10px;
}
.curve-summary {
  margin: 10px 0 0;
  color: #2b2b2b;
  font-weight: 600;
  line-height: 1.4;
}
.help-dialog {
  border: none;
  border-radius: 10px;
  padding: 0;
}
.help-form {
  padding: 16px;
  min-width: min(640px, 92vw);
}
.help-lines {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  line-height: 1.7;
}
.help-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
@media (max-width: 1100px) {
  .config-cards {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }
}
</style>
