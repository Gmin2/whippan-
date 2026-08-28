import { useEffect, useState } from 'react'
import { loadDoc } from '../engine'
import type { Doc, Entry } from '../engine/types'
import Film from '../components/Film'

interface Props {
  ck: CanvasKit
  registry: Entry[]
  slug: string
}

// `?render=<slug>`: the film alone on a plain ground, free-running, no chrome
// and nothing interactive. frame capture and export tooling point here, so
// nothing may be added around the canvas.
export default function RenderRoute({ ck, registry, slug }: Props) {
  const entry = registry.find(e => e.slug === slug)
  const [doc, setDoc] = useState<Doc | null>(null)

  useEffect(() => {
    if (entry) loadDoc(entry).then(setDoc, () => {})
  }, [entry])

  if (!entry) return <p className="p-8 font-mono text-sm">unknown film: {slug}</p>
  if (!doc) return null

  return (
    <div className="grid min-h-screen place-items-center">
      <div id="art" style={{ width: doc.stage.size[0] }}>
        <Film ck={ck} doc={doc} className="h-auto w-full" />
      </div>
    </div>
  )
}
