import assert from 'node:assert/strict'
import test from 'node:test'
import { visibleSimpleCurveSeries } from '../src/curveSelection.js'

test('an empty selection draws profit', () => {
  assert.deepEqual(visibleSimpleCurveSeries({}, false), {
    profit: true, buyHold: false, drawdown: false, quantity: false
  })
  assert.deepEqual(visibleSimpleCurveSeries({}, true), {
    profit: true, buyHold: false, drawdown: false, quantity: false
  })
})

test('profit or BuyHold with drawdown suppresses quantity', () => {
  for (const primary of [{ profit: true }, { buyHold: true }, { profit: true, buyHold: true }]) {
    const visible = visibleSimpleCurveSeries({ ...primary, drawdown: true, quantity: true }, true)
    assert.equal(visible.quantity, false)
    assert.equal(visible.drawdown, true)
  }
  assert.deepEqual(visibleSimpleCurveSeries({ profit: true, drawdown: true, quantity: true }, false), {
    profit: true, buyHold: false, drawdown: true, quantity: false
  })
})

test('drawdown and quantity can share the chart without a primary series', () => {
  assert.deepEqual(visibleSimpleCurveSeries({ drawdown: true, quantity: true }, false), {
    profit: false, buyHold: false, drawdown: true, quantity: true
  })
})

test('BuyHold is hidden when it has no data', () => {
  assert.equal(visibleSimpleCurveSeries({ buyHold: true }, false).profit, true)
})
