export function formatProfitTick(value, compact = false) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  const absolute = Math.abs(number)
  const sign = number < 0 ? '-' : ''
  if (compact && absolute >= 1000) {
    const divisor = absolute >= 1_000_000_000 ? 1_000_000_000 : absolute >= 1_000_000 ? 1_000_000 : 1000
    const suffix = divisor === 1_000_000_000 ? 'B' : divisor === 1_000_000 ? 'M' : 'K'
    return `${sign}$${Number((absolute / divisor).toFixed(2))}${suffix}`
  }
  return `${sign}$${Math.round(absolute).toLocaleString('en-US')}`
}

export function profitAxisLayout(ticks, measureText, formatter = value => formatProfitTick(value, true)) {
  const values = ticks.length ? ticks : [0]
  return {
    gutter: Math.ceil(Math.max(...values.map(value => measureText(formatter(value)))) + 12)
  }
}

export function fitCurveAxis(axis, values, integerQuantity = false) {
  let minimum = axis.min ?? Infinity
  let maximum = axis.max ?? -Infinity
  for (const value of values) {
    const number = Number(value)
    if (!Number.isFinite(number)) continue
    minimum = Math.min(minimum, number)
    maximum = Math.max(maximum, number)
  }
  if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) {
    minimum = 0
    maximum = 1
  }
  const targetStep = (maximum - minimum) / 7 || Math.abs(maximum) / 7 || 1
  const power = 10 ** Math.floor(Math.log10(targetStep))
  const niceStep = [1, 2, 5, 10].map(factor => factor * power).find(value => value >= targetStep)
  const step = integerQuantity ? Math.max(1, niceStep) : niceStep
  const min = Math.floor(minimum / step) * step
  const max = Math.max(Math.ceil(maximum / step) * step, min + step)
  return { ...axis, min, max, interval: step, scale: false }
}
