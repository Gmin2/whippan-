import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import LeftPanel from './components/LeftPanel'
import ToolRail from './components/ToolRail'
import type { Tool } from './components/ToolRail'
import Canvas from './components/Canvas'
import RightPanel from './components/RightPanel'
import { boot, loadDoc } from './engine'
import type { Doc, Entry, Stage } from './engine/types'
import { artboards, findNode, tree } from './doc'
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
  const [selBox, setSelBox] = useState<NodeBox | null>(null)
  const [selRow, setSelRow] = useState(0)
  const [scene, setScene] = useState<string | null>(null)
  const [zoom, setZoom] = useState(0.12)
  const [panels, setPanels] = useState(true)
  const [ground, setGround] = useState('#d9cac8')
  const [groundAlpha, setGroundAlpha] = useState(1)
  // undo holds whole stage snapshots. a drag pushes one entry when it starts,
  // not per pointer move, so undoing a drag undoes the whole gesture.
  const undo = useRef<Stage[]>([])
  const redo = useRef<Stage[]>([])
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
        undo.current.push(structuredClone(prev.stage))
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
      const scenes = prev.stage.scenes.map(s => (s.id === id ? { ...s, ...patch } : s))
      return { ...prev, stage: { ...prev.stage, scenes } }
    })
    if (patch.id && patch.id !== id) setScene(patch.id)
    setRev(r => r + 1)
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
              blur, glow, gradient, ...rest
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
  }, [sel, snapshot])

  // a drag streams patches; snapshot once at the start of the gesture
  const onDrag = useCallback((patch: NodePatch) => {
    if (!dragging.current) {
      dragging.current = true
      snapshot()
    }
    patchNode(patch, true)
  }, [patchNode, snapshot])
  const onDragEnd = useCallback(() => { dragging.current = false }, [])

  const stepHistory = useCallback((dir: 'undo' | 'redo') => {
    const from = dir === 'undo' ? undo.current : redo.current
    const to = dir === 'undo' ? redo.current : undo.current
    const stage = from.pop()
    if (!stage) return
    setDoc(prev => {
      if (!prev) return prev
      to.push(structuredClone(prev.stage))
      return { ...prev, stage }
    })
    setRev(r => r + 1)
  }, [])

  // paper's nudge amounts: 1 small, 8 large. arrows with nothing selected pan,
  // which the canvas owns, so only handle them here when there is a selection.
  const NUDGE = { small: 1, large: 8 }
  const TOOL_KEYS: Record<string, Tool> = {
    v: 'select', h: 'hand', f: 'frame', r: 'rect', p: 'pen', t: 'text', s: 'shader',
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const mod = e.metaKey || e.ctrlKey
      const key = e.key.toLowerCase()

      if (mod && key === 'z') {
        e.preventDefault()
        stepHistory(e.shiftKey ? 'redo' : 'undo')
        return
      }
      if (e.key === 'Escape') { setSel(null); setSelBox(null); return }

      const arrows: Record<string, [number, number]> = {
        ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1],
      }
      const dir = arrows[e.key]
      if (dir && selRef.current) {
        e.preventDefault()
        const step = e.shiftKey ? NUDGE.large : NUDGE.small
        const node = nodeRef.current
        if (!node) return
        patchNodeRef.current({
          x: Math.round((node.x ?? 0) + dir[0] * step),
          y: Math.round((node.y ?? 0) + dir[1] * step),
        })
        return
      }

      if (!mod && !e.altKey && TOOL_KEYS[key]) setTool(TOOL_KEYS[key])
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [stepHistory])

  const renameScene = useCallback((id: string, name: string) => {
    const next = name.replace(/^\d+\s+/, '').trim()
    if (next && next !== id) patchScene(id, { id: next })
  }, [patchScene])

  // refs so the key handler stays mounted once and still sees current state
  const selRef = useRef<Sel | null>(null)
  const nodeRef = useRef<ReturnType<typeof findNode> extends infer T
    ? T extends { node: infer N } ? N | null : null : null>(null)
  const patchNodeRef = useRef<(p: NodePatch) => void>(() => {})

  const boards = useMemo(() => (doc ? artboards(doc) : []), [doc])
  const layers = useMemo(() => (doc ? tree(doc) : []), [doc])
  const found = useMemo(() => (doc ? findNode(doc, sel) : null), [doc, sel])
  const artboard = boards.find(b => b.id === scene) ?? null
  selRef.current = sel
  nodeRef.current = found?.node ?? null
  patchNodeRef.current = patchNode

  const onZoom = useCallback((z: number) => setZoom(z), [])
  const onGround = useCallback((h: string, a: number) => {
    setGround(h)
    setGroundAlpha(a)
  }, [])
  const onSelect = useCallback((box: NodeBox | null, row: number) => {
    setSel(box ? { scene: box.scene, id: box.id } : null)
    setSelBox(box)
    setSelRow(row)
    if (box) setScene(box.scene)
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
        activeScene={scene}
        onSelectNode={(s, id) => { setSel({ scene: s, id }); setScene(s) }}
        onSelectScene={s => { setScene(s); setSel(null); setSelBox(null) }}
        onRename={renameScene}
        onHidePanels={() => setPanels(false)}
      />}
      <ToolRail tool={tool} onTool={setTool} floating={!panels} />
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
        onSelectScene={s => { setScene(s); setSel(null); setSelBox(null) }}
        activeScene={scene}
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
        onMeasure={onMeasure}
      />
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
      />}
    </div>
  )
}
