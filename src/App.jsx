// studio shell: hash-routed views over one engine boot. '#/<slug>' is the
// gallery (svg-harness layout); '#/edit/<slug>' is the editor — doc rail,
// engine canvas with a floating tool dock, inspector, narrating timeline.
import { useEffect, useRef, useState } from 'react'
import { boot, loadDoc, timing } from './engine.js'
import Stage from './Stage.jsx'
import { Pointer, TextTool, Shapes, Picture, PenNib, Play, Pause, Floppy } from './icons.jsx'
import Timeline from './Timeline.jsx'
import Inspector from './Inspector.jsx'
import Gallery from './Gallery.jsx'
import Boards from './Boards.jsx'

const ACCENT = '#606de0'

export default function App() {
  const [ck, setCk] = useState(null)
  const [registry, setRegistry] = useState([])
  const mode = h => h.startsWith('#/edit/') ? 'edit'
    : h.startsWith('#/boards/') ? 'boards' : 'gallery'
  const [view, setView] = useState(mode(location.hash))

  useEffect(() => {
    boot().then(({ CK, registry }) => {
      setCk(CK)
      setRegistry(registry)
    })
    const onHash = () => setView(mode(location.hash))
    addEventListener('hashchange', onHash)
    return () => removeEventListener('hashchange', onHash)
  }, [])

  if (!ck || !registry.length) {
    return <Center>whippan studio — engine loading</Center>
  }
  if (view === 'gallery') {
    return <Gallery ck={ck} registry={registry}
                    onEdit={slug => { location.hash = '/edit/' + slug }} />
  }
  const slug = location.hash.replace(/#\/(edit|boards)\//, '') || registry[0].slug
  return <Editor ck={ck} registry={registry} slug={slug} boards={view === 'boards'}
                 onGallery={s => { location.hash = '/' + s }} />
}

function Editor({ ck, registry, slug, boards, onGallery }) {
  const [doc, setDoc] = useState(null)
  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [selection, setSelection] = useState(null)
  const raf = useRef(null)

  useEffect(() => {
    open(registry.find(e => e.slug === slug) ?? registry[0])
  }, [slug])

  async function open(entry) {
    setPlaying(false)
    setSelection(null)
    setT(0)
    setDoc(await loadDoc(entry))
  }

  const dur = doc ? timing(doc.stage).dur : 0

  useEffect(() => {
    if (!playing || !doc) return
    let last = performance.now()
    const tick = now => {
      const dt = (now - last) / 1000
      last = now
      setT(prev => {
        const next = prev + dt
        return next >= dur ? next % dur : next
      })
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [playing, doc, dur])

  function edit(mutate) {
    setDoc(prev => {
      const draft = {
        ...prev,
        stage: structuredClone(prev.stage),
        anim: structuredClone(prev.anim),
      }
      mutate(draft)
      return draft
    })
  }

  async function save() {
    if (!doc) return
    await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: doc.stageUrl, doc: doc.stage }),
    })
    await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: doc.animUrl, doc: doc.anim }),
    })
  }

  if (!doc) {
    return <Center>loading {slug}</Center>
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Rail registry={registry} current={doc.entry.slug}
              onOpen={e => { location.hash = '/edit/' + e.slug }}
              onGallery={() => onGallery(doc.entry.slug)} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div style={{
            flex: 1, display: boards ? 'block' : 'grid', placeItems: 'center',
            minHeight: 0,
            background: 'radial-gradient(120% 100% at 70% 0%, #242426 0%, #171717 60%)',
            position: 'relative', padding: boards ? 0 : 28,
          }}>
            {boards
              ? <Boards ck={ck} doc={doc}
                        onJump={(start) => {
                          setT(start + 0.01)
                          location.hash = '/edit/' + doc.entry.slug
                        }} />
              : <>
                  <Stage ck={ck} doc={doc} t={t} selection={selection}
                         onSelect={setSelection} onEdit={edit} />
                  <Dock />
                </>}
          </div>
          <Transport t={t} dur={dur} playing={playing} boards={boards}
                     onPlay={() => setPlaying(p => !p)}
                     onScrub={v => { setPlaying(false); setT(v) }}
                     onBoards={() => {
                       location.hash = (boards ? '/edit/' : '/boards/') +
                         doc.entry.slug
                     }}
                     onSave={save} />
        </div>
        <Inspector doc={doc} selection={selection} onEdit={edit} />
      </div>
      <Timeline doc={doc} t={t} selection={selection}
                onScrub={v => { setPlaying(false); setT(v) }}
                onSelect={setSelection} />
    </div>
  )
}

