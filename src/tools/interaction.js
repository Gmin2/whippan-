import { gsap } from 'gsap'

// Vertical fisheye for list rows, ported from the sibling gsap-harness
// playground: the row under the cursor scales up, shifts right and
// sharpens; neighbors follow with a sine falloff over `spread` px; far
// rows dim and blur. Feed update() the pointer clientY. Rows should have
// transformOrigin 'left center'.
export function fisheyeList(items, opts = {}) {
  const spread = opts.spread ?? 150
  const scaleAmt = opts.scale ?? 0.18
  const shift = opts.shift ?? 26
  const dim = opts.dim ?? 0.3
  const blur = opts.blur ?? 2
  const duration = opts.duration ?? 0.25

  const update = (clientY) => {
    items.forEach((el) => {
      const r = el.getBoundingClientRect()
      const d = Math.abs(r.top + r.height / 2 - clientY)
      const t = Math.max(0, 1 - d / spread)
      const e = Math.sin((t * Math.PI) / 2)
      gsap.to(el, {
        x: shift * e,
        scale: 1 + scaleAmt * e,
        opacity: dim + (1 - dim) * e,
        filter: `blur(${((1 - e) * blur).toFixed(2)}px)`,
        duration,
        ease: 'power2.out',
        overwrite: 'auto',
      })
    })
  }
  return { update }
}

/** Press squash + release pop (ported from gsap-harness). */
export function pressFeedback(target, scale = 0.82) {
  return {
    press: () => gsap.to(target, { scale, duration: 0.15, ease: 'power2.out' }),
    release: () => gsap.to(target, { scale: 1, duration: 0.45, ease: 'back.out(2.5)' }),
  }
}

/**
 * 1D dock lens: icons near the cursor magnify and rise with a sine falloff,
 * macOS-dock style but gentle enough to stay inside a pill. Feed update()
 * the pointer clientX.
 */
export function dockLens(items, opts = {}) {
  const radius = opts.radius ?? 90
  const maxScale = opts.maxScale ?? 1.32
  const rise = opts.rise ?? 5
  const update = (mx) => {
    items.forEach((el) => {
      const r = el.getBoundingClientRect()
      const d = Math.abs(mx - (r.left + r.width / 2))
      const t = Math.max(0, 1 - d / radius)
      const e = Math.sin((t * Math.PI) / 2)
      gsap.to(el, {
        scale: 1 + (maxScale - 1) * e,
        y: -rise * e,
        duration: 0.2,
        ease: 'power2.out',
        overwrite: 'auto',
      })
    })
  }
  const reset = () => {
    gsap.killTweensOf(items)
    gsap.to(items, { scale: 1, y: 0, duration: 0.45, ease: 'power2.out' })
  }
  return { update, reset }
}
