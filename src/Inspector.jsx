// rounded-card inspector, design-reference style: content / color / font /
// geometry for the selected node, plus its animation tracks. edits mutate
// the doc in memory and the canvas re-renders the same frame.
export default function Inspector({ doc, selection, onEdit }) {
  if (!selection) {
    return (
      <Panel>
        <div style={{ color: '#6a6a68', padding: '20px 4px' }}>
          select a layer on the canvas or the timeline
        </div>
      </Panel>
    )
  }
  const scene = doc.stage.scenes.find(s => s.id === selection.sceneId)
  const node = scene?.nodes.find(n => n.id === selection.nodeId)
  if (!node) return <Panel />

  const tracks = (doc.anim.tracks ?? []).filter(t => t.target === node.id)

  const set = (field, value) => onEdit(draft => {
    const sc = draft.stage.scenes.find(s => s.id === selection.sceneId)
    const n = sc.nodes.find(n => n.id === selection.nodeId)
    setPath(n, field, value)
  })

  return (
    <Panel>
      <Card title={node.id}>
        {node.text !== undefined && (
          <Field label="content">
            <input value={node.text}
                   onChange={e => set('text', e.target.value)} style={txt} />
          </Field>
        )}
        <Row>
          <Num label="x" value={node.x} onChange={v => set('x', v)} />
          <Num label="y" value={node.y} onChange={v => set('y', v)} />
        </Row>
        {node.w !== undefined && (
          <Row>
            <Num label="w" value={node.w} onChange={v => set('w', v)} />
            <Num label="h" value={node.h} onChange={v => set('h', v)} />
          </Row>
        )}
        {node.radius !== undefined && (
          <Num label="radius" value={node.radius} onChange={v => set('radius', v)} />
        )}
        {node.rot !== undefined && (
          <Num label="rot" value={node.rot} onChange={v => set('rot', v)} />
        )}
      </Card>

      {(node.fill || node.color) && (
        <Card title="color">
          <Field label={node.fill ? 'fill' : 'ink'}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="color" value={node.fill || node.color}
                     onChange={e => set(node.fill ? 'fill' : 'color', e.target.value)}
                     style={{ width: 26, height: 26, border: 'none',
                              background: 'none', padding: 0 }} />
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11 }}>
                {node.fill || node.color}
              </span>
            </div>
          </Field>
        </Card>
      )}

      {node.font && (
        <Card title="font">
          <Row>
            <Num label="size" value={node.font.size}
                 onChange={v => set('font.size', v)} />
            <Num label="weight" value={node.font.weight ?? 400}
                 onChange={v => set('font.weight', v)} />
          </Row>
        </Card>
      )}

      <Card title="animation">
        {tracks.length === 0 && (
          <div style={{ color: '#6a6a68' }}>no tracks</div>
        )}
        {tracks.map((tr, i) => (
          <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #222' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9a9a97' }}>
                {tr.reveal ? `reveal · ${tr.reveal.unit}`
                  : tr.enter ? `enter · ${tr.enter.preset ?? tr.enter}`
                  : tr.state ? `state · ${tr.state}`
                  : Object.keys(tr.keys ?? {}).join(' ')}
              </span>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11 }}>
                at {(tr.at ?? 0).toFixed(2)}s{tr.loop ? ' ∞' : ''}
              </span>
            </div>
          </div>
        ))}
      </Card>
    </Panel>
  )
}

function setPath(obj, path, value) {
  const parts = path.split('.')
  let o = obj
  for (const p of parts.slice(0, -1)) o = o[p]
  o[parts[parts.length - 1]] = value
}

const txt = {
  width: '100%', background: '#1a1a1a', border: '1px solid #262626',
  borderRadius: 7, color: '#e8e8e6', padding: '5px 8px', outline: 'none',
}

function Panel({ children }) {
  return (
    <div style={{
      width: 264, background: '#141414', borderLeft: '1px solid #222',
      padding: 12, overflowY: 'auto', display: 'flex',
      flexDirection: 'column', gap: 10,
    }}>{children}</div>
  )
}

function Card({ title, children }) {
  return (
    <div style={{ background: '#191919', borderRadius: 10, padding: 12 }}>
      <div style={{ fontSize: 11, letterSpacing: '.08em', color: '#8a8a88',
                    textTransform: 'lowercase', marginBottom: 8 }}>{title}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {children}
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <span style={{ fontSize: 11, color: '#6a6a68' }}>{label}</span>
      {children}
    </label>
  )
}

function Row({ children }) {
  return <div style={{ display: 'flex', gap: 8 }}>{children}</div>
}

function Num({ label, value, onChange }) {
  return (
    <Field label={label}>
      <input type="number" value={value ?? 0}
             onChange={e => onChange(parseFloat(e.target.value) || 0)}
             style={{ ...txt, width: 86 }} />
    </Field>
  )
}
