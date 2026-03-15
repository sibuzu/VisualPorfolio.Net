import { defineStore } from 'pinia'
import { runAnalysis, savePfo } from '../api'

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
    error: ''
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
    async analyze(projectId, options = {}) {
      this.loading = true
      this.error = ''
      try {
        this.analysis = await runAnalysis(projectId, {
          equities: this.equities,
          date_range: options.date_range || { all: true },
          options: options.options || { risk_free_rate: 0, mdd_count: 5, commission_per_trade: 0 }
        })
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.loading = false
      }
    },
    async saveProjectPfo(projectId) {
      this.error = ''
      try {
        const items = this.equities.map((eq, i) => ({
          index: i,
          filename: eq.filename,
          color: eq.color,
          weight: eq.weight
        }))
        return savePfo(projectId, items)
      } catch (e) {
        this.error = e.message
        throw e
      }
    }
  }
})
