import { useRef, useState } from 'react'
import { ChevronDown, ChevronRight, FileIcon, Frame, PanelIcon, Plus, Rect, TypeMark } from '../icons'
import FilmMenu from './FilmMenu'
import type { Sel } from '../doc'
import type { Entry } from '../engine/types'

interface TreeNode {
  id: string
  kind: string
  label: string
  /** 0 for a loose node or a container, 1 for a group's member */
  depth: number
}

interface TreeScene {
  scene: string
  label: string
  nodes: TreeNode[]
}

interface Props {
  registry: Entry[]
  film: string
  onPickFilm(slug: string): void
  pages: string[]
  activePage: string
  tree: TreeScene[]
  selected: Sel | null
  /** the rest of the selection, highlighted the same way */
  others: Sel[]
  activeScene: string | null
  onSelectNode(scene: string, id: string, additive?: boolean): void
  /** drop a layer just behind `beforeId` in paint order, or null for the front */
  onReorder(scene: string, id: string, beforeId: string | null): void
  onSelectScene(scene: string): void
  onRename(id: string, name: string): void
  onHidePanels(): void
  onAddScene(): void
  onExport(): void
  mode: 'design' | 'motion'
  onMode(m: 'design' | 'motion'): void
  dirty: boolean
  saving: 'idle' | 'saving' | 'saved' | 'error'
  saveError: string | null
  onSave(): void
}

function kindIcon(kind: string) {
  if (kind === 'group') return <Frame size={11} />
  if (kind === 'text') return <TypeMark className="text-dim" />
  if (kind === 'image' || kind === 'seq') return <Rect size={11} />
  return <Rect size={11} />
}

function Row({
  depth = 0, icon, label, selected, onClick, onDoubleClick, chevron, open, onToggle,
  onPointerDown, dim, line,
}: {
  depth?: number
  icon: React.ReactNode
  label: string
  selected?: boolean
  onClick?(e: React.MouseEvent): void
  onDoubleClick?(): void
  chevron?: boolean
  open?: boolean
  onToggle?(): void
  onPointerDown?(e: React.PointerEvent): void
  /** the row being dragged, shown as a ghost of itself */
  dim?: boolean
  /** where the drop would land: above this row, or below it for the last gap */
  line?: 'above' | 'below'
}) {
  return (
    <div
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onPointerDown={onPointerDown}
      className={`relative flex h-[26px] w-full cursor-default items-center gap-1.5 pr-2
                  text-left ${dim ? 'opacity-40' : ''}
                  ${selected ? 'bg-row' : 'hover:bg-black/[0.035]'}`}
      style={{ paddingLeft: 8 + depth * 14 }}
    >
      {line && (
        <span className={`pointer-events-none absolute left-2 right-2 h-px bg-[#5e92f4]
                          ${line === 'above' ? 'top-0' : 'bottom-0'}`} />
      )}
      <span
        onClick={e => { e.stopPropagation(); onToggle?.() }}
        className={`grid h-3.5 w-3.5 shrink-0 place-items-center text-faint
                    ${chevron ? '' : 'invisible'}`}
      >
        {open ? <ChevronDown size={9} /> : <ChevronRight size={9} />}
      </span>
      <span className="grid w-4 shrink-0 place-items-center text-dim">{icon}</span>
      <span className="truncate">{label}</span>
    </div>
  )
}

