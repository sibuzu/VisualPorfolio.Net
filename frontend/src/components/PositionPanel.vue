<template>
  <section>
    <h3>口數分析</h3>
    <table>
      <thead>
        <tr><th>策略</th><th>方向</th><th>進場</th><th>出場</th><th>損益</th></tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in rows" :key="i">
          <td>{{ r.strategy_index }}</td>
          <td>{{ r.side }}</td>
          <td>{{ r.entry }}</td>
          <td>{{ r.exit }}</td>
          <td>{{ r.pnl }}</td>
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
const rows = computed(() => analysis.value.position_analysis || [])
</script>

<style scoped>
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid var(--line); padding: 6px; }
</style>
