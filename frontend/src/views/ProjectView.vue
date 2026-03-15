<template>
  <main class="wrap" v-if="projectStore.activeProject">
    <aside class="panel sidebar" :style="{ width: sidebarWidth + 'px' }">
      <h2>{{ projectStore.activeProject.project_name }}</h2>
      <p class="muted">{{ projectStore.activeProject.project_id }}</p>
      <p class="muted">{{ readonly ? '唯讀檢視' : '可編輯' }}</p>

      <div class="row">
        <label>共享</label>
        <input :disabled="readonly" type="checkbox" :checked="projectStore.activeProject.shared" @change="toggleShared($event)" />
      </div>

      <div class="row">
        <input type="file" accept=".srp,.xrp" :disabled="readonly" @change="upload" />
      </div>

      <div class="files">
        <div v-for="f in projectStore.files" :key="f.filename" class="file-row">
          <span>{{ f.filename }}</span>
          <button v-if="!readonly" @click="removeFile(f.filename)">x</button>
        </div>
      </div>

      <div class="equity-manager-wrap">
        <EquityManager :readonly="readonly" />
      </div>

      <button v-if="!readonly" @click="savePfoFile">儲存 PFO</button>
      <button @click="refreshAnalysis">更新分析</button>
    </aside>

    <div
      class="splitter"
      role="separator"
      aria-label="調整左側寬度"
      @mousedown="startResize"
    ></div>

    <section class="panel content">
      <p v-if="viewError" class="error">{{ viewError }}</p>
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button>
      </div>

      <SummaryPanel v-if="activeTab === '獲利報表'" />
      <EquityCurvePanel v-if="activeTab === '獲利曲線'" />
      <MonthlyBarPanel v-if="activeTab === '逐年獲利'" />
      <PositionPanel v-if="activeTab === '口數分析'" />
      <WinLossPanel v-if="activeTab === '贏輸分析'" />
      <CommissionPanel v-if="activeTab === '分潤退傭'" />
      <DiversityPanel v-if="activeTab === '多樣性分析'" />
    </section>
  </main>

  <main v-else class="loading">
    <p v-if="viewError" class="error">{{ viewError }}</p>
    <p v-else>載入專案中...</p>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ensureGuestId } from '../api'
import { useProjectStore } from '../stores/project'
import { usePortfolioStore } from '../stores/portfolio'
import EquityManager from '../components/EquityManager.vue'
import SummaryPanel from '../components/SummaryPanel.vue'
import EquityCurvePanel from '../components/EquityCurvePanel.vue'
import MonthlyBarPanel from '../components/MonthlyBarPanel.vue'
import PositionPanel from '../components/PositionPanel.vue'
import WinLossPanel from '../components/WinLossPanel.vue'
import CommissionPanel from '../components/CommissionPanel.vue'
import DiversityPanel from '../components/DiversityPanel.vue'

const route = useRoute()
const projectStore = useProjectStore()
const portfolioStore = usePortfolioStore()
const guest = ensureGuestId()

const tabs = ['獲利報表', '獲利曲線', '逐年獲利', '口數分析', '贏輸分析', '分潤退傭', '多樣性分析']
const activeTab = ref('獲利報表')
const viewError = ref('')
const sidebarWidth = ref(300)
const resizing = ref(false)

const readonly = computed(() => {
  const p = projectStore.activeProject
  if (!p) return true
  return p.user_id !== guest && p.shared
})

async function loadAll() {
  viewError.value = ''
  try {
    await projectStore.loadProject(route.params.projectId)
    portfolioStore.setFilesAsEquities(projectStore.files)
    await refreshAnalysis()
  } catch (e) {
    viewError.value = e.message || '載入專案失敗'
  }
}

async function refreshAnalysis() {
  viewError.value = ''
  try {
    await portfolioStore.analyze(route.params.projectId)
  } catch (e) {
    viewError.value = e.message || '執行分析失敗'
  }
}

async function upload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  viewError.value = ''
  try {
    await projectStore.uploadFile(route.params.projectId, file)
    portfolioStore.setFilesAsEquities(projectStore.files)
    await refreshAnalysis()
  } catch (e) {
    viewError.value = e.message || '上傳失敗'
  }
  event.target.value = ''
}

async function removeFile(filename) {
  viewError.value = ''
  try {
    await projectStore.deleteFile(route.params.projectId, filename)
    portfolioStore.setFilesAsEquities(projectStore.files)
    await refreshAnalysis()
  } catch (e) {
    viewError.value = e.message || '刪除失敗'
  }
}

async function toggleShared(event) {
  viewError.value = ''
  try {
    await projectStore.patchProject(route.params.projectId, { shared: event.target.checked })
  } catch (e) {
    viewError.value = e.message || '更新失敗'
  }
}

async function savePfoFile() {
  viewError.value = ''
  try {
    await portfolioStore.saveProjectPfo(route.params.projectId)
    alert('已儲存為 project.pfo')
  } catch (e) {
    viewError.value = e.message || '儲存 PFO 失敗'
  }
}

function onMouseMove(event) {
  if (!resizing.value) return
  const minW = 240
  const maxW = 640
  sidebarWidth.value = Math.max(minW, Math.min(maxW, event.clientX - 14))
}

function stopResize() {
  resizing.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function startResize() {
  if (window.innerWidth <= 900) return
  resizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

watch(
  () => route.params.projectId,
  () => loadAll()
)

onMounted(() => {
  loadAll()
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
.wrap {
  display: flex;
  gap: 14px;
  padding: 14px;
  min-height: 100vh;
  align-items: stretch;
}
.sidebar {
  flex: 0 0 auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(100vh - 28px);
  overflow: auto;
}
.splitter {
  width: 8px;
  cursor: col-resize;
  border-radius: 8px;
  background: linear-gradient(to right, transparent 0, #d6dde5 45%, #d6dde5 55%, transparent 100%);
}
.content {
  flex: 1 1 auto;
  padding: 12px;
  min-width: 0;
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
button {
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  cursor: pointer;
}
button.active {
  border-color: var(--accent);
  color: var(--accent);
}
.file-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}
.files {
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  padding: 8px 0;
}
.equity-manager-wrap {
  border-top: 1px solid var(--line);
  padding-top: 8px;
}
.row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.loading {
  padding: 24px;
}
.muted {
  color: var(--muted);
}
.error {
  color: #b00020;
}
@media (max-width: 900px) {
  .wrap {
    display: block;
  }
  .sidebar {
    width: 100% !important;
    max-height: none;
    margin-bottom: 10px;
  }
  .splitter {
    display: none;
  }
}
</style>
