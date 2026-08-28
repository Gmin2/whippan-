// playback sound for the gallery: the doc's bed through an <audio> element
// and the engine-derived sfx events through webaudio, both slaved to the
// film clock. create one per loaded doc, drive it with the same play/pause/
// seek the canvas uses.
import { sfx } from './index'
import type { Doc, SfxEvent } from './types'

const bufferCache = new Map<string, AudioBuffer>()
let ctx: AudioContext | null = null

function audioCtx(): AudioContext {
  if (!ctx) ctx = new AudioContext()
  return ctx
}

async function buffer(src: string): Promise<AudioBuffer> {
  const hit = bufferCache.get(src)
  if (hit) return hit
  const raw = await fetch(src).then(r => r.arrayBuffer())
  const decoded = await audioCtx().decodeAudioData(raw)
  bufferCache.set(src, decoded)
  return decoded
}

function eventFile(e: SfxEvent): string {
  if (e.kind === 'tick') return `/assets/sfx/tick_0${(e.variant % 8) + 1}.wav`
  if (e.kind === 'pop') return `/assets/sfx/pop_0${(e.variant % 8) + 1}.wav`
  return `/assets/sfx/${e.kind}.wav`
}

export interface Sound {
  play(t: number): void
  pause(): void
  seek(t: number): void
  /** the film wrapped: restart the score from the top */
  loop(t: number): void
  dispose(): void
  hasAudio: boolean
}

export function createSound(doc: Doc): Sound {
  const audio = doc.stage.audio
  const events: SfxEvent[] = JSON.parse(
    sfx(JSON.stringify(doc.stage), JSON.stringify(doc.anim)))
  const bed = audio?.src ? new Audio(audio.src) : null
  if (bed) bed.volume = Math.min(1, audio?.gain ?? 0.8)
  const bedStart = audio?.start ?? 0
  let scheduled: AudioBufferSourceNode[] = []
  let playing = false

  // warm the buffers so the first play is on time
  for (const f of new Set(events.map(eventFile))) buffer(f).catch(() => {})

  function stopScheduled() {
    for (const node of scheduled) {
      try { node.stop() } catch { /* already finished */ }
    }
    scheduled = []
  }

  async function scheduleFrom(t: number) {
    const ac = audioCtx()
    if (ac.state === 'suspended') await ac.resume()
    const now = ac.currentTime
    for (const e of events) {
      if (e.t < t - 0.05) continue
      const b = bufferCache.get(eventFile(e))
      if (!b) continue
      const src = ac.createBufferSource()
      src.buffer = b
      const g = ac.createGain()
      g.gain.value = (e.gain ?? 0.5) * 0.9
      src.connect(g)
      g.connect(ac.destination)
      src.start(now + Math.max(0, e.t - t))
      scheduled.push(src)
    }
  }

  return {
    play(t) {
      playing = true
      if (bed) {
        bed.currentTime = bedStart + t
        bed.play().catch(() => {})
      }
      scheduleFrom(t)
    },
    pause() {
      playing = false
      if (bed) bed.pause()
      stopScheduled()
    },
    seek(t) {
      if (bed) bed.currentTime = bedStart + t
      if (playing) {
        stopScheduled()
        scheduleFrom(t)
      }
    },
    loop(t) {
      if (!playing) return
      if (bed) bed.currentTime = bedStart + t
      stopScheduled()
      scheduleFrom(t)
    },
    dispose() {
      this.pause()
    },
    hasAudio: !!bed || events.length > 0,
  }
}
