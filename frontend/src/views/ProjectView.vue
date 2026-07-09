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
        <span class="status-inline" :title="readonly ? '可檢視' : '可編輯'" :aria-label="readonly ? '可檢視' : '可編輯'">
          <svg v-if="readonly" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M2.062,12.346C3.773,17,7.675,20,12,20s8.227-3,9.938-7.654a.993.993,0,0,0,0-.692C20.227,7,16.325,4,12,4S3.773,7,2.062,11.654A.993.993,0,0,0,2.062,12.346ZM12,6c3.373,0,6.451,2.343,7.929,6-1.478,3.657-4.556,6-7.929,6s-6.451-2.343-7.929-6C5.549,8.343,8.627,6,12,6Zm0,10a4,4,0,1,0-4-4A4,4,0,0,0,12,16Zm0-6a2,2,0,1,1-2,2A2,2,0,0,1,12,10Z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" aria-hidden="true">
            <path d="M18.111,2.293,9.384,11.021a.977.977,0,0,0-.241.39L8.052,14.684A1,1,0,0,0,9,16a.987.987,0,0,0,.316-.052l3.273-1.091a.977.977,0,0,0,.39-.241l8.728-8.727a1,1,0,0,0,0-1.414L19.525,2.293A1,1,0,0,0,18.111,2.293ZM11.732,13.035l-1.151.384.384-1.151L16.637,6.6l.767.767Zm7.854-7.853-.768.767-.767-.767.767-.768ZM3,5h8a1,1,0,0,1,0,2H4V20H17V13a1,1,0,0,1,2,0v8a1,1,0,0,1-1,1H3a1,1,0,0,1-1-1V6A1,1,0,0,1,3,5Z"/>
          </svg>
        </span>
        <span class="id-line-spacer"></span>
        <button
          type="button"
          class="copy-project-btn"
          :disabled="!canCloneProject"
          @click="copyProjectWithPrompt"
        >
          <svg viewBox="0 0 512 512" aria-hidden="true">
            <path d="M464 0H144c-26.51 0-48 21.49-48 48v48H48c-26.51 0-48 21.49-48 48v320c0 26.51 21.49 48 48 48h320c26.51 0 48-21.49 48-48v-48h48c26.51 0 48-21.49 48-48V48c0-26.51-21.49-48-48-48zM362 464H54a6 6 0 0 1-6-6V150a6 6 0 0 1 6-6h42v224c0 26.51 21.49 48 48 48h224v42a6 6 0 0 1-6 6zm96-96H150a6 6 0 0 1-6-6V54a6 6 0 0 1 6-6h308a6 6 0 0 1 6 6v308a6 6 0 0 1-6 6z"/>
          </svg>
          <span>複製專案</span>
        </button>
        <button
          type="button"
          class="copy-project-btn"
          @click="downloadProject"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7.293,13.707a1,1,0,1,1,1.414-1.414L11,14.586V3a1,1,0,0,1,2,0V14.586l2.293-2.293a1,1,0,0,1,1.414,1.414l-4,4a1,1,0,0,1-.325.216.986.986,0,0,1-.764,0,1,1,0,0,1-.325-.216ZM22,12a1,1,0,0,0-1,1v7H3V13a1,1,0,0,0-2,0v8a1,1,0,0,0,1,1H22a1,1,0,0,0,1-1V13A1,1,0,0,0,22,12Z"/>
          </svg>
          <span>下載專案</span>
        </button>
      </p>
      <p v-if="copyHint" class="hint">{{ copyHint }}</p>

      <div class="equity-manager-wrap">
        <div class="manager-head">
          <h3 class="manager-title">策略組合管理</h3>
          <div class="manager-actions">
            <button type="button" class="copy-project-btn file-btn" :disabled="readonly || buyHoldLoading" @click="openBuyHoldDialog">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12,2 C6.48,2 2,6.48 2,12 C2,17.52 6.48,22 12,22 C17.52,22 22,17.52 22,12 C22,6.48 17.52,2 12,2 Z M16,13 L13,13 L13,16 C13,16.55 12.55,17 12,17 C11.45,17 11,16.55 11,16 L11,13 L8,13 C7.45,13 7,12.55 7,12 C7,11.45 7.45,11 8,11 L11,11 L11,8 C11,7.45 11.45,7 12,7 C12.55,7 13,7.45 13,8 L13,11 L16,11 C16.55,11 17,11.45 17,12 C17,12.55 16.55,13 16,13 Z"/>
              </svg>
              <span>Buy&amp;Hold</span>
            </button>
            <button type="button" class="copy-project-btn file-btn" :disabled="readonly" @click="openFilePicker">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12,2 C6.48,2 2,6.48 2,12 C2,17.52 6.48,22 12,22 C17.52,22 22,17.52 22,12 C22,6.48 17.52,2 12,2 Z M16,13 L13,13 L13,16 C13,16.55 12.55,17 12,17 C11.45,17 11,16.55 11,16 L11,13 L8,13 C7.45,13 7,12.55 7,12 C7,11.45 7.45,11 8,11 L11,11 L11,8 C11,7.45 11.45,7 12,7 C12.55,7 13,7.45 13,8 L13,11 L16,11 C16.55,11 17,11.45 17,12 C17,12.55 16.55,13 16,13 Z"/>
              </svg>
              <span>新增績效</span>
            </button>
            <button type="button" class="copy-project-btn file-btn" :disabled="readonly" @click="openProjectUploadPicker">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M23,13v8a1,1,0,0,1-1,1H2a1,1,0,0,1-1-1V13a1,1,0,0,1,2,0v7H21V13a1,1,0,0,1,2,0ZM12,18a1,1,0,0,0,1-1V5.414l2.293,2.293a1,1,0,0,0,1.414-1.414l-4-4a1,1,0,0,0-1.414,0l-4,4A1,1,0,1,0,8.707,7.707L11,5.414V17A1,1,0,0,0,12,18Z"/>
              </svg>
              <span>上傳專案</span>
            </button>
          </div>
          <input ref="fileInputRef" class="file-input-hidden" type="file" accept=".srp,.xrp,.sea" multiple :disabled="readonly" @change="upload" />
          <input ref="projectUploadInputRef" class="file-input-hidden" type="file" accept=".gsea" :disabled="readonly" @change="uploadProjectPackageFile" />
        </div>
        <div v-if="buyHoldOpen" class="modal-backdrop">
          <form class="buy-hold-dialog" @submit.prevent="submitBuyHold">
            <div class="buy-hold-title-row">
              <h4>Buy&amp;Hold</h4>
              <button type="button" class="icon-btn" title="Buy&Hold 說明" aria-label="Buy&Hold 說明" @click="buyHoldHelpOpen = !buyHoldHelpOpen">
                <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24" aria-hidden="true">
                  <path d="M0 0h24v24H0z" fill="none"></path>
                  <path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z"></path>
                </svg>
              </button>
            </div>
            <div v-if="buyHoldHelpOpen" class="buy-hold-help">
              <p>股票代碼如 2330, 0050, 會配息再投資</p>
              <p>期貨代碼如 TX, TE, TF, GTF, 會 rollover，並用槓桿</p>
            </div>
            <label class="buy-hold-field">
              <span>日期</span>
              <input v-model="buyHoldForm.date" class="range-date-input" type="text" placeholder="YYYY-MM-DD" autocomplete="off" />
            </label>
            <label class="buy-hold-field">
              <span>金額(萬)</span>
              <input v-model="buyHoldForm.amount_wan" type="text" inputmode="decimal" autocomplete="off" />
            </label>
            <div class="buy-hold-field">
              <span>商品</span>
              <div class="product-toggle">
                <label>
                  <input :checked="buyHoldForm.product_type === '股票'" type="radio" value="股票" @change="setBuyHoldProduct('股票')" />
                  <span>股票</span>
                </label>
                <label>
                  <input :checked="buyHoldForm.product_type === '期貨'" type="radio" value="期貨" @change="setBuyHoldProduct('期貨')" />
                  <span>期貨</span>
                </label>
              </div>
            </div>
            <label class="buy-hold-field">
              <span>代碼</span>
              <input v-model="buyHoldForm.code" type="text" autocomplete="off" />
            </label>
            <label v-if="buyHoldForm.product_type === '期貨'" class="buy-hold-field">
              <span>槓桿</span>
              <input v-model="buyHoldForm.leverage" type="text" inputmode="decimal" autocomplete="off" />
            </label>
            <p v-if="buyHoldError" class="error buy-hold-error">{{ buyHoldError }}</p>
            <div class="buy-hold-actions">
              <button type="button" class="copy-project-btn" :disabled="buyHoldLoading" @click="closeBuyHoldDialog">取消</button>
              <button type="submit" class="copy-project-btn file-btn" :disabled="buyHoldLoading">{{ buyHoldLoading ? '建立中...' : '建立' }}</button>
            </div>
          </form>
        </div>
        <div class="manager-range-row">
          <label class="range-check-label">
            <input type="checkbox" :checked="dateRangeEnabled" @change="onDateRangeEnabledChange" />
            <span>指定範圍</span>
          </label>
          <input
            type="date"
            class="range-date-input"
            :value="dateRangeStart"
            :disabled="!dateRangeEnabled"
            inputmode="none"
            @keydown="blockDateTyping"
            @paste.prevent
            @drop.prevent
            @change="onDateRangeStartChange"
          />
          <span class="range-sep">~</span>
          <input
            type="date"
            class="range-date-input"
            :value="dateRangeEnd"
            :disabled="!dateRangeEnabled"
            inputmode="none"
            @keydown="blockDateTyping"
            @paste.prevent
            @drop.prevent
            @change="onDateRangeEndChange"
          />
        </div>
        <EquityManager :readonly="readonly" />
        <p v-if="portfolioStore.updatingConfig || portfolioStore.loading" class="updating-hint">更新計算中...</p>
      </div>
    </aside>

    <div
      class="splitter"
      role="separator"
      aria-label="調整左側寬度"
      @mousedown="startResize"
    ></div>

    <section class="panel content">
      <a class="help-link" href="/docs" target="vp-docs" title="Help" aria-label="Help">
        <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24" aria-hidden="true">
          <path d="M0 0h24v24H0z" fill="none"/>
          <path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z"/>
        </svg>
      </a>
      <p v-if="viewError" class="error">{{ viewError }}</p>
      <RouterLink v-if="showBackHome" class="error-back-link" to="/">&lt;back to home&gt;</RouterLink>
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button>
      </div>

      <SummaryPanel v-if="activeTab === '獲利報表'" :readonly="readonly" />
      <EquityCurvePanel v-if="activeTab === '獲利曲線'" />
      <MonthlyBarPanel v-if="activeTab === '逐年獲利'" />
      <WinLossPanel v-if="activeTab === '贏輸分析'" />
      <CommissionPanel v-if="activeTab === '分潤退傭'" :readonly="readonly" />
      <DiversityPanel v-if="activeTab === '多樣性分析'" />
      <DynamicCompoundingPanel v-if="activeTab === '動態複利'" :readonly="readonly" />
      <StrategyDescriptionPanel
        v-if="activeTab === '其他'"
        :readonly="readonly"
        :project-id="String(route.params.projectId || '')"
      />
    </section>
  </main>

  <main v-else class="loading">
    <p v-if="viewError" class="error">{{ viewError }}</p>
    <RouterLink v-if="showBackHome" class="error-back-link" to="/">&lt;back to home&gt;</RouterLink>
    <p v-else>載入專案中...</p>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { authMe, currentUserId, downloadProjectPackage, uploadProjectPackage } from '../api'
