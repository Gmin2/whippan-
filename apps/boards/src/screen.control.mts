/**
 * Does screen.ts measure the composition, or just the block library?
 *
 * It did not, at first. Everything materialised through blocks.ts inherits
 * corpus geometry by construction, so on 2026-09-01 a screen with every block
 * piled on one point, and another scattered with nothing aligned, both scored
 * a perfect 8 of 8. `alignment` was counting marks, and a pill's own rect and
 * label share an x by construction.
 *
 * Fixed by measuring alignment between BLOCKS and adding a cross-block text
 * collision check. Keep this file passing: if a bad case ever scores clean
 * again, the checks have drifted back to grading the library.
 *
 *   npx tsx apps/boards/src/screen.control.mts
 *
 * Everything materialised through blocks.ts inherits corpus geometry by
 * construction. If a deliberately awful placement still scores well, the
 * checks are grading the library and telling us nothing about the model.
 */
const { BLOCKS, blockByKey } = await import('./blocks.js')
const { scoreScreen, failing } = await import('./screen.js')

const size: [number, number] = [1920, 1080]
const accent = '#ff5c1a'
const build = (place: { block: string; x: number; y: number; opts?: any }[]) => {
  let stage: any = { size, scenes: [{ id: 's1', nodes: [] }] }
  const nodes: any[] = []
  for (const p of place) {
    const def = blockByKey(p.block)
    if (!def) continue
    nodes.push(...def.make({ stage, accent, x: p.x, y: p.y }, p.opts ?? {}))
    stage = { size, scenes: [{ id: 's1', nodes }] }
  }
  return nodes
}

const cases: Record<string, { block: string; x: number; y: number; opts?: any }[]> = {
  'the model, centred': [
    { block: 'surface', x: 960, y: 540 },
    { block: 'line-stack', x: 960, y: 400 },
    { block: 'pill', x: 960, y: 780 },
  ],
  'all piled on one point': [
    { block: 'surface', x: 960, y: 540 },
    { block: 'line-stack', x: 960, y: 540 },
    { block: 'pill', x: 960, y: 540 },
  ],
  'scattered, no alignment': [
    { block: 'pill', x: 271, y: 133 },
    { block: 'title-sub', x: 1488, y: 902 },
    { block: 'icon-tile', x: 703, y: 617 },
    { block: 'label-value', x: 1301, y: 244 },
  ],
  'half of it off the canvas': [
    { block: 'surface', x: 1850, y: 540 },
    { block: 'title-sub', x: 60, y: 1040 },
  ],
  'twelve blocks, no room': Array.from({ length: 12 }, (_, i) => ({
    block: 'pill', x: 200 + (i % 4) * 500, y: 150 + Math.floor(i / 4) * 380,
  })),
}

console.log(`${'case'.padEnd(24)}fails  scores`)
for (const [name, place] of Object.entries(cases)) {
  const nodes = build(place)
  const checks = scoreScreen(nodes, size)
  const brief = checks.map(c => `${c.key.slice(0, 4)} ${c.score.toFixed(1)}`).join('  ')
  console.log(`${name.padEnd(24)}${String(failing(checks)).padStart(3)}    ${brief}`)
}
