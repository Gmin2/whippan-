import { useState } from 'react'
import { ChevronDown, ChevronRight, FileIcon, Frame, PanelIcon, Plus, TypeMark } from '../icons'
import type { Layer } from '../doc'

interface Props {
  title: string
  pages: string[]
  activePage: string
  layers: Layer[]
  selected: string | null
  onSelect(id: string): void
}

function Row({ depth = 0, icon, label, selected, onClick, chevron }: {
  depth?: number
  icon: React.ReactNode
  label: string
  selected?: boolean
  onClick?(): void
  chevron?: boolean
}) {
  const [open, setOpen] = useState(false)
  return (
    <button
      onClick={onClick}
      className={`flex h-[26px] w-full items-center gap-1.5 pr-2 text-left
                  ${selected ? 'bg-row' : 'hover:bg-black/[0.035]'}`}
      style={{ paddingLeft: 8 + depth * 14 }}
    >
      <span
        onClick={e => { e.stopPropagation(); setOpen(o => !o) }}
        className={`grid h-3.5 w-3.5 shrink-0 place-items-center text-faint
                    ${chevron ? '' : 'invisible'}`}
      >
        {open ? <ChevronDown size={9} /> : <ChevronRight size={9} />}
      </span>
      <span className="grid w-4 shrink-0 place-items-center text-dim">{icon}</span>
      <span className="truncate">{label}</span>
    </button>
  )
}

export default function LeftPanel({ title, pages, activePage, layers, selected, onSelect }: Props) {
  const [tab, setTab] = useState<'design' | 'theme'>('design')

  return (
    <aside className="flex h-full w-panel shrink-0 flex-col bg-panel">
      {/* file row */}
      <div className="flex h-[41px] shrink-0 items-center gap-2.5 border-b border-hair px-3">
        <span className="grid h-[18px] w-[18px] shrink-0 place-items-center">
          <span className="relative block h-3 w-3">
            <span className="absolute left-0 top-0 h-2 w-2 rounded-[2px] bg-black/70" />
            <span className="absolute bottom-0 right-0 h-2 w-2 rounded-[2px] bg-black/30" />
          </span>
        </span>
        <span className="flex-1 truncate font-medium">{title}</span>
        <button className="text-dim transition-colors hover:text-ink" title="hide panels">
          <PanelIcon size={15} />
        </button>
      </div>

      {/* design / theme segmented control */}
      <div className="shrink-0 p-2">
        <div className="flex rounded-[7px] bg-black/[0.05] p-[2px]">
          {(['design', 'theme'] as const).map(k => (
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

      {/* pages */}
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

      {/* layer tree */}
      <div className="min-h-0 flex-1 overflow-y-auto pb-4">
        {layers.map(l => (
          <Row
            key={l.id}
            icon={l.kind === 'text' ? <TypeMark className="text-dim" /> : <Frame size={12} />}
            label={l.name}
            chevron={l.kind === 'frame'}
            selected={l.id === selected}
            onClick={() => onSelect(l.id)}
          />
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
