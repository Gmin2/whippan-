import { useCallback, useState } from 'react'
import LeftPanel from './components/LeftPanel'
import ToolRail from './components/ToolRail'
import type { Tool } from './components/ToolRail'
import Canvas from './components/Canvas'
import RightPanel from './components/RightPanel'
import { BOARD, LAYERS } from './doc'

export default function App() {
  const [tool, setTool] = useState<Tool>('select')
  const [selected, setSelected] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)

  const selection = BOARD.artboards.find(a => a.id === selected) ?? null
  const onZoom = useCallback((z: number) => setZoom(z), [])

  return (
    <div className="flex h-full w-full">
      <LeftPanel
        title={BOARD.title}
        pages={BOARD.pages}
        activePage={BOARD.activePage}
        layers={LAYERS}
        selected={selected}
        onSelect={setSelected}
      />
      <ToolRail tool={tool} onTool={setTool} />
      <Canvas board={BOARD} selected={selected} onSelect={setSelected} onZoom={onZoom} />
      <RightPanel board={BOARD} zoom={zoom} selection={selection} />
    </div>
  )
}
