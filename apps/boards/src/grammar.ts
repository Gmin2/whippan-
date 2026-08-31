import type { Anim, Doc, Track } from './engine/types'

/**
 * The reference grammar, as checks on a document.
 *
 * `analysis/README.md` distils 29 frame-precise teardowns into nine patterns
 * the whole reference set converges on. They spent months as prose, which is
 * the weakest form of a rule. These are the ones that can be decided from the
 * document alone, before anything is rendered.
 *
 * The measured motivation: `conform/BASELINE.md` records that we render **38%
 * of the reference motion** on average, 21 of 28 films under half. The
 * teardowns already say why — pattern 7, "the camera never fully stops" — so
 * these checks exist to name which pattern a given film is breaking rather
 * than reporting one aggregate number nobody can act on.
 *
 * Nothing here blocks. A note is a note. The references are what the good ones
 * do, not a law, and every film in the corpus breaks something deliberately.
 */

export interface Note {
  /** warn is a clear break with the reference grammar; note is worth knowing */
  level: 'warn' | 'note'
  /** which cross-video pattern this comes from, so the prose is one lookup away */
  pattern: number
  /** scene id where it applies, or '' for the whole film */
  scene: string
  text: string
}

/**
 * Pattern 7 — the camera never fully stops.
 *
 * "even holds carry a sub-pixel drift or a slow push. static frames are
 * avoided." Several references run 60 to 95 seconds with zero hard cuts and
 * still never sit still.
 *
 * Judged on `motionMass`, not on whether a track exists. The first version of
 * this check asked about coverage and scored r = -0.21 against the rendered
 * result, which is to say it was worse than nothing: `terminal` is one looped
 * glow over a still frame and it passed. Amplitude scores r = 0.51 against our
 * own rendered energy, so this is the version that earns its place.
 *
 * The threshold comes from the corpus rather than taste. Films the harness
 * measures well — sunflower, design, radio-main, crab, survey — all sit above
 * 0.45 mass per second. Everything under 0.15 renders close to still.
 */
const MOVING = 0.15
const LIVELY = 0.45

export function checkCamera(doc: Doc): Note[] {
  const out: Note[] = []
  const mass = new Map(motionMass(doc).map(m => [m.scene, m]))
  for (const scene of doc.stage.scenes) {
    const m = mass.get(scene.id)
    if (!m) continue
    if (m.mass < 0.02) {
      out.push({
        level: 'warn', pattern: 7, scene: scene.id,
        text: `nothing measurably moves across ${fmt(m.dur)}; the references never hold a still frame`,
      })
    } else if (m.mass < MOVING) {
      out.push({
        level: 'warn', pattern: 7, scene: scene.id,
        text: `barely moves (${m.mass.toFixed(2)}/s); the films that read well sit above ${LIVELY}`,
      })
    } else if (m.mass < LIVELY) {
      out.push({
        level: 'note', pattern: 7, scene: scene.id,
        text: `moves a little (${m.mass.toFixed(2)}/s); a slow camera push would carry the hold`,
      })
    }
    const cam = tracksOf(doc.anim).some(
      t => (t.target === scene.id || hasCam(t)))
    if (!cam && (scene.dur ?? 3) >= 2 && m.mass < LIVELY) {
      out.push({
        level: 'note', pattern: 7, scene: scene.id,
        text: 'no camera move; the references carry a push even through a hold',
      })
    }
  }
  return out
}

/**
 * Pattern 1 — cuts punctuate, morphs narrate.
 *
 * Hard cuts are reserved for chapter boundaries; everything inside a chapter is
 * a dissolve, wash, blur-resolve or physical morph. terminal, atlas, x-anim,
 * radio-main and ravie run their whole length on zero or two hard cuts.
 */
