import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import LeftPanel from './components/LeftPanel'
import ToolRail from './components/ToolRail'
import type { Tool } from './components/ToolRail'
import Canvas from './components/Canvas'
import RightPanel from './components/RightPanel'
import AssetPicker from './components/AssetPicker'
import EffectPicker from './components/EffectPicker'
import ExportDialog from './components/ExportDialog'
import Timeline from './components/Timeline'
import { boot, ensureImage, loadDoc, saveDoc } from './engine'
import type { Anim, Doc, Entry, Node, Stage } from './engine/types'
import { artboards, findNode, tree } from './doc'
import { groupBox } from './measure'
import { patchTrack, tracksFor } from './tracks'
import type { TrackPatch } from './tracks'
import { docDur } from './engine'
import { sceneAt } from './motion'
import {
  addNode, addScene, deleteNode, deleteScene, duplicateNode, newImage, newPath,
  newRect, newSvg, newText, reorderNode, moveNodeBefore, groupNodes, ungroupNodes, groupOf,
  membersOf,
} from './ops'
import type { Reorder } from './ops'
import {
  applyMotion, applyStyle, clearMotion, clipboard, copyMotion, copyNodes, copyStyle,
  motionClip, pasteNodes, styleClip,
} from './clipboard'
import ContextMenu from './components/ContextMenu'
import AIBar from './components/AIBar'
import BlockPicker from './components/BlockPicker'
import { BLOCKS, blockByKey, filmAccent } from './blocks'
import { checkDensity, checkFit } from './fit'
import type { Fit } from './fit'
import { askImage, askMotion, askScreen, askVector, capabilities, motionContext } from './ai'
import type { AiKind, Capability, MotionProposal } from './ai'
import { AI_TOOLS } from './components/ToolRail'
import type { Item } from './components/ContextMenu'
import type { NodePatch, ScenePatch, Sel } from './doc'
import type { NodeBox } from './measure'

/** the film boards opens on; ?film=<slug> picks another out of the registry */
const DEFAULT_FILM = 'whippan'

