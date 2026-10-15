<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const modeOptions = [
  { value: 'backtest', label: '回測時已計算' },
  { value: 'fixed_quantity', label: '固定口數' },
  { value: 'risk_factor', label: '風險因子' },
  { value: 'target_leverage', label: '槓桿倍數目標' },
  { value: 'profit_step', label: '固定獲利一口' },
  { value: 'fixed_amount', label: '固定金額一口' },
  { value: 'fixed_risk', label: '固定風險' },
  { value: 'profit_risk', label: '獲利風險' },
  { value: 'target_margin', label: '保證金目標' },
  { value: 'kelly', label: '凱利投注' }
]

const fields = [
  { key: 'fixed_quantity', label: '固定口數', modes: ['fixed_quantity'], step: 'any' },
  { key: 'risk_factor', label: '風險因子', modes: ['risk_factor'], step: 'any' },
  { key: 'leverage', label: '槓桿倍數', modes: ['target_leverage'], step: 'any' },
  { key: 'initial_quantity', label: '初始口數', modes: ['profit_step'], step: 'any' },
  { key: 'minimum_quantity', label: '最小口數', modes: ['profit_step'], step: 'any' },
  { key: 'profit_base', label: '獲利基數', modes: ['profit_step'], step: 'any' },
  { key: 'amount_per_quantity', label: '交易一口金額', modes: ['fixed_amount'], step: 'any' },
  { key: 'fixed_risk_ratio', label: '固定風險比例', modes: ['fixed_risk'], step: 'any' },
  { key: 'initial_risk_ratio', label: '初始資金風險比例', modes: ['profit_risk'], step: 'any' },
  { key: 'profit_risk_ratio', label: '已獲利風險比例', modes: ['profit_risk'], step: 'any' },
  { key: 'loss_per_trade', label: '每次交易風險金額', modes: ['fixed_risk', 'profit_risk'], step: 'any' },
  { key: 'margin_ratio', label: '保證金目標比例', modes: ['target_margin'], step: 'any' },
  { key: 'margin_per_quantity', label: '每口保證金', modes: ['target_margin'], step: 'any' },
  { key: 'stake_percent', label: '下注比例 (%)', modes: ['kelly'], step: 'any' },
  { key: 'chip_size', label: 'ChipSize', modes: ['kelly'], step: 'any' }
]

const settings = ref({
  mode: 'fixed_quantity', initial_capital: 1000000, fixed_quantity: 1,
  risk_factor: 0.002, leverage: 0.2, leverage_funds: 'cumulative',
  initial_quantity: 50, minimum_quantity: 0, profit_base: 100000,
  amount_per_quantity: 400000, fixed_risk_ratio: 0.02,
  initial_risk_ratio: 0.02, profit_risk_ratio: 0.05, loss_per_trade: 10000,
  margin_ratio: 0.1, margin_per_quantity: 100000, stake_percent: 10,
  chip_size: 0, maximum_quantity: 0, integer_quantity: false,
  date_start: '', date_end: ''
})
const authUser = ref('')
const authReady = ref(false)
const authBusy = ref(false)
const authMode = ref('login')
const authUserId = ref('')
const authPassword = ref('')
const authPasswordConfirm = ref('')
const authError = ref('')
const performances = ref([])
const importantPerformances = ref([])
const currentPerformance = ref(null)
const managementBusy = ref(false)
const managementError = ref('')
const newPerformanceName = ref('')
const copyHint = ref('')
const dateRangeEnabled = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)
const report = ref(null)
const settingsDirty = ref(false)
const busy = ref(false)
const error = ref('')
const activeTab = ref('overview')
const activeSection = ref('compound')
const activePeriod = ref('monthly')
const chartElement = ref(null)
let chart = null
let resizeObserver = null
let reportRequestId = 0
let recalculateTimer = null
let calculateQueued = false

const resultModeLabel = computed(() => modeOptions.find(row => row.value === report.value?.settings?.mode)?.label || '')
const visibleFields = computed(() => fields.filter(row => row.modes.includes(settings.value.mode)))
const currentSection = computed(() => report.value?.[activeSection.value] || null)
const currentSummary = computed(() => currentSection.value?.summary || {})
const currentPeriods = computed(() => currentSection.value?.periods?.[activePeriod.value] || [])
const currentDetails = computed(() => currentSection.value?.detail || [])
const source = computed(() => report.value?.source || null)
const periodLabels = { annual: '年度', monthly: '月份', weekly: '週別', daily: '日期' }
const tabs = [
  { value: 'overview', label: '績效總覽' },
  { value: 'periods', label: '週期報表' },
  { value: 'details', label: '交易明細' },
  { value: 'parameters', label: '策略參數' }
]

function formatNumber(value, digits = 2) {
  return new Intl.NumberFormat('zh-TW', { maximumFractionDigits: digits, minimumFractionDigits: 0 }).format(Number(value || 0))
}

