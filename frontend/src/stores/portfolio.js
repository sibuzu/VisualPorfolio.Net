import { defineStore } from 'pinia'
import { getPfo, runAnalysis, savePfo } from '../api'

function normalizeFileKey(v) {
  if (!v) return ''
  const s = String(v).trim().replace(/\\/g, '/')
  const parts = s.split('/')
  return (parts[parts.length - 1] || '').toLowerCase()
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
    strategyDescription: ''
  }),
  actions: {
    setFilesAsEquities(files) {
      const existingByFile = new Map(this.equities.map((x) => [x.filename, x]))
      this.equities = files
        .filter((f) => f.filename.endsWith('.srp') || f.filename.endsWith('.xrp'))
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
            color: sv.color || eq.color,
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
    },
    async restoreProjectConfig(projectId) {
      this.strategyDescription = ''
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
          risk_free_rate: 0,
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
        this.analysis = await runAnalysis(projectId, {
          equities: this.equities,
          date_range: options.date_range || { all: true },
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
        return savePfo(projectId, items, this.commissionConfig, this.strategyDescription)
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
