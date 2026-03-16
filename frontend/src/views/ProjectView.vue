<template>
  <main class="wrap" v-if="projectStore.activeProject">
    <aside class="panel sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="title-row">
        <h2 class="project-title">{{ projectStore.activeProject.project_name }}</h2>
        <RouterLink class="back-link" to="/">回主頁</RouterLink>
      </div>
      <p class="muted id-line">
        <span>{{ projectStore.activeProject.project_id }}</span>
        <button
          type="button"
          class="copy-link-btn"
          title="複製專案連結"
          aria-label="複製專案連結"
          @click="copyProjectLink"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8,11h8v2H8V11z M20.1,12H22c0-2.76-2.24-5-5-5h-4v1.9h4C18.71,8.9,20.1,10.29,20.1,12z M3.9,12c0-1.71,1.39-3.1,3.1-3.1h4 V7H7c-2.76,0-5,2.24-5,5s2.24,5,5,5h4v-1.9H7C5.29,15.1,3.9,13.71,3.9,12z M19,12h-2v3h-3v2h3v3h2v-3h3v-2h-3V12z"/>
          </svg>
        </button>
        <span class="status-inline">{{ readonly ? '（可檢視）' : '（可編輯）' }}</span>
      </p>
      <p v-if="copyHint" class="hint">{{ copyHint }}</p>

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
const copyHint = ref('')
const sidebarWidth = ref(390)
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

async function copyProjectLink() {
  const url = `${window.location.origin}/projects/${route.params.projectId}`
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      const ta = document.createElement('textarea')
      ta.value = url
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    copyHint.value = '已複製專案連結'
    setTimeout(() => {
      copyHint.value = ''
    }, 1500)
  } catch (e) {
    viewError.value = e.message || '複製連結失敗'
  }
}

function onMouseMove(event) {
  if (!resizing.value) return
  const minW = 360
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
.copy-link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 0;
  background: transparent;
  padding: 0;
}
.copy-link-btn svg {
  width: 21px;
  height: 21px;
  fill: #6b7280;
  transition: fill 120ms ease-in-out;
}
.copy-link-btn:hover svg,
.copy-link-btn:focus-visible svg {
  fill: var(--accent);
}
.copy-link-btn:focus-visible {
  outline: 0;
}
.hint {
  margin: 0 0 4px;
  color: #0f766e;
  font-size: 12px;
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