import { useProjectStore } from '../stores/project'
import { usePortfolioStore } from '../stores/portfolio'
import EquityManager from '../components/EquityManager.vue'
import SummaryPanel from '../components/SummaryPanel.vue'
import EquityCurvePanel from '../components/EquityCurvePanel.vue'
import MonthlyBarPanel from '../components/MonthlyBarPanel.vue'
import WinLossPanel from '../components/WinLossPanel.vue'
import CommissionPanel from '../components/CommissionPanel.vue'
import DiversityPanel from '../components/DiversityPanel.vue'
import DynamicCompoundingPanel from '../components/DynamicCompoundingPanel.vue'
import StrategyDescriptionPanel from '../components/StrategyDescriptionPanel.vue'

const route = useRoute()
const projectStore = useProjectStore()
const portfolioStore = usePortfolioStore()
const currentUser = ref(currentUserId())
const DEFAULT_TITLE = 'VisualPortfolio.Net'

const tabs = ['獲利報表', '獲利曲線', '逐年獲利', '贏輸分析', '分潤退傭', '多樣性分析', '動態複利', '其他']
const activeTab = ref('獲利報表')
const viewError = ref('')
const copyHint = ref('')
const sidebarWidth = ref(390)
const resizing = ref(false)
const fileInputRef = ref(null)
const projectUploadInputRef = ref(null)
const buyHoldOpen = ref(false)
const buyHoldHelpOpen = ref(false)
const buyHoldLoading = ref(false)
const buyHoldError = ref('')
const BUY_HOLD_DEFAULTS = {
  date: '2020-01-01',
  amount_wan: '100',
  product_type: '股票',
  stock_code: '0050',
  futures_code: 'TX',
  leverage: '5'
}
const BUY_HOLD_STORAGE_KEY = 'visualportfolio.buyHold.defaults'
const buyHoldForm = ref(defaultBuyHoldForm())

