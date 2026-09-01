import { motionTool, screenTool, filmTool, type Tool } from './schema.js'
import { checkTracks, checkScenes, type Track } from './validate.js'
import type {
  Capability, FilmProposal, FilmRequest, ImageRequest, MotionProposal, MotionRequest,
  ModelOption, ScreenProposal, ScreenRequest, VectorRequest,
} from './types.js'

/**
 * The three model providers behind the prompt bar, matching what paper runs on:
 * QuiverAI's Arrow for vectors and Google's Nano Banana for images, plus Claude
 * for motion, which is the one that is actually ours.
 *
 * Keys are read here and never leave the process. A missing key is not an
 * error: the capability simply reports itself as not ready and the bar says so
 * rather than failing when you press the button.
 */

// overridable so a proxy, a regional endpoint or a test double can stand in
const ANTHROPIC = process.env.ANTHROPIC_BASE_URL ?? 'https://api.anthropic.com/v1/messages'
// the Responses endpoint, not chat completions: the gpt-5.6 line refuses
// function tools on /v1/chat/completions unless reasoning is off, and the
// reasoning is the reason to use it for layout
const OPENAI = process.env.OPENAI_BASE_URL ?? 'https://api.openai.com/v1/responses'
const OPENAI_EFFORT = process.env.OPENAI_REASONING_EFFORT ?? 'medium'
// Moonshot publish an Anthropic-shaped endpoint alongside their OpenAI one, so
// Kimi costs us a base url rather than a second implementation
const MOONSHOT = process.env.MOONSHOT_BASE_URL ?? 'https://api.moonshot.ai/anthropic/v1/messages'

/**
 * Model ids move faster than this file does, so they are overridable. Correct
 * one with an env var rather than a deploy if a provider renames it.
 */
const MODEL_IDS = {
  gpt: process.env.OPENAI_MODEL ?? 'gpt-5.6-sol',
  kimi: process.env.MOONSHOT_MODEL ?? 'kimi-k2.6',
}
const QUIVER = process.env.QUIVERAI_BASE_URL ?? 'https://api.quiver.ai/v1/svgs/generations'
const GEMINI = process.env.GEMINI_BASE_URL
  ?? 'https://generativelanguage.googleapis.com/v1beta/models'

const key = (name: string) => process.env[name]?.trim() || null

// the quiver key has been written both ways in practice; accept either rather
// than have the capability report itself not ready next to a key that is set
const quiverKey = () => key('QUIVERAI_API_KEY') ?? key('QUIVER_API_KEY')
// likewise Kimi: the vendor is Moonshot but the key is usually written KIMI_
const moonshotKey = () => key('MOONSHOT_API_KEY') ?? key('KIMI_API_KEY')

export function capabilities(): Capability[] {
  return [
    // the three text kinds share one model list, since any of them can run on
    // whichever providers this deployment holds a key for
    { kind: 'motion', provider: providerLabel(), ready: textReady(), reason: textReason(), models: textModels() },
    { kind: 'film', provider: providerLabel(), ready: textReady(), reason: textReason(), models: textModels() },
    { kind: 'screen', provider: providerLabel(), ready: textReady(), reason: textReason(), models: textModels() },
    {
      kind: 'image',
      provider: 'Google',
      ready: !!key('GEMINI_API_KEY'),
      reason: key('GEMINI_API_KEY') ? undefined : 'set GEMINI_API_KEY on the server',
      models: [
        { id: 'gemini-3.1-flash-image', label: 'Nano Banana 2', note: 'the workhorse' },
        { id: 'gemini-3-pro-image', label: 'Nano Banana Pro', note: '4K, legible text' },
        { id: 'gemini-3.1-flash-lite-image', label: 'Nano Banana 2 Lite', note: 'cheapest' },
      ],
    },
    {
      kind: 'vector',
      provider: 'QuiverAI',
      ready: !!quiverKey(),
      reason: quiverKey() ? undefined : 'set QUIVERAI_API_KEY on the server',
      models: [
        { id: 'arrow-1.1', label: 'Arrow 1.1', note: 'general purpose' },
        { id: 'arrow-1.1-max', label: 'Arrow 1.1 Max', note: 'precision, slower' },
      ],
    },
  ]
}

class Missing extends Error {}
export const isMissingKey = (e: unknown) => e instanceof Missing

function need(name: string): string {
  const v = key(name)
  if (!v) throw new Missing(`${name} is not set on the server`)
  return v
}

