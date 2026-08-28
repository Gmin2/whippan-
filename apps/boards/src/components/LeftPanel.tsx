import { useState } from 'react'
import { ChevronDown, ChevronRight, FileIcon, Frame, PanelIcon, Plus, Rect, TypeMark } from '../icons'
import FilmMenu from './FilmMenu'
import type { Sel } from '../doc'
import type { Entry } from '../engine/types'

interface TreeNode {
  id: string
  kind: string
  label: string
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
  activeScene: string | null
  onSelectNode(scene: string, id: string): void
  onSelectScene(scene: string): void
  onRename(id: string, name: string): void
  onHidePanels(): void
  dirty: boolean
  saving: 'idle' | 'saving' | 'saved' | 'error'
  saveError: string | null
  onSave(): void
}

function kindIcon(kind: string) {
  if (kind === 'text') return <TypeMark className="text-dim" />
  if (kind === 'image' || kind === 'seq') return <Rect size={11} />
  return <Rect size={11} />
}

function Row({ depth = 0, icon, label, selected, onClick, onDoubleClick, chevron, open, onToggle }: {
  depth?: number
  icon: React.ReactNode
  label: string
  selected?: boolean
  onClick?(): void
  onDoubleClick?(): void
  chevron?: boolean
  open?: boolean
  onToggle?(): void
}) {
  return (
    <div
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      className={`flex h-[26px] w-full cursor-default items-center gap-1.5 pr-2 text-left
                  ${selected ? 'bg-row' : 'hover:bg-black/[0.035]'}`}
      style={{ paddingLeft: 8 + depth * 14 }}
    >
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
  pages, activePage, tree, selected, activeScene,
  onSelectNode, onSelectScene, onRename, onHidePanels,
  dirty, saving, saveError, onSave,
}: Props) {
  const [tab, setTab] = useState<'design' | 'motion'>('design')
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [editing, setEditing] = useState<string | null>(null)

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
              onClick={() => setTab(k)}
              className={`h-[26px] flex-1 rounded-[5px] capitalize transition-colors
                          ${tab === k
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
          <span className="flex-1 font-medium">Pages</span>
          <button className="text-dim transition-colors hover:text-ink" title="new page">
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
            {open[s.scene] && s.nodes.map(n => (
              <Row
                key={n.id}
                depth={1}
                icon={kindIcon(n.kind)}
                label={n.label}
                selected={selected?.scene === s.scene && selected?.id === n.id}
                onClick={() => onSelectNode(s.scene, n.id)}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="flex h-9 shrink-0 items-center gap-2 px-3 text-dim">
        <button className="transition-colors hover:text-ink">What&apos;s new</button>
        <span className="text-faint">·</span>
        <button className="transition-colors hover:text-ink">Feedback</button>
      </div>
    </aside>
  )
}
