/**
 * Calibration for `screen.ts`, run from the repo root.
 *
 * A scorer nobody has calibrated is a scorer that measures its author's taste.
 * These are the two controls: the 331 authored scenes must sit near the top of
 * every check, and a screen doing everything the corpus says not to must fail
 * most of them. Three checks were respecified after the first run, when the
 * corpus scored 10% — they were applying corpus-wide statistics to individual
 * scenes, which is a different claim.
 *
 *   npx tsx apps/boards/src/screen.calibrate.mts
 */
import { scoreScreen, failing, type Check } from './screen.js'
import { readFileSync, readdirSync } from 'node:fs'

// runnable from the repo root or from apps/boards
const DOCS = process.cwd().endsWith('apps/boards') ? '../../docs' : 'docs'

const keys = ['alignment', 'collision', 'type scale', 'achromatic', 'one hue', 'ink', 'radius', 'margin']
const acc = new Map<string, number[]>(keys.map(k => [k, []]))
let scenes = 0, clean = 0

for (const f of readdirSync(DOCS).filter(n => n.endsWith('.stage.json'))) {
  const stage = JSON.parse(readFileSync(`${DOCS}/${f}`, 'utf8'))
  for (const sc of stage.scenes) {
    if (!sc.nodes?.length) continue
    scenes++
    const checks = scoreScreen(sc.nodes, stage.size)
    for (const c of checks) acc.get(c.key)!.push(c.score)
    if (!failing(checks)) clean++
  }
}
const med = (a: number[]) => a.sort((x, y) => x - y)[Math.floor(a.length / 2)]
console.log(`the corpus: ${scenes} scenes\n`)
console.log('check         median   below 0.6')
for (const k of keys) {
  const a = acc.get(k)!
  console.log(`${k.padEnd(14)}${med([...a]).toFixed(2).padStart(5)}   ` +
              `${((a.filter(v => v < 0.6).length / a.length) * 100).toFixed(0)}%`)
}
console.log(`\nscenes passing every check: ${clean} of ${scenes} (${(100*clean/scenes).toFixed(0)}%)`)

// negative control: everything the corpus says not to do
const bad = [
  { id: 'a', type: 'text', x: 137, y: 80, text: 'Welcome', color: '#000000', font: { size: 37 } },
  { id: 'b', type: 'text', x: 400, y: 300, text: 'Our Features', color: '#22cc44', font: { size: 19 } },
  { id: 'c', type: 'rect', x: 300, y: 500, w: 400, h: 120, radius: 7, fill: '#ee3311' },
  { id: 'd', type: 'rect', x: 900, y: 500, w: 300, h: 90, radius: 3, fill: '#3366ff' },
]
console.log('\nnegative control (off-scale type, pure black, four hues, odd radii):')
for (const c of scoreScreen(bad as any, [1920, 1080])) {
  console.log(`  ${c.key.padEnd(13)}${c.score.toFixed(2)}  ${c.detail}`)
}
