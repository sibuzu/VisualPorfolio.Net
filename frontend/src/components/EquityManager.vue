<template>
  <section>
    <h3>Equity Manager</h3>
    <table>
      <thead>
        <tr>
          <th>Active</th>
          <th>Color</th>
          <th>Name</th>
          <th>File</th>
          <th>Contract</th>
          <th>Weight</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(e, i) in store.equities" :key="e.filename">
          <td><input :disabled="readonly" type="checkbox" v-model="e.active" @change="refresh" /></td>
          <td><input :disabled="readonly" type="color" v-model="e.color" @change="refresh" /></td>
          <td><input :disabled="readonly" v-model="e.name" @change="refresh" /></td>
          <td>{{ e.filename }}</td>
          <td><input :disabled="readonly" type="number" min="0" step="0.1" v-model.number="e.contract" @change="refresh" /></td>
          <td><input :disabled="readonly" type="number" min="0" step="0.1" v-model.number="e.weight" @change="refresh" /></td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '../stores/portfolio'

const props = defineProps({ readonly: Boolean })
const route = useRoute()
const store = usePortfolioStore()

async function refresh() {
  await store.analyze(route.params.projectId)
}
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  font-size: 14px;
}
input[type='number'], input[type='text'], input:not([type]) {
  width: 100%;
}
</style>
