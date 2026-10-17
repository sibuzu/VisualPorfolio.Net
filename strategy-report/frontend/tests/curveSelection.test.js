import assert from 'node:assert/strict'
import test from 'node:test'
import { nextSimpleCurveSelection, visibleSimpleCurveSeries } from '../src/curveSelection.js'

const keys = ['profit', 'buyHold', 'drawdown', 'quantity']
const active = selection => keys.filter(key => selection[key]).join('+')

test('all reachable simple curve selections match the nine allowed combinations', () => {
  const legal = new Set([
    'profit', 'profit+drawdown', 'profit+quantity', 'profit+buyHold',
    'profit+buyHold+drawdown', 'profit+buyHold+quantity',
    'drawdown', 'drawdown+quantity', 'quantity'
  ])
  const initial = visibleSimpleCurveSeries({}, true)
  const visited = new Set([active(initial)])
  const queue = [initial]
  while (queue.length) {
    const current = queue.shift()
    for (const key of keys) {
      const next = nextSimpleCurveSelection(current, key, true)
      const combination = active(next)
      assert.ok(legal.has(combination), `${active(current)} → ${key} → ${combination}`)
      if (!visited.has(combination)) {
        visited.add(combination)
        queue.push(next)
      }
    }
  }
  assert.deepEqual(visited, legal)
})

test('clicking an incompatible option replaces the prior option and never leaves a hidden selection', () => {
  const choose = (selected, key) => nextSimpleCurveSelection(selected, key, true)
  assert.equal(active(choose({ profit: true, quantity: true }, 'drawdown')), 'profit+drawdown')
  assert.equal(active(choose({ profit: true, drawdown: true }, 'quantity')), 'profit+quantity')
  assert.equal(active(choose({ drawdown: true, quantity: true }, 'profit')), 'profit+drawdown')
  assert.equal(active(choose({ drawdown: true }, 'buyHold')), 'profit+buyHold+drawdown')
  assert.equal(active(choose({ quantity: true }, 'buyHold')), 'profit+buyHold+quantity')
  assert.equal(active(choose({ profit: true, buyHold: true, drawdown: true }, 'profit')), 'drawdown')
})

test('BuyHold requires available data and an active profit curve', () => {
  assert.equal(active(visibleSimpleCurveSeries({ buyHold: true }, true)), 'profit')
  assert.equal(active(visibleSimpleCurveSeries({ buyHold: true }, false)), 'profit')
  assert.equal(active(nextSimpleCurveSelection({ profit: true }, 'buyHold', false)), 'profit')
  assert.equal(active(visibleSimpleCurveSeries({ profit: true, buyHold: true }, false)), 'profit')
  assert.equal(active(visibleSimpleCurveSeries({}, true)), 'profit')
})

test('without BuyHold data, every button sequence stays within the six available combinations', () => {
  const legal = new Set(['profit', 'profit+drawdown', 'profit+quantity',
    'drawdown', 'drawdown+quantity', 'quantity'])
  const visited = new Set(['profit'])
  const queue = [visibleSimpleCurveSeries({}, false)]
  while (queue.length) {
    for (const key of keys) {
      const next = nextSimpleCurveSelection(queue[0], key, false)
      const combination = active(next)
      assert.ok(legal.has(combination))
      if (!visited.has(combination)) {
        visited.add(combination)
        queue.push(next)
      }
    }
    queue.shift()
  }
  assert.deepEqual(visited, legal)
})