function formatPercent(value) {
  return `${formatNumber(value, 2)}%`
}

function chooseFile(file) {
  selectedFile.value = null
  if (!file) return false
  const ext = file.name.toLowerCase().split('.').pop()
  if (!['srp', 'sea'].includes(ext)) {
    managementError.value = '請選擇 .srp 或 .sea 檔案。'
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    managementError.value = '檔案不可超過 20 MiB。'
    return false
  }
  selectedFile.value = file
  managementError.value = ''
  report.value = null
  settingsDirty.value = false
  return true
}

async function handleFileInput(event) {
  const valid = chooseFile(event.target.files?.[0])
  event.target.value = ''
  if (valid) await createPerformance()
}

function messageFromDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(row => `${row.loc?.at(-1) || '欄位'}：${row.msg}`).join('；')
  return '計算失敗，請檢查檔案與設定。'
}

function routePerformanceId() {
  return window.location.pathname.match(/^\/performances\/(SR-[A-Z]{6})\/?$/)?.[1] || ''
}

function settingsPayload() {
  const payload = { ...settings.value }
  if (!dateRangeEnabled.value || !payload.date_start) delete payload.date_start
  if (!dateRangeEnabled.value || !payload.date_end) delete payload.date_end
  return payload
}

async function loadPerformances() {
  const [ownedResponse, importantResponse] = await Promise.all([
    fetch('/api/performances', { credentials: 'same-origin' }),
    fetch('/api/performances/important', { credentials: 'same-origin' })
  ])
  const [owned, important] = await Promise.all([
    ownedResponse.json().catch(() => ({})), importantResponse.json().catch(() => ({}))
  ])
  if (!ownedResponse.ok) throw new Error(messageFromDetail(owned.detail))
  if (!importantResponse.ok) throw new Error(messageFromDetail(important.detail))
  performances.value = owned.performances || []
  importantPerformances.value = important.performances || []
}

async function openPerformance(itemId, pushRoute = true) {
  managementError.value = ''
  try {
    const response = await fetch(`/api/performances/${itemId}`, { credentials: 'same-origin' })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    clearReport()
    currentPerformance.value = data.performance
    settings.value = {
      ...settings.value, ...data.performance.settings,
      date_start: data.performance.settings.date_start || '',
      date_end: data.performance.settings.date_end || ''
    }
    dateRangeEnabled.value = Boolean(settings.value.date_start || settings.value.date_end)
    if (pushRoute) window.history.pushState({}, '', `/performances/${itemId}`)
    await calculate()
  } catch (cause) {
    managementError.value = cause.message || '無法開啟績效。'
  }
}

function goHome(pushRoute = true) {
  currentPerformance.value = null
  clearReport()
  if (pushRoute) window.history.pushState({}, '', '/')
  loadPerformances().catch(cause => { managementError.value = cause.message || '無法載入績效。' })
}

async function handleRouteChange() {
  const itemId = routePerformanceId()
  if (itemId) await openPerformance(itemId, false)
  else goHome(false)
}

async function createPerformance() {
  if (!selectedFile.value || managementBusy.value) return
  managementBusy.value = true
  managementError.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('name', newPerformanceName.value.trim())
    const response = await fetch('/api/performances', { method: 'POST', body: form, credentials: 'same-origin' })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    newPerformanceName.value = ''
    await loadPerformances()
    await openPerformance(data.performance.performance_id)
  } catch (cause) {
    managementError.value = cause.message || '建立績效失敗。'
  } finally {
    selectedFile.value = null
    managementBusy.value = false
  }
}

