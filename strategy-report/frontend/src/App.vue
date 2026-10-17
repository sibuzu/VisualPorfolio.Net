<script setup>
import * as echarts from 'echarts'
import BuyHoldDialog from './BuyHoldDialog.vue'
import HelpIcon from './HelpIcon.vue'
import SummaryPanel from './SummaryPanel.vue'
import ReportDateInput from './ReportDateInput.vue'
import { visibleSimpleCurveSeries } from './curveSelection.js'
import { profitDrawdownSegments } from './profitPlot.js'
import { fitCurveAxis, formatProfitTick, profitAxisLayout } from './profitAxis.js'
import { buildPeriodPlotData, nextPeriodMetricSelection, periodDrawdownLabel, withoutUnavailableBuyHold } from './periodComparison.js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const modeOptions = [
  { value: 'backtest', label: '回測時已計算' },
  { value: 'dynamic_compounding', label: '動態複利' },
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

const modeHelp = {
  fixed_quantity: '每筆來源口數乘以固定口數；設定為 1 時使用原始口數。',
  risk_factor: '口數倍率 = 目前資金 × 風險因子 ÷（該筆 ATR × 每點價值），取最接近的整數。',
  target_leverage: '口數倍率 = 指定資金 × 槓桿倍數 ÷ 原始部位金額；指定資金可選固定本金或累加獲利。',
  profit_step: '口數倍率 = 初始口數 + 累計獲利 ÷ 獲利基數，且不低於最小口數。',
  fixed_amount: '口數倍率 = 目前資金 ÷ 交易一口金額。',
  fixed_risk: '口數倍率 = 目前資金 × 固定風險比例 ÷ 每次交易風險金額，向下取整。',
  profit_risk: '尚未獲利時，依目前資金與初始資金風險比例計算；獲利後，依初始資金與已獲利部分各自的風險比例計算。',
  target_margin: '口數倍率 = 目前資金 × 保證金目標比例 ÷ 每口保證金。',
  kelly: '口數倍率 = 目前資金 × 下注比例 ÷ 100 ÷ ChipSize。'
}

