/**
 * Orthogonal connectors for the seam between two scenes: leave horizontally,
 * turn once at a shared middle column, arrive horizontally. Corners are arcs
 * rather than mitres, which is what stops a dense fan of morph threads reading
 * as a grid.
 */
export function elbow(
  x1: number, y1: number, x2: number, y2: number, radius = 10,
): string {
  const midX = (x1 + x2) / 2
  const dy = y2 - y1
  if (Math.abs(dy) < 0.5) return `M ${x1} ${y1} L ${x2} ${y2}`

  const r = Math.min(radius, Math.abs(dy) / 2, Math.abs(midX - x1), Math.abs(x2 - midX))
  const down = dy > 0 ? 1 : -1
  const fwd = x2 > x1 ? 1 : -1

  return [
    `M ${x1} ${y1}`,
    `L ${midX - r * fwd} ${y1}`,
    `Q ${midX} ${y1} ${midX} ${y1 + r * down}`,
    `L ${midX} ${y2 - r * down}`,
    `Q ${midX} ${y2} ${midX + r * fwd} ${y2}`,
    `L ${x2} ${y2}`,
  ].join(' ')
}
