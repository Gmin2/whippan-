/**
 * Does a pill label read on its own fill, whatever the accent is?
 *
 * It did not. `labelFor` returned white for anything called "accent", which
 * put white type on a lime pill at about 1.4:1. A light accent is exactly as
 * common as a dark one and the role name says nothing about which you have,
 * so the ink is picked by luminance now. Keep this passing.
 *
 *   npx tsx apps/boards/src/blocks.label.mts
 */
const { BLOCKS } = await import('./blocks.js')
const def = BLOCKS.find(b => b.key === 'pill')!
const stage: any = { size: [1920, 1080], fps: 30, scenes: [] }
const lin = (c: number) => { const x = c / 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4 }
const L = (h: string) => { const n = parseInt(h.slice(1), 16)
  return 0.2126 * lin((n >> 16) & 255) + 0.7152 * lin((n >> 8) & 255) + 0.0722 * lin(n & 255) }
const ratio = (a: string, b: string) => { const [x, y] = [L(a), L(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05) }

let bad = 0
for (const accent of ['#ddfb5c', '#fa5d19', '#2f7df0', '#ffffff', '#111111', '#1eb583']) {
  const made: any[] = def.make({ stage, accent, paper: '#eef1fb', x: 960, y: 540 },
                               { text: 'Start for free', role: 'accent' })
  const rect = made.find(n => n.type === 'rect')
  const txt = made.find(n => n.type === 'text')
  const r = ratio(txt.color, rect.fill)
  if (r < 4.5) bad++
  console.log(`accent ${accent}  label ${txt.color}  contrast ${r.toFixed(1)}:1  ${r >= 4.5 ? 'ok' : 'UNREADABLE'}`)
}
console.log(bad ? `\n${bad} accents give an unreadable label` : '\nevery accent gets a readable label')
