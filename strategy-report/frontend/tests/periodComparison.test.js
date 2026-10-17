import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildPeriodPlotData, nextPeriodMetricSelection, periodDrawdownLabel, withoutUnavailableBuyHold
} from '../src/periodComparison.js'

test('period buttons allow all nine listed combinations and keep at most two', () => {
  const legal = [
    ['simple'], ['simple', 'compound'], ['simple', 'buyhold'], ['simple', 'drawdown'],
    ['compound'], ['compound', 'buyhold'], ['compound', 'drawdown'],
    ['buyhold'], ['buyhold', 'drawdown']
  ]
  const legalKeys = new Set(legal.map(items => [...items].sort().join(',')))
  const reached = new Set()
  for (const first of ['simple', 'compound', 'buyhold']) {
    for (const second of ['simple', 'compound', 'buyhold', 'drawdown']) {
      let selected = nextPeriodMetricSelection(['compound'], first)
      if (selected.length > 1) selected = nextPeriodMetricSelection(selected, 'compound')
      selected = nextPeriodMetricSelection(selected, second)
      const key = [...selected].sort().join(',')
      assert.ok(legalKeys.has(key), selected.join(','))
      reached.add(key)
    }
  }
  assert.deepEqual([...reached].sort(), [...legalKeys].sort())
  assert.deepEqual(nextPeriodMetricSelection(['simple'], 'simple'), ['simple'])
  assert.deepEqual(nextPeriodMetricSelection(['simple', 'drawdown'], 'simple'), ['simple', 'drawdown'])
  assert.deepEqual(nextPeriodMetricSelection(['buyhold', 'drawdown'], 'drawdown'), ['buyhold'])
  assert.deepEqual(nextPeriodMetricSelection(['simple', 'compound'], 'buyhold'), ['simple', 'buyhold'])
  assert.deepEqual(nextPeriodMetricSelection(['compound', 'buyhold'], 'drawdown'), ['compound', 'drawdown'])
  assert.deepEqual(withoutUnavailableBuyHold(['buyhold', 'drawdown']), ['compound', 'drawdown'])
  assert.deepEqual(withoutUnavailableBuyHold(['buyhold']), ['compound'])
})

test('third selection keeps the specified metric or the selected drawdown', () => {
  for (const [selected, clicked, expected] of [
    [['simple', 'compound'], 'drawdown', ['simple', 'drawdown']],
    [['simple', 'buyhold'], 'drawdown', ['simple', 'drawdown']],
    [['compound', 'buyhold'], 'drawdown', ['compound', 'drawdown']],
    [['simple', 'drawdown'], 'compound', ['compound', 'drawdown']],
    [['compound', 'drawdown'], 'buyhold', ['buyhold', 'drawdown']],
    [['buyhold', 'drawdown'], 'simple', ['simple', 'drawdown']],
    [['simple', 'buyhold'], 'compound', ['compound', 'buyhold']],
    [['simple', 'compound'], 'buyhold', ['simple', 'buyhold']],
    [['compound', 'buyhold'], 'simple', ['simple', 'compound']]
  ]) {
    assert.deepEqual(nextPeriodMetricSelection(selected, clicked), expected,
      `${selected.join('+')} → ${clicked}`)
  }
  assert.equal(periodDrawdownLabel(nextPeriodMetricSelection(['simple', 'drawdown'], 'buyhold')), 'BH DD')
})

test('drawdown follows simple, compound, or BuyHold and stays positive', () => {
  const report = {
    simple: { periods: { annual: [
      { period: '2024', profit: 100, mdd: -15 }, { period: '2025', profit: 200, mdd: 25 }
    ] } },
    compound: { periods: { annual: [
      { period: '2024', profit: 1000, mdd: 150 }, { period: '2025', profit: 2000, mdd: 250 }
    ] } },
    buy_hold: { periods: { annual: [{ period: '2024', profit: 400, mdd: 80 }] } }
  }
  assert.deepEqual(buildPeriodPlotData(report, 'annual', ['simple', 'compound']).rows[0],
    { period: '2024', simple: 100, compound: 1000 })
  assert.deepEqual(buildPeriodPlotData(report, 'annual', ['simple', 'drawdown']).rows[0],
    { period: '2024', simple: 100, drawdown: 15 })
  assert.deepEqual(buildPeriodPlotData(report, 'annual', ['compound', 'drawdown']).rows[0],
    { period: '2024', compound: 1000, drawdown: 150 })
  const buyHoldDrawdown = buildPeriodPlotData(report, 'annual', ['buyhold', 'drawdown'])
  assert.deepEqual(buyHoldDrawdown.series.map(item => item.key), ['buyhold', 'drawdown'])
  assert.deepEqual(buyHoldDrawdown.rows, [{ period: '2024', buyhold: 400, drawdown: 80 }])
  assert.deepEqual(buildPeriodPlotData(report, 'annual', ['compound', 'buyhold']).rows, [
    { period: '2024', compound: 1000, buyhold: 400 },
    { period: '2025', compound: 2000, buyhold: null }
  ])
})

test('selected drawdown label follows its paired performance', () => {
  for (const [source, label] of [
    ['simple', '單口DD'], ['compound', '複合DD'], ['buyhold', 'BH DD']
  ]) {
    const selected = [source, 'drawdown']
    assert.equal(periodDrawdownLabel(selected), label)
    assert.equal(buildPeriodPlotData({}, 'annual', selected).series.at(-1).label, label)
  }
})