export default function App() {
  const [ck, setCk] = useState<CanvasKit | null>(null)
  const [registry, setRegistry] = useState<Entry[]>([])
  const [film, setFilm] = useState(
    () => new URLSearchParams(location.search).get('film') ?? DEFAULT_FILM)
  const [doc, setDoc] = useState<Doc | null>(null)
  const [error, setError] = useState<string | null>(null)
  // every accepted edit bumps this, which re-renders the affected boards
  const [rev, setRev] = useState(0)

  const [tool, setTool] = useState<Tool>('select')
  const [sel, setSel] = useState<Sel | null>(null)
  /**
   * Nodes selected alongside the primary one. The primary stays first-class:
   * it is what the inspector reads and what a resize handle belongs to, while
   * move, delete, duplicate, copy and order act on the whole set.
   */
  const [extra, setExtra] = useState<Sel[]>([])
  const [selBox, setSelBox] = useState<NodeBox | null>(null)
  const [selRow, setSelRow] = useState(0)
  const [seam, setSeam] = useState<string | null>(null)
  const [scene, setScene] = useState<string | null>(null)
  const [zoom, setZoom] = useState(0.12)
  const [panels, setPanels] = useState(true)
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [saveError, setSaveError] = useState<string | null>(null)
  /** the block library, opened from the insert tool */
  const [blocks, setBlocks] = useState(false)
  /** which prompt bar is open, if any */
  const [ai, setAi] = useState<AiKind | null>(null)
  const [caps, setCaps] = useState<Capability[]>([])
  const [aiBusy, setAiBusy] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)
  const [proposal, setProposal] = useState<MotionProposal | null>(null)
  /** a composed screen waiting on a decision, with its fit budget already run */
  const [screen, setScreen] = useState<
    { note: string; nodes: Node[]; bg?: string; fit: Fit[] } | null>(null)
  /** the group you have stepped inside; its members then select directly */
  const [inside, setInside] = useState<string | null>(null)
  /** bumped to ask the canvas to open its text field on the selection */
  const [editRequest, setEditRequest] = useState(0)
  /** where the right-click menu is open, in client pixels */
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null)
  const [picking, setPicking] = useState(false)
  const [effects, setEffects] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [mode, setMode] = useState<'design' | 'motion'>('design')
  const [playhead, setPlayhead] = useState(0)
  const [playing, setPlaying] = useState(false)
  const raf = useRef(0)
  const [ground, setGround] = useState('#d9cac8')
  const [groundAlpha, setGroundAlpha] = useState(1)
  // undo holds whole stage snapshots. a drag pushes one entry when it starts,
  // not per pointer move, so undoing a drag undoes the whole gesture.
  // both layers, because motion mode edits anim.json as well as stage.json
  const undo = useRef<{ stage: Stage; anim: Anim }[]>([])
  const redo = useRef<{ stage: Stage; anim: Anim }[]>([])
  const dragging = useRef(false)

  useEffect(() => {
    boot().then(({ CK, registry: reg }) => {
      setCk(CK)
      setRegistry(reg)
      const entry: Entry | undefined = reg.find(e => e.slug === film) ?? reg[0]
      if (!entry) { setError('empty registry'); return }
      document.title = `${entry.title} · whippan boards`
      // the loader caches by slug, so edit on a copy and leave the cache clean
      return loadDoc(entry).then(d => setDoc({ ...d, stage: structuredClone(d.stage) }))
    }).catch(e => setError(String(e)))
  }, [film])

  // switching film clears everything that belonged to the old document
  const pickFilm = useCallback((slug: string) => {
    setFilm(slug)
    setDoc(null)
    setSel(null)
    setExtra([])
    setSelBox(null)
    setScene(null)
    undo.current = []
    redo.current = []
    const url = new URL(location.href)
    url.searchParams.set('film', slug)
    history.replaceState(null, '', url)
  }, [])

  const snapshot = useCallback(() => {
    setDoc(prev => {
      if (prev) {
        undo.current.push({
          stage: structuredClone(prev.stage),
          anim: structuredClone(prev.anim),
        })
        if (undo.current.length > 100) undo.current.shift()
        redo.current = []
      }
      return prev
    })
  }, [])

  const patchScene = useCallback((id: string, patch: ScenePatch) => {
    snapshot()
    setDoc(prev => {
      if (!prev) return prev
      const scenes = prev.stage.scenes.map(s => {
        if (s.id !== id) return s
        const { transition, ...rest } = patch
        const next: typeof s = { ...s, ...rest }
        // null clears it, which the engine reads back as a hard cut
        if (transition !== undefined) {
          if (transition === null) delete next.transition
          else next.transition = transition
        }
        return next
      })
      return { ...prev, stage: { ...prev.stage, scenes } }
    })
    if (patch.id && patch.id !== id) setScene(patch.id)
    setRev(r => r + 1)
    setDirty(true)
  }, [snapshot])

  const patchNode = useCallback((patch: NodePatch, transient = false) => {
    if (!sel) return
    if (!transient) snapshot()
    setDoc(prev => {
      if (!prev) return prev
      const scenes = prev.stage.scenes.map(s => {
        if (s.id !== sel.scene) return s
        return {
          ...s,
          nodes: s.nodes.map(n => {
            if (n.id !== sel.id) return n
            const {
              fontSize, fontFamily, fontWeight, opacity,
              blur, glow, gradient, goo, streak, ...rest
            } = patch
            const next: typeof n = { ...n, ...rest }
            if (fontSize != null || fontFamily != null || fontWeight != null) {
              next.font = {
                ...(n.font ?? {}),
                ...(fontSize != null ? { size: fontSize } : {}),
                ...(fontFamily != null ? { family: fontFamily } : {}),
                ...(fontWeight != null ? { weight: fontWeight } : {}),
              }
            }
            // opacity is not a node field: the engine reads it off the same
            // keys map the animation overlay writes into
            if (opacity != null) {
              next.keys = { ...(n.keys ?? {}), opacity: [{ t: 0, v: opacity }] }
            }
            // null means remove the section entirely, undefined means leave it
            if (blur !== undefined) { if (blur === null) delete next.blur; else next.blur = blur }
            if (goo !== undefined) { if (goo === null) delete next.goo; else next.goo = goo }
            if (streak !== undefined) {
              if (streak === null) delete next.streak; else next.streak = streak
            }
            if (glow !== undefined) { if (glow === null) delete next.glow; else next.glow = glow }
            if (gradient !== undefined) {
              if (gradient === null) delete next.gradient
              else next.gradient = gradient
            }
            return next
          }),
        }
      })
      return { ...prev, stage: { ...prev.stage, scenes } }
    })
    setRev(r => r + 1)
    setDirty(true)
  }, [sel, snapshot])

  /**
   * Move every node in the selection by the same delta.
   *
   * The primary node is driven by an absolute patch (it is the one that snaps),
   * so the rest follow the distance it actually travelled rather than the
   * distance the pointer did.
   */
  const shiftOthers = useCallback((dx: number, dy: number) => {
    const current = docRef.current
    const picked = selectionRef.current
    // the primary is driven by its own absolute patch; everything else follows.
    // a selected group brings its members, because the format has no nesting:
    // members hold absolute coordinates and a static move moves all of them.
    // the group's own motion, which the engine composes, lives in its tracks.
    const others = [
      ...picked.slice(1),
      ...(current
        ? picked.flatMap(p => membersOf(current.stage, p.scene, p.id)
            .map(id => ({ scene: p.scene, id })))
        : []),
    ]
    if (!others.length || (!dx && !dy)) return
    setDoc(prev => {
      if (!prev) return prev
      const scenes = prev.stage.scenes.map(s => {
        const here = others.filter(o => o.scene === s.id)
        if (!here.length) return s
        return {
          ...s,
          nodes: s.nodes.map(n => here.some(o => o.id === n.id)
            ? { ...n, x: Math.round((n.x ?? 0) + dx), y: Math.round((n.y ?? 0) + dy) }
            : n),
        }
      })
      return { ...prev, stage: { ...prev.stage, scenes } }
    })
  }, [])

  /** arrow keys, which move the whole selection rather than just the primary */
  const nudge = useCallback((dx: number, dy: number) => {
    const node = nodeRef.current
    if (!node) return
    snapshot()
    patchNode({ x: Math.round((node.x ?? 0) + dx), y: Math.round((node.y ?? 0) + dy) }, true)
    shiftOthers(dx, dy)
  }, [patchNode, shiftOthers, snapshot])

  const selectAll = useCallback(() => {
    const current = docRef.current
    const target = selRef.current?.scene ?? sceneRef.current
    const scene = current?.stage.scenes.find(s => s.id === target)
      ?? current?.stage.scenes[0]
    if (!scene?.nodes.length) return
    const all = scene.nodes.map(n => ({ scene: scene.id, id: n.id }))
    setSel(all[0])
    setExtra(all.slice(1))
    setScene(scene.id)
  }, [])

  // a drag streams patches; snapshot once at the start of the gesture
  const onDrag = useCallback((patch: NodePatch, follow?: { dx: number; dy: number }) => {
    if (!dragging.current) {
      dragging.current = true
      snapshot()
    }
    patchNode(patch, true)
    if (follow) shiftOthers(follow.dx, follow.dy)
  }, [patchNode, shiftOthers, snapshot])
  const onDragEnd = useCallback(() => { dragging.current = false }, [])

  const stepHistory = useCallback((dir: 'undo' | 'redo') => {
    const from = dir === 'undo' ? undo.current : redo.current
    const to = dir === 'undo' ? redo.current : undo.current
    const snap = from.pop()
    if (!snap) return
    setDoc(prev => {
      if (!prev) return prev
      to.push({ stage: structuredClone(prev.stage), anim: structuredClone(prev.anim) })
      return { ...prev, stage: snap.stage, anim: snap.anim }
    })
    setRev(r => r + 1)
    setDirty(true)
  }, [])

  // paper's nudge amounts: 1 small, 8 large. arrows with nothing selected pan,
  // which the canvas owns, so only handle them here when there is a selection.
  const NUDGE = { small: 1, large: 8 }
  const TOOL_KEYS: Record<string, Tool> = {
    v: 'select', h: 'hand', f: 'frame', r: 'rect', p: 'pen', t: 'text', s: 'shader',
  }

  // ask the server what it actually has keys for, once
  useEffect(() => { capabilities().then(setCaps).catch(() => setCaps([])) }, [])

  useEffect(() => {
    if (!dirty) return
    const warn = (e: BeforeUnloadEvent) => { e.preventDefault() }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const mod = e.metaKey || e.ctrlKey
      const key = e.key.toLowerCase()

      if (e.key === ' ' && modeRef.current === 'motion') {
        e.preventDefault()
        setPlaying(p => !p)
        return
      }
      if (mod && e.shiftKey && key === 'e') {
        e.preventDefault()
        setExporting(true)
        return
      }
      if (mod && e.shiftKey && key === 'k') {
        e.preventDefault()
        setPicking(true)
        return
      }
      if (mod && key === 's') {
        e.preventDefault()
        saveRef.current()
        return
      }
      // alt makes copy and paste mean the attributes rather than the node:
      // styles in design, timing in motion
      if (mod && e.altKey && (key === 'c' || key === 'v')) {
        e.preventDefault()
        const motion = modeRef.current === 'motion'
        if (key === 'c') (motion ? copyMotionRef : copyStyleRef).current()
        else (motion ? pasteMotionRef : pasteStyleRef).current()
        return
      }
      if (mod && (key === 'c' || key === 'x')) {
        e.preventDefault()
        copyRef.current()
        if (key === 'x') removeRef.current()
        return
      }
      if (mod && key === 'v') {
        e.preventDefault()
        pasteRef.current()
        return
      }
      if (mod && key === 'a') {
        e.preventDefault()
        selectAllRef.current()
        return
      }
      // paint order: bracket alone steps, with shift it goes all the way
      if (mod && (e.key === ']' || e.key === '[')) {
        e.preventDefault()
        const up = e.key === ']'
        reorderRef.current(e.shiftKey ? (up ? 'front' : 'back') : (up ? 'up' : 'down'))
        return
      }
      if (mod && key === 'g') {
        e.preventDefault()
        ;(e.shiftKey ? ungroupRef : groupRef).current()
        return
      }
      if (mod && key === 'd') {
        e.preventDefault()
        duplicateRef.current()
        return
      }
      if (e.key === 'Backspace' || e.key === 'Delete') {
        e.preventDefault()
        removeRef.current()
        return
      }
      if (mod && key === 'z') {
        e.preventDefault()
        stepHistory(e.shiftKey ? 'redo' : 'undo')
        return
      }
      if (e.key === 'Escape') {
        // stepping back out of a group first, then clearing
        if (insideRef.current) { exitGroupRef.current(); return }
        setSel(null); setExtra([]); setSelBox(null)
        return
      }

      const arrows: Record<string, [number, number]> = {
        ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1],
      }
      const dir = arrows[e.key]
      if (dir && selRef.current) {
        e.preventDefault()
        const step = e.shiftKey ? NUDGE.large : NUDGE.small
        nudgeRef.current(dir[0] * step, dir[1] * step)
        return
      }

      if (!mod && !e.altKey && TOOL_KEYS[key]) setTool(TOOL_KEYS[key])
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [stepHistory])

  const save = useCallback(async () => {
    const current = docRef.current
    if (!current) return
    setSaving('saving')
    setSaveError(null)
    try {
      await saveDoc(current.entry.slug, current.stage, current.anim)
      setDirty(false)
      setSaving('saved')
      setTimeout(() => setSaving(s => (s === 'saved' ? 'idle' : s)), 1600)
    } catch (e) {
      setSaving('error')
      setSaveError(String(e))
    }
  }, [])

  /** apply a pure stage operation as one undoable step */
  const apply = useCallback((fn: (stage: Stage) => Stage | null) => {
    snapshot()
    let changed = false
    setDoc(prev => {
      if (!prev) return prev
      const next = fn(prev.stage)
      if (!next || next === prev.stage) return prev
      changed = true
      return { ...prev, stage: next }
    })
    if (changed) { setRev(r => r + 1); setDirty(true) }
  }, [snapshot])

  const createNode = useCallback((
    sceneId: string, kind: 'rect' | 'text',
    box: { x: number; y: number; w: number; h: number },
  ) => {
    const stage = docRef.current?.stage
    if (!stage) return
    const node = kind === 'text'
      ? newText(stage, box.x, box.y)
      : newRect(stage, box.x, box.y, box.w, box.h)
    apply(st => addNode(st, sceneId, node))
    setSel({ scene: sceneId, id: node.id })
    setScene(sceneId)
  }, [apply])

  /**
   * Placing a block. It arrives as a group plus its members, so the whole thing
   * is one selectable object and one track can animate it.
   */
  const insertBlock = useCallback((key: string, opts: Record<string, unknown>) => {
    const current = docRef.current
    const target = sceneRef.current ?? current?.stage.scenes[0]?.id
    const def = blockByKey(key)
    if (!current || !target || !def) return
    const [w, h] = current.stage.size
    const made = def.make(
      { stage: current.stage, accent: filmAccent(current.stage), x: w / 2, y: h / 2 },
      opts,
    )
    apply(st => made.reduce((acc, n) => addNode(acc, target, n), st))
    const group = made.find(n => n.type === 'group')
    if (group) { setSel({ scene: target, id: group.id }); setExtra([]); setInside(null) }
    setScene(target)
    setBlocks(false)
  }, [apply])

  const insertImage = useCallback(async (src: string) => {
    const current = docRef.current
    const target = sceneRef.current ?? current?.stage.scenes[0]?.id
    if (!current || !ck || !target) return
    // decode it before it lands, so the board paints the image immediately
    // rather than a hole that fills in on the next edit
    if (!src.endsWith('/')) await ensureImage(ck, current, src)
    const [cw, ch] = current.stage.size
    const node = newImage(current.stage, src, cw / 2, ch / 2)
    apply(st => addNode(st, target, node))
    setSel({ scene: target, id: node.id })
  }, [apply, ck])

  const createPath = useCallback((
    sceneId: string, pts: { x: number; y: number }[], closed: boolean,
  ) => {
    const stage = docRef.current?.stage
    if (!stage) return
    const node = newPath(stage, pts, closed)
    if (!node) return
    apply(st => addNode(st, sceneId, node))
    setSel({ scene: sceneId, id: node.id })
    setScene(sceneId)
  }, [apply])

  /** edit the animation overlay for a node */
  const patchMotionFor = useCallback((
    target: string, patch: TrackPatch, transient = false,
  ) => {
    if (!transient) snapshot()
    setDoc(prev => (prev ? { ...prev, anim: patchTrack(prev.anim, target, patch) } : prev))
    setRev(r => r + 1)
    setDirty(true)
  }, [snapshot])

  const patchMotion = useCallback((patch: TrackPatch) => {
    const s = selRef.current
    if (s) patchMotionFor(s.id, patch)
  }, [patchMotionFor])

  /**
   * Retiming from the timeline. A drag streams patches, so the snapshot is
   * taken once when the gesture starts: one drag is one undo, not thirty.
   */
  const retiming = useRef(false)
  const motionGesture = useCallback((
    target: string, patch: TrackPatch, done: boolean,
  ) => {
    if (!retiming.current) {
      retiming.current = true
      snapshot()
    }
    patchMotionFor(target, patch, true)
    if (done) retiming.current = false
  }, [patchMotionFor, snapshot])

  const removeSelection = useCallback(() => {
    const picked = selectionRef.current
    if (picked.length) {
      apply(st => picked.reduce((acc, p) => deleteNode(acc, p.scene, p.id), st))
      setSel(null)
      setExtra([])
      setSelBox(null)
      return
    }
    const sc = sceneRef.current
    if (sc) apply(st => deleteScene(st, sc))
  }, [apply])

  const duplicateSelection = useCallback(() => {
    const picked = selectionRef.current
    if (!picked.length) return
    const made: Sel[] = []
    apply(st => {
      let next = st
      for (const p of picked) {
        const out = duplicateNode(next, p.scene, p.id)
        if (!out) continue
        next = out.stage
        made.push({ scene: p.scene, id: out.id })
      }
      return made.length ? next : null
    })
    // the copies become the selection, the way every design tool behaves
    if (made.length) { setSel(made[0]); setExtra(made.slice(1)) }
  }, [apply])

  const copySelection = useCallback(() => {
    const current = docRef.current
    if (current) copyNodes(current, selectionRef.current)
  }, [])

  const paste = useCallback(() => {
    const clip = clipboard.get()
    const current = docRef.current
    // paste lands in the scene you are looking at, not the one it came from
    const target = selRef.current?.scene ?? sceneRef.current ?? current?.stage.scenes[0]?.id
    if (!clip || !current || !target) return
    snapshot()
    let made: Sel[] = []
    setDoc(prev => {
      if (!prev) return prev
      const out = pasteNodes(prev.stage, prev.anim, target, clip)
      if (!out) return prev
      made = out.ids.map(id => ({ scene: target, id }))
      return { ...prev, stage: out.stage, anim: out.anim }
    })
    if (made.length) {
      setSel(made[0])
      setExtra(made.slice(1))
      setScene(target)
      setRev(r => r + 1)
      setDirty(true)
    }
  }, [snapshot])

  /** paint order, over the whole selection so a group keeps its own stacking */
  const reorderSelection = useCallback((where: Reorder) => {
    const picked = selectionRef.current
    if (!picked.length) return
    // front and up walk forwards, back and down backwards, so a multi-node
    // move keeps the group stacked the way it already was
    const order = where === 'front' || where === 'up' ? picked : [...picked].reverse()
    apply(st => order.reduce((acc, p) => reorderNode(acc, p.scene, p.id, where), st))
  }, [apply])

  const reorderTo = useCallback((scene: string, id: string, beforeId: string | null) => {
    apply(st => moveNodeBefore(st, scene, id, beforeId))
  }, [apply])

  /** an edit that touches the overlay rather than the stage */
  const applyAnim = useCallback((fn: (anim: Anim) => Anim | null) => {
    snapshot()
    let changed = false
    setDoc(prev => {
      if (!prev) return prev
      const next = fn(prev.anim)
      if (!next || next === prev.anim) return prev
      changed = true
      return { ...prev, anim: next }
    })
    if (changed) { setRev(r => r + 1); setDirty(true) }
  }, [snapshot])

  /**
   * Running a prompt. Motion comes back as a proposal rather than an edit: it
   * is shown, and only lands on the document when it is accepted. Image and
   * vector make a node straight away, because there is nothing to judge until
   * you can see it on the board.
   */
  const runAi = useCallback(async (
    kind: AiKind, prompt: string, model: string, extra: Record<string, unknown>,
  ) => {
    const current = docRef.current
    if (!current) return
    setAiBusy(true)
    setAiError(null)
    try {
      if (kind === 'screen') {
        const target = sceneRef.current ?? current.stage.scenes[0]?.id
        if (!target) throw new Error('no scene to compose into')
        const accent = filmAccent(current.stage)
        const out = await askScreen({
          prompt, model,
          size: current.stage.size,
          accent,
          blocks: BLOCKS.map(b => ({
            key: b.key, name: b.name, blurb: b.blurb, slots: b.slots.map(s => s.key),
          })),
        })
        if (!out.place.length) throw new Error('the model placed nothing it could build')
        // materialise through the library, so the geometry is the corpus's and
        // not the model's, then run the budget on what will actually land
        let stage = current.stage
        const nodes: Node[] = []
        for (const p of out.place) {
          const def = blockByKey(p.block)
          if (!def) continue
          const made = def.make({ stage, accent, x: p.x, y: p.y }, p.opts ?? {})
          nodes.push(...made)
          // each block must see the ids the last one took
          stage = { ...stage, scenes: stage.scenes.map(sc =>
            sc.id === target ? { ...sc, nodes: [...sc.nodes, ...made] } : sc) }
        }
        const density = checkDensity(nodes)
        setScreen({
          note: out.note, nodes, bg: out.bg,
          fit: [...checkFit(nodes, current.stage.size), ...(density ? [density] : [])],
        })
        return
      }
      if (kind === 'motion') {
        const picked = selectionRef.current
        const sceneId = picked[0]?.scene ?? sceneRef.current
        const index = current.stage.scenes.findIndex(s => s.id === sceneId)
        const sc = current.stage.scenes[index]
        if (!sc) throw new Error('select something on a board first')
        const ids = new Set(picked.map(p => p.id))
        const nodes = sc.nodes.filter(n => ids.has(n.id))
        const tracks = (current.anim.tracks ?? []).filter(t => ids.has(t.target as string))
        const out = await askMotion({
          prompt, model,
          ...motionContext(sc, nodes, tracks, index, current.stage.scenes.length),
        })
        if (!out.tracks.length) throw new Error('the model proposed nothing that applies here')
        setProposal(out)
        return
      }
      const target = sceneRef.current ?? current.stage.scenes[0]?.id
      if (!target) throw new Error('no scene to put it in')
      const [cw, ch] = current.stage.size

      if (kind === 'image') {
        const out = await askImage({ prompt, model, ...extra })
        if (ck) await ensureImage(ck, current, out.dataUrl)
        const node = newImage(current.stage, out.dataUrl, cw / 2, ch / 2)
        apply(st => addNode(st, target, node))
        setSel({ scene: target, id: node.id })
        setExtra([])
      } else {
        const out = await askVector({ prompt, model, ...extra })
        const node = newSvg(current.stage, out.svg, cw / 2, ch / 2)
        if (!node) throw new Error('that svg had no drawable outline')
        apply(st => addNode(st, target, node))
        setSel({ scene: target, id: node.id })
        setExtra([])
      }
      setAi(null)
    } catch (e) {
      setAiError(e instanceof Error ? e.message : String(e))
    } finally {
      setAiBusy(false)
    }
  }, [apply, ck])

  /** accept a composed screen: its blocks land in the scene you were looking at */
  const acceptScreen = useCallback(() => {
    const target = selRef.current?.scene ?? sceneRef.current ?? docRef.current?.stage.scenes[0]?.id
    if (!screen || !target) return
    apply(st => {
      let next = screen.nodes.reduce((acc, n) => addNode(acc, target, n), st)
      if (screen.bg) {
        next = { ...next, scenes: next.scenes.map(s => (s.id === target ? { ...s, bg: screen.bg } : s)) }
      }
      return next
    })
    const group = screen.nodes.find(n => n.type === 'group')
    if (group) { setSel({ scene: target, id: group.id }); setExtra([]) }
    setScreen(null)
    setAi(null)
  }, [screen, apply])

  /** accept a motion proposal: its tracks replace what those nodes had */
  const acceptProposal = useCallback(() => {
    if (!proposal) return
    const targets = new Set(proposal.tracks.map(t => t.target as string))
    applyAnim(a => ({
      ...a,
      tracks: [
        ...(a.tracks ?? []).filter(t => !targets.has(t.target as string)),
        ...proposal.tracks,
      ],
    }))
    setProposal(null)
    setAi(null)
  }, [proposal, applyAnim])

  /**
   * Grouping.
   *
   * The container's centre is the middle of what it holds, measured off what
   * is actually painted rather than the authored x/y, because a text node's
   * box is decided by its shaping and only the renderer knows it.
   */
  const groupSelection = useCallback(() => {
    const picked = selectionRef.current
    const current = docRef.current
    if (picked.length < 2 || !current) return
    const scene = picked[0].scene
    if (picked.some(p => p.scene !== scene)) return
    const box = groupBox(boxesRef.current, scene, picked.map(p => p.id))
    if (!box) return
    let made: string | null = null
    apply(st => {
      const out = groupNodes(st, scene, picked.map(p => p.id),
                            { x: box.x + box.w / 2, y: box.y + box.h / 2 })
      if (!out) return null
      made = out.id
      return out.stage
    })
    if (made) { setSel({ scene, id: made }); setExtra([]); setInside(null) }
  }, [apply])

  const ungroupSelection = useCallback(() => {
    const picked = selectionRef.current
    const current = docRef.current
    if (!picked.length || !current) return
    const scene = picked[0].scene
    // ungroup what is selected, or the group you are standing inside
    const ids = picked
      .filter(p => current.stage.scenes.find(s => s.id === scene)?.nodes
        .some(n => n.id === p.id && n.type === 'group'))
      .map(p => p.id)
    const targets = ids.length ? ids : insideRef.current ? [insideRef.current] : []
    if (!targets.length) return
    let freed: string[] = []
    apply(st => {
      const out = ungroupNodes(st, scene, targets)
      if (!out) return null
      freed = out.ids
      return out.stage
    })
    setInside(null)
    if (freed.length) {
      setSel({ scene, id: freed[0] })
      setExtra(freed.slice(1).map(id => ({ scene, id })))
    }
  }, [apply])

  /** stepping out selects the container you were inside */
  const exitGroup = useCallback(() => {
    const g = insideRef.current
    const scene = selRef.current?.scene ?? sceneRef.current
    setInside(null)
    if (g && scene) { setSel({ scene, id: g }); setExtra([]); setSelBox(null) }
  }, [])

  const copyStyleFrom = useCallback(() => {
    const current = docRef.current
    const s = selRef.current
    if (current && s) copyStyle(current, s)
  }, [])

  const pasteStyleTo = useCallback(() => {
    const style = styleClip.get()
    const picked = selectionRef.current
    if (style && picked.length) apply(st => applyStyle(st, picked, style))
  }, [apply])

  const copyMotionFrom = useCallback(() => {
    const current = docRef.current
    const s = selRef.current
    if (current && s) copyMotion(current, s)
  }, [])

  const pasteMotionTo = useCallback(() => {
    const tracks = motionClip.get()
    const picked = selectionRef.current
    if (tracks?.length && picked.length) applyAnim(a => applyMotion(a, picked, tracks))
  }, [applyAnim])

  const clearMotionOn = useCallback(() => {
    const picked = selectionRef.current
    if (picked.length) applyAnim(a => clearMotion(a, picked))
  }, [applyAnim])

  /** put the selection's motion at the playhead, which is where you are looking */
  const startAtPlayhead = useCallback((local: number) => {
    const picked = selectionRef.current
    if (!picked.length) return
    const at = Math.round(local * 30) / 30
    snapshot()
    for (const p of picked) patchMotionFor(p.id, { at: Number(at.toFixed(4)) }, true)
  }, [patchMotionFor, snapshot])

  const createScene = useCallback((afterId?: string) => {
    let id: string | null = null
    apply(st => {
      const out = addScene(st, afterId ?? sceneRef.current ?? undefined)
      id = out.id
      return out.stage
    })
    if (id) { setScene(id); setSel(null); setExtra([]); setSelBox(null) }
  }, [apply])

  const renameScene = useCallback((id: string, name: string) => {
    const next = name.replace(/^\d+\s+/, '').trim()
    if (next && next !== id) patchScene(id, { id: next })
  }, [patchScene])

  // refs so the key handler stays mounted once and still sees current state
  const selRef = useRef<Sel | null>(null)
  const selectionRef = useRef<Sel[]>([])
  const copyRef = useRef<() => void>(() => {})
  const pasteRef = useRef<() => void>(() => {})
  const reorderRef = useRef<(w: Reorder) => void>(() => {})
  const selectAllRef = useRef<() => void>(() => {})
  const nudgeRef = useRef<(dx: number, dy: number) => void>(() => {})
  const groupRef = useRef<() => void>(() => {})
  const ungroupRef = useRef<() => void>(() => {})
  const exitGroupRef = useRef<() => void>(() => {})
  /** the painted geometry of the current frame, kept off the render path */
  const boxesRef = useRef<NodeBox[]>([])
  const takeBoxes = useCallback((b: NodeBox[]) => { boxesRef.current = b }, [])
  const insideRef = useRef<string | null>(null)
  const copyStyleRef = useRef<() => void>(() => {})
  const pasteStyleRef = useRef<() => void>(() => {})
  const copyMotionRef = useRef<() => void>(() => {})
  const pasteMotionRef = useRef<() => void>(() => {})
  const nodeRef = useRef<ReturnType<typeof findNode> extends infer T
    ? T extends { node: infer N } ? N | null : null : null>(null)
  const patchNodeRef = useRef<(p: NodePatch) => void>(() => {})
  const docRef = useRef<Doc | null>(null)
  const saveRef = useRef<() => void>(() => {})
  const sceneRef = useRef<string | null>(null)
  const modeRef = useRef<'design' | 'motion'>('design')
  const removeRef = useRef<() => void>(() => {})
  const duplicateRef = useRef<() => void>(() => {})

  const filmDur = doc ? docDur(doc.stage) : 0
  const motionAt = doc ? sceneAt(doc, playhead) : { index: 0, id: '', local: 0 }

  // playback: one clock, wrapping at the end of the film
  useEffect(() => {
    if (!playing || !filmDur) return
    let last = performance.now()
    const tick = (now: number) => {
      const dt = (now - last) / 1000
      last = now
      setPlayhead(p => (p + dt) % filmDur)
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [playing, filmDur])

  // leaving motion mode should not leave a clock running
  useEffect(() => { if (mode !== 'motion') setPlaying(false) }, [mode])

  const boards = useMemo(() => (doc ? artboards(doc) : []), [doc])
  const layers = useMemo(() => (doc ? tree(doc) : []), [doc])
  const found = useMemo(() => (doc ? findNode(doc, sel) : null), [doc, sel])
  /** the primary node first, then everything else picked with it */
  const selection = useMemo(() => (sel ? [sel, ...extra] : []), [sel, extra])
  const artboard = boards.find(b => b.id === scene) ?? null

  /** what the prompt bar says it will act on, so you can see it before sending */
  const aiSubject = ai === 'motion'
    ? (selection.length > 1 ? `${selection.length} nodes` : sel?.id ?? 'nothing selected')
    : scene
      ? `into ${scene}`
      : ''

  /**
   * What the right-click menu offers. Design mode is about the object, motion
   * mode is about its timing, and the two share ordering and deletion because
   * those mean the same thing in both.
   */
  const menuItems: Item[] = useMemo(() => {
    const one = sel
    const many = selection.length
    const node = found?.node ?? null
    const has = many > 0
    const label = many > 1 ? `${many} nodes` : one?.id ?? ''

    if (!has) {
      return [
        { label: 'Paste', keys: '⌘V', disabled: !clipboard.has(), run: () => pasteRef.current() },
        { label: 'Select all in scene', keys: '⌘A', run: () => selectAllRef.current() },
        { sep: true },
        { label: 'Add scene after this', run: () => createScene(scene ?? undefined) },
        {
          label: 'Delete scene', danger: true, disabled: !scene,
          run: () => { if (scene) apply(st => deleteScene(st, scene)) },
        },
      ]
    }

    const shared: Item[] = [
      { sep: true },
      { label: 'Bring to front', keys: '⇧⌘]', run: () => reorderRef.current('front') },
      { label: 'Bring forward', keys: '⌘]', run: () => reorderRef.current('up') },
      { label: 'Send backward', keys: '⌘[', run: () => reorderRef.current('down') },
      { label: 'Send to back', keys: '⇧⌘[', run: () => reorderRef.current('back') },
      { sep: true },
      { label: `Delete ${label}`, keys: '⌫', danger: true, run: () => removeRef.current() },
    ]

    if (mode === 'motion') {
      return [
        {
          label: 'Copy motion', keys: '⌥⌘C', disabled: many !== 1,
          run: copyMotionFrom,
        },
        {
          label: many > 1 ? `Paste motion onto ${many}` : 'Paste motion', keys: '⌥⌘V',
          disabled: !motionClip.has(), run: pasteMotionTo,
        },
        { label: 'Clear motion', run: clearMotionOn },
        { sep: true },
        {
          label: `Start at playhead  ${motionAt.local.toFixed(2)}s`,
          run: () => startAtPlayhead(motionAt.local),
        },
        ...shared,
      ]
    }

    return [
      {
        label: 'Edit text', keys: '⏎', disabled: node?.type !== 'text' || many !== 1,
        run: () => setEditRequest(n => n + 1),
      },
      { sep: true },
      { label: 'Copy', keys: '⌘C', run: () => copyRef.current() },
      { label: 'Paste', keys: '⌘V', disabled: !clipboard.has(), run: () => pasteRef.current() },
      { label: 'Duplicate', keys: '⌘D', run: () => duplicateRef.current() },
      { sep: true },
      {
        label: many > 1 ? `Group ${many} nodes` : 'Group', keys: '⌘G',
        disabled: many < 2, run: () => groupRef.current(),
      },
      {
        label: 'Ungroup', keys: '⇧⌘G',
        disabled: node?.type !== 'group' && !inside,
        run: () => ungroupRef.current(),
      },
      { sep: true },
      { label: 'Copy styles', keys: '⌥⌘C', disabled: many !== 1, run: copyStyleFrom },
      {
        label: many > 1 ? `Paste styles onto ${many}` : 'Paste styles', keys: '⌥⌘V',
        disabled: !styleClip.has(), run: pasteStyleTo,
      },
      ...shared,
    ]
  }, [
    sel, selection.length, found, mode, scene, motionAt.local, inside, apply, createScene,
    copyMotionFrom, pasteMotionTo, clearMotionOn, startAtPlayhead, copyStyleFrom,
    pasteStyleTo,
  ])
  selRef.current = sel
  selectionRef.current = selection
  copyRef.current = copySelection
  pasteRef.current = paste
  reorderRef.current = reorderSelection
  selectAllRef.current = selectAll
  nudgeRef.current = nudge
  groupRef.current = groupSelection
  ungroupRef.current = ungroupSelection
  exitGroupRef.current = exitGroup
  insideRef.current = inside
  copyStyleRef.current = copyStyleFrom
  pasteStyleRef.current = pasteStyleTo
  copyMotionRef.current = copyMotionFrom
  pasteMotionRef.current = pasteMotionTo
  nodeRef.current = found?.node ?? null
  patchNodeRef.current = patchNode
  docRef.current = doc
  if (import.meta.env.DEV) {
    const w = window as unknown as Record<string, unknown>
    w.__doc = doc
    w.__sel = { sel, extra, inside, geo: found?.node ?? null }
  }
  saveRef.current = save
  sceneRef.current = scene
  modeRef.current = mode
  removeRef.current = removeSelection
  duplicateRef.current = duplicateSelection

  const onZoom = useCallback((z: number) => setZoom(z), [])
  const onGround = useCallback((h: string, a: number) => {
    setGround(h)
    setGroundAlpha(a)
  }, [])
  const onSelect = useCallback((box: NodeBox | null, row: number, additive = false) => {
    setSeam(null)
    setSelRow(row)
    if (!box) { setSel(null); setExtra([]); setSelBox(null); return }
    // a click lands on the container, not the contents, until you go inside
    const g = docRef.current ? groupOf(docRef.current.stage, box.scene, box.id) : null
    const hit: Sel = g && g !== inside ? { scene: box.scene, id: g } : { scene: box.scene, id: box.id }
    setScene(box.scene)

    if (!additive) {
      setSel(hit)
      setExtra([])
      setSelBox(hit.id === box.id ? box : null)
      return
    }
    // shift-clicking the primary promotes the next one rather than leaving the
    // set headless, and shift-clicking a follower just drops it
    const current = selectionRef.current
    if (current.some(p => p.id === hit.id && p.scene === hit.scene)) {
      const rest = current.filter(p => !(p.id === hit.id && p.scene === hit.scene))
      setSel(rest[0] ?? null)
      setExtra(rest.slice(1))
      if (!rest.length) setSelBox(null)
      return
    }
    setSel(hit)
    setExtra(current)
    setSelBox(box)
  }, [inside])

  /** what a marquee sweep landed on, replacing the selection wholesale */
  const onSelectMany = useCallback((picked: Sel[], row: number) => {
    setSeam(null)
    setSelRow(row)
    setSel(picked[0] ?? null)
    setExtra(picked.slice(1))
    if (picked[0]) setScene(picked[0].scene)
    if (!picked.length) setSelBox(null)
  }, [])
  const onMeasure = useCallback((box: NodeBox | null) => setSelBox(box), [])

  if (error)
    return <div className="grid h-full place-items-center text-dim">{error}</div>
  if (!ck || !doc)
    return <div className="grid h-full place-items-center text-dim">booting engine</div>

  return (
    <div className="relative flex h-full w-full">
      {!panels && (
        <button
          onClick={() => setPanels(true)}
          className="absolute left-3 top-3 z-30 flex h-[34px] items-center gap-2.5
                     rounded-[8px] border border-black/10 bg-panel px-3
                     shadow-[0_6px_20px_-8px_rgba(0,0,0,0.4)]"
        >
          <span className="relative block h-3 w-3">
            <span className="absolute left-0 top-0 h-2 w-2 rounded-[2px] bg-black/70" />
            <span className="absolute bottom-0 right-0 h-2 w-2 rounded-[2px] bg-black/30" />
          </span>
          <span className="font-medium">{doc.entry.title}</span>
        </button>
      )}
      {panels && <LeftPanel
        registry={registry}
        film={film}
        onPickFilm={pickFilm}
        pages={['Page 1']}
        activePage="Page 1"
        tree={layers}
        selected={sel}
        others={extra}
        activeScene={scene}
        onReorder={reorderTo}
        onSelectNode={(s, id, additive) => {
          setScene(s)
          if (!additive) { setSel({ scene: s, id }); setExtra([]); return }
          const current = selectionRef.current
          if (current.some(p => p.id === id && p.scene === s)) {
            const rest = current.filter(p => !(p.id === id && p.scene === s))
            setSel(rest[0] ?? null)
            setExtra(rest.slice(1))
            return
          }
          setSel({ scene: s, id })
          setExtra(current)
        }}
        onSelectScene={s => { setScene(s); setSel(null); setExtra([]); setSelBox(null) }}
        mode={mode}
        onMode={setMode}
        onRename={renameScene}
        onHidePanels={() => setPanels(false)}
        onAddScene={() => createScene()}
        onExport={() => setExporting(true)}
        dirty={dirty}
        saving={saving}
        saveError={saveError}
        onSave={save}
      />}
      <ToolRail
        tool={tool}
        onTool={t => {
          if (t === 'add') { setBlocks(true); return }
          if (t === 'image') { setPicking(true); return }
          if (t === 'shader') { setEffects(true); return }
          if (t in AI_TOOLS) {
            const kind = AI_TOOLS[t as keyof typeof AI_TOOLS]
            // clicking the same one again closes it, the way a panel toggle reads
            setAi(prev => (prev === kind ? null : kind))
            setProposal(null)
            setAiError(null)
            return
          }
          setTool(t)
        }}
        floating={!panels}
      />
      {menu && (
        <ContextMenu x={menu.x} y={menu.y} items={menuItems} onClose={() => setMenu(null)} />
      )}

      {blocks && doc && (
        <BlockPicker
          accent={filmAccent(doc.stage)}
          onInsert={insertBlock}
          onClose={() => setBlocks(false)}
        />
      )}

      {picking && (
        <AssetPicker onClose={() => setPicking(false)}
                     onPick={a => { void insertImage(a.src) }} />
      )}
      {effects && (
        <EffectPicker node={found?.node ?? null} onClose={() => setEffects(false)}
                      onApply={patchNode} />
      )}
      {exporting && (
        <ExportDialog
          slug={doc.entry.slug}
          title={doc.entry.title}
          stage={doc.stage}
          anim={doc.anim}
          dur={filmDur}
          onClose={() => setExporting(false)}
        />
      )}
      <div className="relative flex min-w-0 flex-1 flex-col">
        {ai && (
          <AIBar
            kind={ai}
            caps={caps}
            subject={aiSubject}
            busy={aiBusy}
            error={aiError}
            proposal={ai === 'motion' ? proposal : null}
            screen={ai === 'screen' ? screen : null}
            onAcceptScreen={acceptScreen}
            onDiscardScreen={() => setScreen(null)}
            onRun={(prompt, model, extra) => void runAi(ai, prompt, model, extra)}
            onAccept={acceptProposal}
            onDiscard={() => setProposal(null)}
            onClose={() => { setAi(null); setProposal(null); setScreen(null); setAiError(null) }}
          />
        )}
        <Canvas
        ck={ck}
        doc={doc}
        rev={rev}
        ground={ground}
        title={[doc.entry.title, 'json in, launch film out']}
        boards={boards}
        selected={sel}
        selRow={selRow}
        onSelect={onSelect}
        others={extra}
        onSelectMany={onSelectMany}
        onSelectScene={s => { setScene(s); setSel(null); setExtra([]); setSelBox(null) }}
        activeScene={scene}
        tool={tool}
        onCreate={createNode}
        onAddScene={createScene}
        onCreatePath={createPath}
        onToolDone={() => setTool('select')}
        mode={mode}
        playhead={playhead}
        selectedSeam={seam}
        onSelectSeam={id => { setSeam(id); if (id) { setSel(null); setExtra([]); setSelBox(null) } }}
        onZoom={onZoom}
        geo={found ? {
          x: found.node.x ?? 0,
          y: found.node.y ?? 0,
          w: found.node.w ?? selBox?.w ?? 0,
          h: found.node.h ?? selBox?.h ?? 0,
          ...(found.node.type === 'text'
            ? { fontSize: found.node.font?.size ?? 48 }
            : {}),
        } : null}
        onDrag={onDrag}
        onDragEnd={onDragEnd}
        onEditText={text => patchNode({ text }, true)}
        onEditStart={snapshot}
        onEditEnd={commit => { if (!commit) undo.current.pop() }}
        editRequest={editRequest}
        inside={inside}
        onEnterGroup={setInside}
        onBoxes={takeBoxes}
        onContext={(x, y) => setMenu({ x, y })}
        onSelectTarget={(s, id) => { setSel({ scene: s, id }); setExtra([]); setScene(s) }}
        onShiftTrack={(target, at, done) => motionGesture(target, { at }, done)}
        onMeasure={onMeasure}
        />
        {mode === 'motion' && (
          <Timeline
            doc={doc}
            dur={filmDur}
            t={playhead}
            playing={playing}
            selected={sel}
            onSeek={v => { setPlaying(false); setPlayhead(v) }}
            onPlay={setPlaying}
            onSelectNode={(s, id) => { setSel({ scene: s, id }); setScene(s) }}
            onRetime={(target, prop, keys, done) =>
              motionGesture(target, { keys: { [prop]: keys } }, done)}
            onShiftTrack={(target, at, done) =>
              motionGesture(target, { at }, done)}
          />
        )}
      </div>
      {panels && <RightPanel
        ground={ground}
        groundAlpha={groundAlpha}
        onGround={onGround}
        zoom={zoom}
        selection={found ? null : artboard}
        node={found?.node ?? null}
        nodeBox={selBox}
        canvas={doc.stage.size}
        onPatch={patchScene}
        onPatchNode={patchNode}
        mode={mode}
        tracks={sel ? tracksFor(doc.anim, sel.id) : []}
        sceneId={scene}
        localTime={motionAt.local}
        sceneDur={doc.stage.scenes.find(s => s.id === motionAt.id)?.dur ?? 3}
        onPatchMotion={patchMotion}
        seam={seam ? boards.find(b => b.id === seam) ?? null : null}
        seamFrom={seam
          ? boards[boards.findIndex(b => b.id === seam) - 1] ?? null
          : null}
        onPatchSeam={t => { if (seam) patchScene(seam, { transition: t }) }}
      />}
    </div>
  )
}
