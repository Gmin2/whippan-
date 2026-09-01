/**
 * Does a glass panel's label ever run back under its dot?
 *
 * It did, on every label longer than about two words. The engine centres text
 * at x, and the block positioned it as if it were left anchored, so a long
 * label grew backwards into the dot. The row is laid out left to right now
 * and the card is sized to fit. Keep this passing.
 *
 *   npx tsx apps/boards/src/blocks.panel.mts
 */
const { BLOCKS } = await import('./blocks.js')
const def = BLOCKS.find(b => b.key === 'glass-panel')!
const stage: any = { size: [1920, 1080], fps: 30, scenes: [] }
const labels = ['Ok', 'Call Router', 'Arden — calm and considered',
                'Checking account permissions right now', 'Routing to: Billing skill']
let bad = 0
for (const title of labels) {
  const made: any[] = def.make({ stage, accent: '#2f7df0', paper: '#05060a', x: 960, y: 540 },
                               { title, tier: 4 })
  const card = made.find(n => n.id.startsWith('glass') && n.w > 100)
  const dot = made.find(n => n.gradient && n.w < 100)
  const txt = made.find(n => n.type === 'text')
  // engine centres text, so its left edge is x - width/2
  const w = title.length * txt.font.size * 0.52
  const textL = txt.x - w / 2
  const dotR = dot.x + dot.w / 2
  const textR = txt.x + w / 2
  const cardR = card.x + card.w / 2
  const clear = textL >= dotR && textR <= cardR
  if (!clear) bad++
  console.log(`${clear ? 'ok  ' : 'BAD '} "${title.slice(0, 30)}"  dotR ${dotR.toFixed(0)}` +
    ` textL ${textL.toFixed(0)}  textR ${textR.toFixed(0)} cardR ${cardR.toFixed(0)}`)
}
console.log(bad ? `\n${bad} labels collide` : '\nevery label clears the dot and stays inside the card')
