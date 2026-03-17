<template>
  <main class="admin-wrap">
    <section class="panel admin-card">
      <div class="head">
        <h1>Admin</h1>
        <div class="row">
          <span class="muted">User: admin</span>
          <button @click="logout">Logout</button>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <h2>Projects</h2>
      <table class="table">
        <thead>
          <tr>
            <th>project_id</th>
            <th>project_name</th>
            <th>user_id</th>
            <th>access_time</th>
            <th>action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in projects" :key="p.project_id">
            <td>{{ p.project_id }}</td>
            <td>{{ p.project_name }}</td>
            <td>{{ p.user_id }}</td>
            <td>{{ p.access_time }}</td>
            <td class="action-cell">
              <button @click="openProject(p.project_id)">Open</button>
              <button @click="setDemo(p.project_id)">Set Demo</button>
              <button @click="removeProject(p.project_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>

      <h2>Users</h2>
      <table class="table">
        <thead>
          <tr>
            <th>user_id</th>
            <th>access_time</th>
            <th>projects</th>
            <th>action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.user_id">
            <td>{{ u.user_id }}</td>
            <td>{{ u.access_time || '-' }}</td>
            <td>
              <span v-if="!u.projects?.length">-</span>
              <span v-else>{{ u.projects.map((p) => p.project_id).join(', ') }}</span>
            </td>
            <td>
              <button :disabled="u.user_id === 'admin'" @click="removeUser(u.user_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  adminDeleteProject,
  adminDeleteUser,
  adminListProjects,
  adminSetDemoProject,
  adminListUsers,
  adminLogin,
  adminLogout,
  adminMe
} from '../api'

const router = useRouter()
const projects = ref([])
const users = ref([])
const error = ref('')

async function load() {
  const [p, u] = await Promise.all([adminListProjects(), adminListUsers()])
  projects.value = p
  users.value = u
}

async function ensureAdmin() {
  try {
    await adminMe()
    await load()
  } catch {
    const pwd = prompt('Admin password')
    if (!pwd) {
      router.replace('/')
      return
    }
    try {
      await adminLogin(pwd)
      await load()
    } catch (e) {
      error.value = e.message || 'Admin login failed'
      router.replace('/')
    }
  }
}

async function removeProject(projectId) {
  if (!confirm(`Delete project ${projectId}?`)) return
  error.value = ''
  try {
    await adminDeleteProject(projectId)
    await load()
  } catch (e) {
    error.value = e.message || 'Delete project failed'
  }
}

function openProject(projectId) {
  const url = `${window.location.origin}/projects/${projectId}`
  window.open(url, '_blank', 'noopener,noreferrer')
}

async function setDemo(projectId) {
  if (!confirm(`Set ${projectId} as demo project VP-ZDEMOZ?`)) return
  error.value = ''
  try {
    await adminSetDemoProject(projectId)
    await load()
  } catch (e) {
    error.value = e.message || 'Set demo failed'
  }
}

async function removeUser(userId) {
  if (!confirm(`Delete user ${userId} and all owned projects?`)) return
  error.value = ''
  try {
    await adminDeleteUser(userId)
    await load()
  } catch (e) {
    error.value = e.message || 'Delete user failed'
  }
}

async function logout() {
  await adminLogout()
  router.replace('/')
}

onMounted(() => {
  ensureAdmin()
})
</script>

<style scoped>
.admin-wrap {
  padding: 16px;
}
.admin-card {
  padding: 16px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 16px;
}
th, td {
  border: 1px solid var(--line);
  padding: 6px;
  text-align: left;
}
.action-cell {
  white-space: nowrap;
}
button {
  padding: 6px 10px;
  border: 1px solid var(--accent);
  border-radius: 8px;
  background: var(--accent);
  color: white;
  cursor: pointer;
  margin-right: 6px;
}
.action-cell button:last-child {
  margin-right: 0;
}
.muted {
  color: var(--muted);
}
.error {
  color: #b00020;
}
</style>
