import { useCallback, useEffect, useMemo, useState } from 'react'
import LeftPanel from './components/LeftPanel'
import ToolRail from './components/ToolRail'
import type { Tool } from './components/ToolRail'
import Canvas from './components/Canvas'
import RightPanel from './components/RightPanel'
import { boot, loadDoc } from './engine'
import type { Doc, Entry } from './engine/types'
import { artboards, layers } from './doc'

/** the film boards opens on; ?film=<slug> picks another out of the registry */
const DEFAULT_FILM = 'whippan'

export default function App() {
  const [ck, setCk] = useState<CanvasKit | null>(null)
  const [doc, setDoc] = useState<Doc | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [tool, setTool] = useState<Tool>('select')
  const [selected, setSelected] = useState<string | null>(null)
  const [zoom, setZoom] = useState(0.55)
  const [ground, setGround] = useState('#d9cac8')
  const [groundAlpha, setGroundAlpha] = useState(1)

  useEffect(() => {
    const slug = new URLSearchParams(location.search).get('film') ?? DEFAULT_FILM
    boot().then(({ CK, registry }) => {
      setCk(CK)
      const entry: Entry | undefined =
        registry.find(e => e.slug === slug) ?? registry[0]
      if (!entry) { setError('empty registry'); return }
      document.title = `${entry.title} · whippan boards`
      return loadDoc(entry).then(setDoc)
    }).catch(e => setError(String(e)))
  }, [])

  const boards = useMemo(() => (doc ? artboards(doc) : []), [doc])
  const tree = useMemo(() => (doc ? layers(doc) : []), [doc])
  const selection = boards.find(b => b.id === selected) ?? null
  const onZoom = useCallback((z: number) => setZoom(z), [])
  const onGround = useCallback((h: string, a: number) => {
    setGround(h)
    setGroundAlpha(a)
  }, [])

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
        layers={tree}
        selected={selected}
        onSelect={setSelected}
      />
      <ToolRail tool={tool} onTool={setTool} />
      <Canvas
        ck={ck}
        doc={doc}
        ground={ground}
        title={[doc.entry.title, 'json in, launch film out']}
        boards={boards}
        selected={selected}
        onSelect={setSelected}
        onZoom={onZoom}
      />
      <RightPanel
        ground={ground}
        groundAlpha={groundAlpha}
        onGround={onGround}
        zoom={zoom}
        selection={selection}
      />
    </div>
  )
}