function defaultBuyHoldForm(productType = BUY_HOLD_DEFAULTS.product_type) {
  const stockCode = BUY_HOLD_DEFAULTS.stock_code
  const futuresCode = BUY_HOLD_DEFAULTS.futures_code
  return {
    date: BUY_HOLD_DEFAULTS.date,
    amount_wan: BUY_HOLD_DEFAULTS.amount_wan,
    product_type: productType,
    code: productType === '期貨' ? futuresCode : stockCode,
    stock_code: stockCode,
    futures_code: futuresCode,
    leverage: BUY_HOLD_DEFAULTS.leverage
  }
}

function normalizeBuyHoldForm(raw) {
  const source = raw && typeof raw === 'object' ? raw : {}
  const productType = source.product_type === '期貨' ? '期貨' : '股票'
  const defaults = defaultBuyHoldForm(productType)
  const sourceCode = String(source.code || '').trim()
  const stockCode = productType === '股票'
    ? String(sourceCode || source.stock_code || defaults.stock_code)
    : String(source.stock_code || defaults.stock_code)
  const futuresCode = productType === '期貨'
    ? String(sourceCode || source.futures_code || defaults.futures_code)
    : String(source.futures_code || defaults.futures_code)
  return {
    date: String(source.date || defaults.date),
    amount_wan: String(source.amount_wan || defaults.amount_wan),
    product_type: productType,
    code: productType === '期貨' ? futuresCode : stockCode,
    stock_code: stockCode,
    futures_code: futuresCode,
    leverage: String(source.leverage || defaults.leverage)
  }
}