/**
 * Which wire a model id speaks, and which key opens it.
 *
 * Only two protocols exist here. Anthropic Messages covers Claude and Kimi
 * both, because Moonshot publish an Anthropic-shaped endpoint and their docs
 * say to migrate by swapping base_url and key alone. OpenAI is the one that
 * genuinely needed a second implementation.
 */
type Wire = {
  proto: 'anthropic' | 'openai'
  url: string
  keyName: string
  /** resolves the key, since some providers are written under several names */
  auth: () => string | null
}

export function wireFor(model: string): Wire {
  const m = model.toLowerCase()
  if (m.startsWith('kimi') || m.startsWith('moonshot')) {
    return { proto: 'anthropic', url: MOONSHOT, keyName: 'KIMI_API_KEY', auth: moonshotKey }
  }
  if (m.startsWith('gpt') || /^o\d/.test(m)) {
    return { proto: 'openai', url: OPENAI, keyName: 'OPENAI_API_KEY', auth: () => key('OPENAI_API_KEY') }
  }
  return {
    proto: 'anthropic', url: ANTHROPIC, keyName: 'ANTHROPIC_API_KEY',
    auth: () => key('ANTHROPIC_API_KEY'),
  }
}

/** every model the deployment has a key for, best first */
function textModels(): ModelOption[] {
  const out: ModelOption[] = []
  if (key('ANTHROPIC_API_KEY')) {
    out.push(
      { id: 'claude-sonnet-5', label: 'Claude Sonnet 5', note: 'fast enough to iterate', provider: 'Anthropic' },
      { id: 'claude-opus-5', label: 'Claude Opus 5', note: 'better taste, slower', provider: 'Anthropic' },
    )
  }
  if (key('OPENAI_API_KEY')) {
    out.push({ id: MODEL_IDS.gpt, label: 'GPT-5.6 Sol', note: 'strong on layout', provider: 'OpenAI' })
  }
  if (moonshotKey()) {
    out.push({ id: MODEL_IDS.kimi, label: 'Kimi K2.6', note: 'cheapest per film', provider: 'Moonshot' })
  }
  return out
}

const textReady = () =>
  !!(key('ANTHROPIC_API_KEY') || key('OPENAI_API_KEY') || moonshotKey())

/** the first model we have a key for, used when the caller names none */
function defaultModel(): string {
  const m = textModels()[0]
  if (!m) throw new Missing('no model key is set on the server')
  return m.id
}

const providerLabel = () => {
  const names: string[] = []
  if (key('ANTHROPIC_API_KEY')) names.push('Anthropic')
  if (key('OPENAI_API_KEY')) names.push('OpenAI')
  if (moonshotKey()) names.push('Moonshot')
  return names.join(' / ') || 'Anthropic'
}

const textReason = () =>
  textReady() ? undefined : 'set ANTHROPIC_API_KEY, OPENAI_API_KEY or MOONSHOT_API_KEY on the server'

/**
 * The contract the model has to write against. This is the same set of rules
 * AUTHORING states, compressed to what actually bites: the silent failures.
 */
const CONTRACT = `You write whippan animation tracks. A track is JSON:

  { "target": "<node id>", "at": <scene-local seconds>, "keys": { "<prop>": [{ "t": <relative>, "v": <number>, "ease": <ease> }] } }

Rules that fail silently if broken, so never break them:
- "at" is scene-local and shifts the whole track. Key "t" is RELATIVE to "at".
- ONE track per node per property. A later track REPLACES an earlier one.
- "x" and "y" keys are OFFSETS from the node's stage position. Every other
  property is absolute.
- Only use node ids that were given to you.

Shorthands you may use instead of raw keys, one per track:
- "enter": one of pop, rise-fade, drop, slide-left, slide-right, spring-in, fade
- "reveal": { "unit": "word"|"glyph"|"type"|"scramble", "stagger": <s>, "dur": <s> }

Ease is a name ("outCubic", "inCubic", "inOutCubic", "spring"), four bezier
numbers, or { "spring": [damping, cycles] }.

Timing measured off 29 launch films, treat it as the house style:
- in-scene motion 140-280ms. Past 350ms reads slow.
- entrances ease out, 200-280ms, starting ~80ms in.
- exits ease in, ~150ms.
- text travel under 40px. Stagger between siblings 40-80ms.

Reply with ONLY a JSON object, no prose and no code fence:
{ "note": "<one short line on what you did>", "tracks": [ ...tracks... ] }`

