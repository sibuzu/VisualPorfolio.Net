<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

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
const fileInput = ref(null)
const selectedFile = ref(null)
const report = ref(null)
const settingsDirty = ref(false)
const busy = ref(false)
const error = ref('')
const dragging = ref(false)
const activeTab = ref('overview')
const activeSection = ref('compound')
const activePeriod = ref('monthly')
const chartElement = ref(null)
let chart = null
let resizeObserver = null

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
  if (!file) return
  const ext = file.name.toLowerCase().split('.').pop()
  if (!['srp', 'sea'].includes(ext)) {
    error.value = '請選擇 .srp 或 .sea 檔案。'
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    error.value = '檔案不可超過 20 MiB。'
    return
  }
  selectedFile.value = file
  error.value = ''
  report.value = null
  settingsDirty.value = false
}

function handleFileInput(event) {
  chooseFile(event.target.files?.[0])
}

function handleDrop(event) {
  dragging.value = false
  chooseFile(event.dataTransfer?.files?.[0])
}

function messageFromDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(row => `${row.loc?.at(-1) || '欄位'}：${row.msg}`).join('；')
  return '計算失敗，請檢查檔案與設定。'
}

async function calculate() {
  if (!selectedFile.value || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const payload = { ...settings.value }
    if (!payload.date_start) delete payload.date_start
    if (!payload.date_end) delete payload.date_end
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('settings', JSON.stringify(payload))
    const response = await fetch('/api/report', { method: 'POST', body: form })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(messageFromDetail(data.detail))
    report.value = data
    settingsDirty.value = false
    activeTab.value = 'overview'
    await nextTick()
    renderChart()
  } catch (cause) {
    error.value = cause.message || '無法連線到報表服務。'
  } finally {
    busy.value = false
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
  chart.setOption({
    animationDuration: 350,
    grid: { left: 66, right: 70, top: 28, bottom: 55 },
    tooltip: { trigger: 'axis', valueFormatter: value => formatNumber(value, 2) },
    legend: { bottom: 4, data: ['淨值', '回撤'] },
    xAxis: { type: 'category', data: curve.map(row => row.timestamp.slice(0, 10)), boundaryGap: false, axisLabel: { hideOverlap: true } },
    yAxis: [
      { type: 'value', scale: true, axisLabel: { formatter: value => formatNumber(value, 0) }, splitLine: { lineStyle: { color: '#e6ecec' } } },
      { type: 'value', name: '回撤', min: 0, axisLabel: { formatter: value => formatNumber(value, 0) }, splitLine: { show: false } }
    ],
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 14, bottom: 33, borderColor: 'transparent' }],
    series: [
      { name: '淨值', type: 'line', data: curve.map(row => row.equity), showSymbol: false, smooth: false, lineStyle: { width: 2.5, color: '#0b7183' }, areaStyle: { color: 'rgba(11,113,131,.10)' } },
      { name: '回撤', type: 'line', yAxisIndex: 1, data: curve.map(row => row.drawdown), showSymbol: false, lineStyle: { width: 1.5, color: '#d77953' } }
    ]
  }, true)
  chart.resize()
}

