import puppeteer from '/Users/mintu/coding/startup/json-edit/studio/node_modules/.pnpm/puppeteer-core@25.3.0/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js'
const exe = '/Users/mintu/coding/portfolio/ui/tools/svgs/svg-harness/.pptr-cache/chrome-headless-shell/mac_arm-150.0.7871.24/chrome-headless-shell-mac-arm64/chrome-headless-shell'
const b = await puppeteer.launch({ executablePath: exe, args: ['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader','--enable-webgl'] })
const p = await b.newPage()
await p.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 })
p.on('pageerror', e => console.log('[pageerror]', e.message))
await p.goto('http://localhost:8902/', { waitUntil: 'networkidle0' })
await new Promise(r => setTimeout(r, 11000))
console.log(await p.evaluate(() => {
  const B = window.boards
  if (!B) return 'no hook'
  const left = document.querySelector('canvas').getBoundingClientRect().left
  const sx = (1 * (1920 + 320) + 960) * B.cam.zoom + B.cam.pan.x + left
  const sy = 420 * B.cam.zoom + B.cam.pan.y
  return JSON.stringify({
    cam: B.cam,
    canvasLeft: left,
    frameCount: B.frames.length,
    board1Boxes: B.frames[1].boxes.map(b => b.id),
    computedPoint: { sx, sy },
    located: B.locate(sx, sy),
    picked: B.pick(sx, sy)?.id ?? null,
  }, null, 1)
}))
await b.close()
