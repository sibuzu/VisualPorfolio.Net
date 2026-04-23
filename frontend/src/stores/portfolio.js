import { defineStore } from 'pinia'
import { getGseaGroup, runAnalysis, saveGseaGroup } from '../api'

function defaultDynamicCompoundingConfig() {
  return {
    initial_capital: 80000000,
    initial_ratio: 0.1,
    add_threshold_profit: 100000000,
    add_ratio: 0.15,
    rollback_amount: 20000000,
    rollback_percent: 0,
    max_multiple: 10
  }
}

function normalizeFileKey(v) {
  if (!v) return ''
  const s = String(v).trim().replace(/\\/g, '/')
  const parts = s.split('/')
  return (parts[parts.length - 1] || '').toLowerCase()
}

function normalizeColor(value, fallback = '#0a9396') {
  const raw = String(value || '').trim()
  if (!raw) return fallback
  const hexMatch = raw.match(/^#([0-9a-fA-F]{6})$/)
  if (hexMatch) return `#${hexMatch[1].toLowerCase()}`
  if (typeof document !== 'undefined') {
    const el = document.createElement('div')
    el.style.color = ''
    el.style.color = raw
    if (el.style.color) {
      document.body.appendChild(el)
      const rgb = getComputedStyle(el).color
      document.body.removeChild(el)
      const m = rgb.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/i)
      if (m) {
        const r = Number(m[1]).toString(16).padStart(2, '0')
        const g = Number(m[2]).toString(16).padStart(2, '0')
        const b = Number(m[3]).toString(16).padStart(2, '0')
        return `#${r}${g}${b}`
      }
    }
  }
  return fallback
}

