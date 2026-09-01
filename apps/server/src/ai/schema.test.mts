/**
 * The structured-output plumbing, checked without a key.
 *
 * These are the failures that cost real money to find in production: a model
 * that answers in prose, one that names a block the library does not have, and
 * two tracks on one property quietly erasing each other.
 *
 *   cd apps/server && npx tsx src/ai/schema.test.mts
 */
process.env.ANTHROPIC_API_KEY = 'test-key'
const { runMotion, runScreen } = await import('./providers.js')

let sent: any = null
const reply = (content: any[]) => ({ ok: true, json: async () => ({ content }) }) as any

// 1. the request must force a tool call, and tool_use input must be used
globalThis.fetch = (async (_u: any, init: any) => {
  sent = JSON.parse(init.body)
  return reply([{ type: 'tool_use', name: 'propose_motion', input: {
    note: 'from the tool', tracks: [{ target: 'a', at: 0, keys: { opacity: [{ t: 0, v: 0 }, { t: 0.2, v: 1 }] } }],
  } }])
}) as any

const req = {
  prompt: 'fade it in', nodes: [{ id: 'a', type: 'text' }, { id: 'b', type: 'rect' }],
  scene: { id: 's1', dur: 2, index: 0, total: 3 }, tracks: [],
}
let r = await runMotion(req as any)
console.log('tool_choice sent  :', JSON.stringify(sent.tool_choice))
console.log('target enum       :', JSON.stringify(
  sent.tools[0].input_schema.properties.tracks.items.properties.target.enum))
console.log('note from tool    :', r.note, '| tracks', r.tracks.length)

// 2. a model that ignores the tool and writes prose must still work
globalThis.fetch = (async () => reply([{ type: 'text',
  text: 'Sure!\n```json\n{"note":"scraped","tracks":[{"target":"a","keys":{"y":[{"t":0,"v":10}]}}]}\n```' }])) as any
r = await runMotion(req as any)
console.log('prose fallback    :', r.note, '| tracks', r.tracks.length)

// 3. a track aimed outside the selection is dropped
globalThis.fetch = (async () => reply([{ type: 'tool_use', name: 'propose_motion', input: {
  note: 'x', tracks: [{ target: 'zzz', keys: { opacity: [{ t: 0, v: 1 }] } }] } }])) as any
r = await runMotion(req as any)
console.log('unaimed dropped   :', r.tracks.length === 0)

// 4. two tracks on one property get folded, and the problem is reported
globalThis.fetch = (async () => reply([{ type: 'tool_use', name: 'propose_motion', input: {
  note: 'x', tracks: [
    { target: 'a', at: 0, keys: { opacity: [{ t: 0, v: 0 }, { t: 0.2, v: 1 }] } },
    { target: 'a', at: 1, keys: { opacity: [{ t: 0, v: 1 }, { t: 0.2, v: 0 }] } },
  ] } }])) as any
r = await runMotion(req as any)
console.log('folded to         :', r.tracks.length, 'track,',
  JSON.stringify((r.tracks[0] as any).keys.opacity))
console.log('reported          :', r.problems?.[0]?.fixed, '-', r.problems?.[0]?.rule)

// 5. a block the library does not have cannot be placed
globalThis.fetch = (async (_u: any, init: any) => {
  sent = JSON.parse(init.body)
  return reply([{ type: 'tool_use', name: 'compose_screen', input: {
    note: 'x', place: [{ block: 'pill', x: 100, y: 100 }, { block: 'invented', x: 0, y: 0 }] } }])
}) as any
const sr = await runScreen({ prompt: 'p', size: [1920, 1080], accent: '#f00',
  blocks: [{ key: 'pill', name: 'Pill', blurb: '', slots: [
    { key: 'text', kind: 'text' }, { key: 'role', kind: 'role' }, { key: 'tier', kind: 'tier' },
  ] }] } as any)
// placement is a discriminated union now, one variant per block, so each
// variant pins its own block key with a const rather than sharing an enum
const variants = sent.tools[0].input_schema.properties.place.items.anyOf
console.log('block variants    :', JSON.stringify(variants.map((v: any) => v.properties.block.const)))
console.log('pill slot types   :', JSON.stringify(
  Object.fromEntries(Object.entries(variants[0].properties.opts.properties)
    .map(([k, v]: any) => [k, v.enum ? `enum(${v.enum.length})` : v.type]))))
console.log('invented dropped  :', sr.place.length === 1)
