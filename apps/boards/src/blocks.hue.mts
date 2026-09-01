/**
 * Does deriving a lit ramp hold the source hue?
 *
 * It did not. Mixing toward white and black in RGB moves the channels at
 * different rates, so a field and its subject built from ONE colour landed in
 * two different 20-degree buckets and `screen.ts` flagged them, correctly.
 * shade() works in HSL now. Keep this passing: a lit palette that drifts is
 * the difference between one accent and a scene that looks like two.
 *
 *   npx tsx apps/boards/src/blocks.hue.mts
 */
const { BLOCKS } = await import('./blocks.js')
// shade is private, so exercise it through a block that uses it heavily
const def = BLOCKS.find(b => b.key === 'lit-field')!
const stage: any = { size: [1920, 1080], fps: 30, scenes: [] }

const bucket = (hex: string) => {
  const n = parseInt(hex.slice(1), 16)
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => v / 255)
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn
  if (d < 0.02) return -1
  let h = mx === r ? ((g - b) / d + 6) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
  return Math.floor((h * 60) / 20)
}

let bad = 0
for (const hue of ['#2f7df0', '#fa5d19', '#1eb583', '#d83008', '#7c8cf8', '#ddfb5c']) {
  const made = def.make({ stage, accent: hue, paper: '#05060a', x: 960, y: 540 }, { hue })
  const cols = made.flatMap((n: any) =>
    [n.fill, ...(n.gradient?.stops ?? []).map((s: any) => s.color)]).filter(Boolean)
  const want = bucket(hue)
  const off = cols.filter((c: string) => bucket(c) !== -1 && bucket(c) !== want)
  if (off.length) bad++
  console.log(`${hue}  bucket ${want}  derived ${cols.length}  off-hue ${off.length}` +
    (off.length ? `  ${off.slice(0, 3).join(' ')}` : ''))
}
console.log(bad ? `\n${bad} hues still drift` : '\nevery derived colour stays in its own hue bucket')
