export function profitDrawdownSegments(curve, drawdowns) {
  if (!curve.length) return []
  const points = new Map(curve.map(row => [row.timestamp, row]))
  const lastTimestamp = curve[curve.length - 1].timestamp
  const segments = []

  for (const episode of drawdowns.slice(0, 5)) {
    const peak = points.get(episode.started_at)
    const bottom = points.get(episode.bottomed_at)
    if (!peak || !bottom) continue
    const end = episode.recovered_at && points.has(episode.recovered_at)
      ? episode.recovered_at : lastTimestamp
    segments.push([[episode.started_at, peak.equity], [end, peak.equity]])
    segments.push([[episode.started_at, bottom.equity], [episode.bottomed_at, bottom.equity]])
  }
  return segments
}
