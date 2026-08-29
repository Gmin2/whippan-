// nucleo ui set, inlined. the frame, rect and sidebar glyphs are not in the
// library so they are drawn here as plain geometry rather than pulled from
// some other pack.

type P = { size?: number; className?: string }

const S = (p: P, box: number, children: React.ReactNode) => (
  <svg width={p.size ?? 16} height={p.size ?? 16} viewBox={`0 0 ${box} ${box}`}
       fill="none" stroke="currentColor" strokeWidth="1.5"
       strokeLinecap="round" strokeLinejoin="round" className={p.className}>
    {children}
  </svg>
)

export const Pointer = (p: P) => S(p, 12,
  <path d="m1.455.814l9.367,3.422c.447.163.434.801-.019.946l-4.258,1.363-1.363,4.258c-.145.454-.782.467-.946.019L.814,1.455c-.146-.399.242-.787.641-.641Z" />)

export const Hand = (p: P) => S(p, 18, <>
  <path d="M10.75,8.25V2.5c0-.69-.564-1.25-1.25-1.25s-1.25,.56-1.25,1.25v5.75" />
  <path d="M13.25,8.25V3.25c0-.69-.564-1.25-1.25-1.25s-1.25,.56-1.25,1.25v5" />
  <path d="M8.25,8.25V3.25c0-.69-.564-1.25-1.25-1.25s-1.25,.56-1.25,1.25V12.053" />
  <path d="M5.75,11.215l-1.768-2.252c-.426-.543-1.215-.635-1.755-.211s-.604,1.131-.211,1.755l2.551,3.924c.738,1.135,2,1.82,3.354,1.82h3.83c2.209,0,4-1.791,4-4V4c0-.69-.564-1.25-1.25-1.25s-1.25,.56-1.25,1.25v4.25" />
</>)

/** artboard: four corner brackets, the shape paper uses for a frame */
export const Frame = (p: P) => S(p, 12, <>
  <path d="M1 4V2.5A1.5 1.5 0 0 1 2.5 1H4" />
  <path d="M8 1h1.5A1.5 1.5 0 0 1 11 2.5V4" />
  <path d="M11 8v1.5a1.5 1.5 0 0 1-1.5 1.5H8" />
  <path d="M4 11H2.5A1.5 1.5 0 0 1 1 9.5V8" />
</>)

export const Rect = (p: P) => S(p, 12,
  <rect x="1.25" y="1.25" width="9.5" height="9.5" rx="1.5" />)

export const Pen = (p: P) => S(p, 18, <>
  <path d="M10 9.545L5.07 14.475" />
  <path d="M15.241 8.057l-1.592 4.496c-.117.33-.397.575-.74.645l-7.157 1.481c-.528.109-.996-.358-.886-.886l1.481-7.157c.071-.343.316-.623.645-.74l4.496-1.592" />
  <path d="M11.496 2.296l-.301.301c-.391.391-.391 1.024 0 1.414l2.169 2.169 2.169 2.169c.391.391 1.024.391 1.414 0l.301-.301" />
  <circle cx="10" cy="9.545" r=".75" fill="currentColor" />
</>)

export const SquarePlus = (p: P) => S(p, 12, <>
  <rect x="1.25" y="1.25" width="9.5" height="9.5" rx="2" />
  <line x1="8.25" y1="6" x2="3.75" y2="6" />
  <line x1="6" y1="8.25" x2="6" y2="3.75" />
</>)

export const Image = (p: P) => S(p, 12, <>
  <path d="m2.32,10.516l4.723-4.723c.391-.391,1.024-.391,1.414,0l2.293,2.293" />
  <circle cx="4" cy="4" r="1" fill="currentColor" strokeWidth="0" />
  <rect x="1.25" y="1.25" width="9.5" height="9.5" rx="2" />
</>)

/** scale/transform: a frame with a live corner handle */
export const Transform = (p: P) => S(p, 12, <>
  <path d="M1.25 4.5v-2a1.25 1.25 0 0 1 1.25-1.25h2" />
  <path d="M10.75 7.5v2a1.25 1.25 0 0 1-1.25 1.25h-2" />
  <path d="M1.25 8v1.5a1.25 1.25 0 0 0 1.25 1.25H4" />
  <rect x="6.5" y="1.25" width="4.25" height="4.25" rx="1" />
</>)

/** shader: a gem face, paper's last tool */
export const Gem = (p: P) => S(p, 12, <>
  <path d="M1.5 4.6 3.3 1.6a.8.8 0 0 1 .7-.4h4a.8.8 0 0 1 .7.4l1.8 3a.8.8 0 0 1-.05.9l-3.8 4.7a.8.8 0 0 1-1.25 0L1.55 5.5a.8.8 0 0 1-.05-.9Z" />
  <path d="M1.4 4.75h9.2" />
</>)