async function patchPerformance(itemId, changes) {
  const response = await fetch(`/api/performances/${itemId}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin', body: JSON.stringify(changes)
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(messageFromDetail(data.detail))
  performances.value = performances.value.map(item => item.performance_id === itemId ? data.performance : item)
  if (currentPerformance.value?.performance_id === itemId) currentPerformance.value = data.performance
  await loadPerformances()
}

async function copyPerformance(item) {
  const name = window.prompt('請輸入複製後的績效名稱', `${item.name} 副本`)
  if (name === null) return
  try {
    const response = await fetch(`/api/performances/${item.performance_id}/copy`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin', body: JSON.stringify({ name: name.trim() })
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    await loadPerformances()
    await openPerformance(data.performance.performance_id)
  } catch (cause) {
    if (currentPerformance.value) error.value = cause.message || '複製績效失敗。'
    else managementError.value = cause.message || '複製績效失敗。'
  }
}

function downloadPerformance(item) {
  window.location.href = `/api/performances/${item.performance_id}/download`
}

async function copyPerformanceLink(item) {
  try {
    const url = `${window.location.origin}/performances/${item.performance_id}`
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = url
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      textarea.remove()
    }
    copyHint.value = '已複製績效連結'
    setTimeout(() => { copyHint.value = '' }, 1500)
  } catch (cause) {
    error.value = cause.message || '複製連結失敗。'
  }
}

async function renamePerformance(item) {
  const entered = window.prompt('請輸入新績效名稱', item.name)
  if (entered === null) return
  try {
    await patchPerformance(item.performance_id, { name: entered.trim() })
  } catch (cause) {
    if (currentPerformance.value) error.value = cause.message || '改名失敗。'
    else managementError.value = cause.message || '改名失敗。'
  }
}

async function toggleImportant(item) {
  try {
    await patchPerformance(item.performance_id, { important: !item.important })
  } catch (cause) {
    managementError.value = cause.message || '更新失敗。'
  }
}

async function removePerformance(item) {
  if (!window.confirm(`確定刪除績效「${item.name}」嗎？`)) return
  try {
    const response = await fetch(`/api/performances/${item.performance_id}`, {
      method: 'DELETE', credentials: 'same-origin'
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    if (currentPerformance.value?.performance_id === item.performance_id) goHome()
    else await loadPerformances()
  } catch (cause) {
    managementError.value = cause.message || '刪除失敗。'
  }
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('sv-SE')
}

async function refreshAuth() {
  try {
    const response = await fetch('/api/auth/me', { credentials: 'same-origin' })
    if (response.ok) {
      const data = await response.json()
      authUser.value = data.user_id || ''
      try {
        await loadPerformances()
        if (routePerformanceId()) await openPerformance(routePerformanceId(), false)
      } catch (cause) {
        managementError.value = cause.message || '無法載入績效。'
      }
    } else if (response.status !== 401) {
      const data = await response.json().catch(() => ({}))
      authError.value = messageFromDetail(data.detail)
    }
  } catch {
    authError.value = '無法連線到登入服務。'
  } finally {
    authReady.value = true
  }
}

async function submitAuth() {
  if (!authUserId.value || !authPassword.value || authBusy.value) return
  if (authMode.value === 'signup' && authPassword.value !== authPasswordConfirm.value) {
    authError.value = 'Password confirm mismatch'
    return
  }
  authBusy.value = true
  authError.value = ''
  try {
    const payload = { user_id: authUserId.value.trim(), password: authPassword.value }
    if (authMode.value === 'signup') {
      const signupResponse = await fetch('/api/auth/signup', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin', body: JSON.stringify(payload)
      })
      const signupData = await signupResponse.json().catch(() => ({}))
      if (!signupResponse.ok) throw new Error(messageFromDetail(signupData.detail))
    }
    const response = await fetch('/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin', body: JSON.stringify(payload)
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    authUser.value = data.user_id
    authMode.value = 'login'
    authPassword.value = ''
    authPasswordConfirm.value = ''
    try {
      await loadPerformances()
      if (routePerformanceId()) await openPerformance(routePerformanceId(), false)
    } catch (cause) {
      managementError.value = cause.message || '無法載入績效。'
    }
  } catch (cause) {
    authError.value = cause.message || '登入失敗。'
  } finally {
    authBusy.value = false
  }
}

function toggleAuthMode() {
  authMode.value = authMode.value === 'login' ? 'signup' : 'login'
  authError.value = ''
  authPasswordConfirm.value = ''
}

function clearReport() {
  reportRequestId += 1
  clearTimeout(recalculateTimer)
  recalculateTimer = null
  calculateQueued = false
  busy.value = false
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.dispose()
  chart = null
  selectedFile.value = null
  report.value = null
  settingsDirty.value = false
  if (fileInput.value) fileInput.value.value = ''
}

async function logout() {
  try {
    const response = await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' })
    if (!response.ok) throw new Error('登出失敗。')
    authUser.value = ''
    authMode.value = 'login'
    authPassword.value = ''
    currentPerformance.value = null
    performances.value = []
    importantPerformances.value = []
    managementError.value = ''
    window.history.replaceState({}, '', '/')
    clearReport()
  } catch (cause) {
    error.value = cause.message || '登出失敗。'
  }
}

async function calculate() {
  if (!currentPerformance.value) return
  if (busy.value) {
    calculateQueued = true
    return
  }
  const itemId = currentPerformance.value.performance_id
  const requestId = ++reportRequestId
  const payload = settingsPayload()
  const payloadKey = JSON.stringify(payload)
  busy.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/performances/${itemId}/report`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: payloadKey, credentials: 'same-origin'
    })
    const data = await response.json().catch(() => ({}))
    if (requestId !== reportRequestId || currentPerformance.value?.performance_id !== itemId) return
    if (response.status === 401) {
      authUser.value = ''
      authMode.value = 'login'
      currentPerformance.value = null
      performances.value = []
      importantPerformances.value = []
      clearReport()
      authError.value = '登入已失效，請重新登入。'
      return
    }
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    report.value = data
    currentPerformance.value = { ...currentPerformance.value, settings: payload }
    settingsDirty.value = JSON.stringify(settingsPayload()) !== payloadKey
    activeTab.value = 'overview'
    await nextTick()
    renderChart()
  } catch (cause) {
    if (requestId === reportRequestId) error.value = cause.message || '無法連線到報表服務。'
  } finally {
    if (requestId === reportRequestId) {
      busy.value = false
      if (calculateQueued || JSON.stringify(settingsPayload()) !== payloadKey) {
        calculateQueued = false
        clearTimeout(recalculateTimer)
        recalculateTimer = setTimeout(calculate, 350)
      }
    }
  }
}

