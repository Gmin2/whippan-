/**
 * Guards on the way in. The engine fails silently on a malformed document — a
 * scene with no nodes simply renders nothing — so the API refuses anything that
 * is not recognisably a film rather than letting a client bug overwrite one.
 */

export const SLUG = /^[a-z0-9][a-z0-9-]{0,63}$/i

export interface Invalid { error: string }

export function validateDoc(body: unknown): Invalid | { stage: unknown; anim: unknown } {
  if (!body || typeof body !== 'object') return { error: 'body must be an object' }
  const { stage, anim } = body as { stage?: unknown; anim?: unknown }

  if (!stage || typeof stage !== 'object') return { error: 'stage missing' }
  const scenes = (stage as { scenes?: unknown }).scenes
  if (!Array.isArray(scenes) || scenes.length === 0) {
    return { error: 'stage has no scenes' }
  }
  for (const [i, s] of scenes.entries()) {
    if (!s || typeof s !== 'object') return { error: `scene ${i} is not an object` }
    const scene = s as { id?: unknown; nodes?: unknown }
    if (typeof scene.id !== 'string' || !scene.id) {
      return { error: `scene ${i} has no id` }
    }
    if (!Array.isArray(scene.nodes)) return { error: `scene ${scene.id} has no nodes array` }
  }
  const size = (stage as { size?: unknown }).size
  if (!Array.isArray(size) || size.length !== 2) return { error: 'stage.size must be [w, h]' }

  if (!anim || typeof anim !== 'object') return { error: 'anim missing' }
  if (!Array.isArray((anim as { tracks?: unknown }).tracks)) {
    return { error: 'anim has no tracks array' }
  }

  return { stage, anim }
}
