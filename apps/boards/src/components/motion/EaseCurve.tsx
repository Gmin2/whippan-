import { useMemo } from 'react'
import { easeCurve } from '../../engine'
import { easeFn } from './ease'

const W = 253
const H = 84
const X0 = 8
const X1 = W - 8
const Y0 = 70 // value 0
const Y1 = 14 // value 1

const px = (t: number) => X0 + t * (X1 - X0)
const py = (v: number) => Y0 - v * (Y0 - Y1)

interface Props {
  ease: unknown
  /** 0..1 through the eased segment, or null when the playhead is outside it */
  progress: number | null
}

/**
 * The ease drawn as a graph: time across, value up. The dashed diagonal is
 * linear, so an ease reads as how far it bows away from it.
 */
const STEPS = 72

export default function EaseCurve({ ease, progress }: Props) {
  // the renderer's own curve: a graph drawn from a second implementation is a
  // graph that can quietly disagree with the film
  const curve = useMemo(() => easeCurve(ease, STEPS + 1), [ease])
  const fn = useMemo(() => {
    if (!curve) return easeFn(ease)
    // between samples, and past the last one, fall back to reading the ends
    return (t: number) => {
      const x = Math.min(1, Math.max(0, t)) * STEPS
      const i = Math.floor(x)
      const a = curve[Math.min(STEPS, i)]
      const b = curve[Math.min(STEPS, i + 1)]
      return a + (b - a) * (x - i)
    }
  }, [curve, ease])

  const steps = STEPS
  const pts: string[] = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    pts.push(`${px(t).toFixed(2)},${py(fn(t)).toFixed(2)}`)
  }
  const line = `M${pts.join('L')}`
  const area = `${line}L${px(1).toFixed(2)},${Y0}L${X0},${Y0}Z`
  const at = progress == null ? null : Math.min(1, Math.max(0, progress))

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} className="block">
      <defs>
        <linearGradient id="ease-fade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5e92f4" stopOpacity="0.16" />
          <stop offset="100%" stopColor="#5e92f4" stopOpacity="0" />
        </linearGradient>
      </defs>

      <rect x="0.5" y="0.5" width={W - 1} height={H - 1} rx="6"
            fill="#fff" stroke="rgba(0,0,0,0.08)" />

      <line x1={X0} y1={Y1} x2={X1} y2={Y1} stroke="rgba(0,0,0,0.07)" strokeDasharray="2 3" />
      <line x1={X0} y1={Y0} x2={X1} y2={Y0} stroke="rgba(0,0,0,0.07)" strokeDasharray="2 3" />
      <line x1={X0} y1={Y0} x2={X1} y2={Y1} stroke="rgba(0,0,0,0.12)" strokeDasharray="1 4" />

      <path d={area} fill="url(#ease-fade)" />
      <path d={line} fill="none" stroke="#5e92f4" strokeWidth="1.6"
            strokeLinecap="round" strokeLinejoin="round" />

      <circle cx={px(0)} cy={py(0)} r="2.4" fill="#fff" stroke="#5e92f4" strokeWidth="1.4" />
      <circle cx={px(1)} cy={py(fn(1))} r="2.4" fill="#5e92f4" />

      {at != null && (
        <>
          <line x1={px(at)} y1={Y1 - 10} x2={px(at)} y2={Y0 + 10}
                stroke="rgba(0,0,0,0.18)" />
          <circle cx={px(at)} cy={py(fn(at))} r="3" fill="#5e92f4"
                  stroke="#fff" strokeWidth="1.4" />
        </>
      )}
    </svg>
  )
}
