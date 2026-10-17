const metrics = [
  { key: 'simple', label: '單口績效', color: '#0b7183' },
  { key: 'compound', label: '複合績效', color: '#1d4ed8' },
  { key: 'buyhold', label: 'BuyHold', color: '#7c3aed' },
  { key: 'drawdown', label: 'Drawdown', color: '#d77953' }
]
const performanceKeys = ['simple', 'compound', 'buyhold']

export function nextPeriodMetricSelection(selected, key) {
  if (!metrics.some(metric => metric.key === key)) return selected
  if (selected.includes(key)) {
    const remaining = selected.filter(item => item !== key)
    return remaining.length && remaining[0] !== 'drawdown' ? remaining : selected
  }
  if (key === 'drawdown') {
    const source = performanceKeys.find(item => selected.includes(item))
    return source ? [source, 'drawdown'] : selected
  }
  if (selected.includes('drawdown')) return [key, 'drawdown']
  const current = performanceKeys.filter(item => selected.includes(item))
  if (current.length < 2) return performanceKeys.filter(item => item === current[0] || item === key)
  const keep = { simple: 'compound', compound: 'buyhold', buyhold: 'simple' }[key]
  return performanceKeys.filter(item => item === keep || item === key)
}

export function withoutUnavailableBuyHold(selected) {
  const remaining = selected.filter(key => key !== 'buyhold')
  return remaining.length === 0 ? ['compound']
    : remaining[0] === 'drawdown' ? ['compound', 'drawdown'] : remaining
}

export function periodDrawdownLabel(selected) {
  const source = selected.find(key => key !== 'drawdown')
  return source === 'simple' ? '單口DD' : source === 'buyhold' ? 'BH DD' : '複合DD'
}

export function buildPeriodPlotData(report, period, selected) {
  const active = metrics.filter(metric => selected.includes(metric.key)).map(metric =>
    metric.key === 'drawdown' ? { ...metric, label: periodDrawdownLabel(selected) } : metric)
  const drawdownSource = selected.find(key => key !== 'drawdown') || 'compound'
  const rowsFor = key => report?.[key === 'buyhold' ? 'buy_hold' : key]?.periods?.[period] || []
  const sources = new Map([...new Set(active.map(metric => metric.key === 'drawdown' ? drawdownSource : metric.key))]
    .map(key => [key, new Map(rowsFor(key).map(row => [row.period, row]))]))
  const periods = new Set([...sources.values()].flatMap(source => [...source.keys()]))
  const rows = [...periods].sort().map(label => {
    const row = { period: label }
    for (const metric of active) {
      const source = sources.get(metric.key === 'drawdown' ? drawdownSource : metric.key)?.get(label)
      row[metric.key] = source == null ? null
        : metric.key === 'drawdown' ? Math.abs(source.mdd) : source.profit
    }
    return row
  })
  return { rows, series: active }
}