export const usePortfolioStore = defineStore('portfolio', {
  state: () => ({
    equities: [],
    analysis: {
      summary: {},
      equity_curve: [],
      monthly: [],
      annual: [],
      weekly: [],
      position_analysis: [],
      win_loss: {},
      commission: {},
      diversity: {},
      mdd_markers: [],
      dynamic_compounding: {
        weekly: {},
        monthly: {}
      }
    },
    loading: false,
    error: '',
    updatingConfig: false,
    commissionConfig: null,
    strategyDescription: '',
    dateRangeConfig: {
      enabled: false,
      start: '',
      end: ''
    },
    sharpeConfig: {
      capital: 100,
      risk_free_rate: 0
    },
    dynamicCompoundingConfig: defaultDynamicCompoundingConfig()
  }),
  actions: {
    setFilesAsEquities(files) {
      const existingByFile = new Map(this.equities.map((x) => [x.filename, x]))
      this.equities = files
        .filter((f) => {
          const name = String(f.filename || '').toLowerCase()
          return name.endsWith('.sea') || name.endsWith('.gsea')
        })
        .map((f, i) => ({
          filename: f.filename,
          active: true,
          contract: existingByFile.get(f.filename)?.contract ?? 1,
          weight: existingByFile.get(f.filename)?.weight ?? 1,
          color: existingByFile.get(f.filename)?.color ?? ['#0a9396', '#bb3e03', '#005f73', '#ca6702'][i % 4],
          name: existingByFile.get(f.filename)?.name ?? f.filename,
          index: i
        }))
    },
    applySavedConfigFromXml(xmlText) {
      if (!xmlText || typeof DOMParser === 'undefined') return
      let doc
      try {
        doc = new DOMParser().parseFromString(xmlText, 'application/xml')
      } catch {
        return
      }

      const nodes = Array.from(doc.querySelectorAll('Equity'))

      if (nodes.length) {
        const saved = nodes.map((n) => ({
          index: Number(n.getAttribute('Index') ?? -1),
          filename: n.getAttribute('FileName') || '',
          color: n.getAttribute('Color') || '',
          weight: n.getAttribute('Weight') || '',
          contract: n.getAttribute('Count') || '1',
          active: (n.getAttribute('Active') || '1') !== '0',
          name: n.getAttribute('Name') || ''
        }))

        const byFile = new Map()
        for (const item of saved) {
          const raw = String(item.filename || '')
          if (raw) byFile.set(raw, item)
          const base = normalizeFileKey(raw)
          if (base) byFile.set(base, item)
        }
        this.equities = this.equities.map((eq) => {
          const eqRaw = String(eq.filename || '')
          const eqBase = normalizeFileKey(eqRaw)
          const sv = byFile.get(eqRaw) || byFile.get(eqBase)
          if (!sv) return eq
          const weight = Number(sv.weight)
          const contract = Number(sv.contract)
          return {
            ...eq,
            color: normalizeColor(sv.color, eq.color),
            weight: Number.isFinite(weight) ? weight : eq.weight,
            contract: Number.isFinite(contract) ? contract : eq.contract,
            active: typeof sv.active === 'boolean' ? sv.active : eq.active,
            name: sv.name || eq.name,
            index: Number.isFinite(sv.index) && sv.index >= 0 ? sv.index : eq.index
          }
        })
        this.equities.sort((a, b) => (a.index ?? 9999) - (b.index ?? 9999))
      }

      const cnode = doc.querySelector('CommissionConfig')
      if (cnode) {
        const cfg = {}
        const keys = [
          'ref_capital',
          'init_capital',
          'leverage',
          'fee_rate',
          'rebate_rate',
          'quarter_share_rate',
          'bonus_threshold1',
          'bonus_rate1',
          'bonus_threshold2',
          'bonus_rate2',
          'bonus_threshold3',
          'bonus_rate3',
          'bonus_threshold4',
          'bonus_rate4'
        ]
        for (const key of keys) {
          const raw = cnode.getAttribute(key)
          const n = Number(raw)
          if (raw != null && Number.isFinite(n)) {
            cfg[key] = n
          }
        }
        if (Object.keys(cfg).length) {
          this.commissionConfig = cfg
        }
      }

      const dnode = doc.querySelector('description')
      this.strategyDescription = dnode?.textContent || ''

      const rnode = doc.querySelector('DateRangeConfig')
      if (rnode) {
        const enabledRaw = String(rnode.getAttribute('enabled') ?? rnode.getAttribute('use_range') ?? '0')
        this.dateRangeConfig = {
          enabled: enabledRaw === '1' || enabledRaw.toLowerCase() === 'true',
          start: String(rnode.getAttribute('start') || ''),
          end: String(rnode.getAttribute('end') || '')
        }
      } else {
        this.dateRangeConfig = { enabled: false, start: '', end: '' }
      }

      const snode = doc.querySelector('SharpeConfig')
      if (snode) {
        const capital = Number(snode.getAttribute('capital'))
        const rf = Number(snode.getAttribute('risk_free_rate'))
        this.sharpeConfig = {
          capital: Number.isFinite(capital) && capital > 0 ? capital : 100,
          risk_free_rate: Number.isFinite(rf) ? rf : 0
        }
      } else {
        this.sharpeConfig = { capital: 100, risk_free_rate: 0 }
      }

      const dcnode = doc.querySelector('DynamicCompoundingConfig')
      if (dcnode) {
        this.setDynamicCompoundingConfig({
          initial_capital: Number(dcnode.getAttribute('initial_capital')),
          initial_ratio: Number(dcnode.getAttribute('initial_ratio')),
          add_threshold_profit: Number(dcnode.getAttribute('add_threshold_profit')),
          add_ratio: Number(dcnode.getAttribute('add_ratio')),
          rollback_amount: Number(dcnode.getAttribute('rollback_amount')),
          rollback_percent: Number(dcnode.getAttribute('rollback_percent')),
          max_multiple: Number(dcnode.getAttribute('max_multiple'))
        })
      } else {
        this.dynamicCompoundingConfig = defaultDynamicCompoundingConfig()
      }
    },
    applySavedConfigFromGroupJson(groupText) {
      if (!groupText) return
      let doc
      try {
        const cleaned = String(groupText).replace(/,(\s*[}\]])/g, '$1')
        doc = JSON.parse(cleaned)
        if (typeof doc === 'string') {
          doc = JSON.parse(doc)
        }
      } catch {
        return
      }
      const groupItems = Array.isArray(doc?.group) ? doc.group : []
      if (groupItems.length) {
        const saved = groupItems.map((item, i) => {
          const project = String(item?.project || '')
          const projectName = String(item?.project_name || '') || project
          const metadata = item?.metadata && typeof item.metadata === 'object' ? item.metadata : {}
          return {
            index: Number(i),
            filename: `${project}.sea`,
            color: String(metadata?.color || ''),
            weight: item?.weight,
            contract: item?.count,
            active: metadata?.active !== false,
            name: projectName
          }
        })

        const byFile = new Map()
        for (const item of saved) {
          const raw = String(item.filename || '')
          if (raw) byFile.set(raw, item)
          const base = normalizeFileKey(raw)
          if (base) byFile.set(base, item)
        }

        this.equities = this.equities.map((eq) => {
          const eqRaw = String(eq.filename || '')
          const eqBase = normalizeFileKey(eqRaw)
          const sv = byFile.get(eqRaw) || byFile.get(eqBase)
          if (!sv) return eq
          const weight = Number(sv.weight)
          const contract = Number(sv.contract)
          return {
            ...eq,
            color: normalizeColor(sv.color, eq.color),
            weight: Number.isFinite(weight) ? weight : eq.weight,
            contract: Number.isFinite(contract) ? contract : eq.contract,
            active: typeof sv.active === 'boolean' ? sv.active : eq.active,
            name: sv.name || eq.name,
            index: Number.isFinite(sv.index) && sv.index >= 0 ? sv.index : eq.index
          }
        })
        this.equities.sort((a, b) => (a.index ?? 9999) - (b.index ?? 9999))
      }

      const cfg = doc?.project_config && typeof doc.project_config === 'object' ? doc.project_config : {}
      if (cfg.commission_config && typeof cfg.commission_config === 'object') {
        this.commissionConfig = { ...cfg.commission_config }
      }
      this.strategyDescription = String(cfg.description || '')
      const dateRange = cfg.date_range_config && typeof cfg.date_range_config === 'object' ? cfg.date_range_config : {}
      this.dateRangeConfig = {
        enabled: !!dateRange.enabled,
        start: String(dateRange.start || ''),
        end: String(dateRange.end || '')
      }
      const sharpe = cfg.sharpe_config && typeof cfg.sharpe_config === 'object' ? cfg.sharpe_config : {}
      const capital = Number(sharpe.capital)
      const rf = Number(sharpe.risk_free_rate)
      this.sharpeConfig = {
        capital: Number.isFinite(capital) && capital > 0 ? capital : 100,
        risk_free_rate: Number.isFinite(rf) ? rf : 0
      }
      const dyn = cfg.dynamic_compounding_config && typeof cfg.dynamic_compounding_config === 'object'
        ? cfg.dynamic_compounding_config
        : {}
      this.setDynamicCompoundingConfig(dyn)
    },
    async restoreGseaGroupConfig(projectId) {
      this.strategyDescription = ''
      this.dateRangeConfig = { enabled: false, start: '', end: '' }
      this.sharpeConfig = { capital: 100, risk_free_rate: 0 }
      this.dynamicCompoundingConfig = defaultDynamicCompoundingConfig()
      try {
        const raw = await getGseaGroup(projectId)
        const text = String(raw || '')
        if (text.trim().startsWith('<')) {
          this.applySavedConfigFromXml(text)
        } else {
          this.applySavedConfigFromGroupJson(text)
        }
      } catch (e) {
        if (!/group\\.json not found/i.test(String(e?.message || ''))) {
          this.error = e.message || '載入策略設定失敗'
        }
      }
    },
    async analyze(projectId, options = {}) {
      this.loading = true
      this.error = ''
      try {
        const baseOptions = {
          risk_free_rate: Number(this.sharpeConfig?.risk_free_rate || 0),
          capital: Number(this.sharpeConfig?.capital || 100),
          mdd_count: 5,
          commission_per_trade: 0,
          dynamic_compounding: {
            initial_capital: Number(this.dynamicCompoundingConfig?.initial_capital || 80000000),
            initial_ratio: Number(this.dynamicCompoundingConfig?.initial_ratio || 0.1),
            add_threshold_profit: Number(this.dynamicCompoundingConfig?.add_threshold_profit || 100000000),
            add_ratio: Number(this.dynamicCompoundingConfig?.add_ratio || 0.15),
            rollback_amount: Number(this.dynamicCompoundingConfig?.rollback_amount || 20000000),
            rollback_percent: Number(this.dynamicCompoundingConfig?.rollback_percent || 0),
            max_multiple: Number(this.dynamicCompoundingConfig?.max_multiple || 10)
          }
        }
        if (this.commissionConfig) {
          baseOptions.commission_config = this.commissionConfig
        }
        const mergedOptions = {
          ...baseOptions,
          ...(options.options || {})
        }
        const activeDateRange = options.date_range || this._toDateRangePayload(this.dateRangeConfig)
        this.analysis = await runAnalysis(projectId, {
          equities: this.equities,
          date_range: activeDateRange,
          options: mergedOptions
        })
        const cfg = this.analysis?.commission?.config
        if (cfg && typeof cfg === 'object') {
          this.commissionConfig = { ...cfg }
        }
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.loading = false
      }
    },
    setCommissionConfig(config) {
      if (!config || typeof config !== 'object') return
      this.commissionConfig = { ...config }
    },
    setStrategyDescription(text) {
      this.strategyDescription = String(text || '')
    },
    setDateRangeConfig(config) {
      this.dateRangeConfig = {
        enabled: !!config?.enabled,
        start: String(config?.start || ''),
        end: String(config?.end || '')
      }
    },
    setSharpeConfig(config) {
      const capital = Number(config?.capital)
      const riskFree = Number(config?.risk_free_rate)
      this.sharpeConfig = {
        capital: Number.isFinite(capital) && capital > 0 ? capital : 100,
        risk_free_rate: Number.isFinite(riskFree) ? riskFree : 0
      }
    },
    setDynamicCompoundingConfig(config) {
      const defaults = defaultDynamicCompoundingConfig()
      const initialCapital = Number(config?.initial_capital)
      const initialRatio = Number(config?.initial_ratio)
      const addThresholdProfit = Number(config?.add_threshold_profit)
      const addRatio = Number(config?.add_ratio)
      const rollbackAmount = Number(config?.rollback_amount)
      const rollbackPercent = Number(config?.rollback_percent)
      const maxMultiple = Number(config?.max_multiple)
      this.dynamicCompoundingConfig = {
        initial_capital: Number.isFinite(initialCapital) && initialCapital > 0 ? initialCapital : defaults.initial_capital,
        initial_ratio: Number.isFinite(initialRatio) && initialRatio >= 0 ? initialRatio : defaults.initial_ratio,
        add_threshold_profit: Number.isFinite(addThresholdProfit) ? addThresholdProfit : defaults.add_threshold_profit,
        add_ratio: Number.isFinite(addRatio) && addRatio >= 0 ? addRatio : defaults.add_ratio,
        rollback_amount: Number.isFinite(rollbackAmount) && rollbackAmount >= 0 ? rollbackAmount : defaults.rollback_amount,
        rollback_percent: Number.isFinite(rollbackPercent) && rollbackPercent >= 0 ? rollbackPercent : defaults.rollback_percent,
        max_multiple: Number.isFinite(maxMultiple) && maxMultiple >= 0 ? maxMultiple : defaults.max_multiple
      }
    },
    _toDateRangePayload(config) {
      if (!config?.enabled) return { all: true }
      return {
        all: false,
        start: config.start || null,
        end: config.end || null
      }
    },
    async saveGseaGroup(projectId) {
      this.error = ''
      try {
        const items = this.equities.map((eq, i) => ({
          index: i,
          filename: eq.filename,
          color: eq.color,
          weight: Number(eq.weight || 0),
          contract: Number(eq.contract || 0),
          active: !!eq.active,
          name: eq.name || eq.filename
        }))
        return saveGseaGroup(
          projectId,
          items,
          this.commissionConfig,
          this.strategyDescription,
          this.dateRangeConfig,
          this.sharpeConfig,
          this.dynamicCompoundingConfig
        )
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async persistAndAnalyze(projectId, options = {}) {
      this.updatingConfig = true
      this.error = ''
      try {
        await this.saveGseaGroup(projectId)
        await this.analyze(projectId, options)
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.updatingConfig = false
      }
    }
  }
})
