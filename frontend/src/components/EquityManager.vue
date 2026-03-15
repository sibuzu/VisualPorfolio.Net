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
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 3h6l1 2h4v2H4V5h4l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM7 9h2v9H7V9z"/>
              </svg>
            </button>
          </td>
          <td><input :disabled="readonly" type="checkbox" v-model="e.active" @change="refresh" /></td>
          <td><input :disabled="readonly" type="color" v-model="e.color" @change="refresh" /></td>
          <td>{{ e.name }}</td>
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
import { useProjectStore } from '../stores/project'

defineProps({ readonly: Boolean })
const route = useRoute()
const store = usePortfolioStore()
const projectStore = useProjectStore()

async function refresh() {
  await store.analyze(route.params.projectId)
}

async function removeEquity(equity) {
  if (!confirm(`確定要刪除策略檔案「${equity.filename}」嗎？`)) return
  await projectStore.deleteFile(route.params.projectId, equity.filename)
  store.setFilesAsEquities(projectStore.files)
  await refresh()
}
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  font-size: 14px;
  word-break: break-word;
}
input[type='number'] {
  width: 100%;
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
th:nth-child(3), td:nth-child(3) { width: 56px; text-align: center; }
th:nth-child(5), td:nth-child(5) { width: 52px; }
th:nth-child(6), td:nth-child(6) { width: 52px; }
</style>
