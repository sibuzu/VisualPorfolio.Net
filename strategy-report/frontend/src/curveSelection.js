export function visibleSimpleCurveSeries(selection, hasBuyHold) {
  const visible = {
    profit: Boolean(selection.profit),
    buyHold: Boolean(hasBuyHold && selection.buyHold),
    drawdown: Boolean(selection.drawdown),
    quantity: Boolean(selection.quantity)
  }

  if (!Object.values(visible).some(Boolean)) visible.profit = true
  if ((visible.profit || visible.buyHold) && visible.drawdown) visible.quantity = false
  return visible
}
