<template>
  <section>
    <div class="head-row">
      <h3>動態複利</h3>
      <button type="button" class="help-btn" @click="openHelp">Help</button>
    </div>

    <div class="form-grid">
      <label class="field">
        <span>初始資金</span>
        <input :value="draft.initial_capital" type="number" step="1" min="1" :disabled="props.readonly" @change="onFieldChange('initial_capital', $event.target.value)" />
      </label>
      <label class="field">
        <span>MDD（參考）</span>
        <input :value="refMdd" type="text" readonly />
      </label>
      <label class="field">
        <span>初始比例</span>
        <input :value="draft.initial_ratio" type="number" step="0.0001" min="0" :disabled="props.readonly" @change="onFieldChange('initial_ratio', $event.target.value)" />
      </label>
      <label class="field">
        <span>獲利達加碼</span>
        <input :value="draft.add_threshold_profit" type="number" step="1" :disabled="props.readonly" @change="onFieldChange('add_threshold_profit', $event.target.value)" />
      </label>
      <label class="field">
        <span>加碼比例</span>
        <input :value="draft.add_ratio" type="number" step="0.0001" min="0" :disabled="props.readonly" @change="onFieldChange('add_ratio', $event.target.value)" />
      </label>
      <label class="field">
        <span>回徹金額</span>
        <input :value="draft.rollback_amount" type="number" step="1" min="0" :disabled="props.readonly" @change="onFieldChange('rollback_amount', $event.target.value)" />
      </label>
      <label class="field">
        <span>最大倍數</span>
        <input :value="draft.max_multiple" type="number" step="0.01" min="0" :disabled="props.readonly" @change="onFieldChange('max_multiple', $event.target.value)" />
      </label>
    </div>

    <div class="action-row">
      <button type="button" :disabled="props.readonly || portfolioStore.loading || portfolioStore.updatingConfig" @click="applyConfig">
        套用並重算
      </button>
      <span v-if="portfolioStore.loading || portfolioStore.updatingConfig" class="busy">更新計算中...</span>
    </div>

    <table class="grid">
      <thead>
        <tr>
          <th>項目</th>
          <th>初始淨值</th>
          <th>最終淨值</th>
          <th>獲利倍數</th>
          <th>CAGR(%)</th>
          <th>MDD(%)</th>
          <th>MDD($)</th>
          <th>達到 10 倍規模日期</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>每週調整</td>
          <td>{{ moneyInt(weekly.initial_net_value) }}</td>
          <td>{{ moneyInt(weekly.final_net_value) }}</td>
          <td>{{ ratio(weekly.profit_multiple) }}</td>
          <td>{{ pct(weekly.cagr_pct) }}</td>
          <td>{{ pct(weekly.mdd_pct) }}</td>
          <td>{{ moneyInt(weekly.mdd_amount) }}</td>
          <td>{{ weekly.reach_10x_date || '未達成' }}</td>
        </tr>
        <tr>
          <td>每月調整</td>
          <td>{{ moneyInt(monthly.initial_net_value) }}</td>
          <td>{{ moneyInt(monthly.final_net_value) }}</td>
          <td>{{ ratio(monthly.profit_multiple) }}</td>
          <td>{{ pct(monthly.cagr_pct) }}</td>
          <td>{{ pct(monthly.mdd_pct) }}</td>
          <td>{{ moneyInt(monthly.mdd_amount) }}</td>
          <td>{{ monthly.reach_10x_date || '未達成' }}</td>
        </tr>
      </tbody>
    </table>

    <dialog ref="helpDialogRef" class="help-dialog">
      <form method="dialog" class="help-form">
        <h4>動態複利規則</h4>
        <p>一開始用 {{ percentText(draft.initial_ratio) }}</p>
        <p>累積獲利 &gt; {{ moneyInt(draft.add_threshold_profit) }}，下一期切到 {{ percentText(draft.add_ratio) }}</p>
        <p>切到 {{ percentText(draft.add_ratio) }} 後，只要從高點回撤 &gt; {{ moneyInt(draft.rollback_amount) }}，下一期切回 {{ percentText(draft.initial_ratio) }}</p>
        <p>切回 {{ percentText(draft.initial_ratio) }} 後，只要再賺回 {{ moneyInt(draft.rollback_amount) }}（創新高），下一期再切回 {{ percentText(draft.add_ratio) }}</p>
        <p>交易資金 {{ moneyInt(draft.max_multiple * draft.initial_capital) }} 封頂，最大為 {{ num2(draft.max_multiple) }} 倍初始資金。</p>
        <div class="help-actions">
          <button type="submit">關閉</button>
        </div>
      </form>
    </dialog>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '../stores/portfolio'

const props = defineProps({
  readonly: { type: Boolean, default: false }
})

const route = useRoute()
const portfolioStore = usePortfolioStore()
const { analysis } = storeToRefs(portfolioStore)
const helpDialogRef = ref(null)

const draft = ref({
  initial_capital: 80000000,
  initial_ratio: 0.1,
  add_threshold_profit: 100000000,
  add_ratio: 0.15,
  rollback_amount: 20000000,
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
      max_multiple: Number(cfg?.max_multiple || 10)
    }
  },
  { immediate: true, deep: true }
)

const refMdd = computed(() => moneyInt(Number(analysis.value?.summary?.mdd || 0)))
const weekly = computed(() => analysis.value?.dynamic_compounding?.weekly || {})
const monthly = computed(() => analysis.value?.dynamic_compounding?.monthly || {})

function onFieldChange(key, value) {
  const n = Number(String(value || '').replace(/,/g, '').trim())
  if (!Number.isFinite(n)) return
  draft.value = { ...draft.value, [key]: n }
}

async function applyConfig() {
  portfolioStore.setDynamicCompoundingConfig(draft.value)
  await portfolioStore.persistAndAnalyze(route.params.projectId)
}

function openHelp() {
  helpDialogRef.value?.showModal()
}

function moneyInt(v) {
  const n = Math.round(Number(v || 0))
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function ratio(v) {
  return Number(v || 0).toFixed(4)
}

function pct(v) {
  return Number(v || 0).toFixed(2)
}

function percentText(v) {
  return `${(Number(v || 0) * 100).toFixed(2)}%`
}

function num2(v) {
  return Number(v || 0).toFixed(2)
}
</script>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.help-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
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
.action-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}
.busy {
  color: var(--muted);
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
.help-dialog {
  border: none;
  border-radius: 10px;
  padding: 0;
}
.help-form {
  padding: 16px;
  min-width: min(640px, 92vw);
}
.help-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