const fields = [
  { key: 'dynamic_initial_ratio', label: '初始比例', modes: ['dynamic_compounding'], step: 'any' },
  { key: 'dynamic_add_ratio', label: '加碼比例', modes: ['dynamic_compounding'], step: 'any' },
  { key: 'dynamic_profit_threshold', label: '獲利達加碼', modes: ['dynamic_compounding'], step: 'any' },
  { key: 'dynamic_max_multiple', label: '最大倍數', modes: ['dynamic_compounding'], step: 'any' },
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
  mode: 'fixed_quantity', initial_capital: 1000000, backtest_initial_capital: null, fixed_quantity: 1,
  dynamic_initial_ratio: 0.10, dynamic_add_ratio: 0.15, dynamic_profit_threshold: 100000000,
  dynamic_drawdown_threshold: '2000', dynamic_max_multiple: 10, dynamic_interval: 'weekly',
  dynamic_lot_rounding: 'retain',
  risk_factor: 0.002, leverage: 0.2, leverage_funds: 'cumulative',
  initial_quantity: 50, minimum_quantity: 0, profit_base: 100000,
  amount_per_quantity: 400000, fixed_risk_ratio: 0.02,
  initial_risk_ratio: 0.02, profit_risk_ratio: 0.05, loss_per_trade: 10000,
  margin_ratio: 0.1, margin_per_quantity: 100000, stake_percent: 10,
  chip_size: 0, maximum_quantity: 0, integer_quantity: false,
  date_start: '', date_end: '', buy_hold: null
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
const activeTab = ref('simple-summary')
const activePeriod = ref('annual')
const periodSelected = ref(['compound'])
const buyHoldOpen = ref(false)
const reportHelpOpen = ref(false)
const capitalHelpOpen = ref(false)
const chartElement = ref(null)
const sidebarWidth = ref(360)
const resizingSidebar = ref(false)
const detailTableElement = ref(null)
const detailPages = ref({ simple: 1, compound: 1, buyhold: 1 })
const detailScrollTops = { simple: 0, compound: 0, buyhold: 0 }
const detailsPageSize = 100
const curveSelection = ref({ profit: true, buyHold: false, drawdown: false, quantity: false })
let chart = null
let resizeObserver = null
let chartResizeFrame = null
let reportRequestId = 0
let recalculateTimer = null
let calculateQueued = false

const resultModeLabel = computed(() => modeOptions.find(row => row.value === report.value?.settings?.mode)?.label || '')
const selectedModeLabel = computed(() => modeOptions.find(row => row.value === settings.value.mode)?.label || '')
const visibleFields = computed(() => fields.filter(row => row.modes.includes(settings.value.mode)))
const currentSection = computed(() => activeSection.value === 'buyhold'
  ? report.value?.buy_hold || null : report.value?.[activeSection.value] || null)
const currentSummary = computed(() => activeSection.value === 'buyhold'
  ? report.value?.buy_hold?.summary || { initial_capital: report.value?.buy_hold?.initial_capital,
      final_capital: report.value?.buy_hold?.final_capital }
  : currentSection.value?.summary || {})
const currentDetails = computed(() => activeSection.value === 'buyhold'
  ? report.value?.buy_hold?.detail || [] : currentSection.value?.detail || [])
const detailsPageCount = computed(() => Math.max(1, Math.ceil(currentDetails.value.length / detailsPageSize)))
const detailsPage = computed({
  get: () => Math.min(detailPages.value[activeSection.value], detailsPageCount.value),
  set: page => { detailPages.value[activeSection.value] = page }
})
const pagedDetails = computed(() => currentDetails.value.slice(
  (detailsPage.value - 1) * detailsPageSize, detailsPage.value * detailsPageSize))
const detailPageNumbers = computed(() => {
  const count = detailsPageCount.value
  if (count <= 7) return Array.from({ length: count }, (_, index) => index + 1)
  return [...new Set([1, count, ...Array.from({ length: 5 }, (_, index) => detailsPage.value + index - 2)
    .filter(page => page > 1 && page < count)])].sort((a, b) => a - b)
})
const hasBuyHoldCurve = computed(() => Boolean(report.value?.buy_hold?.curve?.length))
const simpleCurveVisible = computed(() => visibleSimpleCurveSeries(curveSelection.value, hasBuyHoldCurve.value))
const isFullHeightPlot = computed(() => activeView.value === 'periods' ||
  (activeSection.value === 'simple' && activeView.value === 'curve'))
const simpleCurveItems = computed(() => [
  { key: 'profit', label: '獲利' },
  ...(hasBuyHoldCurve.value ? [{ key: 'buyHold', label: 'BuyHold' }] : []),
  { key: 'drawdown', label: '回撤' },
  { key: 'quantity', label: '口數' }
])
const source = computed(() => report.value?.source || null)
const backtestCapital = computed({
  get: () => settings.value.backtest_initial_capital ?? source.value?.source_initial_capital ?? 100000,
  set: value => {
    settings.value.backtest_initial_capital = value
    settings.value.initial_capital = value
  }
})
const backtestHelp = computed(() => {
  const sourceCapital = source.value?.source_initial_capital
  const override = settings.value.backtest_initial_capital
  let detail = sourceCapital == null
    ? '來源未提供初始資金'
    : `來源有提供初始資金=${sourceCapital}`
  if (override != null || sourceCapital == null) {
    detail += `，已設定初始資金=${override ?? 100000}`
  }
  return `直接使用來源報表的交易口數與初始資金；${detail}。可手動設定初始資金，變動初始資金會變動年化報酬。`
})
const dynamicHelp = computed(() => {
  const cfg = settings.value
  const initialRisk = Number(cfg.initial_capital) * Number(cfg.dynamic_initial_ratio)
  const maxRisk = initialRisk * Number(cfg.dynamic_max_multiple)
  const drawdown = String(cfg.dynamic_drawdown_threshold).trim()
  const drawdownLabel = drawdown.endsWith('%') ? drawdown : `${formatNumber(Number(drawdown) * 10000, 0)}`
  return [
    `一開始用 ${formatPercent(Number(cfg.dynamic_initial_ratio) * 100)}，初始 MDD 風險控制為 ${formatNumber(initialRisk, 0)}。`,
    `累積獲利超過 ${formatNumber(cfg.dynamic_profit_threshold, 0)}，下一期切到 ${formatPercent(Number(cfg.dynamic_add_ratio) * 100)}。`,
    `從高點回撤超過 ${drawdownLabel}，下一期切回初始比例；淨值再創新高後切回加碼比例。`,
    `MDD 風險控制上限為 ${formatNumber(maxRisk, 0)}；複利間隔：${cfg.dynamic_interval === 'monthly' ? '每月' : '每週'}。`
  ].join('\n')
})
const periodLabels = { annual: '每年', semiannual: '每半年', quarterly: '每季', monthly: '每月' }
const periodMetricOptions = computed(() => [
  { key: 'simple', label: '單口績效' },
  { key: 'compound', label: '複合績效' },
  ...(report.value?.buy_hold ? [{ key: 'buyhold', label: 'BuyHold' }] : []),
  { key: 'drawdown', label: periodSelected.value.includes('drawdown')
    ? periodDrawdownLabel(periodSelected.value) : 'Drawdown' }
])
const periodPlotData = computed(() => buildPeriodPlotData(
  report.value, activePeriod.value, periodSelected.value))

function togglePeriodMetric(key) {
  periodSelected.value = nextPeriodMetricSelection(periodSelected.value, key)
}

const baseTabs = [
  { value: 'simple-summary', label: '單口績效', section: 'simple', view: 'summary' },
  { value: 'simple-curve', label: '單口曲線', section: 'simple', view: 'curve' },
  { value: 'simple-details', label: '單口明細', section: 'simple', view: 'details' },
  { value: 'compound-summary', label: '複合績效', section: 'compound', view: 'summary' },
  { value: 'compound-curve', label: '複合曲線', section: 'compound', view: 'curve' },
  { value: 'compound-details', label: '複合明細', section: 'compound', view: 'details' },
  { value: 'compound-periods', label: '逐年績效', section: 'compound', view: 'periods' }
]
const tabs = computed(() => report.value?.buy_hold
  ? [...baseTabs.flatMap(tab => tab.value === 'compound-summary'
      ? [tab, { value: 'buyhold-summary', label: 'BH績效', section: 'buyhold', view: 'summary' }]
      : [tab]),
      { value: 'buyhold-details', label: 'BH明細', section: 'buyhold', view: 'buyhold' }]
  : baseTabs)
const selectedTab = computed(() => tabs.value.find(tab => tab.value === activeTab.value) || tabs.value[0])
const activeSection = computed(() => selectedTab.value.section)
const activeView = computed(() => selectedTab.value.view)
const buyHoldName = computed(() => {
  const bh = settings.value.buy_hold
  if (!bh) return '無'
  const suffix = bh.product_type === '期貨' ? `_${Number(bh.leverage)}X` : ''
  return `BH${bh.code}_${Number(bh.amount_wan)}萬${suffix}`
})
function applyBuyHold(value) {
  settings.value.buy_hold = value
  buyHoldOpen.value = false
}

function formatNumber(value, digits = 2) {
  return new Intl.NumberFormat('zh-TW', { maximumFractionDigits: digits, minimumFractionDigits: 0 }).format(Number(value || 0))
}

function formatMoney(value) {
  const amount = Number(value || 0)
  return `${amount < 0 ? '-' : ''}$${formatNumber(Math.abs(amount), 0)}`
}

function formatQuantity(value) {
  const quantity = Number(value || 0)
  const magnitude = Math.abs(quantity)
  const digits = magnitude > 1000 ? 1 : magnitude > 100 ? 2 : magnitude > 10 ? 3 : 4
  return formatNumber(quantity, digits)
}

function formatBuyHoldQuantity(value) {
  return formatQuantity(value)
}

function isBuyHoldAdjustment(action) {
  return /除權|除息|分割|換倉/.test(action || '')
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
  return window.location.pathname.match(/^\/reports\/(SR-[A-Z]{6})\/?$/)?.[1] || ''
}

function settingsPayload() {
  const payload = { ...settings.value, date_range_enabled: dateRangeEnabled.value }
  if (!payload.date_start) delete payload.date_start
  if (!payload.date_end) delete payload.date_end
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
      backtest_initial_capital: data.performance.settings.backtest_initial_capital ?? null,
      date_start: data.performance.settings.date_start || data.performance.source_range?.start || '',
      date_end: data.performance.settings.date_end || data.performance.source_range?.end || '',
      buy_hold: data.performance.settings.buy_hold || null
    }
    dateRangeEnabled.value = data.performance.settings.date_range_enabled
      ?? Boolean(data.performance.settings.date_start || data.performance.settings.date_end)
    if (pushRoute) window.history.pushState({}, '', `/reports/${itemId}`)
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
    const url = `${window.location.origin}/reports/${item.performance_id}`
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
  buyHoldOpen.value = false
  reportHelpOpen.value = false
  capitalHelpOpen.value = false
  activeTab.value = 'simple-summary'
  activePeriod.value = 'annual'
  periodSelected.value = ['compound']
  detailPages.value = { simple: 1, compound: 1, buyhold: 1 }
  detailScrollTops.simple = 0
  detailScrollTops.compound = 0
  detailScrollTops.buyhold = 0
  curveSelection.value = { profit: true, buyHold: false, drawdown: false, quantity: false }
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

function updateFullHeightPlot() {
  if (!isFullHeightPlot.value || !chartElement.value) return
  const viewportHeight = window.innerHeight
  const chartTop = chartElement.value.getBoundingClientRect().top
  const available = chartTop >= 0 && chartTop < viewportHeight
    ? viewportHeight - chartTop - 8 : viewportHeight - 16
  chartElement.value.style.height = `${Math.max(240, Math.floor(available))}px`
  chart?.resize()
}

function onSidebarMouseMove(event) {
  if (!resizingSidebar.value) return
  sidebarWidth.value = Math.max(360, Math.min(640, event.clientX - 14))
}

function stopSidebarResize() {
  resizingSidebar.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function startSidebarResize() {
  if (window.innerWidth <= 900) return
  resizingSidebar.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function renderChart() {
  if (!['curve', 'periods'].includes(activeView.value) || !chartElement.value || !currentSection.value) return
  if (chart && chart.getDom() !== chartElement.value) {
    resizeObserver?.disconnect()
    chart.dispose()
    chart = null
  }
  if (!chart) {
    chart = echarts.init(chartElement.value)
    resizeObserver = new ResizeObserver(() => {
      if (chartResizeFrame != null) return
      chartResizeFrame = requestAnimationFrame(() => {
        chartResizeFrame = null
        if (isFullHeightPlot.value) renderChart()
        else chart?.resize()
      })
    })
    resizeObserver.observe(chartElement.value)
  }
  if (isFullHeightPlot.value) updateFullHeightPlot()
  else chartElement.value.style.removeProperty('height')
  if (activeView.value === 'periods') {
    const { rows, series } = periodPlotData.value
    const values = [0, ...series.flatMap(item => rows.map(row => row[item.key]))]
    const axis = fitCurveAxis({ type: 'value', min: 0 }, values)
    const fontFamily = getComputedStyle(chartElement.value).fontFamily
    const measureContext = document.createElement('canvas').getContext('2d')
    measureContext.font = `12px ${fontFamily}`
    const tickCount = Math.min(30, Math.round((axis.max - axis.min) / axis.interval))
    const ticks = Array.from({ length: tickCount + 1 }, (_, index) => axis.min + index * axis.interval)
    const gutter = profitAxisLayout(ticks, label => measureContext.measureText(label).width,
      value => formatProfitTick(value, true)).gutter
    const valueAxis = (position, splitLine) => ({
      ...axis, position,
      axisLine: { show: true, lineStyle: { color: '#111' } },
      axisTick: { show: true },
      axisLabel: { color: '#111', margin: 4, formatter: value => formatProfitTick(value, true) },
      splitLine: { show: splitLine, lineStyle: { color: '#ddd', type: 'dashed' } }
    })
    chart.setOption({
      animationDuration: 250,
      grid: { left: gutter, right: gutter, top: 8, bottom: 32, containLabel: false },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
        valueFormatter: value => value == null ? '—' : formatProfitTick(value) },
      xAxis: { type: 'category', data: rows.map(row => row.period),
        axisLabel: { hideOverlap: true, interval: 'auto' },
        axisLine: { lineStyle: { color: '#111' } } },
      yAxis: [valueAxis('left', true), valueAxis('right', false)],
      series: series.map(item => ({
        name: item.label, type: 'bar', barMaxWidth: 34,
        itemStyle: { color: item.color },
        data: rows.map(row => row[item.key] ?? null)
      }))
    }, true)
    chart.resize()
    return
  }
  const curve = currentSection.value.curve || []
  const reference = report.value.buy_hold
  const hasReference = Boolean(reference?.curve?.length)
  const hasDrawdown = curve.some(row => row.drawdown > 0)
  const timestamp = value => new Date(value.length === 10 ? `${value}T00:00:00` : value.replace(' ', 'T')).getTime()
  const equityName = activeSection.value === 'simple' ? '獲利' : '資金'
  if (activeSection.value === 'simple') {
    const visible = simpleCurveVisible.value
    const hasPrimary = visible.profit || visible.buyHold
    const leftKind = hasPrimary ? 'profit' : visible.drawdown ? 'drawdown' : 'quantity'
    const hasRightAxis = (leftKind === 'profit' && (visible.drawdown || visible.quantity)) ||
      (leftKind === 'drawdown' && visible.quantity)
    const maxQuantity = curve.reduce((maximum, row) => Math.max(maximum, Number(row.open_position) || 0), 1)
    const integerQuantity = curve.every(row => Number.isInteger(Number(row.open_position) || 0))
    const valueAxis = (name, min, splitLine) => ({
      type: 'value', name, ...(min == null ? { scale: true } : { min }),
      axisLabel: { formatter: value => formatNumber(value, 0) },
      splitLine: { show: splitLine, lineStyle: { color: '#e6ecec' } }
    })
    const quantityAxis = right => ({
      type: 'value', name: '口數', min: 0, ...(right ? { max: maxQuantity * 4 } : {}),
      ...(integerQuantity ? { minInterval: 1 } : {}),
      axisLabel: { formatter: value => formatQuantity(value) },
      splitLine: { show: !right, lineStyle: { color: '#e6ecec' } }
    })
    const axes = [leftKind === 'quantity' ? quantityAxis(false) : valueAxis(
      leftKind === 'profit' ? '' : '回撤', leftKind === 'profit' ? null : 0, true)]
    if (hasRightAxis) axes.push(visible.quantity ? quantityAxis(true) : valueAxis('回撤', 0, false))
    const secondaryAxis = kind => leftKind === kind ? 0 : 1
    const series = []
    if (visible.profit) series.push({
      name: '獲利', type: 'line', yAxisIndex: 0,
      data: curve.map(row => [timestamp(row.timestamp), row.equity]),
      showSymbol: false, lineStyle: { width: 2.5, color: '#0b7183' },
      itemStyle: { color: '#0b7183' }, areaStyle: { color: 'rgba(11,113,131,.10)' }
    })
    if (visible.buyHold) series.push({
      name: 'BuyHold', type: 'line', yAxisIndex: 0,
      data: reference.curve.map(row => [timestamp(row.timestamp), row.profit]),
      showSymbol: false, lineStyle: { width: 2, color: '#7c3aed' }, itemStyle: { color: '#7c3aed' }
    })
    if (visible.drawdown) series.push({
      name: '回撤', type: 'line', yAxisIndex: secondaryAxis('drawdown'),
      data: curve.map(row => [timestamp(row.timestamp), row.drawdown]),
      showSymbol: false, lineStyle: { width: 1.5, color: '#d77953' }, itemStyle: { color: '#d77953' }
    })
    if (visible.quantity) series.push({
      name: '口數', type: 'line', yAxisIndex: secondaryAxis('quantity'),
      data: curve.map(row => [timestamp(row.timestamp), row.open_position]),
      showSymbol: false, lineStyle: { width: 1.5, color: '#657587' }, itemStyle: { color: '#657587' }
    })
    const axisKinds = [leftKind, ...(hasRightAxis ? [visible.quantity ? 'quantity' : 'drawdown'] : [])]
    axes.forEach((axis, index) => {
      const values = series.filter(item => (item.yAxisIndex || 0) === index)
        .flatMap(item => item.data.map(([, value]) => value))
      axes[index] = fitCurveAxis(axis, values, axisKinds[index] === 'quantity' && integerQuantity)
    })
    if (!hasRightAxis) axes.push({ ...axes[0], position: 'right', splitLine: { show: false } })

    const fontFamily = getComputedStyle(chartElement.value).fontFamily
    const measureCanvas = document.createElement('canvas')
    const measureContext = measureCanvas.getContext('2d')
    measureContext.font = `12px ${fontFamily}`
    const axisFormatter = kind => kind === 'quantity' ? formatQuantity : value => formatProfitTick(value, true)
    const ticksFor = axis => {
      const count = Math.min(30, Math.round((axis.max - axis.min) / axis.interval))
      return Array.from({ length: count + 1 }, (_, index) => axis.min + index * axis.interval)
    }
    const labelWidth = (axis, kind) => profitAxisLayout(ticksFor(axis),
      label => measureContext.measureText(label).width, axisFormatter(kind)).gutter
    const leftGutter = labelWidth(axes[0], leftKind)
    const rightGutter = hasRightAxis ? labelWidth(axes[1], axisKinds[1]) : leftGutter
    const classicAxis = (axis, position, kind) => ({
      ...axis, position, name: '',
      axisLine: { show: true, lineStyle: { color: '#111', width: 1 } },
      axisTick: { show: true, lineStyle: { color: '#111' } },
      axisLabel: { color: '#111', fontSize: 12, fontFamily, margin: 4, formatter: axisFormatter(kind) },
      splitLine: position === 'left'
        ? { show: true, lineStyle: { color: '#aaa', type: 'dashed', width: 1 } }
        : { show: false }
    })
    const toDate = value => {
      const date = new Date(value)
      return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}`
    }
    const firstTime = curve.length ? timestamp(curve[0].timestamp) : 0
    const lastTime = curve.length ? timestamp(curve[curve.length - 1].timestamp) : 1
    const mddLines = visible.profit ? profitDrawdownSegments(curve, currentSection.value.drawdowns || [])
      .map((segment, index) => ({
        name: `MDD ${index + 1}`, type: 'line', showSymbol: false, silent: true,
        tooltip: { show: false }, animation: false, z: 5,
        data: segment.map(([date, value]) => [timestamp(date), value]),
        lineStyle: { color: '#e00000', width: 1.5 }
      })) : []
    const styledSeries = series.map(item => {
      const color = item.name === '獲利' || series.length === 1 ? '#111'
        : item.name === 'BuyHold' ? '#7c3aed' : item.name === '回撤' ? '#d77953' : '#657587'
      return { ...item, areaStyle: undefined, lineStyle: { color, width: series.length === 1 ? 0.75 : 1.25 },
        itemStyle: { color }, z: 4 }
    })
    chart.setOption({
      animationDuration: 350,
      backgroundColor: '#fff',
      grid: { left: leftGutter, right: rightGutter, top: 10, bottom: 28, containLabel: false,
        show: true, backgroundColor: '#fff', borderColor: '#111', borderWidth: 1 },
      tooltip: {
        trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: '#777', type: 'dotted' } },
        formatter: items => {
          const points = items.filter(item => item.seriesName !== '基準線' && !item.seriesName.startsWith('MDD '))
          if (!points.length) return ''
          const date = new Date(points[0].data[0])
          const dateText = `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`
          return `${dateText}<br>${points.map(item => `${item.marker}${item.seriesName}：${item.seriesName === '口數' ? formatQuantity(item.data[1]) : formatProfitTick(item.data[1])}`).join('<br>')}`
        }
      },
      xAxis: {
        type: 'time', boundaryGap: false,
        axisLine: { show: true, lineStyle: { color: '#111' } },
        axisTick: { show: true, lineStyle: { color: '#111' } },
        axisLabel: { color: '#111', fontSize: 12, hideOverlap: true, formatter: toDate },
        splitLine: { show: true, lineStyle: { color: '#aaa', type: 'dashed' } },
        minorSplitLine: { show: true, lineStyle: { color: '#ddd', type: 'dotted' } }
      },
      yAxis: [classicAxis(axes[0], 'left', leftKind),
        classicAxis(axes[1], 'right', hasRightAxis ? axisKinds[1] : leftKind)],
      series: [
        { name: '基準線', type: 'line', silent: true, showSymbol: false, tooltip: { show: false },
          data: [[firstTime, 0], [lastTime, 0]], lineStyle: { color: '#243bff', width: 1 }, z: 2 },
        ...styledSeries,
        ...mddLines
      ]
    }, true)
    chart.resize()
    return
  }
  chart.setOption({
    animationDuration: 350,
    grid: { left: 66, right: hasDrawdown ? 70 : 24, top: 52, bottom: 40, containLabel: true },
    tooltip: { trigger: 'axis', valueFormatter: value => formatNumber(value, 2) },
    legend: { top: 2, data: [equityName, '回撤', ...(hasReference ? [reference.name] : [])] },
    xAxis: { type: 'time', boundaryGap: false, axisLabel: { hideOverlap: true } },
    yAxis: [
      { type: 'value', scale: true, axisLabel: { formatter: value => formatNumber(value, 0) }, splitLine: { lineStyle: { color: '#e6ecec' } } },
      { type: 'value', name: '回撤', min: 0, show: hasDrawdown, axisLabel: { formatter: value => formatNumber(value, 0) }, splitLine: { show: false } }
    ],
    series: [
      { name: equityName, type: 'line', data: curve.map(row => [timestamp(row.timestamp), row.equity]), showSymbol: false, smooth: false, lineStyle: { width: 2.5, color: '#0b7183' }, itemStyle: { color: '#0b7183' }, areaStyle: { color: 'rgba(11,113,131,.10)' } },
      { name: '回撤', type: 'line', yAxisIndex: 1, data: curve.map(row => [timestamp(row.timestamp), row.drawdown]), showSymbol: false, lineStyle: { width: 1.5, color: '#d77953' }, itemStyle: { color: '#d77953' } },
      ...(hasReference ? [{ name: reference.name, type: 'line', data: reference.curve.map(row => [timestamp(row.timestamp), activeSection.value === 'simple' ? row.profit : row.equity]), showSymbol: false, lineStyle: { width: 2, color: '#7c3aed' }, itemStyle: { color: '#7c3aed' } }] : [])
    ]
  }, true)
  chart.resize()
}

watch([activeTab, activePeriod, periodSelected, report], () => nextTick(renderChart))
watch(report, value => {
  if (activeTab.value.startsWith('buyhold-') && !value?.buy_hold) activeTab.value = 'simple-summary'
  if (!value?.buy_hold && periodSelected.value.includes('buyhold'))
    periodSelected.value = withoutUnavailableBuyHold(periodSelected.value)
})
watch(activeTab, () => {
  const section = activeSection.value
  const scrollTop = detailScrollTops[section]
  nextTick(() => {
    if (['details', 'buyhold'].includes(activeView.value) && detailTableElement.value) {
      detailTableElement.value.scrollTop = scrollTop
    }
  })
})
watch(curveSelection, () => nextTick(renderChart), { deep: true })
function goToDetailsPage(page) {
  detailsPage.value = Math.min(Math.max(page, 1), detailsPageCount.value)
  detailScrollTops[activeSection.value] = 0
  nextTick(() => { if (detailTableElement.value) detailTableElement.value.scrollTop = 0 })
}
function rememberDetailScroll(event) {
  detailScrollTops[activeSection.value] = event.target.scrollTop
}
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
  if (!currentSection.value && kind !== 'buyhold') return
  const rows = kind === 'periods' ? periodPlotData.value.rows : currentDetails.value
  if (!rows.length) return
  const buyHoldFutures = kind === 'buyhold' && report.value?.settings?.buy_hold?.product_type === '期貨'
  const columns = kind === 'buyhold'
    ? [['__row_number__', '#'], ['timestamp', '日期'], ['symbol', '標的'],
      ...(buyHoldFutures ? [['contract', '合約']] : []), ['action', '動作'],
      ['quantity', report.value?.settings?.buy_hold?.product_type === '股票' ? '股數' : '口數'],
      ['price', '收盤價'], ...(buyHoldFutures ? [['price_basis', '價別']] : []),
      ['position', '部位'], ['profit', '當日損益'], ['equity', '累積淨值']]
    : kind === 'details'
      ? [['__row_number__', '#'], ['timestamp', '時間'], ['symbol', '標的'], ['side', '買賣'], ['quantity', report.value?.settings?.mode === 'dynamic_compounding' && activeSection.value === 'compound' ? '倍率' : '口數'], ['price', '價格'], ['position', '部位'], ['profit', '損益'], ['equity', '累積淨值'], ['action', '訊號']]
      : [['period', '期間'], ...periodPlotData.value.series.map(item => [item.key, `${item.label}($)`])]
  const lines = [
    `${csvCell('來源檔案')},${csvCell(source.value?.filename)}`,
    `${csvCell('策略')},${csvCell(source.value?.strategy)}`,
    `${csvCell('資金管理模式')},${csvCell(activeSection.value === 'buyhold' ? 'BuyHold' : activeSection.value === 'simple' ? '單純績效' : resultModeLabel.value)}`,
    `${csvCell('區間')},${csvCell(`${report.value?.settings?.date_start || '全部'} ~ ${report.value?.settings?.date_end || '全部'}`)}`,
    '', columns.map(item => csvCell(item[1])).join(','),
    ...rows.map((row, index) => columns.map(([key]) => csvCell(key === '__row_number__' ? index + 1 : row[key])).join(','))
  ]
  const blob = new Blob(['\ufeff', lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${(source.value?.strategy || 'strategy').replaceAll(/[\\/:*?"<>|]/g, '_')}-${activeSection.value}-${kind === 'buyhold' ? 'daily-close' : kind === 'details' ? 'details' : activePeriod.value}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handleRouteChange)
  window.removeEventListener('resize', updateFullHeightPlot)
  window.removeEventListener('mousemove', onSidebarMouseMove)
  window.removeEventListener('mouseup', stopSidebarResize)
  window.visualViewport?.removeEventListener('resize', updateFullHeightPlot)
  if (chartResizeFrame != null) cancelAnimationFrame(chartResizeFrame)
  stopSidebarResize()
  clearReport()
})
onMounted(() => {
  window.addEventListener('popstate', handleRouteChange)
  window.addEventListener('resize', updateFullHeightPlot)
  window.addEventListener('mousemove', onSidebarMouseMove)
  window.addEventListener('mouseup', stopSidebarResize)
  window.visualViewport?.addEventListener('resize', updateFullHeightPlot)
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
        <aside class="panel sidebar" :style="{ width: sidebarWidth + 'px' }">
          <div class="title-row">
            <h1 class="project-title">{{ currentPerformance.name }}</h1>
            <a class="back-link" href="/" @click.prevent="goHome()">回主頁</a>
          </div>
          <div class="id-line">
            <span>{{ currentPerformance.performance_id }}</span>
            <button type="button" class="copy-link-btn" title="複製績效連結" aria-label="複製績效連結" @click="copyPerformanceLink(currentPerformance)">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8,11h8v2H8V11z M20.1,12H22c0-2.76-2.24-5-5-5h-4v1.9h4C18.71,8.9,20.1,10.29,20.1,12z M3.9,12c0-1.71,1.39-3.1,3.1-3.1h4 V7H7c-2.76,0-5,2.24-5,5s2.24,5,5,5h4v-1.9H7C5.29,15.1,3.9,13.71,3.9,12z M19,12h-2v3h-3v2h3v3h2v-3h3v-2h-3V12z"/></svg>
            </button>
            <button v-if="currentPerformance.is_owner" type="button" class="status-inline" title="可編輯" aria-label="可編輯" @click="renamePerformance(currentPerformance)">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.111,2.293,9.384,11.021a.977.977,0,0,0-.241.39L8.052,14.684A1,1,0,0,0,9,16a.987.987,0,0,0,.316-.052l3.273-1.091a.977.977,0,0,0,.39-.241l8.728-8.727a1,1,0,0,0,0-1.414L19.525,2.293A1,1,0,0,0,18.111,2.293ZM11.732,13.035l-1.151.384.384-1.151L16.637,6.6l.767.767Zm7.854-7.853-.768.767-.767-.767.767-.768ZM3,5h8a1,1,0,0,1,0,2H4V20H17V13a1,1,0,0,1,2,0v8a1,1,0,0,1-1,1H3a1,1,0,0,1-1-1V6A1,1,0,0,1,3,5Z"/></svg>
            </button>
            <span v-else class="status-inline" title="可檢視" aria-label="可檢視">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.062,12.346C3.773,17,7.675,20,12,20s8.227-3,9.938-7.654a.993.993,0,0,0,0-.692C20.227,7,16.325,4,12,4S3.773,7,2.062,11.654A.993.993,0,0,0,2.062,12.346ZM12,6c3.373,0,6.451,2.343,7.929,6-1.478,3.657-4.556,6-7.929,6s-6.451-2.343-7.929-6C5.549,8.343,8.627,6,12,6Zm0,10a4,4,0,1,0-4-4A4,4,0,0,0,12,16Zm0-6a2,2,0,1,1-2,2A2,2,0,0,1,12,10Z"/></svg>
            </span>
            <span class="id-line-spacer"></span>
            <button type="button" class="copy-project-btn" @click="copyPerformance(currentPerformance)">
              <svg viewBox="0 0 512 512" aria-hidden="true"><path d="M464 0H144c-26.51 0-48 21.49-48 48v48H48c-26.51 0-48 21.49-48 48v320c0 26.51 21.49 48 48 48h320c26.51 0 48-21.49 48-48v-48h48c26.51 0 48-21.49 48-48V48c0-26.51-21.49-48-48-48zM362 464H54a6 6 0 0 1-6-6V150a6 6 0 0 1 6-6h42v224c0 26.51 21.49 48 48 48h224v42a6 6 0 0 1-6 6zm96-96H150a6 6 0 0 1-6-6V54a6 6 0 0 1 6-6h308a6 6 0 0 1 6 6v308a6 6 0 0 1-6 6z"/></svg>
              <span>複製</span>
            </button>
            <button type="button" class="copy-project-btn" @click="downloadPerformance(currentPerformance)">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.293,13.707a1,1,0,1,1,1.414-1.414L11,14.586V3a1,1,0,0,1,2,0V14.586l2.293-2.293a1,1,0,0,1,1.414,1.414l-4,4a1,1,0,0,1-.325.216.986.986,0,0,1-.764,0,1,1,0,0,1-.325-.216ZM22,12a1,1,0,0,0-1,1v7H3V13a1,1,0,0,0-2,0v8a1,1,0,0,0,1,1H22a1,1,0,0,0,1-1V13A1,1,0,0,0,22,12Z"/></svg>
              <span>下載</span>
            </button>
          </div>
          <p v-if="copyHint" class="hint" role="status">{{ copyHint }}</p>

          <section class="settings-panel">
            <div class="panel-heading settings-heading">
              <h2>績效資金管理</h2>
              <span v-if="busy" class="report-calculating" role="status">正在計算報表…</span>
            </div>
            <div class="manager-range-row">
              <label class="range-check-label"><input v-model="dateRangeEnabled" type="checkbox" /><span>指定</span></label>
              <ReportDateInput v-model="settings.date_start" label="開始日期" :disabled="!dateRangeEnabled" />
              <span class="range-sep">~</span>
              <ReportDateInput v-model="settings.date_end" label="結束日期" :disabled="!dateRangeEnabled" />
            </div>
            <div class="buy-hold-row">
              <button type="button" class="copy-project-btn" @click="buyHoldOpen = true"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z" /></svg><span>Buy&amp;Hold</span></button>
              <span class="muted">{{ buyHoldName }}</span>
            </div>
            <p v-if="report?.buy_hold?.error" class="error-message" role="alert">{{ report.buy_hold.error }}</p>
            <div class="capital-heading">
              <h3 class="capital-title">資金管理</h3>
              <button type="button" class="help-icon-button capital-help-button" aria-label="資金管理說明" title="資金管理說明" aria-controls="capital-help" :aria-expanded="capitalHelpOpen" @click="capitalHelpOpen = !capitalHelpOpen"><HelpIcon /></button>
            </div>
            <div v-show="capitalHelpOpen" id="capital-help" class="capital-help">
              <strong>{{ selectedModeLabel }}</strong>
              <p>{{ settings.mode === 'backtest' ? backtestHelp : settings.mode === 'dynamic_compounding' ? dynamicHelp : modeHelp[settings.mode] }}</p>
              <p v-if="settings.mode !== 'backtest' && settings.mode !== 'dynamic_compounding'">口數倍率會乘以來源交易口數。最大口數設為 0 表示無上限；勾選「口數為整數」時，倍率向下取整。</p>
            </div>
            <div class="form-stack">
              <label class="field"><span>管理模式</span><select v-model="settings.mode"><option v-for="option in modeOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
              <template v-if="settings.mode === 'backtest'">
                <label class="field"><span>初始資金</span><input v-model.number="backtestCapital" class="capital-input" type="number" min="0.01" step="any" /></label>
                <button v-if="settings.backtest_initial_capital != null" type="button" class="capital-reset-button" @click="settings.backtest_initial_capital = null">恢復來源／預設初始資金</button>
              </template>
              <label v-else class="field"><span>初始資金</span><input v-model.number="settings.initial_capital" class="capital-input" type="number" min="0.01" step="any" /></label>
              <label v-for="field in visibleFields" :key="field.key" class="field"><span>{{ field.label }}</span><input v-model.number="settings[field.key]" type="number" min="0" :step="field.step" /></label>
              <template v-if="settings.mode === 'dynamic_compounding'">
                <label class="field"><span>回撤金額(萬,%)</span><input v-model.trim="settings.dynamic_drawdown_threshold" type="text" placeholder="2000 或 5%" /></label>
                <label class="field"><span>複利間隔</span><select v-model="settings.dynamic_interval"><option value="weekly">每週</option><option value="monthly">每月</option></select></label>
                <label class="field"><span>口數小數點</span><select v-model="settings.dynamic_lot_rounding"><option value="floor">捨去</option><option value="ceil">進位</option><option value="round">四捨五入</option><option value="retain">保留</option></select></label>
              </template>
              <label v-if="settings.mode === 'target_leverage'" class="field"><span>槓桿資金</span><select v-model="settings.leverage_funds"><option value="cumulative">累加獲利</option><option value="fixed">固定資金</option></select></label>
              <template v-if="settings.mode !== 'backtest' && settings.mode !== 'dynamic_compounding'"><label class="field"><span>最大口數 <small>0 = 無上限</small></span><input v-model.number="settings.maximum_quantity" type="number" min="0" step="any" /></label><label class="check-field"><input v-model="settings.integer_quantity" type="checkbox" /><span>口數為整數</span></label></template>
            </div>
            <p v-if="!busy && settingsDirty" class="field-help" role="status">設定已變更，將自動重新計算。</p>
            <p v-if="error" class="error-message" role="alert">{{ error }}</p>
          </section>
        </aside>

        <div class="splitter" role="separator" aria-label="調整左側寬度" aria-orientation="vertical" @mousedown="startSidebarResize"></div>

        <section class="panel results">
          <div v-if="!report" class="empty-state">
            <div class="empty-illustration" aria-hidden="true"><div class="empty-line one"></div><div class="empty-line two"></div><div class="empty-line three"></div></div>
            <h2>尚無報表</h2>
            <p>正在載入已儲存的績效報表。</p>
          </div>

          <template v-else>
            <nav class="tab-bar" aria-label="報表內容"><button v-for="tab in tabs" :key="tab.value" type="button" :class="{ active: activeTab === tab.value }" :aria-pressed="activeTab === tab.value" @click="activeTab = tab.value">{{ tab.label }}</button></nav>
            <button type="button" class="help-icon-button report-help-button" aria-label="報表說明" title="報表說明" :aria-expanded="reportHelpOpen" @click="reportHelpOpen = !reportHelpOpen"><HelpIcon /></button>
            <div v-if="reportHelpOpen" class="report-help">
              <p>{{ source.strategy }} · {{ source.filename }} · {{ source.format.toUpperCase() }}</p>
              <p>單口績效顯示原始策略損益；複合績效套用左側資金管理設定（{{ resultModeLabel }}）。Buy&amp;Hold 使用自己的金額，單口曲線顯示其損益，複合曲線顯示其資金淨值。</p>
              <p>初始資金：{{ formatNumber(currentSummary.initial_capital) }} · 最終淨值：{{ formatNumber(currentSummary.final_capital) }} · 每大點價值：{{ formatNumber(source.point_value) }} · 交易成本：{{ currentSummary.trade_cost }}</p>
              <details><summary>策略參數</summary><div class="table-scroll"><table><thead><tr><th>參數</th><th>數值</th></tr></thead><tbody><tr v-for="(value, name) in { ...source.params, ...source.strategy_params }" :key="name"><td>{{ name }}</td><td>{{ value }}</td></tr></tbody></table></div></details>
              <button type="button" class="print-button" @click="printReport">列印 / 儲存 PDF</button>
            </div>
            <p class="print-meta">{{ currentPerformance.name }} · {{ selectedTab.label }} · 資金管理：{{ resultModeLabel }} · 初始資金：{{ formatNumber(currentSummary.initial_capital) }} · Buy&amp;Hold：{{ buyHoldName }}</p>
            <p v-if="activeSection === 'buyhold' && activeView === 'summary' && report.buy_hold.error" class="error-message" role="alert">{{ report.buy_hold.error }}</p>
            <SummaryPanel v-if="activeView === 'summary' && currentSection?.summary" :section="currentSection" :symbol="activeSection === 'buyhold' ? report.settings.buy_hold?.code : source.symbol" :compound="activeSection !== 'simple'" />
            <p v-else-if="activeView === 'summary'" class="no-data">沒有可用的每日收盤行情</p>
            <div v-else-if="activeView === 'curve'" class="chart-panel">
              <h3 v-if="activeSection !== 'simple'">{{ selectedTab.label }}</h3>
              <div v-if="activeSection === 'simple'" class="curve-series-controls" role="group" aria-label="曲線項目">
                <button v-for="item in simpleCurveItems" :key="item.key" type="button"
                  :class="[item.key, { active: curveSelection[item.key], suppressed: curveSelection[item.key] && !simpleCurveVisible[item.key] }]"
                  :aria-pressed="curveSelection[item.key]"
                  :title="item.key === 'quantity' && curveSelection.quantity && !simpleCurveVisible.quantity ? '獲利或 BuyHold 與回撤同時顯示時，口數不繪製' : ''"
                  @click="curveSelection[item.key] = !curveSelection[item.key]">{{ item.label }}</button>
              </div>
              <div ref="chartElement" class="chart" :class="{ 'full-height-chart': isFullHeightPlot }" role="img" :aria-label="`${selectedTab.label}，顯示${activeSection === 'simple' ? simpleCurveItems.filter(item => simpleCurveVisible[item.key]).map(item => item.label).join('、') : '資金、回撤'}`"></div>
            </div>

            <div v-else-if="activeView === 'periods'" class="chart-panel period-chart-panel">
              <div class="period-metric-switch" role="group" aria-label="績效比較項目">
                <button v-for="item in periodMetricOptions" :key="item.key" type="button"
                  :class="[item.key, { active: periodSelected.includes(item.key) }]"
                  :aria-pressed="periodSelected.includes(item.key)"
                  @click="togglePeriodMetric(item.key)">{{ item.label }}</button>
              </div>
              <div class="period-frequency-row">
                <div class="period-switch" role="radiogroup" aria-label="績效期間">
                  <button v-for="(label, key) in periodLabels" :key="key" type="button" role="radio"
                    :class="{ active: activePeriod === key }" :aria-checked="activePeriod === key"
                    @click="activePeriod = key">{{ label }}</button>
                </div>
                <button type="button" class="secondary-button" :disabled="!periodPlotData.rows.length" @click="downloadCsv('periods')">下載 CSV ↓</button>
              </div>
              <p v-if="!periodPlotData.rows.length" class="no-data">此區間沒有資料</p>
              <div ref="chartElement" class="chart full-height-chart" role="img"
                :aria-label="`${selectedTab.label}，${periodLabels[activePeriod]}，顯示${periodPlotData.series.map(item => item.label).join('、')}`"></div>
            </div>

            <div v-else-if="activeView === 'details' || activeView === 'buyhold'" class="panel table-panel">
              <div class="section-heading detail-heading">
                <div>
                  <span class="section-kicker">{{ activeView === 'buyhold' ? 'DAILY CLOSE' : 'TRADE LOG' }}</span>
                  <h3 v-if="activeView === 'buyhold'">{{ report.buy_hold.name }} · 每日收盤淨值</h3>
                  <p v-if="activeView === 'buyhold' && report.buy_hold.initial_capital != null">初始資金 {{ formatMoney(report.buy_hold.initial_capital) }} · {{ report.buy_hold.detail?.at(-1)?.action === '資金耗盡' ? '停止時淨值' : '最終淨值' }} {{ formatMoney(report.buy_hold.final_capital) }} · 截至 {{ report.buy_hold.end_date }}</p>
                  <p>共 {{ formatNumber(currentDetails.length, 0) }} 筆 · 每頁 {{ detailsPageSize }} 筆</p>
                </div>
                <nav v-if="detailsPageCount > 1" class="detail-pagination" aria-label="明細分頁">
                  <button type="button" :disabled="detailsPage === 1" @click="goToDetailsPage(detailsPage - 1)">上一頁</button>
                  <template v-for="(page, index) in detailPageNumbers" :key="page">
                    <span v-if="index > 0 && page > detailPageNumbers[index - 1] + 1" aria-hidden="true">…</span>
                    <button type="button" :class="{ active: detailsPage === page }" :aria-current="detailsPage === page ? 'page' : undefined" @click="goToDetailsPage(page)">{{ page }}</button>
                  </template>
                  <button type="button" :disabled="detailsPage === detailsPageCount" @click="goToDetailsPage(detailsPage + 1)">下一頁</button>
                </nav>
                <button type="button" class="secondary-button" :disabled="!currentDetails.length" @click="downloadCsv(activeView === 'buyhold' ? 'buyhold' : 'details')">下載 CSV ↓</button>
              </div>
              <p v-if="activeView === 'buyhold' && report.buy_hold.error" class="error-message" role="alert">{{ report.buy_hold.error }}</p>
              <div ref="detailTableElement" class="table-scroll detail-table" @scroll="rememberDetailScroll">
                <table><thead><tr><th class="numeric detail-index">#</th><th>{{ activeView === 'buyhold' ? '日期' : '時間' }}</th><th>標的</th><th>{{ activeView === 'buyhold' ? '動作' : '買賣' }}</th><th class="numeric">{{ activeView === 'buyhold' ? report.settings.buy_hold?.product_type === '股票' ? '股數' : '口數' : report.settings.mode === 'dynamic_compounding' && activeSection === 'compound' ? '倍率' : '口數' }}</th><th class="numeric">{{ activeView === 'buyhold' && report.settings.buy_hold?.product_type === '期貨' ? '收盤／結算價' : activeView === 'buyhold' ? '收盤價' : '價格' }}</th><th class="numeric">部位</th><th class="numeric">{{ activeView === 'buyhold' ? '當日損益' : '損益' }}</th><th class="numeric">累積淨值</th><th v-if="activeView !== 'buyhold'">訊號</th></tr></thead>
                  <tbody><tr v-for="(row, index) in pagedDetails" :key="activeView === 'buyhold' ? index : row.index"><td class="numeric detail-index">{{ (detailsPage - 1) * detailsPageSize + index + 1 }}</td><td>{{ row.timestamp }}</td><td>{{ row.symbol }}<span v-if="activeView === 'buyhold' && row.contract"> {{ row.contract }}</span></td><td><span class="side-pill" :class="activeView === 'buyhold' && isBuyHoldAdjustment(row.action) ? 'adjustment' : row.side === 'B' ? 'buy' : row.side === 'S' ? 'sell' : row.side === 'M' ? 'mark' : ''">{{ activeView === 'buyhold' ? row.action : row.side === 'B' ? '買進' : row.side === 'S' ? '賣出' : '—' }}</span></td><td class="numeric">{{ activeView === 'buyhold' ? formatBuyHoldQuantity(row.quantity) : report.settings.mode === 'dynamic_compounding' && activeSection === 'compound' ? `${formatQuantity(row.multiplier)}X` : formatQuantity(row.quantity) }}</td><td class="numeric">{{ formatNumber(row.price, 4) }}<span v-if="activeView === 'buyhold' && row.price_basis === '結算'" class="price-basis"> 結算</span></td><td class="numeric">{{ activeView === 'buyhold' ? formatBuyHoldQuantity(row.position) : formatQuantity(row.position) }}</td><td class="numeric" :class="{ negative: row.profit < 0 }">{{ formatNumber(row.profit, 0) }}</td><td>{{ formatNumber(row.equity, 0) }}</td><td v-if="activeView !== 'buyhold'">{{ row.action || '—' }}</td></tr><tr v-if="!currentDetails.length"><td :colspan="activeView === 'buyhold' ? 9 : 10" class="no-data">{{ activeView === 'buyhold' ? '沒有可用的每日收盤行情' : '此區間沒有交易' }}</td></tr></tbody>
                </table>
              </div>
            </div>


          </template>
        </section>
      </div>
    </main>

    <BuyHoldDialog v-if="buyHoldOpen" :settings="settings.buy_hold" @apply="applyBuyHold" @close="buyHoldOpen = false" />
  </div>
</template>
