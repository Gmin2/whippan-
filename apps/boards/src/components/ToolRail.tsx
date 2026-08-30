import {
  Frame, Gem, Hand, Image, ImageSparkle, Pen, PenSparkle, Pointer, Rect, Sparkle,
  SquarePlus, Transform, TypeMark,
} from '../icons'

export type Tool = 'select' | 'hand' | 'frame' | 'rect' | 'pen' | 'text' | 'add'
  | 'image' | 'transform' | 'shader'
  | 'ai-screen' | 'ai-motion' | 'ai-image' | 'ai-vector'

/** the tools that open the prompt bar rather than changing what a drag does */
export const AI_TOOLS = {
  'ai-screen': 'screen', 'ai-motion': 'motion',
  'ai-image': 'image', 'ai-vector': 'vector',
} as const

interface Props {
  tool: Tool
  onTool(t: Tool): void
  /** with the panels hidden the rail detaches and floats over the canvas */
  floating?: boolean
}

// buttons are 40x36 with dividers between the three groups, measured off the
// paper rail. the active tool is the only filled chip.
const GROUPS: { tool: Tool; icon: React.ReactNode; title: string }[][] = [
  [
    { tool: 'select', icon: <Pointer size={14} />, title: 'select' },
    { tool: 'hand', icon: <Hand size={16} />, title: 'pan' },
  ],
  [
    { tool: 'frame', icon: <Frame size={15} />, title: 'artboard' },
    { tool: 'rect', icon: <Rect size={15} />, title: 'rectangle' },
    { tool: 'pen', icon: <Pen size={16} />, title: 'pen' },
    { tool: 'text', icon: <TypeMark />, title: 'text' },
    { tool: 'add', icon: <SquarePlus size={15} />, title: 'insert' },
  ],
  [
    { tool: 'image', icon: <Image size={15} />, title: 'image' },
    { tool: 'transform', icon: <Transform size={15} />, title: 'transform' },
    { tool: 'shader', icon: <Gem size={15} />, title: 'shader' },
  ],
  [
    { tool: 'ai-screen', icon: <SquarePlus size={14} />, title: 'create screen' },
    { tool: 'ai-motion', icon: <Sparkle size={14} />, title: 'create motion' },
    { tool: 'ai-image', icon: <ImageSparkle size={15} />, title: 'create image' },
    { tool: 'ai-vector', icon: <PenSparkle size={15} />, title: 'create svg' },
  ],
]

export default function ToolRail({ tool, onTool, floating }: Props) {
  return (
    <nav className={floating
      ? `absolute left-3 top-[58px] z-30 flex w-rail flex-col items-center rounded-[10px]
         border border-black/10 bg-panel py-1 shadow-[0_6px_20px_-8px_rgba(0,0,0,0.4)]`
      : 'flex h-full w-rail shrink-0 flex-col items-center border-r border-hair bg-panel pt-0.5'}>
      {GROUPS.map((group, gi) => (
        <div key={gi} className="contents">
          {gi > 0 && <span className="my-2 h-px w-5 bg-hair" />}
          {group.map(b => (
            <button
              key={b.tool}
              title={b.title}
              onClick={() => onTool(b.tool)}
              className={`grid h-9 w-9 shrink-0 place-items-center rounded-md transition-colors
                          ${tool === b.tool
                            ? 'inset-control text-ink'
                            : 'text-ink/70 hover:bg-black/[0.05] hover:text-ink'}`}
            >
              {b.icon}
            </button>
          ))}
        </div>
      ))}
    </nav>
  )
}
