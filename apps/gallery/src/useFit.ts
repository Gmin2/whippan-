import { useLayoutEffect, useRef, useState } from 'react'

/**
 * Fit a film's native size into whatever box it is given, never upscaling
 * past 1:1. Films here run from 998x720 to 2994x1618, so the page cannot
 * pick one aspect and letterbox everything into it — the frame has to take
 * the shape of the document.
 *
 * `reserve` is the vertical space the transport needs under the film.
 */
export function useFit(w: number, h: number, reserve = 116) {
  const ref = useRef<HTMLDivElement>(null)
  const [box, setBox] = useState({ w: 0, h: 0 })

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const measure = () => {
      const r = el.getBoundingClientRect()
      const availW = r.width
      const availH = Math.max(120, r.height - reserve)
      const k = Math.min(availW / w, availH / h, 1)
      setBox({ w: Math.round(w * k), h: Math.round(h * k) })
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [w, h, reserve])

  return { ref, w: box.w, h: box.h }
}