export default function LeftPanel({
  registry, film, onPickFilm,
  pages, activePage, tree, selected, others, activeScene, onReorder,
  onSelectNode, onSelectScene, onRename, onHidePanels, onAddScene, onExport,
  mode, onMode, dirty, saving, saveError, onSave,
}: Props) {
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [editing, setEditing] = useState<string | null>(null)

  const picked = (scene: string, id: string) =>
    (selected?.scene === scene && selected.id === id)
    || others.some(o => o.scene === scene && o.id === id)

  /**
   * Dragging a layer to restack it.
   *
   * The gap the pointer is over is worked out from the row heights rather than
   * from hover events, so the insertion line still tracks when the pointer
   * leaves the panel sideways. Display index 0 is the front of the scene, so
   * the doc index a drop lands on is counted from the other end.
   */
  const lists = useRef<Record<string, HTMLDivElement | null>>({})
  const [drag, setDrag] = useState<
    { scene: string; id: string; from: number; count: number; gap: number } | null
  >(null)
  const live = useRef<typeof drag>(null)

  const beginDrag = (
    e: React.PointerEvent, scene: string, id: string, from: number, count: number,
    rows: TreeNode[],
  ) => {
    if (e.button !== 0) return
    const start = { x: e.clientX, y: e.clientY }
    let armed = false

    const move = (ev: PointerEvent) => {
      if (!armed) {
        if (Math.abs(ev.clientY - start.y) + Math.abs(ev.clientX - start.x) < 4) return
        armed = true
      }
      const box = lists.current[scene]?.getBoundingClientRect()
      if (!box) return
      const row = box.height / Math.max(1, count)
      const gap = Math.max(0, Math.min(count, Math.round((ev.clientY - box.top) / row)))
      const next = { scene, id, from, count, gap }
      live.current = next
      setDrag(next)
    }
    const up = () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
      const d = live.current
      live.current = null
      setDrag(null)
      if (!d || !armed) return
      // dropping into your own gap changes nothing
      const to = d.gap > d.from ? d.gap - 1 : d.gap
      if (to === d.from) return
      // a row only moves among its own siblings: a member cannot be dragged out
      // of its group, and a loose node cannot be dragged into one
      const me = rows[d.from]
      const sibling = (r: TreeNode) => r.depth === me.depth
      // the row it lands above in the list is the one it goes behind in paint
      // order, since the list runs front to back
      let above: TreeNode | null = null
      for (let i = to; i < rows.length; i++) {
        const r = rows[i]
        if (r.id !== id && sibling(r)) { above = r; break }
      }
      onReorder(scene, id, above?.id ?? null)
    }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
  }

  const lineFor = (scene: string, d: number, count: number): 'above' | 'below' | undefined => {
    if (!drag || drag.scene !== scene) return undefined
    if (drag.gap === d) return 'above'
    if (drag.gap === count && d === count - 1) return 'below'
    return undefined
  }

  return (
    <aside className="flex h-full w-panel shrink-0 flex-col bg-panel">
      <div className="flex h-[41px] shrink-0 items-center gap-2.5 border-b border-hair px-3">
        <span className="grid h-[18px] w-[18px] shrink-0 place-items-center">
          <span className="relative block h-3 w-3">
            <span className="absolute left-0 top-0 h-2 w-2 rounded-[2px] bg-black/70" />
            <span className="absolute bottom-0 right-0 h-2 w-2 rounded-[2px] bg-black/30" />
          </span>
        </span>
        <FilmMenu registry={registry} current={film} onPick={onPickFilm} />
        <button
          onClick={onSave}
          title={saveError ?? (dirty ? 'unsaved changes — ⌘S' : 'saved')}
          className={`shrink-0 rounded-[5px] px-1.5 py-0.5 text-[11px] transition-colors
                      ${saving === 'error' ? 'text-[#c0392b]'
                        : dirty ? 'text-flame hover:bg-black/[0.05]'
                        : 'text-faint'}`}
        >
          {saving === 'saving' ? 'saving…'
            : saving === 'error' ? 'failed'
            : saving === 'saved' ? 'saved'
            : dirty ? '• save' : 'saved'}
        </button>
        <button onClick={onHidePanels} title="hide panels"
                className="shrink-0 text-dim transition-colors hover:text-ink">
          <PanelIcon size={15} />
        </button>
      </div>

      {/* the document is two layers, so the app is two modes */}
      <div className="shrink-0 p-2">
        <div className="flex rounded-[7px] bg-black/[0.05] p-[2px]">
          {(['design', 'motion'] as const).map(k => (
            <button
              key={k}
              onClick={() => onMode(k)}
              className={`h-[26px] flex-1 rounded-[5px] capitalize transition-colors
                          ${mode === k
                            ? 'bg-surface font-medium shadow-[0_1px_2px_rgba(0,0,0,0.07)]'
                            : 'text-dim hover:text-ink'}`}
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      <div className="shrink-0">
        <div className="flex h-[26px] items-center gap-1.5 px-2">
          <ChevronDown size={9} className="text-faint" />
          <span className="flex-1 font-medium">Scenes</span>
          <button onClick={onAddScene} title="new scene"
                  className="text-dim transition-colors hover:text-ink">
            <Plus size={12} />
          </button>
        </div>
        {pages.map(p => (
          <Row key={p} icon={<FileIcon size={12} />} label={p} selected={p === activePage} />
        ))}
      </div>

      <div className="my-2 h-px shrink-0 bg-hair" />

      <div className="min-h-0 flex-1 overflow-y-auto pb-4">
        {tree.map(s => (
          <div key={s.scene}>
            {editing === s.scene ? (
              <div className="flex h-[26px] items-center gap-1.5 pl-[30px] pr-2">
                <input
                  autoFocus
                  defaultValue={s.label}
                  onBlur={e => { onRename(s.scene, e.target.value.trim()); setEditing(null) }}
                  onKeyDown={e => {
                    if (e.key === 'Enter') (e.target as HTMLInputElement).blur()
                    if (e.key === 'Escape') setEditing(null)
                  }}
                  className="min-w-0 flex-1 rounded-[3px] bg-surface px-1 outline-none
                             ring-2 ring-[#2d52f0]/40"
                />
              </div>
            ) : (
              <Row
                icon={<Frame size={12} />}
                label={s.label}
                chevron
                open={open[s.scene]}
                onToggle={() => setOpen(o => ({ ...o, [s.scene]: !o[s.scene] }))}
                selected={!selected && activeScene === s.scene}
                onClick={() => onSelectScene(s.scene)}
                onDoubleClick={() => setEditing(s.scene)}
              />
            )}
            {open[s.scene] && (
              <div ref={el => { lists.current[s.scene] = el }}>
                {/* topmost first, the way every layer list reads; the document
                    stores them the other way round, which is paint order */}
                {[...s.nodes].reverse().map((n, d) => (
                  <Row
                    key={n.id}
                    depth={1 + n.depth}
                    icon={kindIcon(n.kind)}
                    label={n.label}
                    selected={picked(s.scene, n.id)}
                    dim={drag?.id === n.id && drag.scene === s.scene}
                    line={lineFor(s.scene, d, s.nodes.length)}
                    onPointerDown={e =>
                      beginDrag(e, s.scene, n.id, d, s.nodes.length, [...s.nodes].reverse())}
                    onClick={e => onSelectNode(s.scene, n.id, e.shiftKey || e.metaKey || e.ctrlKey)}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="shrink-0 border-t border-hair px-2 py-2">
        <button
          onClick={onExport}
          className="inset-control flex h-[28px] w-full items-center justify-center gap-2
                     transition-colors hover:bg-black/[0.02]"
        >
          <span>Export</span>
          <span className="text-faint">⇧⌘E</span>
        </button>
      </div>

      <div className="flex h-9 shrink-0 items-center gap-2 px-3 text-dim">
        <button className="transition-colors hover:text-ink">What&apos;s new</button>
        <span className="text-faint">·</span>
        <button className="transition-colors hover:text-ink">Feedback</button>
      </div>
    </aside>
  )
}