export function checkCuts(doc: Doc): Note[] {
  const scenes = doc.stage.scenes
  const total = scenes.reduce((a, s) => a + (s.dur ?? 3), 0)
  const seams = scenes.slice(1)
  const hard = seams.filter(s => (s.transition?.kind ?? 'cut') === 'cut' && !s.transition?.morph)
  const out: Note[] = []
  if (!seams.length || total <= 0) return out

  // one every eight seconds is already busier than most of the reference set
  const per8 = (hard.length / total) * 8
  if (per8 > 1.6) {
    out.push({
      level: 'warn', pattern: 1, scene: '',
      text: `${hard.length} hard cuts in ${fmt(total)}; the references reserve cuts for chapter breaks`,
    })
  }
  if (hard.length === seams.length && seams.length >= 3) {
    out.push({
      level: 'warn', pattern: 1, scene: '',
      text: 'every seam is a hard cut; nothing narrates, everything punctuates',
    })
  }
  return out
}

/**
 * Pattern 6 — zero springs almost everywhere.
 *
 * Overshoot is rare across the whole set. Energy comes from 1-frame pops,
 * 3-4 frame crash zooms, motion blur and beat-locked cuts. The exceptions
 * (crab, the ai-1 physics chips) spring precisely because they sell
 * physicality. We offer spring as a first-class chip in the inspector, which
 * makes it far easier to reach for than the corpus warrants.
 */
export function checkSprings(doc: Doc): Note[] {
  let springs = 0
  let eased = 0
  for (const t of tracksOf(doc.anim)) {
    for (const keys of Object.values(t.keys ?? {})) {
      for (const k of keys) {
        if (k.ease === undefined) continue
        eased++
        if (isSpring(k.ease)) springs++
      }
    }
  }
  if (!eased || springs === 0) return []
  const share = springs / eased
  return share > 0.15
    ? [{
        level: 'warn', pattern: 6, scene: '',
        text: `${springs} of ${eased} eased keys spring; the references keep overshoot for selling physicality`,
      }]
    : []
}

/**
 * Pattern 3 — one colour, hoarded.
 *
 * A single brand hue does nearly all the work and foreign colour is reserved to
 * mean something. Measured on the corpus: 67% of colour marks are achromatic
 * and about one text node in five carries the accent. Measured again on three
 * fresh references: the accent is 3 to 6% of pixels.
 */
export function checkAccent(doc: Doc): Note[] {
  const out: Note[] = []
  for (const scene of doc.stage.scenes) {
    const texts = scene.nodes.filter(n => n.type === 'text' && n.text)
    if (texts.length < 3) continue
    const hues = new Map<string, number>()
    let accented = 0
    for (const n of texts) {
      const h = hueBucket(n.color)
      if (h === null) continue
      accented++
      hues.set(h, (hues.get(h) ?? 0) + 1)
    }
    if (accented / texts.length > 0.5) {
      out.push({
        level: 'warn', pattern: 3, scene: scene.id,
        text: `${accented} of ${texts.length} lines carry colour; the corpus holds it to about one in five`,
      })
    }
    if (hues.size > 2) {
      out.push({
        level: 'warn', pattern: 3, scene: scene.id,
        text: `${hues.size} different hues; a second colour should mean something`,
      })
    }
  }
  return out
}

/**
 * Pattern 5 — the product ui arrives whole.
 *
 * Dashboards materialise by staggered opacity or blur cascades. No chart
 * draw-ons, no stat count-ups except where the count IS the story. A group
 * whose members each animate separately is a draw-on: the group should arrive
 * as one thing.
 */
export function checkWholeArrival(doc: Doc): Note[] {
  const out: Note[] = []
  const animated = new Set(
    tracksOf(doc.anim).map(t => t.target).filter((t): t is string => typeof t === 'string'))
  for (const scene of doc.stage.scenes) {
    for (const g of scene.nodes.filter(n => n.type === 'group')) {
      const members = scene.nodes.filter(n => n.group === g.id)
      const moving = members.filter(m => animated.has(m.id))
      if (members.length >= 3 && moving.length >= 3 && !animated.has(g.id)) {
        out.push({
          level: 'note', pattern: 5, scene: scene.id,
          text: `${g.id}: ${moving.length} members animate separately; the references bring a surface in whole`,
        })
      }
    }
  }
  return out
}

