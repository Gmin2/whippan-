# whippan studio

the editor for whippan documents. react renders the chrome; every pixel on
the canvas comes from the whippan engine (rust -> wasm) through the shared
skia painter. the ui follows the grammar of the reference motion editors:
the timeline narrates the canvas, controls bloom from their trigger, and
the whole app is meant to be filmable.

dev: `npm install && npm run dev` (port 8900).

`vendor/` holds build artifacts from the whippan engine repo (wasm pkg,
painter, canvaskit, fonts). rebuild there, copy here.
