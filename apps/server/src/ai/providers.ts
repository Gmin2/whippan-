import { motionTool, screenTool, filmTool, type Tool } from './schema.js'
import { checkTracks, checkScenes, type Track } from './validate.js'
import type {
  Capability, FilmProposal, FilmRequest, ImageRequest, MotionProposal, MotionRequest,
  ScreenProposal, ScreenRequest, VectorRequest,
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
const QUIVER = process.env.QUIVERAI_BASE_URL ?? 'https://api.quiver.ai/v1/svgs/generations'
const GEMINI = process.env.GEMINI_BASE_URL
  ?? 'https://generativelanguage.googleapis.com/v1beta/models'

const key = (name: string) => process.env[name]?.trim() || null

export function capabilities(): Capability[] {
  return [
    {
      kind: 'motion',
      provider: 'Anthropic',
      ready: !!key('ANTHROPIC_API_KEY'),
      reason: key('ANTHROPIC_API_KEY') ? undefined : 'set ANTHROPIC_API_KEY on the server',
      models: [
        { id: 'claude-sonnet-5', label: 'Claude Sonnet 5', note: 'fast enough to iterate' },
        { id: 'claude-opus-5', label: 'Claude Opus 5', note: 'better taste, slower' },
      ],
    },
    {
      kind: 'film',
      provider: 'Anthropic',
      ready: !!key('ANTHROPIC_API_KEY'),
      reason: key('ANTHROPIC_API_KEY') ? undefined : 'set ANTHROPIC_API_KEY on the server',
      models: [
        { id: 'claude-opus-5', label: 'Claude Opus 5', note: 'a whole film is worth the wait' },
        { id: 'claude-sonnet-5', label: 'Claude Sonnet 5', note: 'faster first draft' },
      ],
    },
    {
      kind: 'screen',
      provider: 'Anthropic',
      ready: !!key('ANTHROPIC_API_KEY'),
      reason: key('ANTHROPIC_API_KEY') ? undefined : 'set ANTHROPIC_API_KEY on the server',
      models: [
        { id: 'claude-sonnet-5', label: 'Claude Sonnet 5', note: 'fast enough to iterate' },
        { id: 'claude-opus-5', label: 'Claude Opus 5', note: 'better taste, slower' },
      ],
    },
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
      ready: !!key('QUIVERAI_API_KEY'),
      reason: key('QUIVERAI_API_KEY') ? undefined : 'set QUIVERAI_API_KEY on the server',
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
  const auth = need('ANTHROPIC_API_KEY')
  const model = req.model || 'claude-sonnet-5'

  const brief = [
    `Scene "${req.scene.id}", ${req.scene.dur}s long, beat ${req.scene.index + 1} of ${req.scene.total}.`,
    `Nodes selected:\n${JSON.stringify(req.nodes, null, 1)}`,
    req.tracks.length
      ? `Their current tracks, which you are editing:\n${JSON.stringify(req.tracks, null, 1)}`
      : 'These nodes have no motion yet.',
    `What the director asked for: ${req.prompt}`,
  ].join('\n\n')

  const parsed = await callTool(auth, model, CONTRACT, brief, motionTool(req), 2000)
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
  auth: string, model: string, system: string, brief: string, tool: Tool, maxTokens: number,
): Promise<Record<string, unknown>> {
  const res = await fetch(ANTHROPIC, {
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
- Margins are generous: keep content inside the middle 80% horizontally and the
  middle 70% vertically. These are posters with a UI in the middle.
- ONE THOUGHT PER SCENE. Three sentences is two scenes. Two to four blocks is a
  screen; eight is a mess.
- One accent. About one text node in five carries it, no more.
- Copy is short and concrete. No taglines that could belong to any product.

Counters, rolling numbers and alternating headlines are the "swap-slot" block,
never one line of text you intend to animate.`

export async function runScreen(req: ScreenRequest): Promise<ScreenProposal> {
  const auth = need('ANTHROPIC_API_KEY')
  const model = req.model || 'claude-sonnet-5'
  const [w, h] = req.size

  const brief = [
    `Canvas ${w} x ${h}. Centre is ${Math.round(w / 2)}, ${Math.round(h / 2)}.`,
    `The film's accent is ${req.accent}; a block with a role of "accent" takes it.`,
    `Blocks you may place:\n${req.blocks
      .map(b => `  ${b.key} - ${b.blurb}\n    opts: ${b.slots.join(', ')}`)
      .join('\n')}`,
    `What the director asked for: ${req.prompt}`,
  ].join('\n\n')

  const parsed = await callTool(auth, model, SCREEN_CONTRACT, brief, screenTool(req), 2000)
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
- It opens on the product doing something, not on a title card.
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
  const auth = need('ANTHROPIC_API_KEY')
  const model = req.model || 'claude-opus-5'
  const [w, h] = req.size

  const brief = [
    `Canvas ${w} x ${h}. Centre is ${Math.round(w / 2)}, ${Math.round(h / 2)}.`,
    `The film's accent is ${req.accent}.`,
    `Blocks you may place:\n${req.blocks
      .map(b => `  ${b.key} - ${b.blurb}\n    opts: ${b.slots.join(', ')}`)
      .join('\n')}`,
    `Entrances: ${req.enters.join(', ')}`,
    `Transitions: ${req.transitions.join(', ')}`,
    `What the director asked for: ${req.prompt}`,
  ].join('\n\n')

  const parsed = await callTool(auth, model, FILM_CONTRACT, brief, filmTool(req), 8000)
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
  const auth = need('QUIVERAI_API_KEY')
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