export async function runMotion(req: MotionRequest): Promise<MotionProposal> {
  const model = req.model || defaultModel()

  const brief = [
    `Scene "${req.scene.id}", ${req.scene.dur}s long, beat ${req.scene.index + 1} of ${req.scene.total}.`,
    `Nodes selected:\n${JSON.stringify(req.nodes, null, 1)}`,
    req.tracks.length
      ? `Their current tracks, which you are editing:\n${JSON.stringify(req.tracks, null, 1)}`
      : 'These nodes have no motion yet.',
    `What the director asked for: ${req.prompt}`,
  ].join('\n\n')

  const parsed = await callTool(model, CONTRACT, brief, motionTool(req), 2000)
  const raw = Array.isArray(parsed.tracks) ? parsed.tracks as Record<string, unknown>[] : []
  const allowed = new Set(req.nodes.map(n => n.id))

  // a track aimed at a node that was not in the selection would animate
  // something the director never pointed at
  const aimed = raw.filter(t => typeof t.target === 'string' && allowed.has(t.target as string))
  // the schema cannot say "one track per node per property"; this can
  const { tracks, problems } = checkTracks(aimed as Track[], {
    size: undefined, dur: req.scene.dur,
  })

  return {
    note: typeof parsed.note === 'string' ? parsed.note : 'proposed motion',
    tracks: tracks as Record<string, unknown>[],
    problems: problems.length ? problems : undefined,
  }
}

/**
 * Ask for one tool call and take its input as the answer.
 *
 * `tool_choice` makes the shape non-optional, which removes the two failure
 * modes prose prompting cannot: a reply wrapped in a sentence, and an enum
 * value the library cannot materialise. Kimi K3 speaks the same Messages API,
 * so this covers both models. If a deployment's model returns prose anyway we
 * still scrape it, rather than failing a request we could have honoured.
 */
async function callTool(
  model: string, system: string, brief: string, tool: Tool, maxTokens: number,
): Promise<Record<string, unknown>> {
  const wire = wireFor(model)
  const auth = wire.auth()
  if (!auth) throw new Missing(`${wire.keyName} is not set on the server`)
  return wire.proto === 'openai'
    ? callOpenAi(wire.url, auth, model, system, brief, tool, maxTokens)
    : callAnthropic(wire.url, auth, model, system, brief, tool, maxTokens)
}

async function callAnthropic(
  url: string, auth: string, model: string,
  system: string, brief: string, tool: Tool, maxTokens: number,
): Promise<Record<string, unknown>> {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': auth,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      system,
      messages: [{ role: 'user', content: brief }],
      tools: [tool],
      tool_choice: { type: 'tool', name: tool.name },
    }),
  })
  if (!res.ok) throw new Error(`anthropic ${res.status}: ${(await res.text()).slice(0, 300)}`)

  const body = await res.json() as {
    content?: { type: string; text?: string; name?: string; input?: unknown }[]
  }
  const call = (body.content ?? []).find(c => c.type === 'tool_use' && c.name === tool.name)
  if (call?.input) return call.input as Record<string, unknown>
  const text = (body.content ?? []).filter(c => c.type === 'text').map(c => c.text).join('')
  return parseJsonObject(text)
}

/**
 * The same call over the OpenAI Responses API.
 *
 * Chat completions was the obvious choice and it does not work: the gpt-5.6
 * line returns 400 for function tools there unless `reasoning_effort` is
 * 'none', and reasoning is exactly what we want it spending on layout. Only a
 * live call surfaced that.
 *
 * Deliberately NOT `text.format: json_schema` with strict on. Strict mode
 * makes every property required and forbids `minItems`, so our schemas would
 * need a second, provider-specific shape and the two would drift. Function
 * calling takes the schema we already have, and output is validated after.
 *
 * Three shape differences from the Anthropic wire, all of them silent if
 * wrong: the system prompt is `instructions`, a function tool is flat rather
 * than nested under `function`, and arguments arrive as a JSON string.
 */
