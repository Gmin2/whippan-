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
  const [doc, setDoc] = useState<Doc | null>(null)
  const [error, setError] = useState<string | null>(null)
  // every accepted edit bumps this, which re-renders the affected boards
  const [rev, setRev] = useState(0)

  const [tool, setTool] = useState<Tool>('select')
  const [sel, setSel] = useState<Sel | null>(null)
  const [selBox, setSelBox] = useState<NodeBox | null>(null)
  const [scene, setScene] = useState<string | null>(null)
  const [zoom, setZoom] = useState(0.12)
  const [ground, setGround] = useState('#d9cac8')
  const [groundAlpha, setGroundAlpha] = useState(1)
  // undo holds whole stage snapshots. a drag pushes one entry when it starts,
  // not per pointer move, so undoing a drag undoes the whole gesture.
  const undo = useRef<Stage[]>([])
  const redo = useRef<Stage[]>([])
  const dragging = useRef(false)

  useEffect(() => {
    const slug = new URLSearchParams(location.search).get('film') ?? DEFAULT_FILM
    boot().then(({ CK, registry }) => {
      setCk(CK)
      const entry: Entry | undefined = registry.find(e => e.slug === slug) ?? registry[0]
      if (!entry) { setError('empty registry'); return }
      document.title = `${entry.title} · whippan boards`
      // the loader caches by slug, so edit on a copy and leave the cache clean
      return loadDoc(entry).then(d => setDoc({ ...d, stage: structuredClone(d.stage) }))
    }).catch(e => setError(String(e)))
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
            const { fontSize, ...rest } = patch
            const next = { ...n, ...rest }
            if (fontSize != null) next.font = { ...(n.font ?? {}), size: fontSize }
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

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const mod = e.metaKey || e.ctrlKey
      if (mod && e.key.toLowerCase() === 'z') {
        e.preventDefault()
        stepHistory(e.shiftKey ? 'redo' : 'undo')
      }
      if (e.key === 'Escape') { setSel(null); setSelBox(null) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [stepHistory])

  const renameScene = useCallback((id: string, name: string) => {
    const next = name.replace(/^\d+\s+/, '').trim()
    if (next && next !== id) patchScene(id, { id: next })
  }, [patchScene])

  const boards = useMemo(() => (doc ? artboards(doc) : []), [doc])
  const layers = useMemo(() => (doc ? tree(doc) : []), [doc])
  const found = useMemo(() => (doc ? findNode(doc, sel) : null), [doc, sel])
  const artboard = boards.find(b => b.id === scene) ?? null

  const onZoom = useCallback((z: number) => setZoom(z), [])
  const onGround = useCallback((h: string, a: number) => {
    setGround(h)
    setGroundAlpha(a)
  }, [])
  const onSelect = useCallback((box: NodeBox | null) => {
    setSel(box ? { scene: box.scene, id: box.id } : null)
    setSelBox(box)
    if (box) setScene(box.scene)
  }, [])
  const onMeasure = useCallback((box: NodeBox | null) => setSelBox(box), [])

  if (error)
    return <div className="grid h-full place-items-center text-dim">{error}</div>
  if (!ck || !doc)
    return <div className="grid h-full place-items-center text-dim">booting engine</div>

  return (
    <div className="flex h-full w-full">
      <LeftPanel
        title={doc.entry.title}
        pages={['Page 1']}
        activePage="Page 1"
        tree={layers}
        selected={sel}
        activeScene={scene}
        onSelectNode={(s, id) => { setSel({ scene: s, id }); setScene(s) }}
        onSelectScene={s => { setScene(s); setSel(null); setSelBox(null) }}
        onRename={renameScene}
      />
      <ToolRail tool={tool} onTool={setTool} />
      <Canvas
        ck={ck}
        doc={doc}
        rev={rev}
        ground={ground}
        title={[doc.entry.title, 'json in, launch film out']}
        boards={boards}
        selected={sel}
        onSelect={onSelect}
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
      <RightPanel
        ground={ground}
        groundAlpha={groundAlpha}
        onGround={onGround}
        zoom={zoom}
        selection={found ? null : artboard}
        node={found?.node ?? null}
        nodeBox={selBox}
        onPatch={patchScene}
        onPatchNode={patchNode}
      />
    </div>
  )
}
