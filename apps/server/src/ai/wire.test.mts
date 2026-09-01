/**
 * Both wires, checked without a key.
 *
 * The two protocols differ in exactly three places and every one of them is a
 * silent failure if wrong: the auth header, where the system prompt goes, and
 * whether tool arguments arrive as an object or a JSON string. A stub cannot
 * tell us a model writes good screens, but it can tell us we are not dropping
 * its answer on the floor.
 *
 *   cd apps/server && npx tsx src/ai/wire.test.mts
 */
process.env.ANTHROPIC_API_KEY = 'ant-key'
process.env.OPENAI_API_KEY = 'oai-key'
process.env.MOONSHOT_API_KEY = 'moon-key'
process.env.OPENAI_MODEL = 'gpt-5.6-sol'
process.env.MOONSHOT_MODEL = 'kimi-k3'

const { runMotion, capabilities, wireFor } = await import('./providers.js')

const req = (model: string) => ({
  prompt: 'fade it in', model,
  nodes: [{ id: 'a', type: 'text' }],
  scene: { id: 's1', dur: 2, index: 0, total: 3 },
  tracks: [],
})
const track = { target: 'a', at: 0, keys: { opacity: [{ t: 0, v: 0 }, { t: 0.2, v: 1 }] } }

let seen: { url: string; init: any } = { url: '', init: null }
const capture = (body: any) => (async (url: any, init: any) => {
  seen = { url: String(url), init: JSON.parse(init.body) }
  return { ok: true, json: async () => body } as any
})

console.log('routing')
for (const m of ['claude-opus-5', 'kimi-k3', 'gpt-5.6-sol', 'o4-mini']) {
  const w = wireFor(m)
  console.log(`  ${m.padEnd(14)}${w.proto.padEnd(10)}${w.keyName}`)
}

// anthropic wire: tool_use input is an object
globalThis.fetch = capture({ content: [{ type: 'tool_use', name: 'propose_motion',
  input: { note: 'anthropic', tracks: [track] } }] })
let r = await runMotion(req('claude-opus-5') as any)
console.log(`\nanthropic  ${r.note} | tracks ${r.tracks.length}`)
console.log(`  auth header  ${Object.keys(seen.init).includes('model') ? 'x-api-key' : '?'}`)
console.log(`  system       ${'system' in seen.init ? 'top-level field' : 'MISSING'}`)

// kimi: same protocol, different host and key
globalThis.fetch = capture({ content: [{ type: 'tool_use', name: 'propose_motion',
  input: { note: 'kimi', tracks: [track] } }] })
r = await runMotion(req('kimi-k3') as any)
console.log(`\nkimi       ${r.note} | tracks ${r.tracks.length}`)
console.log(`  host         ${new URL(seen.url).host}`)

// openai: arguments arrive as a JSON STRING, system as a message
globalThis.fetch = capture({ choices: [{ message: { tool_calls: [
  { function: { name: 'propose_motion', arguments: JSON.stringify({ note: 'openai', tracks: [track] }) } },
] } }] })
r = await runMotion(req('gpt-5.6-sol') as any)
console.log(`\nopenai     ${r.note} | tracks ${r.tracks.length}`)
console.log(`  host         ${new URL(seen.url).host}`)
console.log(`  system       ${seen.init.messages?.[0]?.role === 'system' ? 'as a message' : 'MISSING'}`)
console.log(`  tool_choice  ${JSON.stringify(seen.init.tool_choice)}`)
console.log(`  schema       ${seen.init.tools[0].function.parameters.properties.tracks.items.properties.target.enum}`)

// openai prose fallback
globalThis.fetch = capture({ choices: [{ message: {
  content: '```json\n{"note":"scraped","tracks":[{"target":"a","keys":{"y":[{"t":0,"v":9}]}}]}\n```' } }] })
r = await runMotion(req('gpt-5.6-sol') as any)
console.log(`\nopenai prose fallback: ${r.note} | tracks ${r.tracks.length}`)

// a model with no key must say so rather than call the wrong provider
delete process.env.OPENAI_API_KEY
try {
  await runMotion(req('gpt-5.6-sol') as any)
  console.log('\nmissing key: NOT CAUGHT')
} catch (e) {
  console.log(`\nmissing key: ${(e as Error).message}`)
}
process.env.OPENAI_API_KEY = 'oai-key'
console.log(`\ncapabilities models: ${capabilities().find(c => c.kind === 'screen')!.models.map(m => m.id).join(', ')}`)