async function callOpenAi(
  url: string, auth: string, model: string,
  system: string, brief: string, tool: Tool, maxTokens: number,
): Promise<Record<string, unknown>> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${auth}` },
    body: JSON.stringify({
      model,
      instructions: system,
      input: brief,
      reasoning: { effort: OPENAI_EFFORT },
      // reasoning tokens come out of this budget too, so leave it room
      max_output_tokens: maxTokens * 4,
      tools: [{
        type: 'function',
        name: tool.name,
        description: tool.description,
        parameters: tool.input_schema,
      }],
      tool_choice: { type: 'function', name: tool.name },
    }),
  })
  if (!res.ok) throw new Error(`openai ${res.status}: ${(await res.text()).slice(0, 300)}`)

  const body = await res.json() as {
    output?: { type?: string; name?: string; arguments?: string;
               content?: { type?: string; text?: string }[] }[]
    output_text?: string
  }
  const call = (body.output ?? []).find(o => o.type === 'function_call' && o.name === tool.name)
  // arguments are a JSON string here, not an object as on the Anthropic wire
  if (call?.arguments) return JSON.parse(call.arguments) as Record<string, unknown>
  const text = body.output_text
    ?? (body.output ?? []).flatMap(o => o.content ?? []).map(c => c.text).join('')
  return parseJsonObject(text ?? '')
}

/** models like to wrap json in a fence or a sentence however firmly you ask */
function parseJsonObject(text: string): Record<string, unknown> {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/)
  const raw = fenced ? fenced[1] : text
  const start = raw.indexOf('{')
  const end = raw.lastIndexOf('}')
  if (start < 0 || end <= start) throw new Error(`no json in the reply: ${text.slice(0, 200)}`)
  return JSON.parse(raw.slice(start, end + 1)) as Record<string, unknown>
}

/** a data url, so the caller can drop it straight into an image node */
/**
 * The contract for composing a screen.
 *
 * The model chooses WHICH blocks and WHERE. It never sets a font size, a radius
 * or a padding, because the block library already holds the ratios measured off
 * the 31 films. That is the whole design: the model cannot emit bad geometry
 * because it is not allowed to express geometry.
 */
const SCREEN_CONTRACT = `You compose a screen for a product launch video by placing BLOCKS.

You never write font sizes, radii, padding or colours. The block library holds
those, measured off 31 real launch films. You choose which blocks, where they
sit, and what words go in them.

Reply with ONLY a JSON object, no prose and no code fence:
{
  "note": "<one short line on what you made>",
  "bg": "<#rrggbb, optional>",
  "place": [ { "block": "<key>", "x": <px>, "y": <px>, "opts": { ... } } ]
}

What the corpus does, and you should too:
- A launch video shows the PRODUCT'S OWN UI: an editor, a terminal, a browser,
  a dashboard. Not a marketing page. There are no testimonials, pricing tables,
  logo walls or feature grids anywhere in the corpus.
- 12.7% of all nodes sit exactly on the canvas centre line. Centre things.
- BLOCKS ON ONE SCREEN SHARE AN X. Give at least half of them the same x, and
  usually that x is the centre. There is no column grid in the corpus, just a
  centre line and one or two column anchors per scene. Blocks at 640, 900 and
  1180 read as scattered even when each one is fine.
- Text colour comes from the block and follows the background, so pick "bg"
  deliberately: a dark bg gets light type automatically. Do not mix a dark bg
  into a light film without a reason.
- Margins are generous: keep content inside the middle 80% horizontally and the
  middle 70% vertically. These are posters with a UI in the middle.
- ONE THOUGHT PER SCENE. Three sentences is two scenes. Two to four blocks is a
  screen; eight is a mess.
- One accent. About one text node in five carries it, no more.
- Copy is short and concrete. No taglines that could belong to any product.

Counters, rolling numbers and alternating headlines are the "swap-slot" block,
never one line of text you intend to animate.

TWO REGISTERS. Pick one per scene and do not mix them.

PRODUCT — the default, and what most beats want. The product's own UI on
light paper, composed from pill, title-sub, line-stack, label-value,
icon-tile, glyph-label, swap-slot, surface. Everything above applies.

LIT — a dark scene about ONE glowing thing. Use it when the subject has no
UI to show: a voice, an agent, a model, a capability, an identity. Never for
a feature list or a screenshot beat.
- "lit-field" goes FIRST in "place" and covers the frame. Every lit scene
  needs exactly one; without it the scene is black paper, not lit space.
- "bg" must be near black. "#05060a" is the one the field falls to.
- ONE hue for the whole scene: pass the SAME hex to every block's "hue".
  Two hues in a lit scene reads as two scenes.
- "lit-subject" is the thing the beat is about. At most one. Give it a
  "title" only when the name matters.