export const ChevronDown = (p: P) => S(p, 12,
  <polyline points="1.75 4.25 6 8.5 10.25 4.25" />)

export const ChevronRight = (p: P) => S(p, 12,
  <polyline points="4.25 10.25 8.5 6 4.25 1.75" />)

export const Plus = (p: P) => S(p, 12, <>
  <line x1="6" y1="1.75" x2="6" y2="10.25" />
  <line x1="1.75" y1="6" x2="10.25" y2="6" />
</>)

export const FileIcon = (p: P) => S(p, 12, <>
  <path d="M6.75 1.25H3.5a1.25 1.25 0 0 0-1.25 1.25v7a1.25 1.25 0 0 0 1.25 1.25h5A1.25 1.25 0 0 0 9.75 9.25V4.25Z" />
  <polyline points="6.5 1.4 6.5 4.25 9.6 4.25" />
</>)

/** panel toggle: a pane with its side rail filled */
export const PanelIcon = (p: P) => S(p, 16, <>
  <rect x="1.5" y="2.5" width="13" height="11" rx="2" />
  <line x1="10" y1="2.5" x2="10" y2="13.5" />
  <rect x="10" y="2.5" width="4.5" height="11" rx="2" fill="currentColor"
        stroke="none" opacity=".85" />
</>)

/** type layer marker, drawn as the letterform paper shows in the tree */
export const TypeMark = ({ className }: { className?: string }) => (
  <span className={`select-none font-medium leading-none ${className ?? ''}`}
        style={{ fontSize: 11 }}>Aa</span>
)

// the ai group. sparkle-3, image-sparkle and pen-sparkle from the same nucleo
// set; the small filled star is `color-2` in the source, drawn with the current
// colour here so it inherits the rail's active state like everything else.
export const Sparkle = (p: P) => S(p, 12, <>
  <polygon points="6.5 1.75 7.845 5.154 11.25 6.5 7.845 7.846 6.5 11.25 5.154 7.846 1.75 6.5 5.154 5.154 6.5 1.75" />
  <path strokeWidth={0} fill="currentColor" d="m3.492,1.492l-.946-.315-.316-.947c-.102-.306-.609-.306-.711,0l-.316.947-.946.315c-.153.051-.257.194-.257.356s.104.305.257.356l.946.315.316.947c.051.153.194.256.355.256s.305-.104.355-.256l.316-.947.946-.315c.153-.051.257-.194.257-.356s-.104-.305-.257-.356h0Z" />
</>)

export const ImageSparkle = (p: P) => S(p, 18, <>
  <rect x="2.75" y="2.75" width="12.5" height="12.5" rx="2" ry="2" />
  <path d="M4.445,15.227l5.64-5.641c.781-.781,2.047-.781,2.828,0l2.336,2.336" />
  <path strokeWidth={0} fill="currentColor" d="M9.158,6.508l-1.263-.421-.421-1.263c-.137-.408-.812-.408-.949,0l-.421,1.263-1.263,.421c-.204,.068-.342,.259-.342,.474s.138,.406,.342,.474l1.263,.421,.421,1.263c.068,.204,.26,.342,.475,.342s.406-.138,.475-.342l.421-1.263,1.263-.421c.204-.068,.342-.259,.342-.474s-.138-.406-.342-.474Z" />
</>)

export const PenSparkle = (p: P) => S(p, 18, <>
  <path d="M2.75,15.25s3.599-.568,4.546-1.515c.947-.947,7.327-7.327,7.327-7.327,.837-.837,.837-2.194,0-3.03-.837-.837-2.194-.837-3.03,0,0,0-6.38,6.38-7.327,7.327s-1.515,4.546-1.515,4.546h0Z" />
  <path strokeWidth={0} fill="currentColor" d="M5.493,3.492l-.946-.315-.316-.947c-.102-.306-.609-.306-.711,0l-.316,.947-.946,.315c-.153,.051-.257,.194-.257,.356s.104,.305,.257,.356l.946,.315,.316,.947c.051,.153,.194,.256,.355,.256s.305-.104,.355-.256l.316-.947,.946-.315c.153-.051,.257-.194,.257-.356s-.104-.305-.257-.356Z" />
  <path strokeWidth={0} fill="currentColor" d="M16.658,12.99l-1.263-.421-.421-1.263c-.137-.408-.812-.408-.949,0l-.421,1.263-1.263,.421c-.204,.068-.342,.259-.342,.474s.138,.406,.342,.474l1.263,.421,.421,1.263c.068,.204,.26,.342,.475,.342s.406-.138,.475-.342l.421-1.263,1.263-.421c.204-.068,.342-.259,.342-.474s-.138-.406-.342-.474Z" />
</>)
