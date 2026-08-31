/**
 * Structured-output schemas for the three things the prompt bar can ask for.
 *
 * Until now a proposal was prose-prompted and its JSON scraped back out of the
 * reply with a regex, which fails in the two ways you would expect: the model
 * wraps the object in a sentence, or it invents a block name that the library
 * cannot materialise. A schema fixes the second properly — the enums below are
 * built from the request, so a model physically cannot name a block, entrance
 * or transition this deployment does not have.
 *
 * These are Anthropic tool definitions. Kimi K3 speaks the same Messages API,
 * so one definition covers both models; an OpenAI binding reuses the same
 * `input_schema` under `response_format: json_schema`.
 *
 * A schema cannot express the AUTHORING contract (ids unique per scene, one
 * track per node per property, x/y keys as offsets). That is `validate.ts`.
 */
import type { FilmRequest, ScreenRequest, MotionRequest } from './types.js'

export interface Tool {
  name: string
  description: string
  input_schema: Record<string, unknown>
}

const str = { type: 'string' }
const num = { type: 'number' }

/** a keyframe: t is relative to the track's `at`, v is the value */
const key = {
  type: 'object',
  required: ['t', 'v'],
  additionalProperties: false,
  properties: {
    t: { ...num, description: 'seconds from the track at, may be negative' },
    v: num,
    // spring is an object, the rest are names
    ease: { anyOf: [str, { type: 'object' }] },
  },
}

const KEYABLE = ['x', 'y', 'w', 'h', 'scale', 'rot', 'opacity', 'blur',
                 'cam_x', 'cam_y', 'cam_zoom']

const track = (targets?: string[]) => ({
  type: 'object',
  required: ['target'],
  additionalProperties: false,
  properties: {
    target: targets?.length
      ? { ...str, enum: targets, description: 'a node id from the selection' }
      : str,
    at: { ...num, description: 'scene-local start; key times are relative to it' },
    keys: {
      type: 'object',
      additionalProperties: false,
      properties: Object.fromEntries(KEYABLE.map(k => [k, { type: 'array', items: key }])),
      description: 'x and y are OFFSETS from the node home; everything else absolute',
    },
    reveal: { type: 'object' },
    enter: str,
    state: str,
    cam: { type: 'object' },
    loop: { type: 'boolean' },
  },
})

const placement = (blocks: string[], enters?: string[]) => ({
  type: 'object',
  required: ['block', 'x', 'y'],
  additionalProperties: false,
  properties: {
    block: { ...str, enum: blocks },
    x: { ...num, description: 'centre of the block, not its left edge' },
    y: { ...num, description: 'centre of the block, not its top edge' },
    opts: { type: 'object', description: 'the block slots, by name' },
    ...(enters ? { enter: { ...str, enum: enters }, at: num } : {}),
  },
})

export function motionTool(req: MotionRequest): Tool {
  return {
    name: 'propose_motion',
    description: 'Return the tracks for the selected nodes.',
    input_schema: {
      type: 'object',
      required: ['note', 'tracks'],
      additionalProperties: false,
      properties: {
        note: { ...str, description: 'one line on what this does' },
        tracks: { type: 'array', items: track(req.nodes.map(n => n.id)) },
      },
    },
  }
}

export function screenTool(req: ScreenRequest): Tool {
  const blocks = req.blocks.map(b => b.key)
  return {
    name: 'compose_screen',
    description: 'Compose one screen out of blocks. The library owns geometry.',
    input_schema: {
      type: 'object',
      required: ['note', 'place'],
      additionalProperties: false,
      properties: {
        note: str,
        bg: { ...str, description: 'hex, or omit to keep the film background' },
        place: { type: 'array', minItems: 1, items: placement(blocks) },
      },
    },
  }
}

export function filmTool(req: FilmRequest): Tool {
  const blocks = req.blocks.map(b => b.key)
  return {
    name: 'compose_film',
    description: 'Compose a film as a sequence of scenes built from blocks.',
    input_schema: {
      type: 'object',
      required: ['note', 'scenes'],
      additionalProperties: false,
      properties: {
        note: str,
        scenes: {
          type: 'array',
          minItems: 1,
          items: {
            type: 'object',
            required: ['id', 'dur', 'place'],
            additionalProperties: false,
            properties: {
              id: { ...str, description: 'unique across the film' },
              dur: { ...num, description: 'seconds' },
              bg: str,
              note: str,
              transition: { ...str, enum: req.transitions },
              place: { type: 'array', minItems: 1, items: placement(blocks, req.enters) },
            },
          },
        },
      },
    },
  }
}