watch([activeTab, activeSection, report], () => nextTick(renderChart))
watch(settings, () => { if (report.value) settingsDirty.value = true }, { deep: true })

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
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></div>
      <div class="brand-text"><strong>STRATEGY REPORT</strong><small>策略績效報表</small></div>
      <div class="header-tag">SRP · SEA</div>
    </header>

    <main>
      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow">策略分析工作台 <span class="eyebrow-line"></span> WEB EDITION</div>
          <h1>讓每一筆交易，<br><em>說清楚績效。</em></h1>
          <p>匯入策略報表，檢視單純績效與資金管理後的結果。從淨值曲線、回撤到逐筆交易，都有清楚的脈絡。</p>
        </div>
        <div class="hero-orbit" aria-hidden="true"><div class="orbit-inner"><svg viewBox="0 0 220 120"><path d="M0 95 L27 80 L48 91 L72 45 L96 59 L120 36 L140 52 L165 20 L184 37 L220 8"/></svg></div></div>
      </section>

      <div class="workspace">
        <aside class="sidebar">
          <section class="panel upload-panel">
            <div class="panel-heading"><span class="step-no">01</span><div><h2>匯入報表</h2><p>選擇策略檔案開始分析</p></div></div>
            <div class="drop-zone" :class="{ dragging }" @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false" @drop.prevent="handleDrop">
              <div class="upload-icon" aria-hidden="true">↥</div>
              <strong>{{ selectedFile ? selectedFile.name : '拖曳檔案到這裡' }}</strong>
              <span>{{ selectedFile ? `${selectedFile.size < 1024 ? '<1' : formatNumber(selectedFile.size / 1024, 0)} KB · 已選取` : '或點選下方按鈕選擇檔案' }}</span>
              <input ref="fileInput" type="file" accept=".srp,.sea" class="sr-only" tabindex="-1" @change="handleFileInput" />
              <button type="button" class="file-button" @click="fileInput?.click()">選擇 .srp / .sea 檔案</button>
            </div>
            <p class="privacy-note">檔案僅用於本次計算，不會儲存為專案。上限 20 MiB。</p>
          </section>

          <section class="panel settings-panel">
            <div class="panel-heading"><span class="step-no">02</span><div><h2>資金管理</h2><p>設定計算方式與日期範圍</p></div></div>
            <div class="form-stack">
              <label class="field"><span>管理模式</span><select v-model="settings.mode"><option v-for="option in modeOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
              <p v-if="settings.mode === 'backtest'" class="mode-hint">直接使用報表口數與報表初始資金；若報表未提供初始資金，採用 100,000。</p>
              <label v-else class="field"><span>初始資金</span><input v-model.number="settings.initial_capital" type="number" min="0.01" step="any" /></label>
              <label v-for="field in visibleFields" :key="field.key" class="field"><span>{{ field.label }}</span><input v-model.number="settings[field.key]" type="number" min="0" :step="field.step" /></label>
              <label v-if="settings.mode === 'target_leverage'" class="field"><span>槓桿資金</span><select v-model="settings.leverage_funds"><option value="cumulative">累加獲利</option><option value="fixed">固定資金</option></select></label>
              <template v-if="settings.mode !== 'backtest'"><label class="field"><span>最大口數 <small>0 = 無上限</small></span><input v-model.number="settings.maximum_quantity" type="number" min="0" step="any" /></label><label class="check-field"><input v-model="settings.integer_quantity" type="checkbox" /><span>口數為整數</span></label></template>
              <div class="field-divider"></div>
              <div class="date-title">分析區間</div>
              <div class="date-grid"><label class="field"><span>開始</span><input v-model="settings.date_start" type="date" /></label><label class="field"><span>結束</span><input v-model="settings.date_end" type="date" /></label></div>
              <p class="field-help">留空代表全部期間。區間開始前的交易會用於計算起始資金。</p>
            </div>
            <button type="button" class="run-button" :disabled="!selectedFile || busy" @click="calculate"><span>{{ busy ? '計算中…' : report ? '重新計算報表' : '產生績效報表' }}</span><span aria-hidden="true">↗</span></button>
            <p v-if="settingsDirty" class="field-help" role="status">設定已變更，按「重新計算報表」更新結果。</p>
            <p v-if="error" class="error-message" role="alert">{{ error }}</p>
          </section>
        </aside>

        <section class="results">
          <div v-if="!report" class="empty-state panel">
            <div class="empty-illustration" aria-hidden="true"><div class="empty-line one"></div><div class="empty-line two"></div><div class="empty-line three"></div></div>
            <span class="empty-kicker">READY WHEN YOU ARE</span>
            <h2>報表即將在此展開</h2>
            <p>先選擇 .srp 或 .sea 檔案，再按「產生績效報表」。</p>
          </div>

          <template v-else>
            <div class="results-header">
              <div><div class="eyebrow dark">分析結果 <span class="eyebrow-line"></span> {{ source.format.toUpperCase() }}</div><h2>{{ source.strategy }}</h2><p>{{ source.filename }} · {{ formatNumber(source.trade_count, 0) }} 筆交易 · {{ source.symbol }}</p></div>
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

    <footer><span>STRATEGY REPORT</span><span>從交易資料到清楚的決策依據</span></footer>
  </div>
</template>