function renderChart() {
  if (activeTab.value !== 'overview' || !chartElement.value || !currentSection.value) return
  if (chart && chart.getDom() !== chartElement.value) {
    resizeObserver?.disconnect()
    chart.dispose()
    chart = null
  }
  if (!chart) {
    chart = echarts.init(chartElement.value)
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartElement.value)
  }
  const curve = currentSection.value.curve || []
  const showZoom = curve.length > 30
  const hasDrawdown = curve.some(row => row.drawdown > 0)
  chart.setOption({
    animationDuration: 350,
    grid: { left: 66, right: hasDrawdown ? 70 : 24, top: 28, bottom: showZoom ? 60 : 38 },
    tooltip: { trigger: 'axis', valueFormatter: value => formatNumber(value, 2) },
    legend: { bottom: 4, data: ['淨值', '回撤'] },
    xAxis: { type: 'category', data: curve.map(row => row.timestamp.slice(0, 10)), boundaryGap: false, axisLabel: { hideOverlap: true } },
    yAxis: [
      { type: 'value', scale: true, axisLabel: { formatter: value => formatNumber(value, 0) }, splitLine: { lineStyle: { color: '#e6ecec' } } },
      { type: 'value', name: '回撤', min: 0, show: hasDrawdown, axisLabel: { formatter: value => formatNumber(value, 0) }, splitLine: { show: false } }
    ],
    dataZoom: [{ type: 'inside' }, ...(showZoom ? [{ type: 'slider', height: 14, bottom: 32, borderColor: 'transparent' }] : [])],
    series: [
      { name: '淨值', type: 'line', data: curve.map(row => row.equity), showSymbol: false, smooth: false, lineStyle: { width: 2.5, color: '#0b7183' }, areaStyle: { color: 'rgba(11,113,131,.10)' } },
      { name: '回撤', type: 'line', yAxisIndex: 1, data: curve.map(row => row.drawdown), showSymbol: false, lineStyle: { width: 1.5, color: '#d77953' } }
    ]
  }, true)
  chart.resize()
}

watch([activeTab, activeSection, report], () => nextTick(renderChart))
function scheduleRecalculation() {
  if (!report.value || !currentPerformance.value) return
  settingsDirty.value = true
  clearTimeout(recalculateTimer)
  recalculateTimer = setTimeout(calculate, 350)
}
watch(settings, scheduleRecalculation, { deep: true })
watch(dateRangeEnabled, scheduleRecalculation)

function csvCell(value) {
  const raw = String(value ?? '')
  const text = typeof value === 'string' && /^[=+@-]/.test(raw) ? `'${raw}` : raw
  return `"${text.replaceAll('"', '""')}"`
}

function printReport() {
  window.print()
}

