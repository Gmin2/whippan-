import type { Node, Scene, Stage } from './engine/types'

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
