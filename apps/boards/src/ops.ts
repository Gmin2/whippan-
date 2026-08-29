import type { Node, Scene, Stage } from './engine/types'
import { svgToPath } from './svg'

/**
 * Document operations. Every one returns a new Stage rather than mutating,
 * so undo can hold plain snapshots and the frame cache can tell which scenes
 * actually changed by object identity.
 */

/** ids must be unique across the whole stage: a track targets an id, and it
 *  applies to every scene that contains one */
export function freshId(stage: Stage, base: string): string {
  const taken = new Set(stage.scenes.flatMap(s => s.nodes.map(n => n.id)))
  let n = 1
  while (taken.has(`${base}${n}`)) n++
  return `${base}${n}`
}

function freshSceneId(stage: Stage): string {
  const taken = new Set(stage.scenes.map(s => s.id))
  let n = stage.scenes.length + 1
  while (taken.has(`s${n}`)) n++
  return `s${n}`
}

export function addNode(stage: Stage, sceneId: string, node: Node): Stage {
  return {
    ...stage,
    scenes: stage.scenes.map(s =>
      s.id === sceneId ? { ...s, nodes: [...s.nodes, node] } : s),
  }
}

export function deleteNode(stage: Stage, sceneId: string, nodeId: string): Stage {
  return {
    ...stage,
    scenes: stage.scenes.map(s =>
      s.id === sceneId ? { ...s, nodes: s.nodes.filter(n => n.id !== nodeId) } : s),
  }
}

/** paper duplicates in place and selects the copy; the copy needs its own id
 *  or the animation overlay would drive both of them at once */
export function duplicateNode(
  stage: Stage, sceneId: string, nodeId: string,
): { stage: Stage; id: string } | null {
  const scene = stage.scenes.find(s => s.id === sceneId)
  const node = scene?.nodes.find(n => n.id === nodeId)
  if (!scene || !node) return null
  const id = freshId(stage, node.type === 'text' ? 'text' : node.type)
  const copy: Node = structuredClone(node)
  copy.id = id
  return { stage: addNode(stage, sceneId, copy), id }
}

/** a new beat, inserted after the given scene (or appended) */
export function addScene(stage: Stage, afterId?: string): { stage: Stage; id: string } {
  const id = freshSceneId(stage)
  const scene: Scene = {
    id,
    bg: '#ffffff',
    dur: 2,
    note: 'new scene',
    nodes: [],
  }
  const at = afterId ? stage.scenes.findIndex(s => s.id === afterId) : -1
  const scenes = [...stage.scenes]
  scenes.splice(at >= 0 ? at + 1 : scenes.length, 0, scene)
  return { stage: { ...stage, scenes }, id }
}

export function deleteScene(stage: Stage, sceneId: string): Stage {
  // a film with no scenes will not render, and the save endpoint rejects it
  if (stage.scenes.length <= 1) return stage
  return { ...stage, scenes: stage.scenes.filter(s => s.id !== sceneId) }
}

export function newRect(stage: Stage, x: number, y: number, w: number, h: number): Node {
  return {
    id: freshId(stage, 'rect'),
    type: 'rect',
    x: Math.round(x),
    y: Math.round(y),
    w: Math.max(1, Math.round(w)),
    h: Math.max(1, Math.round(h)),
    radius: 0,
    fill: '#dddddd',
  }
}

export function newImage(
  stage: Stage, src: string, x: number, y: number, w = 800, h = 500,
): Node {
  const seq = src.endsWith('/')
  return seq
    ? {
      id: freshId(stage, 'seq'),
      type: 'seq',
      src,
      // the real count comes from the folder; 60 is a safe first guess the
      // inspector can correct
      count: 60,
      fps: 30,
      x: Math.round(x), y: Math.round(y), w, h,
    }
    : {
      id: freshId(stage, 'img'),
      type: 'image',
      src,
      x: Math.round(x), y: Math.round(y), w, h, radius: 0,
    }
}

/**
 * A drawn path. `d` is local to the node origin, per the document contract, so
 * the first point becomes (0,0) and the node sits there. Stroked rather than
 * filled by default: the engine fills a path unless `stroke` is set, and an
 * unclosed scribble filling itself is never what you meant.
 */
export function newPath(
  stage: Stage, pts: { x: number; y: number }[], closed: boolean,
): Node | null {
  if (pts.length < 2) return null
  const [o] = pts
  const d = pts
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${(p.x - o.x).toFixed(1)} ${(p.y - o.y).toFixed(1)}`)
    .join(' ') + (closed ? ' Z' : '')
  return {
    id: freshId(stage, 'path'),
    type: 'path',
    x: Math.round(o.x),
    y: Math.round(o.y),
    d,
    fill: '#161616',
    stroke: 3,
  }
}

export function newText(stage: Stage, x: number, y: number): Node {
  return {
    id: freshId(stage, 'text'),
    type: 'text',
    text: 'Text',
    x: Math.round(x),
    y: Math.round(y),
    color: '#161616',
    font: { family: 'inter', weight: 600, size: 72 },
  }
}

/**
 * Paint order. A scene's node array is its z-order: later entries draw over
 * earlier ones, so "bring forward" is a swap towards the end.
 */
export type Reorder = 'front' | 'back' | 'up' | 'down'

export function reorderNode(
  stage: Stage, sceneId: string, nodeId: string, where: Reorder,
): Stage {
  return {
    ...stage,
    scenes: stage.scenes.map(s => {
      if (s.id !== sceneId) return s
      const i = s.nodes.findIndex(n => n.id === nodeId)
      if (i < 0) return s
      const to = where === 'front' ? s.nodes.length - 1
        : where === 'back' ? 0
        : where === 'up' ? i + 1
        : i - 1
      return { ...s, nodes: moved(s.nodes, i, to) }
    }),
  }
}

/** drop a node at an explicit index, which is what dragging a layer row does */
export function moveNodeTo(
  stage: Stage, sceneId: string, nodeId: string, index: number,
): Stage {
  return {
    ...stage,
    scenes: stage.scenes.map(s => {
      if (s.id !== sceneId) return s
      const i = s.nodes.findIndex(n => n.id === nodeId)
      return i < 0 ? s : { ...s, nodes: moved(s.nodes, i, index) }
    }),
  }
}

function moved<T>(list: T[], from: number, to: number): T[] {
  const at = Math.max(0, Math.min(list.length - 1, to))
  if (at === from) return list
  const out = list.slice()
  const [item] = out.splice(from, 1)
  out.splice(at, 0, item)
  return out
}

/**
 * A path node from a generated svg, scaled to a comfortable size on the board
 * and centred where it was asked for. The outline keeps the svg's own
 * coordinates, so the node's w/h carry the scale.
 */
export function newSvg(stage: Stage, svg: string, x: number, y: number): Node | null {
  const vec = svgToPath(svg)
  if (!vec) return null
  const [vw, vh] = vec.size
  // a generated icon arrives in a 12 to 512 unit box; put it on the board at a
  // size you can actually see without having to hunt for it
  const target = Math.min(stage.size[0], stage.size[1]) * 0.22
  const scale = target / Math.max(vw, vh, 1)
  return {
    id: freshId(stage, 'vector'),
    type: 'path',
    x: Math.round(x),
    y: Math.round(y),
    w: Math.round(vw * scale),
    h: Math.round(vh * scale),
    d: vec.d,
    fill: vec.fill,
  }
}
