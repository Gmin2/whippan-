import type { NodePatch } from './doc'

/**
 * The renderer's real effect vocabulary.
 *
 * Paper's shaders are standalone generative layers; ours cannot be, because the
 * engine has no shader stage. What it does have is a set of effects that modify
 * a node, two of which (goo, streak) had no UI at all. This gallery is where
 * they become discoverable.
 */
export interface Effect {
  key: string
  name: string
  group: 'light' | 'motion' | 'material'
  /** what it actually does, in the renderer's terms */
  blurb: string
  /** only meaningful on some node types */
  appliesTo?: string[]
  presets: { name: string; patch: NodePatch }[]
}

export const EFFECTS: Effect[] = [
  {
    key: 'glow',
    name: 'Glow',
    group: 'light',
    blurb: 'a blurred echo behind the body. offset it and it reads as a shadow.',
    presets: [
      { name: 'Rim', patch: { glow: { sigma: 24, opacity: 0.8, dx: 0, dy: 0 } } },
      { name: 'Lit pill', patch: { glow: { sigma: 44, opacity: 1, dx: 0, dy: 0 } } },
      { name: 'Drop shadow', patch: { glow: { sigma: 18, opacity: 0.35, dx: 0, dy: 14, color: '#000000' } } },
      { name: 'Bloom', patch: { glow: { sigma: 80, opacity: 0.55, dx: 0, dy: -10 } } },
    ],
  },
  {
    key: 'blur',
    name: 'Blur',
    group: 'light',
    blurb: 'gaussian defocus on the node itself. depth, soft light pools.',
    presets: [
      { name: 'Soft', patch: { blur: 6 } },
      { name: 'Defocus', patch: { blur: 18 } },
      { name: 'Far', patch: { blur: 48 } },
    ],
  },
  {
    key: 'gradient',
    name: 'Gradient',
    group: 'material',
    blurb: 'linear fill with an angle and stops, computed by the engine.',
    appliesTo: ['rect'],
    presets: [
      {
        name: 'Vertical',
        patch: { gradient: { angle: 90, stops: [{ at: 0, color: '#2d52f0' }, { at: 1, color: '#0d0d0d' }] } },
      },
      {
        name: 'Horizontal',
        patch: { gradient: { angle: 0, stops: [{ at: 0, color: '#ff5c1a' }, { at: 1, color: '#e0645c' }] } },
      },
      {
        name: 'Diagonal',
        patch: { gradient: { angle: 45, stops: [{ at: 0, color: '#ffffff' }, { at: 1, color: '#d9cac8' }] } },
      },
    ],
  },
  {
    key: 'goo',
    name: 'Goo',
    group: 'material',
    blurb: 'nodes sharing a group fuse like metaballs when they come within ~24px.',
    appliesTo: ['rect'],
    presets: [
      { name: 'Group A', patch: { goo: 'a' } },
      { name: 'Group B', patch: { goo: 'b' } },
    ],
  },
  {
    key: 'streak',
    name: 'Streak',
    group: 'motion',
    blurb: 'motion echo. the engine samples its own timeline backwards, so it is '
      + 'only visible while the node is actually moving.',
    appliesTo: ['rect'],
    presets: [
      { name: 'Trail', patch: { streak: { samples: 5, window: 0.06, gain: 0.5 } } },
      { name: 'Whip', patch: { streak: { samples: 8, window: 0.1, gain: 0.75 } } },
    ],
  },
]

export const GROUPS: { key: Effect['group']; label: string }[] = [
  { key: 'light', label: 'light' },
  { key: 'material', label: 'material' },
  { key: 'motion', label: 'motion' },
]