/**
 * How much a scene actually changes, as a fraction of the canvas per second.
 *
 * The first version of the camera check asked whether a track COVERED the
 * scene's duration, and it did not predict the rendered result at all
 * (r = -0.21 against measured energy). Coverage is not motion: `terminal` is
 * one looped glow over a still frame and looked fully covered, while `x-anim`
 * moves constantly and looked the same.
 *
 * This estimates amplitude instead — how far something travels, how much of
 * the frame it occupies, and how much of the scene it happens in. It is a
 * rough model of exactly what conform measures from the pixels, computed from
 * the document so it can be known before rendering.
 */
export function motionMass(doc: Doc): { scene: string; mass: number; dur: number }[] {
  const [W, H] = doc.stage.size
  const area = W * H
  return doc.stage.scenes.map(scene => {
    const dur = scene.dur ?? 3
    const byId = new Map(scene.nodes.map(n => [n.id, n]))
    let mass = 0
    for (const t of tracksOf(doc.anim)) {
      const node = typeof t.target === 'string' ? byId.get(t.target) : undefined
      // a camera move shifts the whole frame, so it is worth the whole canvas
      const share = node ? Math.min(1, nodeArea(node) / area) : (t.target === scene.id ? 1 : 0)
      if (!share) continue

      for (const [prop, keys] of Object.entries(t.keys ?? {})) {
        if (keys.length < 2) continue
        const vs = keys.map(k => k.v)
        const travel = Math.max(...vs) - Math.min(...vs)
        mass += share * amplitude(prop, travel, W)
      }
      // the shorthands move a node about a fifth of its own size, plus opacity
      if (t.enter) mass += share * 1.2
      if (t.reveal) mass += share * 1.5
      if (t.state) mass += share * 0.3
    }
    return { scene: scene.id, mass: mass / Math.max(dur, 0.1), dur }
  })
}

/** what a unit of change in each property is worth, relative to a full fade */
function amplitude(prop: string, travel: number, W: number): number {
  switch (prop) {
    case 'opacity': return travel
    case 'scale': return travel * 2
    case 'x': case 'y': case 'w': case 'h': return Math.min(1, travel / (W * 0.25))
    case 'rot': return Math.min(1, travel / 45)
    // cosmetic: a glow pulse or a defocus barely shifts a pixel average
    case 'blur': return Math.min(0.2, travel / 60)
    default: return prop.startsWith('cam_') ? Math.min(1.5, travel / (W * 0.2)) : 0.15
  }
}

const nodeArea = (n: { w?: number; h?: number; font?: { size?: number }; text?: string }): number => {
  if (n.w && n.h) return n.w * n.h
  // text carries no box; approximate from its shaped extent
  const size = n.font?.size ?? 48
  return (n.text?.length ?? 8) * size * 0.5 * size * 1.2
}

/** every check, in the order a reader should meet them */
export function checkGrammar(doc: Doc): Note[] {
  return [
    ...checkCamera(doc),
    ...checkCuts(doc),
    ...checkSprings(doc),
    ...checkAccent(doc),
    ...checkWholeArrival(doc),
  ]
}

const tracksOf = (anim: Anim): Track[] => anim.tracks ?? []
const fmt = (s = 0) => `${s.toFixed(1)}s`
const hasCam = (t: Track) => !!t.cam || Object.keys(t.keys ?? {}).some(k => k.startsWith('cam_'))

const isSpring = (ease: unknown): boolean =>
  ease === 'spring' || (typeof ease === 'object' && ease !== null && 'spring' in ease)


/**
 * A 20-degree hue bucket, or null for anything achromatic.
 *
 * The corpus concentrates its chromatic marks in ONE bucket per film, so
 * counting buckets is how a second colour announces itself.
 */
function hueBucket(hex?: string): string | null {
  if (!hex || !/^#[0-9a-f]{6}$/i.test(hex)) return null
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  const mx = Math.max(r, g, b)
  const mn = Math.min(r, g, b)
  const d = mx - mn
  if (mx === 0 || d / mx < 0.35) return null
  let h = 0
  if (d) {
    if (mx === r) h = ((g - b) / d) % 6
    else if (mx === g) h = (b - r) / d + 2
    else h = (r - g) / d + 4
  }
  return String(Math.round(((h * 60) + 360) % 360 / 20))
}
