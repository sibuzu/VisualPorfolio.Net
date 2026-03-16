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
        <span class="id-line-spacer"></span>
        <button
          type="button"
          class="copy-project-btn"
          @click="copyProjectWithPrompt"
        >
          <svg viewBox="0 0 512 512" aria-hidden="true">
            <path d="M464 0H144c-26.51 0-48 21.49-48 48v48H48c-26.51 0-48 21.49-48 48v320c0 26.51 21.49 48 48 48h320c26.51 0 48-21.49 48-48v-48h48c26.51 0 48-21.49 48-48V48c0-26.51-21.49-48-48-48zM362 464H54a6 6 0 0 1-6-6V150a6 6 0 0 1 6-6h42v224c0 26.51 21.49 48 48 48h224v42a6 6 0 0 1-6 6zm96-96H150a6 6 0 0 1-6-6V54a6 6 0 0 1 6-6h308a6 6 0 0 1 6 6v308a6 6 0 0 1-6 6z"/>
          </svg>
          <span>複製專案</span>
        </button>
      </p>
      <p v-if="copyHint" class="hint">{{ copyHint }}</p>

      <div class="equity-manager-wrap">
        <div class="manager-head">
          <h3 class="manager-title">策略組合管理</h3>
          <button type="button" class="copy-project-btn file-btn" :disabled="readonly" @click="openFilePicker">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12,2 C6.48,2 2,6.48 2,12 C2,17.52 6.48,22 12,22 C17.52,22 22,17.52 22,12 C22,6.48 17.52,2 12,2 Z M16,13 L13,13 L13,16 C13,16.55 12.55,17 12,17 C11.45,17 11,16.55 11,16 L11,13 L8,13 C7.45,13 7,12.55 7,12 C7,11.45 7.45,11 8,11 L11,11 L11,8 C11,7.45 11.45,7 12,7 C12.55,7 13,7.45 13,8 L13,11 L16,11 C16.55,11 17,11.45 17,12 C17,12.55 16.55,13 16,13 Z"/>
            </svg>
            <span>新增績效</span>
          </button>
          <input ref="fileInputRef" class="file-input-hidden" type="file" accept=".srp,.xrp" multiple :disabled="readonly" @change="upload" />
        </div>
        <EquityManager :readonly="readonly" />
        <p v-if="portfolioStore.updatingConfig" class="updating-hint">更新中...</p>
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
import { authMe, currentUserId } from '../api'
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
const currentUser = ref(currentUserId())

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
  return p.user_id !== currentUser.value
})

async function loadAll() {
  viewError.value = ''
  try {
    await projectStore.loadProject(route.params.projectId)
    portfolioStore.setFilesAsEquities(projectStore.files)
    await portfolioStore.restoreProjectConfig(route.params.projectId)
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
    await portfolioStore.persistAndAnalyze(route.params.projectId)
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

async function copyProjectWithPrompt() {
  const base = projectStore.activeProject?.project_name || 'Project'
  const defaultName = (() => {
    const m = String(base).match(/^(.*)-(\d+)$/)
    if (m) return `${m[1]}-${Number(m[2]) + 1}`
    return `${base}-1`
  })()
  const name = prompt('請輸入複製後的新專案名稱', defaultName)
  if (name == null) return
  const newName = name.trim()
  if (!newName) return

  viewError.value = ''
  try {
    const project = await projectStore.copy(route.params.projectId, newName)
    const targetPath = `/projects/${project.project_id}`
    const targetUrl = `${window.location.origin}${targetPath}`
    const win = window.open(targetUrl, '_blank', 'noopener,noreferrer')
    if (!win) {
      viewError.value = '瀏覽器已阻擋新分頁，請允許彈出視窗後再試'
    }
  } catch (e) {
    viewError.value = e.message || '複製專案失敗'
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
  authMe().then((m) => {
    currentUser.value = m.user_id || currentUserId()
  }).catch(() => {})
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
.id-line-spacer {
  flex: 1 1 auto;
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
.copy-project-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 13px;
}
.copy-project-btn svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
}
.copy-project-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.hint {
  margin: 0 0 4px;
  color: #0f766e;
  font-size: 12px;
}
.updating-hint {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
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
