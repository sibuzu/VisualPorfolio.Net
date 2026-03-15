<template>
  <section>
    <div class="cards">
      <div class="card">
        <div class="label">交易次數</div>
        <div class="val">{{ commission.trade_count || 0 }}</div>
      </div>
      <div class="card">
        <div class="label">總手續費</div>
        <div class="val">{{ num(commission.total_commission) }}</div>
      </div>
      <div class="card">
        <div class="label">手續費後淨值</div>
        <div class="val">{{ num(commission.net_after_commission) }}</div>
      </div>
    </div>

    <h4>年度摘要</h4>
    <table class="table">
      <thead>
        <tr>
          <th>年度</th>
          <th>年度績效</th>
          <th>獎金比率</th>
          <th>績效獎金</th>
          <th>綜合收入</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="y in commission.years || []" :key="y.year">
          <td>{{ y.year }}</td>
          <td>{{ pct(y.year_perf) }}</td>
          <td>{{ pct(y.bonus_rate) }}</td>
          <td>{{ num(y.bonus) }}</td>
          <td>{{ num(y.total_income) }}</td>
        </tr>
      </tbody>
    </table>

    <h4>季度明細</h4>
    <table class="table">
      <thead>
        <tr>
          <th>年度</th>
          <th>季別</th>
          <th>季初資金</th>
          <th>季末資金</th>
          <th>獲利</th>
          <th>分潤</th>
          <th>客戶淨獲利</th>
          <th>手續費退傭</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in quarterRows" :key="r.key">
          <td>{{ r.year }}</td>
          <td>{{ r.quarter }}</td>
          <td>{{ num(r.start_capital) }}</td>
          <td>{{ num(r.end_capital) }}</td>
          <td>{{ num(r.profit) }}</td>
          <td>{{ num(r.share) }}</td>
          <td>{{ num(r.client_net_profit) }}</td>
          <td>{{ num(r.rebate) }}</td>
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
const commission = computed(() => analysis.value.commission || {})
const quarterRows = computed(() => {
  const rows = []
  for (const y of commission.value.years || []) {
    for (const e of y.entries || []) {
      rows.push({
        key: `${y.year}-${e.quarter}`,
        year: y.year,
        ...e
      })
    }
  }
  return rows
})

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
.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(150px, 1fr));
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
h4 {
  margin: 8px 0;
}
</style>
