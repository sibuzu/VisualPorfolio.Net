<template>
  <section>
    <table>
      <tbody>
        <tr v-for="(v, k) in analysis.summary" :key="k">
          <th>{{ k }}</th>
          <td>{{ v }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { usePortfolioStore } from '../stores/portfolio'

const { analysis } = storeToRefs(usePortfolioStore())
</script>

<style scoped>
table {
  border-collapse: collapse;
}
th, td {
  border: 1px solid var(--line);
  padding: 8px;
  text-align: left;
}
</style>