- "glass-panel" stacks into a list, one per row, all sharing an x.
- "meter" is a live waveform: voice, listening, level. Not decoration.
`

export async function runScreen(req: ScreenRequest): Promise<ScreenProposal> {
  const model = req.model || defaultModel()
  const [w, h] = req.size

  const brief = [
    `Canvas ${w} x ${h}. Centre is ${Math.round(w / 2)}, ${Math.round(h / 2)}.`,
    `The film's accent is ${req.accent}; a block with a role of "accent" takes it.`,
    `Blocks you may place:\n${req.blocks
      // slots carry their kind now; join(', ') on the objects printed
      // "[object Object]" and the model was guessing names off the blurb
      .map(b => `  ${b.key} - ${b.blurb}\n    opts: ${b.slots.map(sl => `${sl.key} (${sl.kind})`).join(', ')}`)
      .join('\n')}`,
    `What the director asked for: ${req.prompt}`,
    // a second pass is told what was measured, not asked to guess again
    req.feedback
      ? `Your last attempt was measured against the corpus and failed these checks. Fix them:\n${req.feedback}`
      : '',
  ].filter(Boolean).join('\n\n')

  const parsed = await callTool(model, SCREEN_CONTRACT, brief, screenTool(req), 2000)
  const known = new Set(req.blocks.map(b => b.key))
  const place = Array.isArray(parsed.place) ? parsed.place as ScreenProposal['place'] : []

  return {
    note: typeof parsed.note === 'string' ? parsed.note : 'proposed screen',
    bg: typeof parsed.bg === 'string' ? parsed.bg : undefined,
    // a block the client cannot materialise would silently vanish, so drop it
    // here where it can be counted rather than there where it cannot
    place: place.filter(p => p && known.has(p.block)),
  }
}

/**
 * A whole film in one pass.
 *
 * This is the claim the two-layer format exists to make. The model writes a
 * sequence of beats, each one a set of blocks with an entrance, plus the cut
 * between them. It still never expresses geometry or easing curves: blocks own
 * the layout and the named entrances own the timing, both measured off the same
 * 31 films. What is left for the model is the thing it is actually good at,
 * which is deciding what the film says and in what order.
 */
const FILM_CONTRACT = `You write a product launch film as a sequence of scenes.

You never write font sizes, radii, colours, easing curves or keyframes. Blocks
own the layout and named entrances own the timing, both measured off 31 real
launch films. You choose the beats, the words, the blocks, and the cuts.

Reply with ONLY a JSON object, no prose and no code fence:
{
  "note": "<one short line on the film>",
  "scenes": [
    {
      "id": "s1",
      "dur": <seconds>,
      "bg": "<#rrggbb>",
      "note": "<one line describing the beat, for the storyboard card>",
      "transition": "<how this scene ARRIVES; omit on the first. rarely a cut>",
      "place": [ { "block": "<key>", "x": <px>, "y": <px>, "opts": {...},
                   "enter": "<preset>", "at": <scene-local seconds> } ]
    }
  ]
}

The shape of a launch film, from the corpus:
- 5 to 9 scenes. Content beats dwell 1.5-3.5s, punctuation beats 0.5-1.5s, and
  the end card gets at least 2s. The whole thing runs 15-25s.
- ONE THOUGHT PER SCENE. Two to four blocks. Three sentences is two scenes.
- BLOCKS IN ONE SCENE SHARE AN X. Give at least half of them the same x, and
  usually that x is the centre. There is no column grid in the corpus, just a
  centre line and one or two column anchors per scene.
- Text colour comes from the block and follows the background, so pick "bg"
  deliberately. Keep one paper for the film and change it only to mark a turn.
- It opens on the product doing something, not on a title card.
- TWO REGISTERS, one per scene, never mixed. PRODUCT is the default: the
  product's own UI on light paper. LIT is a dark scene about one glowing
  thing, for a subject with no UI to show — a voice, an agent, a model, an
  identity. A film may use both, but a lit run should be a run, not one
  stray dark beat.
- In a LIT scene: "lit-field" goes FIRST in "place" and covers the frame,
  "bg" is near black ("#05060a"), and the SAME hue hex goes to every
  block's "hue" slot. At most one "lit-subject". "glass-panel" stacks into
  a list sharing an x. "meter" is a live waveform, not decoration.
- It shows the PRODUCT'S OWN UI: an editor, a terminal, a browser, a dashboard.
  There are no testimonials, pricing tables or logo walls anywhere in the corpus.
- The last scene is the end card: a wordmark, optionally a tagline under it and
  a pill. This is the most standardised scene in the corpus.
- CUTS ARE RARE. 8 of 29 reference films have ZERO hard cuts across their whole
  run; higgsfield goes 70 seconds and replit 76 without one. Cuts punctuate a
  chapter change; everything inside a chapter is a dissolve, a settle, a rise or
  a morph. Reach for "cut" only at a real act boundary, and prefer morph:true
  when a node carries across.
- The camera never fully stops. A held frame is a slide, not a film. You do not
  need to write camera moves for holds — those are added for you — but a beat
  that wants a crash zoom, a whip pan or a slow push should say so.
- Stagger siblings 40-80ms apart with "at" so a group of lines reads as one
  gesture rather than a slab.
- Copy is short and concrete. No tagline that could belong to any product.`

