import { defineStore } from 'pinia'
import { getPfo, runAnalysis, savePfo } from '../api'

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
      mdd_markers: []
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
      capital: 1000000,
      risk_free_rate: 0
    }
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
          capital: Number.isFinite(capital) && capital > 0 ? capital : 1000000,
          risk_free_rate: Number.isFinite(rf) ? rf : 0
        }
      } else {
        this.sharpeConfig = { capital: 1000000, risk_free_rate: 0 }
      }
    },
    async restoreProjectConfig(projectId) {
      this.strategyDescription = ''
      this.dateRangeConfig = { enabled: false, start: '', end: '' }
      this.sharpeConfig = { capital: 1000000, risk_free_rate: 0 }
      try {
        const xml = await getPfo(projectId)
        this.applySavedConfigFromXml(xml)
      } catch (e) {
        if (!/PFO not found/i.test(String(e?.message || ''))) {
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
          capital: Number(this.sharpeConfig?.capital || 1000000),
          mdd_count: 5,
          commission_per_trade: 0
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
        capital: Number.isFinite(capital) && capital > 0 ? capital : 1000000,
        risk_free_rate: Number.isFinite(riskFree) ? riskFree : 0
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
    async saveProjectPfo(projectId) {
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
        return savePfo(
          projectId,
          items,
          this.commissionConfig,
          this.strategyDescription,
          this.dateRangeConfig,
          this.sharpeConfig
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
        await this.saveProjectPfo(projectId)
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
