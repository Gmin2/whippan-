import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { Node } from '../engine/types'

interface Props {
  /** the node's painted box, in screen pixels */
  rect: { x: number; y: number; w: number; h: number }
  node: Node
  zoom: number
  /** streams on every keystroke, so the wall reflows as you type */
  onChange(text: string): void
  /** commit keeps the last streamed value; cancel restores the original */
  onDone(commit: boolean): void
}

const DEFAULT_FAMILY = 'Inter'
const DEFAULT_SIZE = 48
const DEFAULT_WEIGHT = 400

/**
 * Editing a text node where it lives.
 *
 * The engine paints text as one shaped line centred on the node's x,y, so this
 * is a single-line field centred on the same point rather than a text box. The
 * engine's own draw of this node is suppressed while the field is open,
 * otherwise the caret would sit over a second copy of the same glyphs.
 *
 * Every keystroke patches the document, so the surrounding wall reflows live
 * and the shaped width you see is the engine's, not the browser's guess.
 */
export default function TextEditor({ rect, node, zoom, onChange, onDone }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [value, setValue] = useState(node.text ?? '')
  const original = useRef(node.text ?? '')
  // a blur fires after Escape too; the key handler wins, this stops the second
  const settled = useRef(false)

  /** when the field mounted, for telling a stolen focus from a real one */
  const born = useRef(0)

  useLayoutEffect(() => {
    const el = input.current
    if (!el) return
    born.current = performance.now()
    el.focus()
    el.select()
  }, [])

  /**
   * The press that opened this field is still in flight, and its click moves
   * focus to the canvas the instant the field mounts. That blur goes nowhere
   * (no relatedTarget) and lands within a frame or two, which is what tells it
   * apart from someone clicking away on purpose.
   */
  const onBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    if (!e.relatedTarget && performance.now() - born.current < 300) {
      input.current?.focus()
      return
    }
    if (settled.current) return
    settled.current = true
    onDone(true)
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' && e.key !== 'Enter' && e.key !== 'Tab') return
      e.preventDefault()
      e.stopPropagation()
      if (settled.current) return
      settled.current = true
      if (e.key === 'Escape') onChange(original.current)
      onDone(e.key !== 'Escape')
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onChange, onDone])

  const size = (node.font?.size ?? DEFAULT_SIZE) * zoom
  const family = node.font?.family ?? DEFAULT_FAMILY

  return (
    <input
      ref={input}
      data-text-editor=""
      value={value}
      spellCheck={false}
      onChange={e => { setValue(e.target.value); onChange(e.target.value) }}
      onBlur={onBlur}
      onPointerDown={e => e.stopPropagation()}
      className="absolute z-20 border-none bg-transparent p-0 text-center outline-none"
      style={{
        // the field is centred on the node's centre and given room to grow, so
        // the caret does not jump when a word pushes past the painted width
        left: rect.x + rect.w / 2 - Math.max(rect.w, 240) / 2,
        top: rect.y + rect.h / 2 - size * 0.72,
        width: Math.max(rect.w, 240),
        height: size * 1.45,
        color: node.color ?? '#000',
        fontFamily: `"${family}", system-ui, sans-serif`,
        fontSize: size,
        fontWeight: node.font?.weight ?? DEFAULT_WEIGHT,
        lineHeight: 1.45,
        caretColor: '#5e92f4',
      }}
    />
  )
}