export async function runFilm(req: FilmRequest): Promise<FilmProposal> {
  const model = req.model || defaultModel()
  const [w, h] = req.size

  const brief = [
    `Canvas ${w} x ${h}. Centre is ${Math.round(w / 2)}, ${Math.round(h / 2)}.`,
    `The film's accent is ${req.accent}.`,
    `Blocks you may place:\n${req.blocks
      // slots carry their kind now; join(', ') on the objects printed
      // "[object Object]" and the model was guessing names off the blurb
      .map(b => `  ${b.key} - ${b.blurb}\n    opts: ${b.slots.map(sl => `${sl.key} (${sl.kind})`).join(', ')}`)
      .join('\n')}`,
    `Entrances: ${req.enters.join(', ')}`,
    `Transitions: ${req.transitions.join(', ')}`,
    `What the director asked for: ${req.prompt}`,
  ].join('\n\n')

  const parsed = await callTool(model, FILM_CONTRACT, brief, filmTool(req), 8000)
  const known = new Set(req.blocks.map(b => b.key))
  const enters = new Set(req.enters)
  const raw = Array.isArray(parsed.scenes) ? parsed.scenes as FilmProposal['scenes'] : []

  const scenes = raw
      .filter(sc => sc && Array.isArray(sc.place))
      .map((sc, i) => ({
        ...sc,
        id: typeof sc.id === 'string' && sc.id ? sc.id : `s${i + 1}`,
        dur: Number.isFinite(sc.dur) ? Number(sc.dur) : 2.4,
        // an unknown block or entrance would vanish silently at materialise
        // time; dropping them here means the count is honest in the proposal
        place: sc.place
          .filter(p => p && known.has(p.block))
          .map(p => ({ ...p, enter: p.enter && enters.has(p.enter) ? p.enter : undefined })),
      }))
      .filter(sc => sc.place.length)

  // two scenes sharing an id would put one track in both places
  const problems = checkScenes(scenes)

  return {
    note: typeof parsed.note === 'string' ? parsed.note : 'proposed film',
    scenes,
    problems: problems.length ? problems : undefined,
  }
}

export async function runImage(req: ImageRequest): Promise<{ dataUrl: string; mime: string }> {
  const auth = need('GEMINI_API_KEY')
  const model = req.model || 'gemini-3.1-flash-image'
  const res = await fetch(`${GEMINI}/${model}:generateContent`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-goog-api-key': auth },
    body: JSON.stringify({
      contents: [{ parts: [{ text: req.prompt }] }],
      generationConfig: {
        responseModalities: ['IMAGE'],
        ...(req.aspect ? { imageConfig: { aspectRatio: req.aspect } } : {}),
      },
    }),
  })
  if (!res.ok) throw new Error(`gemini ${res.status}: ${(await res.text()).slice(0, 300)}`)

  const body = await res.json() as {
    candidates?: { content?: { parts?: { inlineData?: { data: string; mimeType: string } }[] } }[]
  }
  const part = body.candidates?.[0]?.content?.parts?.find(p => p.inlineData)?.inlineData
  if (!part) throw new Error('gemini returned no image')
  return { dataUrl: `data:${part.mimeType};base64,${part.data}`, mime: part.mimeType }
}

export async function runVector(req: VectorRequest): Promise<{ svg: string }> {
  const auth = quiverKey()
  if (!auth) throw new Missing('QUIVERAI_API_KEY is not set on the server')
  const res = await fetch(QUIVER, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${auth}` },
    body: JSON.stringify({
      model: req.model || 'arrow-1.1',
      prompt: req.prompt,
      ...(req.instructions ? { instructions: req.instructions } : {}),
      n: 1,
    }),
  })
  if (!res.ok) throw new Error(`quiver ${res.status}: ${(await res.text()).slice(0, 300)}`)

  const body = await res.json() as { data?: { svg?: string; url?: string }[] }
  const svg = body.data?.[0]?.svg
  if (!svg) throw new Error('quiver returned no svg')
  return { svg }
}
