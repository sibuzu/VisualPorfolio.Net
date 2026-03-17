<template>
  <main class="home">
    <section class="panel card">
      <a class="help-link" href="/docs" target="vp-docs" title="Help" aria-label="Help">
        <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24" aria-hidden="true">
          <path d="M0 0h24v24H0z" fill="none"/>
          <path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z"/>
        </svg>
      </a>
      <h1>VisualPortfolio.Net</h1>
      <p class="muted">使用者：{{ userId }}</p>
      <div class="row">
        <input v-model.trim="newProjectName" placeholder="輸入新專案名稱" @keyup.enter="onCreate" />
        <button :disabled="isGuest" @click="onCreate">建立專案</button>
        <span class="row-spacer"></span>
        <button type="button" class="switch-user-btn" @click="switchUser">Logout</button>
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
            <p class="muted">{{ p.project_id }} <span v-if="formatDate(p.create_time)" class="create-date">({{ formatDate(p.create_time) }})</span></p>
          </div>
          <div class="row">
            <button @click="openProject(p.project_id)">開啟</button>
            <button @click="renameProject(p)">改名</button>
            <button @click="remove(p.project_id)">刪除</button>
          </div>
        </li>
      </ul>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authLogout, authMe } from '../api'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
const router = useRouter()
const route = useRoute()
const userId = ref('')
const newProjectName = ref('')
const isGuest = ref(false)

async function onCreate() {
  if (!newProjectName.value) return
  const projectId = await store.create(newProjectName.value)
  newProjectName.value = ''
  if (projectId) {
    router.push(`/projects/${projectId}`)
  }
}

async function remove(projectId) {
  if (!confirm('確定要刪除此專案嗎？')) return
  await store.remove(projectId)
}

async function renameProject(project) {
  const nextName = prompt('請輸入新專案名稱', project?.project_name || '')
  if (nextName == null) return
  const name = String(nextName).trim()
  if (!name) return
  await store.patchProject(project.project_id, { project_name: name })
}

function openProject(projectId) {
  router.push(`/projects/${projectId}`)
}

function formatDate(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function switchUser() {
  try {
    await authLogout()
  } catch {
    // Ignore logout failure and still jump to login.
  }
  router.push('/login')
}

onMounted(() => {
  authMe().then((m) => {
    userId.value = m.user_id || ''
    isGuest.value = userId.value === 'guest'
    if (isGuest.value) {
      router.replace({ path: '/login', query: { redirect: route.fullPath || '/' } })
      return
    }
    store.loadProjects()
  }).catch(() => {
    router.replace({ path: '/login', query: { redirect: route.fullPath || '/' } })
  })
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
  position: relative;
}
.help-link {
  position: absolute;
  top: 12px;
  right: 12px;
  color: #6b7280;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.help-link svg {
  width: 24px;
  height: 24px;
  fill: currentColor;
  transition: fill 120ms ease-in-out;
}
.help-link:hover {
  color: var(--accent);
}
.row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.row-spacer {
  flex: 1;
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
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.switch-user-btn {
  background: #fff;
  color: var(--accent);
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
.create-date {
  font-size: 12px;
}
.error {
  color: #b00020;
}
</style>