function loadBuyHoldDefaults() {
  if (typeof localStorage === 'undefined') return defaultBuyHoldForm()
  try {
    return normalizeBuyHoldForm(JSON.parse(localStorage.getItem(BUY_HOLD_STORAGE_KEY) || '{}'))
  } catch {
    return defaultBuyHoldForm()
  }
}

function rememberBuyHoldDefaults() {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(BUY_HOLD_STORAGE_KEY, JSON.stringify(normalizeBuyHoldForm(buyHoldForm.value)))
}

function setBuyHoldProduct(productType) {
  const nextProduct = productType === '期貨' ? '期貨' : '股票'
  const currentProduct = buyHoldForm.value.product_type === '期貨' ? '期貨' : '股票'
  const currentCode = String(buyHoldForm.value.code || '').trim()
  const stockCode = currentProduct === '股票'
    ? (currentCode || buyHoldForm.value.stock_code || BUY_HOLD_DEFAULTS.stock_code)
    : (buyHoldForm.value.stock_code || BUY_HOLD_DEFAULTS.stock_code)
  const futuresCode = currentProduct === '期貨'
    ? (currentCode || buyHoldForm.value.futures_code || BUY_HOLD_DEFAULTS.futures_code)
    : (buyHoldForm.value.futures_code || BUY_HOLD_DEFAULTS.futures_code)
  buyHoldForm.value = {
    ...buyHoldForm.value,
    product_type: nextProduct,
    code: nextProduct === '期貨' ? futuresCode : stockCode,
    stock_code: stockCode,
    futures_code: futuresCode,
    leverage: buyHoldForm.value.leverage || BUY_HOLD_DEFAULTS.leverage
  }
}

