<template>
  <section>
    <h4>Config</h4>
    <div class="config-cards">
      <div class="config-card" v-for="c in configRows" :key="c.key">
        <button type="button" class="edit-btn" title="編輯" aria-label="編輯" @click="startEdit(c)">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z"/>
          </svg>
        </button>
        <div class="label">{{ c.label }}</div>
        <div v-if="editingKey === c.key" class="edit-row">
          <input
            ref="editInputRef"
            v-model="draftValue"
            class="edit-input"
            type="text"
            @keydown.enter.prevent="saveEdit(c)"
            @keyup.esc="cancelEdit"
            @blur="cancelEdit"
          />
        </div>
        <div v-else class="val">{{ c.value }}</div>
      </div>
    </div>
    <p v-if="configError" class="error">{{ configError }}</p>

    <section v-for="yb in yearBlocks" :key="yb.year" class="year-block">
      <h4 class="year-title">Year {{ yb.year }}</h4>
      <table class="table">
        <thead>
          <tr>
            <th>季別</th>
            <th>季初資金</th>
            <th>季末資金</th>
            <th>獲利</th>
            <th>季績效</th>
            <th>分潤</th>
            <th>客戶淨獲利</th>
            <th>手續費退傭</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in yb.rows" :key="`${yb.year}-${r.quarter}`" :class="{ 'full-year': r.quarter === '全年' }">
            <td>{{ r.quarter }}</td>
            <td>{{ intNum(r.start_capital) }}</td>
            <td>{{ intNum(r.end_capital) }}</td>
            <td>{{ intNum(r.profit) }}</td>
            <td>{{ pct1(r.quarter_perf) }}</td>
            <td>{{ intNum(r.share) }}</td>
            <td>{{ intNum(r.client_net_profit) }}</td>
            <td>{{ intNum(r.rebate) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="year-metrics">
        <div class="ym-item"><span>年度績效</span><b>{{ pct1(yb.yearPerf) }}</b></div>
        <div class="ym-item"><span>績效獎金</span><b>{{ intNum(yb.bonus) }}</b></div>
        <div class="ym-item"><span>獎金級距</span><b>{{ pct0(yb.bonusRate) }}</b></div>
        <div class="ym-item"><span>綜合所得</span><b>{{ intNum(yb.totalIncome) }}</b></div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '../stores/portfolio'

const props = defineProps({
  readonly: { type: Boolean, default: false }
})

const route = useRoute()
const portfolioStore = usePortfolioStore()
const { analysis, commissionConfig } = storeToRefs(portfolioStore)
const commission = computed(() => analysis.value.commission || {})
const commissionCfg = computed(() => commissionConfig.value || commission.value.config || {})
const editingKey = ref('')
const draftValue = ref('')
const configError = ref('')
const committingByEnter = ref(false)
const editInputRef = ref(null)

const configDefs = [
  { key: 'ref_capital', label: '回測金額(萬)', defaultValue: 840, digits: 0 },
  { key: 'init_capital', label: '初始資金(萬)', defaultValue: 840, digits: 0 },
  { key: 'leverage', label: '資金槓桿', defaultValue: 3, digits: 2 },
  { key: 'fee_rate', label: '每次手續費(%)', defaultValue: 0.05, digits: 2 },
  { key: 'rebate_rate', label: '手續費退傭(%)', defaultValue: 50, digits: 2 },
  { key: 'quarter_share_rate', label: '季分潤(%)', defaultValue: 30, digits: 2 },
  { key: 'bonus_threshold1', label: '績效門檻1(%)', defaultValue: 100, digits: 2 },
  { key: 'bonus_rate1', label: '獎金比率1(%)', defaultValue: 10, digits: 2 },
  { key: 'bonus_threshold2', label: '績效門檻2(%)', defaultValue: 150, digits: 2 },
  { key: 'bonus_rate2', label: '獎金比率2(%)', defaultValue: 20, digits: 2 },
  { key: 'bonus_threshold3', label: '績效門檻3(%)', defaultValue: 200, digits: 2 },
  { key: 'bonus_rate3', label: '獎金比率3(%)', defaultValue: 30, digits: 2 },
  { key: 'bonus_threshold4', label: '績效門檻4(%)', defaultValue: 0, digits: 2 },
  { key: 'bonus_rate4', label: '獎金比率4(%)', defaultValue: 0, digits: 2 }
]

const normalizedConfig = computed(() => {
  const cfg = commissionCfg.value
  const out = {}
  for (const d of configDefs) {
    const n = Number(cfg[d.key])
    out[d.key] = Number.isFinite(n) ? n : d.defaultValue
  }
  return out
})

const configRows = computed(() => {
  return configDefs.map((d) => {
    const v = normalizedConfig.value[d.key]
    return {
      key: d.key,
      label: d.label,
      digits: d.digits,
      value: d.digits === 0 ? num0(v) : num(v)
    }
  })
})
const quarterMap = {
  1: '第一季',
  2: '第二季',
  3: '第三季',
  4: '第四季',
  '1': '第一季',
  '2': '第二季',
  '3': '第三季',
  '4': '第四季',
  '全年': '全年'
}

const yearBlocks = computed(() => {
  return (commission.value.years || []).map((y) => {
    const rows = (y.entries || []).map((e) => {
      const start = Number(e.start_capital || 0)
      const profit = Number(e.profit || 0)
      return {
        quarter: quarterMap[e.quarter] || String(e.quarter),
        start_capital: start,
        end_capital: Number(e.end_capital || 0),
        profit,
        quarter_perf: start > 0 ? profit / start : 0,
        share: Number(e.share || 0),
        client_net_profit: Number(e.client_net_profit || 0),
        rebate: Number(e.rebate || 0)
      }
    })
    return {
      year: y.year,
      rows,
      yearPerf: Number(y.year_perf || 0),
      bonusRate: Number(y.bonus_rate || 0),
      bonus: Number(y.bonus || 0),
      totalIncome: Number(y.total_income || 0)
    }
  })
})

function num(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function num0(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function pct1(v) {
  const n = Number(v || 0) * 100
  return `${n.toFixed(1)}%`
}

function pct0(v) {
  const n = Number(v || 0) * 100
  return `${n.toFixed(0)}%`
}

function intNum(v) {
  const n = Math.round(Number(v || 0))
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function startEdit(row) {
  configError.value = ''
  editingKey.value = row.key
  draftValue.value = String(normalizedConfig.value[row.key] ?? 0)
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
  const n = Number(draftValue.value)
  if (!Number.isFinite(n)) {
    configError.value = '請輸入有效數值'
    committingByEnter.value = false
    return
  }
  const next = {
    ...normalizedConfig.value,
    [row.key]: n
  }
  configError.value = ''
  editingKey.value = ''
  draftValue.value = ''
  try {
    portfolioStore.setCommissionConfig(next)
    if (props.readonly) {
      await portfolioStore.analyze(route.params.projectId)
    } else {
      await portfolioStore.persistAndAnalyze(route.params.projectId)
    }
  } catch (e) {
    configError.value = e.message || '更新分潤設定失敗'
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
</script>

<style scoped>
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
.edit-btn:hover {
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
.label {
  color: var(--muted);
  font-size: 13px;
}
.val {
  font-size: 20px;
  font-weight: 700;
}
.table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  text-align: right;
}
th:first-child, td:first-child,
th:nth-child(2), td:nth-child(2) {
  text-align: center;
}
.year-block {
  margin-top: 10px;
}
.year-title {
  font-size: 36px;
  font-weight: 700;
  margin: 8px 0;
}
.full-year td {
  color: #2f56d6;
  font-weight: 600;
}
.year-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.ym-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
}
.ym-item span {
  color: #111827;
  font-weight: 600;
}
.ym-item b {
  font-size: 20px;
}
h4 {
  margin: 8px 0;
}
@media (max-width: 1100px) {
  .config-cards {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }
  .year-metrics {
    grid-template-columns: repeat(2, minmax(150px, 1fr));
  }
}
</style>
