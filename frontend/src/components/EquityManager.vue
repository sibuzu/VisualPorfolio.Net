<template>
  <section>
    <table>
      <thead>
        <tr>
          <th>刪除</th>
          <th>啟動</th>
          <th>顏色</th>
          <th>名稱</th>
          <th>口數</th>
          <th>權重</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(e, i) in store.equities" :key="e.filename">
          <td>
            <button
              :disabled="readonly"
              class="delete-btn"
              title="刪除策略"
              aria-label="刪除策略"
              @click="removeEquity(e)"
            >
              <svg viewBox="0 0 448 512" aria-hidden="true">
                <path d="M32 464a48 48 0 0 0 48 48h288a48 48 0 0 0 48-48V128H32zm272-256a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zm-96 0a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zm-96 0a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zM432 32H312l-9.4-18.7A24 24 0 0 0 281.1 0H166.8a23.72 23.72 0 0 0-21.4 13.3L136 32H16A16 16 0 0 0 0 48v32a16 16 0 0 0 16 16h416a16 16 0 0 0 16-16V48a16 16 0 0 0-16-16z"/>
              </svg>
            </button>
          </td>
          <td><input :disabled="readonly" type="checkbox" v-model="e.active" @change="refresh" /></td>
          <td>
            <input
              :disabled="readonly"
              class="color-input"
              type="color"
              v-model="e.color"
              @change="refresh"
            />
          </td>
          <td class="name-cell" :title="displayName(e.name)">{{ displayName(e.name) }}</td>
          <td><input :disabled="readonly" type="text" inputmode="decimal" v-model="e.contract" @change="refresh" /></td>
          <td><input :disabled="readonly" type="text" inputmode="decimal" v-model="e.weight" @change="refresh" /></td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '../stores/portfolio'
import { useProjectStore } from '../stores/project'

defineProps({ readonly: Boolean })
const route = useRoute()
const store = usePortfolioStore()
const projectStore = useProjectStore()

function displayName(name) {
  return String(name || '').replace(/\.[^.]+$/, '')
}

async function refresh() {
  await store.persistAndAnalyze(route.params.projectId)
}

async function removeEquity(equity) {
  if (!confirm(`確定要刪除策略檔案「${equity.filename}」嗎？`)) return
  await projectStore.deleteFile(route.params.projectId, equity.filename)
  store.setFilesAsEquities(projectStore.files)
  await store.persistAndAnalyze(route.params.projectId)
}
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  font-size: 14px;
  word-break: normal;
}
input[type='text'] {
  width: 100%;
}
.color-input {
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
}
.delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}
.delete-btn svg {
  width: 16px;
  height: 16px;
  fill: #6b7280;
}
.delete-btn:hover svg {
  fill: #b00020;
}
th:nth-child(1), td:nth-child(1) { width: 40px; text-align: center; }
th:nth-child(2), td:nth-child(2) { width: 44px; text-align: center; }
th:nth-child(3), td:nth-child(3) { width: 44px; text-align: center; }
th:nth-child(4), td:nth-child(4) { min-width: 15ch; }
th:nth-child(5), td:nth-child(5) { width: 52px; }
th:nth-child(6), td:nth-child(6) { width: 52px; }
.name-cell {
  white-space: nowrap;
}
</style>