function Rail({ registry, current, onOpen, onGallery }) {
  let group = null
  return (
    <div style={{
      width: 200, background: '#141414', borderRight: '1px solid #222',
      padding: '14px 0', overflowY: 'auto',
    }}>
      <div style={{ padding: '0 16px 12px', fontWeight: 650 }}>
        whippan <span style={{ color: ACCENT }}>studio</span>
      </div>
      <div onClick={onGallery} style={{
        padding: '4px 16px 10px', fontSize: 11, color: '#8a8a88',
        cursor: 'pointer',
      }}>← gallery</div>
      {registry.map(e => {
        const g = e.group || 'examples'
        const head = g !== group
        group = g
        return (
          <div key={e.slug}>
            {head && (
              <div style={{ padding: '10px 16px 3px', fontSize: 10,
                            letterSpacing: '.14em', color: '#5a5a58',
                            textTransform: 'uppercase' }}>{g}</div>
            )}
            <div
              onClick={() => onOpen(e)}
              style={{
                padding: '5px 16px', cursor: 'pointer',
                color: e.slug === current ? '#fff' : '#8a8a88',
                background: e.slug === current ? '#1d1d1f' : 'none',
                borderLeft: e.slug === current
                  ? `2px solid ${ACCENT}` : '2px solid transparent',
              }}
            >{e.title}</div>
          </div>
        )
      })}
    </div>
  )
}

function Dock() {
  const tools = [
    ['cursor', Pointer, true],
    ['text', TextTool, false],
    ['shape', Shapes, false],
    ['image', Picture, false],
    ['path', PenNib, false],
  ]
  return (
    <div style={{
      position: 'absolute', bottom: 18, left: '50%',
      transform: 'translateX(-50%)', display: 'flex', gap: 4,
      background: '#101010', border: '1px solid #262626',
      borderRadius: 12, padding: 5,
    }}>
      {tools.map(([name, Icon, active]) => (
        <div key={name} title={name} style={{
          width: 32, height: 32, borderRadius: 8, display: 'grid',
          placeItems: 'center', cursor: 'pointer',
          color: active ? '#fff' : '#9a9a97',
          background: active ? ACCENT : 'transparent',
        }}>
          <Icon size={16} />
        </div>
      ))}
    </div>
  )
}

function Transport({ t, dur, playing, boards, onPlay, onScrub, onBoards, onSave }) {
  return (
    <div style={{
      height: 44, display: 'flex', alignItems: 'center', gap: 12,
      padding: '0 14px', background: '#131313', borderTop: '1px solid #222',
    }}>
      <button onClick={onPlay} style={{
        border: 0, background: ACCENT, color: '#fff', borderRadius: 8,
        width: 34, height: 28, cursor: 'pointer', display: 'grid',
        placeItems: 'center',
      }}>{playing ? <Pause size={13} /> : <Play size={13} />}</button>
      <input type="range" min={0} max={dur} step={1 / 60} value={t}
             onChange={e => onScrub(parseFloat(e.target.value))}
             style={{ flex: 1, accentColor: ACCENT }} />
      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11,
                     color: '#8a8a88', width: 96, textAlign: 'right' }}>
        {t.toFixed(2)} / {dur.toFixed(2)}s
      </span>
      <button onClick={onBoards} title="storyboard" style={{
        border: '1px solid #2c2c2c', background: boards ? ACCENT : 'none',
        color: boards ? '#fff' : '#c9c9c6', borderRadius: 8,
        padding: '4px 10px', cursor: 'pointer', font: 'inherit',
      }}>boards</button>
      <button onClick={onSave} title="save" style={{
        border: '1px solid #2c2c2c', background: 'none', color: '#c9c9c6',
        borderRadius: 8, padding: '4px 10px', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 6, font: 'inherit',
      }}><Floppy size={13} /> save</button>
    </div>
  )
}

function Center({ children }) {
  return (
    <div style={{ height: '100%', display: 'grid', placeItems: 'center',
                  color: '#6a6a68' }}>{children}</div>
  )
}