const readonly = computed(() => {
  const p = projectStore.activeProject
  if (!p) return true
  return p.user_id !== currentUser.value
})
const canCloneProject = computed(() => currentUser.value !== 'guest')
const showBackHome = computed(() => /Project not found/i.test(String(viewError.value || '')))
const dateRangeEnabled = computed(() => !!portfolioStore.dateRangeConfig?.enabled)
const dateRangeStart = computed(() => String(portfolioStore.dateRangeConfig?.start || ''))
const dateRangeEnd = computed(() => String(portfolioStore.dateRangeConfig?.end || ''))

function updateDocumentTitle() {
  const name = String(projectStore.activeProject?.project_name || '').trim()
  document.title = name || DEFAULT_TITLE
}

async function loadAll() {
  viewError.value = ''
  try {
    await projectStore.loadProject(route.params.projectId)
    updateDocumentTitle()
    portfolioStore.setFilesAsEquities(projectStore.files)
    await portfolioStore.restoreGseaGroupConfig(route.params.projectId)
    await refreshAnalysis()
  } catch (e) {
    document.title = DEFAULT_TITLE
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

function parsePeriodRange() {
  const period = String(portfolioStore.analysis?.summary?.period || '')
  const m = period.match(/(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})/)
  if (!m) return { start: '', end: '' }
  return { start: m[1], end: m[2] }
}

function ensureDateRangeDefaults(cfg) {
  const next = {
    enabled: !!cfg.enabled,
    start: String(cfg.start || ''),
    end: String(cfg.end || '')
  }
  if (!next.enabled) return next
  const period = parsePeriodRange()
  if (!next.start) next.start = period.start
  if (!next.end) next.end = period.end
  return next
}

function validateDateRange(cfg) {
  if (!cfg.enabled) return ''
  if (!cfg.start || !cfg.end) {
    return '指定範圍啟用時，請輸入開始與結束日期'
  }
  if (cfg.start > cfg.end) {
    return '指定範圍的開始日期不可晚於結束日期'
  }
  return ''
}

async function applyDateRangeChange(nextConfig) {
  const next = ensureDateRangeDefaults(nextConfig)
  portfolioStore.setDateRangeConfig(next)
  const err = validateDateRange(next)
  if (err) {
    viewError.value = err
    return
  }

  viewError.value = ''
  try {
    if (readonly.value) {
      await portfolioStore.analyze(route.params.projectId)
    } else {
      await portfolioStore.persistAndAnalyze(route.params.projectId)
    }
  } catch (e) {
    viewError.value = e.message || '更新日期範圍失敗'
  }
}

async function onDateRangeEnabledChange(event) {
  const enabled = !!event?.target?.checked
  await applyDateRangeChange({
    ...portfolioStore.dateRangeConfig,
    enabled
  })
}

async function onDateRangeStartChange(event) {
  const start = String(event?.target?.value || '')
  await applyDateRangeChange({
    ...portfolioStore.dateRangeConfig,
    start
  })
}

async function onDateRangeEndChange(event) {
  const end = String(event?.target?.value || '')
  await applyDateRangeChange({
    ...portfolioStore.dateRangeConfig,
    end
  })
}

function blockDateTyping(event) {
  // Keep keyboard navigation (Tab) but force value changes via date picker only.
  if (event.key === 'Tab') return
  event.preventDefault()
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

function openProjectUploadPicker() {
  projectUploadInputRef.value?.click()
}

function openBuyHoldDialog() {
  if (readonly.value) return
  buyHoldError.value = ''
  buyHoldHelpOpen.value = false
  buyHoldForm.value = loadBuyHoldDefaults()
  buyHoldOpen.value = true
}

function closeBuyHoldDialog() {
  if (buyHoldLoading.value) return
  buyHoldOpen.value = false
  buyHoldError.value = ''
}

function validateBuyHoldForm() {
  const form = buyHoldForm.value
  if (!String(form.date || '').trim()) return '請輸入日期'
  if (!String(form.amount_wan || '').trim()) return '請輸入金額(萬)'
  if (!String(form.code || '').trim()) return '請輸入代碼'
  if (form.product_type === '期貨' && !String(form.leverage || '').trim()) return '請輸入槓桿'
  return ''
}

async function submitBuyHold() {
  if (readonly.value) return
  const err = validateBuyHoldForm()
  if (err) {
    buyHoldError.value = err
    return
  }

  buyHoldLoading.value = true
  buyHoldError.value = ''
  viewError.value = ''
  try {
    buyHoldForm.value = normalizeBuyHoldForm(buyHoldForm.value)
    rememberBuyHoldDefaults()
    await projectStore.createBuyHold(route.params.projectId, {
      date: String(buyHoldForm.value.date || '').trim(),
      amount_wan: String(buyHoldForm.value.amount_wan || '').trim(),
      product_type: buyHoldForm.value.product_type,
      code: String(buyHoldForm.value.code || '').trim(),
      leverage: buyHoldForm.value.product_type === '期貨' ? String(buyHoldForm.value.leverage || '5').trim() : null
    })
    portfolioStore.setFilesAsEquities(projectStore.files)
    await portfolioStore.persistAndAnalyze(route.params.projectId)
    buyHoldOpen.value = false
    copyHint.value = 'Buy&Hold 建立完成'
    setTimeout(() => {
      copyHint.value = ''
    }, 1500)
  } catch (e) {
    buyHoldError.value = e.message || 'Buy&Hold 建立失敗'
  } finally {
    buyHoldLoading.value = false
  }
}

async function uploadProjectPackageFile(event) {
  const file = Array.from(event?.target?.files || [])[0]
  if (!file) return
  if (projectStore.files.length > 0) {
    const ok = window.confirm('上傳專案將會覆蓋目前專案，是否進行')
    if (!ok) {
      event.target.value = ''
      return
    }
  }
  viewError.value = ''
  try {
    await uploadProjectPackage(route.params.projectId, String(projectStore.activeProject?.project_name || 'Project'), file)
    await loadAll()
    copyHint.value = '上傳專案完成'
    setTimeout(() => {
      copyHint.value = ''
    }, 1500)
  } catch (e) {
    viewError.value = e.message || '上傳專案失敗'
  }
  event.target.value = ''
}

async function downloadProject() {
  viewError.value = ''
  try {
    const { blob, filename } = await downloadProjectPackage(route.params.projectId)
    const href = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = href
    a.download = filename || `${route.params.projectId}.gsea`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(href)
    copyHint.value = '下載專案完成'
    setTimeout(() => {
      copyHint.value = ''
    }, 1500)
  } catch (e) {
    viewError.value = e.message || '下載專案失敗'
  }
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
  if (!canCloneProject.value) return
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
  document.title = DEFAULT_TITLE
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
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding-right: 34px;
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
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
  margin-bottom: 8px;
}
.manager-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.manager-title {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}
.manager-range-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.range-check-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}
.range-date-input {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 4px 6px;
  font-size: 13px;
}
.range-sep {
  color: var(--muted);
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}
.status-inline svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}
.file-input-hidden {
  display: none;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 80px 14px 14px;
  background: rgba(15, 23, 42, 0.35);
}
.buy-hold-dialog {
  width: min(360px, 100%);
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  padding: 12px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.22);
}
.buy-hold-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.buy-hold-title-row h4 {
  margin: 0;
  font-size: 18px;
}
.icon-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.icon-btn svg {
  width: 24px;
  height: 24px;
  fill: currentColor;
}
.buy-hold-help {
  margin: 0 0 10px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.45;
}
.buy-hold-help p {
  margin: 0;
}
.buy-hold-help p + p {
  margin-top: 4px;
}
.buy-hold-field {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
}
.buy-hold-field input[type='text'] {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 5px 7px;
  font-size: 14px;
}
.product-toggle {
  display: inline-flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.product-toggle label {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}
.buy-hold-error {
  margin: 8px 0;
  font-size: 13px;
}
.buy-hold-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
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
.error-back-link {
  color: var(--accent);
  text-decoration: underline;
  display: inline-block;
  margin: 4px 0 8px;
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