function downloadCsv(kind) {
  if (!currentSection.value) return
  const rows = kind === 'details' ? currentDetails.value : currentPeriods.value
  if (!rows.length) return
  const columns = kind === 'details'
    ? [['timestamp', '時間'], ['symbol', '標的'], ['side', '買賣'], ['quantity', '口數'], ['price', '價格'], ['position', '部位'], ['profit', '損益'], ['equity', '累積淨值'], ['action', '訊號']]
    : [['period', '期間'], ['profit', '損益'], ['cumulative', '累積'], ['return_pct', '報酬率 (%)']]
  const lines = [
    `${csvCell('來源檔案')},${csvCell(source.value?.filename)}`,
    `${csvCell('策略')},${csvCell(source.value?.strategy)}`,
    `${csvCell('資金管理模式')},${csvCell(activeSection.value === 'simple' ? '單純績效' : resultModeLabel.value)}`,
    `${csvCell('區間')},${csvCell(`${report.value?.settings?.date_start || '全部'} ~ ${report.value?.settings?.date_end || '全部'}`)}`,
    '', columns.map(item => csvCell(item[1])).join(','),
    ...rows.map(row => columns.map(([key]) => csvCell(row[key])).join(','))
  ]
  const blob = new Blob(['\ufeff', lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${(source.value?.strategy || 'strategy').replaceAll(/[\\/:*?"<>|]/g, '_')}-${activeSection.value}-${kind === 'details' ? 'details' : activePeriod.value}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handleRouteChange)
  clearReport()
})
onMounted(() => {
  window.addEventListener('popstate', handleRouteChange)
  refreshAuth()
})
</script>

<template>
  <div v-if="!authReady" class="auth-wrap"><section class="panel auth-card"><p>檢查登入狀態...</p></section></div>
  <div v-else-if="!authUser" class="auth-wrap">
    <section class="panel auth-card">
      <h1>{{ authMode === 'login' ? 'Login' : 'Sign up' }}</h1>
      <form class="auth-form" @submit.prevent="submitAuth">
        <input v-model.trim="authUserId" type="text" placeholder="user_id" autocomplete="username" required />
        <input v-model="authPassword" type="password" placeholder="password" :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'" required />
        <input v-if="authMode === 'signup'" v-model="authPasswordConfirm" type="password" placeholder="confirm password" autocomplete="new-password" required />
        <button type="submit" :disabled="authBusy">{{ authBusy ? '處理中...' : authMode === 'login' ? 'Login' : 'Create Account' }}</button>
      </form>
      <p v-if="authError" class="auth-error" role="alert">{{ authError }}</p>
      <button type="button" class="auth-switch" @click="toggleAuthMode">{{ authMode === 'login' ? 'Sign up' : 'Back to login' }}</button>
    </section>
  </div>
  <main v-else-if="!currentPerformance" class="performance-home">
    <section class="panel home-card">
      <h1>StrategyReport.Net</h1>
      <p class="muted">使用者：{{ authUser }}</p>
      <div class="home-actions">
        <input v-model.trim="newPerformanceName" type="text" maxlength="160" placeholder="輸入新績效名稱，留空使用 StrategyName" aria-label="新績效名稱" />
        <input ref="fileInput" type="file" accept=".srp,.sea" class="sr-only" tabindex="-1" @change="handleFileInput" />
        <button type="button" class="home-file-button" :disabled="managementBusy" @click="fileInput?.click()">{{ managementBusy ? '上傳中…' : '上傳績效' }}</button>
        <span class="home-spacer"></span>
        <button type="button" class="home-outline-button" @click="logout">Logout</button>
      </div>
      <p class="field-help">績效名稱建立後仍可修改。</p>
      <p v-if="managementError" class="error-message" role="alert">{{ managementError }}</p>
    </section>

    <section class="panel home-card">
      <h2>重要績效</h2>
      <ul class="performance-list">
        <li v-for="item in importantPerformances" :key="`important-${item.performance_id}`" class="performance-item">
          <div><strong>{{ item.name }}</strong><p class="muted">{{ item.performance_id }} · {{ item.owner_id }} <span v-if="formatDate(item.created_at)">({{ formatDate(item.created_at) }})</span></p></div>
          <button type="button" @click="openPerformance(item.performance_id)">開啟</button>
        </li>
      </ul>
      <p v-if="!importantPerformances.length" class="muted">目前沒有重要績效</p>
    </section>

    <section class="panel home-card">
      <h2>個人績效</h2>
      <ul class="performance-list">
        <li v-for="item in performances" :key="item.performance_id" class="performance-item">
          <div><strong>{{ item.name }}</strong><p class="muted">{{ item.performance_id }} <span v-if="formatDate(item.created_at)">({{ formatDate(item.created_at) }})</span> · {{ item.filename }}</p></div>
          <div class="performance-actions">
            <button type="button" @click="openPerformance(item.performance_id)">開啟</button>
            <button type="button" class="home-outline-button" @click="copyPerformance(item)">複製</button>
            <button type="button" class="home-outline-button" @click="renamePerformance(item)">改名</button>
            <button type="button" class="home-outline-button" @click="toggleImportant(item)">{{ item.important ? '取消重要' : '設為重要' }}</button>
            <button type="button" class="home-outline-button" @click="removePerformance(item)">刪除</button>
          </div>
        </li>
      </ul>
      <p v-if="!performances.length" class="muted">目前沒有績效，請先上傳 .srp 或 .sea 檔案。</p>
    </section>
  </main>
  <div v-else class="app-shell">
    <main>
      <div class="workspace">
        <aside class="panel sidebar">
          <div class="title-row">
            <h1 class="project-title">{{ currentPerformance.name }}</h1>
            <a class="back-link" href="/" @click.prevent="goHome()">回主頁</a>
          </div>
          <div class="id-line">
            <span>{{ currentPerformance.performance_id }}</span>
            <button type="button" class="copy-link-btn" title="複製績效連結" aria-label="複製績效連結" @click="copyPerformanceLink(currentPerformance)">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8,11h8v2H8V11z M20.1,12H22c0-2.76-2.24-5-5-5h-4v1.9h4C18.71,8.9,20.1,10.29,20.1,12z M3.9,12c0-1.71,1.39-3.1,3.1-3.1h4 V7H7c-2.76,0-5,2.24-5,5s2.24,5,5,5h4v-1.9H7C5.29,15.1,3.9,13.71,3.9,12z M19,12h-2v3h-3v2h3v3h2v-3h3v-2h-3V12z"/></svg>
            </button>
            <span class="status-inline" :title="currentPerformance.is_owner ? '可編輯' : '可檢視'" :aria-label="currentPerformance.is_owner ? '可編輯' : '可檢視'">
              <svg v-if="currentPerformance.is_owner" viewBox="0 0 24 24" aria-hidden="true"><path d="M18.111,2.293,9.384,11.021a.977.977,0,0,0-.241.39L8.052,14.684A1,1,0,0,0,9,16a.987.987,0,0,0,.316-.052l3.273-1.091a.977.977,0,0,0,.39-.241l8.728-8.727a1,1,0,0,0,0-1.414L19.525,2.293A1,1,0,0,0,18.111,2.293ZM11.732,13.035l-1.151.384.384-1.151L16.637,6.6l.767.767Zm7.854-7.853-.768.767-.767-.767.767-.768ZM3,5h8a1,1,0,0,1,0,2H4V20H17V13a1,1,0,0,1,2,0v8a1,1,0,0,1-1,1H3a1,1,0,0,1-1-1V6A1,1,0,0,1,3,5Z"/></svg>
              <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="M2.062,12.346C3.773,17,7.675,20,12,20s8.227-3,9.938-7.654a.993.993,0,0,0,0-.692C20.227,7,16.325,4,12,4S3.773,7,2.062,11.654A.993.993,0,0,0,2.062,12.346ZM12,6c3.373,0,6.451,2.343,7.929,6-1.478,3.657-4.556,6-7.929,6s-6.451-2.343-7.929-6C5.549,8.343,8.627,6,12,6Zm0,10a4,4,0,1,0-4-4A4,4,0,0,0,12,16Zm0-6a2,2,0,1,1-2,2A2,2,0,0,1,12,10Z"/></svg>
            </span>
            <span class="id-line-spacer"></span>
            <button type="button" class="copy-project-btn" @click="copyPerformance(currentPerformance)">
              <svg viewBox="0 0 512 512" aria-hidden="true"><path d="M464 0H144c-26.51 0-48 21.49-48 48v48H48c-26.51 0-48 21.49-48 48v320c0 26.51 21.49 48 48 48h320c26.51 0 48-21.49 48-48v-48h48c26.51 0 48-21.49 48-48V48c0-26.51-21.49-48-48-48zM362 464H54a6 6 0 0 1-6-6V150a6 6 0 0 1 6-6h42v224c0 26.51 21.49 48 48 48h224v42a6 6 0 0 1-6 6zm96-96H150a6 6 0 0 1-6-6V54a6 6 0 0 1 6-6h308a6 6 0 0 1 6 6v308a6 6 0 0 1-6 6z"/></svg>
              <span>複製績效</span>
            </button>
            <button type="button" class="copy-project-btn" @click="downloadPerformance(currentPerformance)">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.293,13.707a1,1,0,1,1,1.414-1.414L11,14.586V3a1,1,0,0,1,2,0V14.586l2.293-2.293a1,1,0,0,1,1.414,1.414l-4,4a1,1,0,0,1-.325.216.986.986,0,0,1-.764,0,1,1,0,0,1-.325-.216ZM22,12a1,1,0,0,0-1,1v7H3V13a1,1,0,0,0-2,0v8a1,1,0,0,0,1,1H22a1,1,0,0,0,1-1V13A1,1,0,0,0,22,12Z"/></svg>
              <span>下載績效</span>
            </button>
          </div>
          <p v-if="copyHint" class="hint" role="status">{{ copyHint }}</p>

          <section class="settings-panel">
            <div class="panel-heading"><h2>績效資金管理</h2></div>
            <div class="manager-range-row">
              <label class="range-check-label"><input v-model="dateRangeEnabled" type="checkbox" /><span>指定</span></label>
              <input v-model="settings.date_start" type="date" class="range-date-input" aria-label="開始日期" :disabled="!dateRangeEnabled" />
              <span class="range-sep">~</span>
              <input v-model="settings.date_end" type="date" class="range-date-input" aria-label="結束日期" :disabled="!dateRangeEnabled" />
            </div>
            <h3 class="capital-title">資金管理</h3>
            <div class="form-stack">
              <label class="field"><span>管理模式</span><select v-model="settings.mode"><option v-for="option in modeOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
              <p v-if="settings.mode === 'backtest'" class="mode-hint">直接使用報表口數與報表初始資金；若報表未提供初始資金，採用 100,000。</p>
              <label v-else class="field"><span>初始資金</span><input v-model.number="settings.initial_capital" type="number" min="0.01" step="any" /></label>
              <label v-for="field in visibleFields" :key="field.key" class="field"><span>{{ field.label }}</span><input v-model.number="settings[field.key]" type="number" min="0" :step="field.step" /></label>
              <label v-if="settings.mode === 'target_leverage'" class="field"><span>槓桿資金</span><select v-model="settings.leverage_funds"><option value="cumulative">累加獲利</option><option value="fixed">固定資金</option></select></label>
              <template v-if="settings.mode !== 'backtest'"><label class="field"><span>最大口數 <small>0 = 無上限</small></span><input v-model.number="settings.maximum_quantity" type="number" min="0" step="any" /></label><label class="check-field"><input v-model="settings.integer_quantity" type="checkbox" /><span>口數為整數</span></label></template>
            </div>
            <p v-if="busy" class="field-help" role="status">正在計算報表…</p>
            <p v-else-if="settingsDirty" class="field-help" role="status">設定已變更，將自動重新計算。</p>
            <p v-if="error" class="error-message" role="alert">{{ error }}</p>
          </section>
        </aside>

        <section class="panel results">
          <div v-if="!report" class="empty-state">
            <div class="empty-illustration" aria-hidden="true"><div class="empty-line one"></div><div class="empty-line two"></div><div class="empty-line three"></div></div>
            <h2>尚無報表</h2>
            <p>正在載入已儲存的績效報表。</p>
          </div>

          <template v-else>
            <div class="results-header">
              <div><h2>{{ currentPerformance.name }}</h2><p>{{ source.strategy }} · {{ source.filename }} · {{ source.format.toUpperCase() }} · {{ formatNumber(source.trade_count, 0) }} 筆交易 · {{ source.symbol }}</p></div>
              <button type="button" class="print-button" @click="printReport">列印 / 儲存 PDF <span aria-hidden="true">↗</span></button>
            </div>
            <p class="print-meta">資金管理：{{ activeSection === 'simple' ? '單純績效' : resultModeLabel }} · 初始資金：{{ formatNumber(currentSummary.initial_capital) }} · 分析區間：{{ currentSummary.start_date || '—' }} 至 {{ currentSummary.end_date || '—' }}</p>
            <div class="segment-bar"><button type="button" :class="{ active: activeSection === 'simple' }" @click="activeSection = 'simple'">單純績效</button><button type="button" :class="{ active: activeSection === 'compound' }" @click="activeSection = 'compound'">資金管理 · {{ resultModeLabel }}</button></div>
            <nav class="tab-bar" aria-label="報表內容"><button v-for="tab in tabs" :key="tab.value" type="button" :class="{ active: activeTab === tab.value }" @click="activeTab = tab.value">{{ tab.label }}</button></nav>

            <div v-if="activeTab === 'overview'" class="report-content">
              <div class="metric-grid">
                <div class="metric-card primary"><span>最終淨值</span><strong>{{ formatNumber(currentSummary.final_capital) }}</strong><small>起始 {{ formatNumber(currentSummary.initial_capital) }}</small></div>
                <div class="metric-card"><span>淨利</span><strong :class="{ negative: currentSummary.net_profit < 0 }">{{ formatNumber(currentSummary.net_profit) }}</strong><small>{{ formatNumber(currentSummary.trade_count, 0) }} 筆交易</small></div>
                <div class="metric-card"><span>最大回撤</span><strong class="drawdown-value">{{ formatNumber(currentSummary.max_drawdown) }}</strong><small>{{ formatPercent(currentSummary.max_drawdown_pct) }}</small></div>
                <div class="metric-card"><span>獲利 / 回撤</span><strong>{{ formatNumber(currentSummary.profit_over_mdd, 3) }}</strong><small>Sharpe {{ formatNumber(currentSummary.sharpe_ratio) }}</small></div>
              </div>
              <div class="panel chart-panel"><div class="section-heading"><div><span class="section-kicker">PERFORMANCE CURVE</span><h3>淨值與回撤</h3></div><span class="date-badge">{{ currentSummary.start_date || '—' }} → {{ currentSummary.end_date || '—' }}</span></div><div ref="chartElement" class="chart" role="img" :aria-label="`淨值與回撤圖，最終淨值 ${formatNumber(currentSummary.final_capital)}`"></div></div>
              <div class="panel detail-metrics"><div class="section-heading"><div><span class="section-kicker">KEY METRICS</span><h3>績效指標</h3></div></div><div class="metrics-list"><div><span>平均每筆淨利</span><strong>{{ formatNumber(currentSummary.average_net_profit) }}</strong></div><div><span>勝率</span><strong>{{ formatPercent(currentSummary.win_rate_pct) }}</strong></div><div><span>獲利因子</span><strong>{{ formatNumber(currentSummary.profit_factor) }}</strong></div><div><span>Sortino</span><strong>{{ formatNumber(currentSummary.sortino_ratio) }}</strong></div><div><span>Earning Power</span><strong>{{ formatPercent(currentSummary.earning_power_pct) }}</strong></div><div><span>每大點價值</span><strong>{{ formatNumber(currentSummary.big_point_value) }}</strong></div><div><span>交易成本</span><strong>{{ currentSummary.trade_cost }}</strong></div><div v-if="activeSection === 'compound'"><span>年化報酬率</span><strong>{{ formatPercent(currentSummary.annual_return_pct) }}</strong></div></div></div>
              <div v-if="currentSection.drawdowns?.length" class="panel drawdown-panel"><div class="section-heading"><div><span class="section-kicker">DRAWDOWN</span><h3>主要回撤區間</h3></div></div><div class="table-scroll"><table><thead><tr><th>起點</th><th>谷底</th><th>恢復</th><th class="numeric">金額</th><th class="numeric">比率</th></tr></thead><tbody><tr v-for="(row, index) in currentSection.drawdowns" :key="index"><td>{{ row.started_at?.slice(0, 10) }}</td><td>{{ row.bottomed_at?.slice(0, 10) }}</td><td>{{ row.recovered_at?.slice(0, 10) || '未恢復' }}</td><td class="numeric">{{ formatNumber(row.amount) }}</td><td class="numeric">{{ formatPercent(row.percent) }}</td></tr></tbody></table></div></div>
            </div>

            <div v-else-if="activeTab === 'periods'" class="panel table-panel"><div class="section-heading"><div><span class="section-kicker">PERIOD REPORT</span><h3>週期績效</h3></div><button type="button" class="secondary-button" :disabled="!currentPeriods.length" @click="downloadCsv('periods')">下載 CSV ↓</button></div><div class="period-switch"><button v-for="(label, key) in periodLabels" :key="key" type="button" :class="{ active: activePeriod === key }" @click="activePeriod = key">{{ label }}</button></div><div class="table-scroll"><table><thead><tr><th>期間</th><th class="numeric">損益</th><th class="numeric">累積</th><th v-if="activeSection === 'compound'" class="numeric">報酬率</th></tr></thead><tbody><tr v-for="row in currentPeriods" :key="row.period"><td>{{ row.period }}</td><td class="numeric" :class="{ negative: row.profit < 0 }">{{ formatNumber(row.profit) }}</td><td class="numeric">{{ formatNumber(row.cumulative) }}</td><td v-if="activeSection === 'compound'" class="numeric">{{ formatPercent(row.return_pct) }}</td></tr><tr v-if="!currentPeriods.length"><td colspan="4" class="no-data">此區間沒有資料</td></tr></tbody></table></div></div>

            <div v-else-if="activeTab === 'details'" class="panel table-panel"><div class="section-heading"><div><span class="section-kicker">TRADE LOG</span><h3>逐筆交易明細</h3><p>共 {{ formatNumber(currentDetails.length, 0) }} 筆</p></div><button type="button" class="secondary-button" :disabled="!currentDetails.length" @click="downloadCsv('details')">下載 CSV ↓</button></div><div class="table-scroll detail-table"><table><thead><tr><th>時間</th><th>標的</th><th>買賣</th><th class="numeric">口數</th><th class="numeric">價格</th><th class="numeric">部位</th><th class="numeric">損益</th><th class="numeric">累積淨值</th><th>訊號</th></tr></thead><tbody><tr v-for="row in currentDetails" :key="row.index"><td>{{ row.timestamp }}</td><td>{{ row.symbol }}</td><td><span class="side-pill" :class="row.side === 'B' ? 'buy' : 'sell'">{{ row.side === 'B' ? '買進' : '賣出' }}</span></td><td class="numeric">{{ formatNumber(row.quantity, 4) }}</td><td class="numeric">{{ formatNumber(row.price, 4) }}</td><td class="numeric">{{ formatNumber(row.position, 4) }}</td><td class="numeric" :class="{ negative: row.profit < 0 }">{{ formatNumber(row.profit) }}</td><td class="numeric">{{ formatNumber(row.equity) }}</td><td>{{ row.action || '—' }}</td></tr><tr v-if="!currentDetails.length"><td colspan="9" class="no-data">此區間沒有交易</td></tr></tbody></table></div></div>

            <div v-else class="panel table-panel"><div class="section-heading"><div><span class="section-kicker">SOURCE PARAMETERS</span><h3>策略參數</h3></div></div><div class="metadata-summary"><div><span>來源格式</span><strong>{{ source.format.toUpperCase() }}</strong></div><div><span>每大點價值</span><strong>{{ formatNumber(source.point_value) }}</strong></div><div><span>報表初始資金</span><strong>{{ source.source_initial_capital == null ? '未提供' : formatNumber(source.source_initial_capital) }}</strong></div><div><span>資金管理模式</span><strong>{{ resultModeLabel }}</strong></div></div><div class="table-scroll"><table><thead><tr><th>參數</th><th>數值</th></tr></thead><tbody><tr v-for="(value, name) in { ...source.params, ...source.strategy_params }" :key="name"><td>{{ name }}</td><td>{{ value }}</td></tr></tbody></table></div></div>
          </template>
        </section>
      </div>
    </main>

  </div>
</template>
