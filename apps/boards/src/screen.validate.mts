/**
 * Does screen.ts predict anything real?
 *
 * Result 2026-09-01 over 228 scenes: corr -0.218 between score and mae, and
 * scenes passing every check render at 28.8 mae against 48.9 for scenes
 * failing two or more. Weak as a correlation, real as a filter. Treat a
 * failing check as a warning worth acting on, never as a quality score.
 *
 * It scores a screen against corpus statistics, which is a proxy. conform
 * gives per-scene mae against the actual reference video frames, which is
 * ground truth. If the proxy is worth having, a scene that scores well should
 * render closer to its reference than one that scores badly.
 */
import { scoreScreen, failing } from './screen.js'
import { readFileSync } from 'node:fs'

const results = JSON.parse(readFileSync('../../out/conform/results.json', 'utf8'))
const pairs: { score: number; mae: number; fails: number }[] = []

for (const r of results) {
  if (!r.scenes) continue
  const stage = JSON.parse(readFileSync(`../../docs/${r.slug}.stage.json`, 'utf8'))
  for (const sc of r.scenes) {
    const node = stage.scenes.find((s: any) => s.id === sc.id)
    if (!node?.nodes?.length) continue
    const checks = scoreScreen(node.nodes, stage.size)
    const mean = checks.reduce((a, c) => a + c.score, 0) / checks.length
    // scenes above 200 mae are alignment drift, established in BASELINE.md:
    // they compare our render against entirely different reference footage,
    // so they carry no information about screen quality either way
    if (sc.mae > 200) continue
    pairs.push({ score: mean, mae: sc.mae, fails: failing(checks) })
  }
}

const pearson = (a: number[], b: number[]) => {
  const n = a.length
  const ma = a.reduce((x, y) => x + y, 0) / n, mb = b.reduce((x, y) => x + y, 0) / n
  let num = 0, da = 0, db = 0
  for (let i = 0; i < n; i++) {
    num += (a[i] - ma) * (b[i] - mb); da += (a[i] - ma) ** 2; db += (b[i] - mb) ** 2
  }
  return num / Math.sqrt(da * db)
}

console.log(`scenes paired with a reference: ${pairs.length}\n`)
console.log(`corr(screen score, mae)  : ${pearson(pairs.map(p => p.score), pairs.map(p => p.mae)).toFixed(3)}   (want NEGATIVE: better score, closer render)`)
console.log(`corr(checks failed, mae) : ${pearson(pairs.map(p => p.fails), pairs.map(p => p.mae)).toFixed(3)}   (want POSITIVE)`)

const clean = pairs.filter(p => !p.fails), dirty = pairs.filter(p => p.fails >= 2)
const mean = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length
console.log(`\npassing every check   : ${clean.length} scenes, mean mae ${mean(clean.map(p => p.mae)).toFixed(1)}`)
console.log(`failing 2 or more     : ${dirty.length} scenes, mean mae ${mean(dirty.map(p => p.mae)).toFixed(1)}`)
