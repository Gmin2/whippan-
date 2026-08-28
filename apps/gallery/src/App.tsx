import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useSearchParams } from 'react-router-dom'
import { boot } from './engine'
import type { Engine } from './engine'
import Index from './pages/Index'
import FilmPage from './pages/FilmPage'
import RenderRoute from './pages/RenderRoute'

function useEngine(): Engine | null {
  const [eng, setEng] = useState<Engine | null>(null)
  useEffect(() => { boot().then(setEng) }, [])
  return eng
}

export default function App() {
  const eng = useEngine()
  const [q] = useSearchParams()

  if (!eng)
    return (
      <div className="grid min-h-screen place-items-center">
        <span className="label">booting engine</span>
      </div>
    )

  const { CK, registry } = eng

  // the capture route: film full bleed, no chrome, nothing to click
  const isolated = q.get('render')
  if (isolated) return <RenderRoute ck={CK} registry={registry} slug={isolated} />

  return (
    <Routes>
      <Route path="/" element={<Index ck={CK} registry={registry} />} />
      <Route path="/:slug" element={<FilmPage ck={CK} registry={registry} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
