# studio ui — functionality spec

what the studio must do, view by view. this is the contract for the ui
revamp: visual style is free to change, behaviour below is not.

## global shell

- one top bar across every view: brand mark, current film name, a
  segmented mode toggle (design | boards), save button. no other chrome
  outside the active view.
- left rail: film registry grouped (reproductions / examples), click to
  open, current film highlighted. collapsible; boards and design share it.
- hash routes: `#/<slug>` gallery, `#/edit/<slug>` design, `#/boards/<slug>`
  storyboard. mode toggle rewrites the hash, back/forward works.
- save posts stage.json + anim.json back to disk through the dev server.
  cmd+s anywhere. dirty state shown on the save button.
- engine boots once; every view renders through the same wasm + canvaskit
  painter. no second render path, ever.

## boards (storyboard canvas)

the figma-canvas view. no timeline, no inspector, no transport, no layer
list — canvas and floating chrome only.

- one column per scene, ordered left to right.
- script card on top of each column: scene number, id, start + duration,
  and the scene `note` from stage.json. card is part of the canvas
  (pans/zooms with it).
- progression frames flow downward per column: 2-5 samples through the
  scene so entrance, settled state and exit are all visible. each frame
  stamped with its absolute film time.
- frames are engine renders cached as snapshots; pan/zoom never
  re-renders the film.
- navigation: drag empty canvas to pan (grab cursor), wheel pans,
  cmd/ctrl+wheel zooms at the pointer, pinch works. zoom hud bottom
  right with fit-to-view. keyboard: 0 = fit, +/- = zoom steps.
- click a frame (no drag movement) -> switch to design mode with the
  playhead at that frame's time. hover highlights the frame and its
  timestamp.
- click a script card -> edit the note in place, enter saves it into the
  doc (marks dirty).
- still to build on this canvas, in value order:
  - seam threads between columns: which node ids carry across the cut
    or morph-link, drawn as connectors from frame to frame.
  - camera anchor badges on frames where a cam move targets the scene,
    placed at the anchor point.
  - beat ticks: music grid marks on the column edges once the doc has
    bpm, so cut-vs-beat drift is visible at a glance.
  - drag a column to reorder scenes; drag the column gap to retime.

## design (single-scene editor)

the direct-manipulation view. keeps stage + inspector + timeline, all
sharing selection state.

- stage: engine-rendered frame at the playhead. select by click, drag to
  move with snap guides, corner handles resize, outside-corner rotate,
  radius nub on rects, scrubby number fields. spacebar+drag pans, wheel
  zooms. selection/hover boxes drawn in canvas space so they track zoom.
- inspector: properties of the selected node (position, size, radius,
  fill, font...). edits are immediate and undoable, written to the doc.
- timeline: one row per node in scene order, keyframe diamonds per
  property, reveal spans, camera track rows on the scene. scrub head,
  zoomable ruler. click a key -> select node + jump playhead. drag keys
  to retime (still to build: multi-select, box-select keys).
- transport: play/pause, scrubber, time readout. playback loops the
  film. sound: bed + derived sfx should play here exactly like the
  gallery (still to wire; gallery sound.js is the reference impl).

## gallery view (inside studio)

- svg-harness layout: fisheye rail of films, preview card per film,
  click into design mode. this stays until the standalone gallery app
  fully replaces it, then it can die.

## non-goals for the revamp

- no second selection model. boards, stage, timeline, inspector all
  reference nodes by (scene id, node id) and time by absolute film
  seconds.
- no dom-rendered film frames anywhere. frames come from the engine or
  they do not exist.
- no per-view engine boots, no per-view doc fetches. one doc object,
  edits flow through the same `edit(mutate)` path so undo/redo stays
  possible.
