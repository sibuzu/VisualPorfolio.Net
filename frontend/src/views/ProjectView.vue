<template>
  <main class="wrap" v-if="projectStore.activeProject">
    <aside class="panel sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="title-row">
        <h2 class="project-title">{{ projectStore.activeProject.project_name }}</h2>
        <RouterLink class="back-link" to="/">回主頁</RouterLink>
      </div>
      <p class="muted id-line">
        <span>{{ projectStore.activeProject.project_id }}</span>
        <span class="status-inline">{{ readonly ? '（可檢視）' : '（可編輯）' }}</span>
      </p>

      <div class="equity-manager-wrap">
        <div class="manager-head">
          <h3 class="manager-title">策略組合管理</h3>
          <button type="button" class="file-btn" :disabled="readonly" @click="openFilePicker">選擇檔案</button>
          <input ref="fileInputRef" class="file-input-hidden" type="file" accept=".srp,.xrp" multiple :disabled="readonly" @change="upload" />
        </div>
        <EquityManager :readonly="readonly" />
      </div>
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
import WinLossPanel from '../components/WinLossPanel.vue'
import CommissionPanel from '../components/CommissionPanel.vue'
import DiversityPanel from '../components/DiversityPanel.vue'

const route = useRoute()
const projectStore = useProjectStore()
const portfolioStore = usePortfolioStore()
const guest = ensureGuestId()

const tabs = ['獲利報表', '獲利曲線', '逐年獲利', '贏輸分析', '分潤退傭', '多樣性分析']
const activeTab = ref('獲利報表')
const viewError = ref('')
const sidebarWidth = ref(300)
const resizing = ref(false)
const fileInputRef = ref(null)

const readonly = computed(() => {
  const p = projectStore.activeProject
  if (!p) return true
  return p.user_id !== guest
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
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  viewError.value = ''
  try {
    await projectStore.uploadFiles(route.params.projectId, files)
    portfolioStore.setFilesAsEquities(projectStore.files)
    await refreshAnalysis()
  } catch (e) {
    viewError.value = e.message || '上傳失敗'
  }
  event.target.value = ''
}

function openFilePicker() {
  fileInputRef.value?.click()
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
  gap: 6px;
  max-height: calc(100vh - 28px);
  overflow: auto;
  overflow-x: hidden;
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
.project-title {
  margin: 2px 0;
}
.title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}
.back-link {
  color: var(--muted);
  text-decoration: underline;
  font-size: 14px;
  white-space: nowrap;
}
.file-btn {
  border-color: #9aa8b8;
}
button.active {
  border-color: var(--accent);
  color: var(--accent);
}
.equity-manager-wrap {
  border-top: 1px solid var(--line);
  padding-top: 8px;
}
.manager-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.manager-title {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}
.id-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 4px;
}
.status-inline {
  color: inherit;
  font-weight: 600;
}
.file-input-hidden {
  display: none;
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
