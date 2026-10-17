export function visibleSimpleCurveSeries(selection, hasBuyHold) {
  const visible = {
    profit: Boolean(selection.profit),
    buyHold: Boolean(hasBuyHold && selection.buyHold),
    drawdown: Boolean(selection.drawdown),
    quantity: Boolean(selection.quantity)
  }

  if (!visible.profit) visible.buyHold = false
  if (visible.profit && visible.drawdown) visible.quantity = false
  if (!Object.values(visible).some(Boolean)) visible.profit = true
  return visible
}

export function nextSimpleCurveSelection(selection, key, hasBuyHold) {
  const current = visibleSimpleCurveSeries(selection, hasBuyHold)
  if (!Object.hasOwn(current, key) || (key === 'buyHold' && !hasBuyHold)) return current
  const next = { ...current, [key]: !current[key] }
  if (key === 'profit' && !next.profit) next.buyHold = false
  if (key === 'buyHold' && next.buyHold) next.profit = true
  if (key === 'drawdown' && next.drawdown && next.profit) next.quantity = false
  if (key === 'quantity' && next.quantity && next.profit) next.drawdown = false
  return visibleSimpleCurveSeries(next, hasBuyHold)
}
