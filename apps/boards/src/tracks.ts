import type { Anim, Key, Track } from './engine/types'

/**
 * Editing the animation overlay.
 *
 * The binding rule from AUTHORING §4: one track per node per property, and a
 * later track keying the same property REPLACES the earlier one. So a patch
 * finds the track that already owns a field and edits it in place rather than
 * appending a second track that would silently win or lose.
 */

export interface TrackPatch {
  at?: number
  loop?: boolean
  /** replace one property's keys; null removes the property entirely */
  keys?: Record<string, Key[] | null>
  enter?: string | null
  reveal?: Record<string, unknown> | null
  state?: string | null
}

export const tracksFor = (anim: Anim, target: string): Track[] =>
  (anim.tracks ?? []).filter(t => t.target === target)

/** the track that owns a field for this node, or the node's first track */
function ownerOf(anim: Anim, target: string, has: (t: Track) => boolean): number {
  const tracks = anim.tracks ?? []
  const owned = tracks.findIndex(t => t.target === target && has(t))
  if (owned >= 0) return owned
  return tracks.findIndex(t => t.target === target)
}

export function patchTrack(anim: Anim, target: string, patch: TrackPatch): Anim {
  let tracks = [...(anim.tracks ?? [])]

  /** edit the owning track, creating one if the node has none yet */
  const edit = (has: (t: Track) => boolean, fn: (t: Track) => Track | null) => {
    const i = ownerOf({ tracks } as Anim, target, has)
    if (i < 0) {
      const made = fn({ target })
      if (made) tracks.push(made)
      return
    }
    const next = fn({ ...tracks[i] })
    if (next === null) tracks.splice(i, 1)
    else tracks[i] = next
  }

  if (patch.at !== undefined || patch.loop !== undefined) {
    edit(() => true, t => {
      if (patch.at !== undefined) {
        if (patch.at === 0) delete t.at
        else t.at = Math.round(patch.at * 1000) / 1000
      }
      if (patch.loop !== undefined) {
        if (patch.loop) t.loop = true
        else delete t.loop
      }
      return t
    })
  }

  for (const [prop, keys] of Object.entries(patch.keys ?? {})) {
    edit(t => !!t.keys?.[prop], t => {
      const next = { ...(t.keys ?? {}) }
      if (keys === null) delete next[prop]
      else next[prop] = keys
      if (!Object.keys(next).length) {
        delete t.keys
        // a track with nothing left in it should not linger in the document
        const bare = !t.reveal && !t.enter && !t.state && !t.cam
        return bare ? null : t
      }
      t.keys = next
      return t
    })
  }

  if (patch.enter !== undefined) {
    edit(t => t.enter !== undefined, t => {
      if (patch.enter === null) {
        delete t.enter
        return t.keys || t.reveal || t.state ? t : null
      }
      t.enter = patch.enter
      return t
    })
  }

  if (patch.reveal !== undefined) {
    edit(t => t.reveal !== undefined, t => {
      if (patch.reveal === null) {
        delete t.reveal
        return t.keys || t.enter || t.state ? t : null
      }
      t.reveal = patch.reveal
      return t
    })
  }

  if (patch.state !== undefined) {
    edit(t => t.state !== undefined, t => {
      if (patch.state === null) {
        delete t.state
        return t.keys || t.enter || t.reveal ? t : null
      }
      t.state = patch.state
      return t
    })
  }

  // drop any track that ended up empty
  tracks = tracks.filter(t =>
    t.keys || t.reveal || t.enter !== undefined || t.state || t.cam)

  return { ...anim, tracks }
}
