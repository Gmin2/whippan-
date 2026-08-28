import puppeteer from '/Users/mintu/coding/startup/json-edit/studio/node_modules/.pnpm/puppeteer-core@25.3.0/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js'
const exe = '/Users/mintu/coding/portfolio/ui/tools/svgs/svg-harness/.pptr-cache/chrome-headless-shell/mac_arm-150.0.7871.24/chrome-headless-shell-mac-arm64/chrome-headless-shell'
const b = await puppeteer.launch({ executablePath: exe, args: ['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader','--enable-webgl'] })
const p = await b.newPage()
await p.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 })
p.on('pageerror', e => console.log('[pageerror]', e.message))
await p.goto('http://localhost:8902/', { waitUntil: 'networkidle0' })
await new Promise(r => setTimeout(r, 11000))
const pt = await p.evaluate(() => {
  const B = window.boards
  const left = document.querySelector('canvas').getBoundingClientRect().left
  return { x: (1*(1920+320)+960)*B.cam.zoom + B.cam.pan.x + left, y: 420*B.cam.zoom + B.cam.pan.y }
})
console.log('clicking', pt)
await p.mouse.move(pt.x, pt.y)
await new Promise(r => setTimeout(r, 300))
console.log('hover outline present:', await p.evaluate(() =>
  document.querySelectorAll('svg rect[stroke="#2d52f0"]').length))
await p.mouse.down(); await new Promise(r => setTimeout(r, 60)); await p.mouse.up()
await new Promise(r => setTimeout(r, 500))
console.log(await p.evaluate(() => JSON.stringify({
  blueRects: document.querySelectorAll('svg rect[stroke="#2d52f0"]').length,
  svgTexts: [...document.querySelectorAll('svg text')].map(t=>t.textContent).slice(-6),
  rightPanelHeadings: [...document.querySelectorAll('aside p')].map(t=>t.textContent),
})))
await p.screenshot({ path: 'wall-select.png' })
await b.close()
