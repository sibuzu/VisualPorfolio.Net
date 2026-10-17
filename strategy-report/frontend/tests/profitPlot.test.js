import assert from 'node:assert/strict'
import test from 'node:test'
import { profitDrawdownSegments } from '../src/profitPlot.js'

test('drawdown markers follow the C# peak and bottom lines', () => {
  const curve = [
    { timestamp: '2024-01-01 09:00:00', equity: 100 },
    { timestamp: '2024-01-02 09:00:00', equity: 70 },
    { timestamp: '2024-01-03 09:00:00', equity: 110 }
  ]
  assert.deepEqual(profitDrawdownSegments(curve, [{
    started_at: curve[0].timestamp, bottomed_at: curve[1].timestamp,
    recovered_at: curve[2].timestamp
  }]), [
    [[curve[0].timestamp, 100], [curve[2].timestamp, 100]],
    [[curve[0].timestamp, 70], [curve[1].timestamp, 70]]
  ])
})

test('an unrecovered peak line extends to the last plotted date', () => {
  const curve = [
    { timestamp: '2024-01-01 09:00:00', equity: 100 },
    { timestamp: '2024-01-02 09:00:00', equity: 70 },
    { timestamp: '2024-01-03 09:00:00', equity: 80 }
  ]
  assert.deepEqual(profitDrawdownSegments(curve, [{
    started_at: curve[0].timestamp, bottomed_at: curve[1].timestamp, recovered_at: null
  }])[0], [[curve[0].timestamp, 100], [curve[2].timestamp, 100]])
})
