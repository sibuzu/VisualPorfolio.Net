import assert from 'node:assert/strict'
import test from 'node:test'
import { fitCurveAxis, formatProfitTick, profitAxisLayout } from '../src/profitAxis.js'

test('profit axis always uses compact amounts and measures the longest tick', () => {
  const ticks = [-500000, 0, 1000000, 2000000, 3000000]
  const measure = label => label.length * 8
  assert.deepEqual(profitAxisLayout(ticks, measure), { gutter: 60 })
  assert.deepEqual(profitAxisLayout([0, 1, 2], measure, value => String(value)), { gutter: 20 })
  assert.equal(formatProfitTick(3000000), '$3,000,000')
  assert.equal(formatProfitTick(3000000, true), '$3M')
  assert.equal(formatProfitTick(-500000, true), '-$500K')
  assert.equal(formatProfitTick(2500000, true), '$2.5M')
})

test('single and dual curve axes cover their data with readable ticks', () => {
  assert.deepEqual(fitCurveAxis({}, [-500000, 3000000]), {
    min: -500000, max: 3000000, interval: 500000, scale: false
  })
  assert.deepEqual(fitCurveAxis({ min: 0 }, [0, 597600]), {
    min: 0, max: 600000, interval: 100000, scale: false
  })
  assert.deepEqual(fitCurveAxis({ min: 0, max: 4 }, [0, 1], true), {
    min: 0, max: 4, interval: 1, scale: false
  })
})
