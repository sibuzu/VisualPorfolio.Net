<template>
  <section>
    <div class="cards">
      <div class="card" v-for="m in metricRows" :key="m.key">
        <div class="label">{{ m.label }}</div>
        <div class="val">{{ m.value }}</div>
      </div>
    </div>

    <h4>策略明細</h4>
    <table class="table">
      <thead>
        <tr>
          <th>策略</th>
          <th>成交占比</th>
          <th>交易次數</th>
          <th>總交易金額</th>
          <th>平均交易金額</th>
          <th>平均相關性</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in details" :key="d.strategy_index">
          <td>策略{{ Number(d.strategy_index) + 1 }}</td>
          <td>{{ pct(d.amount_share) }}</td>
          <td>{{ num(d.trade_count) }}</td>
          <td>{{ num(d.total_amount) }}</td>
          <td>{{ num(d.avg_amount) }}</td>
          <td>{{ pct(d.avg_correlation) }}</td>
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
const diversity = computed(() => analysis.value.diversity || {})
const details = computed(() => diversity.value.details || [])
const metrics = computed(() => diversity.value.metrics || {})

const metricRows = computed(() => ([
  { key: 'strategy_count', label: '總策略數', value: num(diversity.value.strategy_count) },
  { key: 'N', label: '總交易次數 (N)', value: num(metrics.value.N) },
  { key: 'avg_amount', label: '平均每次交易金額', value: num0(metrics.value.avg_amount) },
  { key: 'N_eff', label: '有效交易次數 (N_eff)', value: num0(metrics.value.N_eff) },
  { key: 'EER', label: '進場效率比 (EER)', value: pct(metrics.value.EER) },
  { key: 'RDR', label: '風險分散率 (RDR)', value: num2(metrics.value.RDR) },
  { key: 'DCI', label: '分散相關指數 (DCI)', value: pct(metrics.value.DCI) },
  { key: 'ISN', label: '獨立策略數 (ISN)', value: num2(metrics.value.ISN) },
  { key: 'DSN', label: '分散策略數 (DSN)', value: num2(metrics.value.DSN) }
]))

function num(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function num0(v) {
  const n = Math.round(Number(v || 0))
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function num2(v) {
  const n = Number(v || 0)
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function pct(v) {
  const n = Number(v || 0) * 100
  return `${n.toFixed(2)}%`
}
</script>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}
.card {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
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
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  text-align: right;
}
th:first-child, td:first-child {
  text-align: center;
}
h4 {
  margin: 8px 0;
}
</style>
