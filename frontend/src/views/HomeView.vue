<template>
  <main class="home">
    <section class="panel card">
      <h1>VisualPortfolio.Net</h1>
      <p class="muted">訪客 ID：{{ guest }}</p>
      <div class="row">
        <input v-model.trim="newProjectName" placeholder="輸入新專案名稱" @keyup.enter="onCreate" />
        <button @click="onCreate">建立專案</button>
      </div>
      <p v-if="store.error" class="error">{{ store.error }}</p>
    </section>

    <section class="panel card">
      <h2>專案列表</h2>
      <p v-if="store.loading">載入中...</p>
      <ul v-else class="list">
        <li v-for="p in store.projects" :key="p.project_id" class="project-item">
          <div>
            <strong>{{ p.project_name }}</strong>
            <p class="muted">{{ p.project_id }}</p>
          </div>
          <div class="row">
            <button @click="openProject(p.project_id)">開啟</button>
            <button @click="remove(p.project_id)">刪除</button>
          </div>
        </li>
      </ul>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ensureGuestId } from '../api'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
const router = useRouter()
const guest = ensureGuestId()
const newProjectName = ref('')

async function onCreate() {
  if (!newProjectName.value) return
  await store.create(newProjectName.value)
  newProjectName.value = ''
}

async function remove(projectId) {
  if (!confirm('確定要刪除此專案嗎？')) return
  await store.remove(projectId)
}

function openProject(projectId) {
  router.push(`/projects/${projectId}`)
}

onMounted(() => {
  store.loadProjects()
})
</script>

<style scoped>
.home {
  max-width: 980px;
  margin: 24px auto;
  padding: 0 16px;
  display: grid;
  gap: 16px;
}
.card {
  padding: 16px;
}
.row {
  display: flex;
  gap: 8px;
  align-items: center;
}
input {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  min-width: 280px;
}
button {
  padding: 8px 12px;
  border: 1px solid var(--accent);
  border-radius: 8px;
  background: var(--accent);
  color: white;
  cursor: pointer;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}
.project-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
}
.muted {
  color: var(--muted);
}
.error {
  color: #b00020;
}
</style>
