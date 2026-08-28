// placeholder shape for the ui pass. it deliberately mirrors a whippan
// document (scenes become artboards, nodes become layers) so wiring the real
// engine in later is a swap of the data source, not a rewrite of the views.

export type LayerKind = 'frame' | 'text'

export interface Layer {
  id: string
  name: string
  kind: LayerKind
}

export interface Artboard {
  id: string
  /** the number paper prints above each board */
  label: string
  name: string
  w: number
  h: number
  dur: number
  note: string
}

export interface Board {
  title: string
  pages: string[]
  activePage: string
  ground: string
  artboards: Artboard[]
  /** free text sitting directly on the canvas, above the boards */
  canvasText: string[]
}

export const BOARD: Board = {
  title: 'solder — launch film',
  pages: ['Page 1'],
  activePage: 'Page 1',
  ground: '#d9cac8',
  canvasText: ['solder', 'prototype hardware fast'],
  artboards: [
    { id: 'i1', label: '1', name: 'today it takes', w: 1920, h: 1080, dur: 1.0, note: "Brew opening: huge 'Today' with the arrow chip" },
    { id: 'i2', label: '2', name: 'it takes →', w: 1920, h: 1080, dur: 1.0, note: 'the arrow chip inflates at the end of the line' },
    { id: 'i3', label: '3', name: 'to prototype hardware', w: 1920, h: 1080, dur: 1.0, note: 'the sentence resolves and holds' },
    { id: 'i4', label: '4', name: 'what parts do I need', w: 1920, h: 1080, dur: 1.0, note: 'question one, two beats, word emphasis' },
    { id: 'i5', label: '5', name: 'weeks counter', w: 1920, h: 1080, dur: 2.0, note: 'the lovable counter, compact pill rolling to 8 weeks' },
    { id: 'i6', label: '6', name: 'meet', w: 1920, h: 1080, dur: 1.0, note: "'Meet' white on solder blue" },
    { id: 'i7', label: '7', name: 'lockup', w: 1920, h: 1080, dur: 2.0, note: 'the real lockup blooms on blue: chip mark + wordmark' },
    { id: 's3', label: '8', name: 'homepage', w: 1920, h: 1080, dur: 1.5, note: 'focus snaps onto the real homepage, camera settles' },
  ],
}

export const LAYERS: Layer[] = [
  ...BOARD.artboards.map(a => ({ id: a.id, name: a.label, kind: 'frame' as const })),
  { id: 't1', name: 'solder', kind: 'text' },
  { id: 't2', name: 'prototype hardware fast', kind: 'text' },
]
