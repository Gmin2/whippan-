// paints one frame of engine draw commands onto a canvaskit canvas.
// the only place draw commands are interpreted — the tracer and the
// conformance harness both go through here.

function drawOne(CK, skc, paint, c, images) {
  let shader = null;
  if (c.grad) {
    const colors = c.grad.stops.map(([, hex]) => {
      const sc = CK.parseColorString(hex);
      sc[3] *= c.opacity;
      return sc;
    });
    const at = c.grad.stops.map(([a]) => a);
    // a radial carries its reach; x0/y0 is then the centre
    shader = c.grad.radius
      ? CK.Shader.MakeRadialGradient(
          [c.grad.x0, c.grad.y0], c.grad.radius,
          colors, at, CK.TileMode.Clamp)
      : CK.Shader.MakeLinearGradient(
          [c.grad.x0, c.grad.y0], [c.grad.x1, c.grad.y1],
          colors, at, CK.TileMode.Clamp);
    paint.setShader(shader);
  } else if (c.noise) {
    // perlin, as its own layer. the same skia shader the native painter
    // builds, so the browser preview and the export agree.
    shader = c.noise.turbulence
      ? CK.Shader.MakeTurbulence(c.noise.freq, c.noise.freq, c.noise.octaves, c.noise.seed, 0, 0)
      : CK.Shader.MakeFractalNoise(c.noise.freq, c.noise.freq, c.noise.octaves, c.noise.seed, 0, 0);
    paint.setShader(shader);
    paint.setAlphaf(c.opacity);
  } else {
    const col = CK.parseColorString(c.color);
    col[3] = c.opacity;
    paint.setColor(col);
    paint.setShader(null);
  }
  // one paint is threaded through every command in the frame, so this has to
  // be set on EVERY command and not only the blended ones — otherwise the
  // first noise layer would grade everything drawn after it
  const modes = {
    screen: CK.BlendMode.Screen, softLight: CK.BlendMode.SoftLight,
    multiply: CK.BlendMode.Multiply, plus: CK.BlendMode.Plus,
    overlay: CK.BlendMode.Overlay,
  };
  paint.setBlendMode(c.blend ? (modes[c.blend] || CK.BlendMode.Overlay) : CK.BlendMode.SrcOver);
  paint.setMaskFilter(c.blur
    ? CK.MaskFilter.MakeBlur(CK.BlurStyle.Normal, c.blur, true)
    : null);
  if (c.stroke) {
    paint.setStyle(CK.PaintStyle.Stroke);
    paint.setStrokeWidth(c.stroke);
    paint.setStrokeCap(CK.StrokeCap.Round);
    paint.setStrokeJoin(CK.StrokeJoin.Round);
  } else {
    paint.setStyle(CK.PaintStyle.Fill);
  }
  skc.save();
  skc.translate(c.x, c.y);
  if (c.rot) skc.rotate(c.rot, 0, 0);
  skc.scale(c.scale, c.scale);
  if (c.op === 'path') {
    const p = cachedPath(CK, c.d);
    if (p) skc.drawPath(p, paint);
  } else if (c.op === 'rect') {
    const rr = CK.RRectXY(
      CK.LTRBRect(-c.w / 2, -c.h / 2, c.w / 2, c.h / 2),
      c.radius, c.radius);
    skc.drawRRect(rr, paint);
  } else if (c.op === 'image') {
    const img = images && images.get(c.src);
    if (img) {
      const dst = CK.LTRBRect(-c.w / 2, -c.h / 2, c.w / 2, c.h / 2);
      const ip = new CK.Paint();
      ip.setAlphaf(c.opacity);
      if (c.radius) {
        skc.save();
        skc.clipRRect(CK.RRectXY(dst, c.radius, c.radius), CK.ClipOp.Intersect, true);
        skc.drawImageRect(img, CK.LTRBRect(0, 0, img.width(), img.height()), dst, ip);
        skc.restore();
      } else {
        skc.drawImageRect(img, CK.LTRBRect(0, 0, img.width(), img.height()), dst, ip);
      }
      ip.delete();
    }
  }
  skc.restore();
  if (shader) shader.delete();
}

export function paintFrame(CK, skc, paint, cmds, images) {
  const gooGroups = new Map();
  for (const c of cmds) {
    if (c.goo) {
      if (!gooGroups.has(c.goo)) gooGroups.set(c.goo, []);
      gooGroups.get(c.goo).push(c);
    }
  }
  const gooDone = new Set();
  for (const c of cmds) {
    if (c.op === 'clear') {
      skc.clear(CK.parseColorString(c.color));
      continue;
    }
    if (c.op === 'camblur') {
      // camera motion blur: the scene renders through a directional blur
      const bf = CK.ImageFilter.MakeBlur(Math.max(c.w, 0.01), Math.max(c.h, 0.01),
        CK.TileMode.Clamp, null);
      const bp = new CK.Paint();
      bp.setImageFilter(bf);
      skc.saveLayer(bp);
      bp.delete(); bf.delete();
      continue;
    }
    if (c.op === 'camblur_end') {
      skc.restore();
      continue;
    }
    // clip/unclip is the scene-level transition clip, wipe/wipe_end is a
    // node-local reveal. neither was handled here at all, so a clipped
    // transition rendered in export and not in the editor.
    if (c.op === 'clip' || c.op === 'wipe') {
      skc.save();
      skc.clipRect(CK.XYWHRect(c.x, c.y, c.w || 0, c.h || 0), CK.ClipOp.Intersect, true);
      continue;
    }
    if (c.op === 'unclip' || c.op === 'wipe_end') {
      skc.restore();
      continue;
    }
    if (c.goo) {
      if (gooDone.has(c.goo)) continue;
      gooDone.add(c.goo);
      // blur then re-sharpen alpha: overlapping shapes fuse into metaballs
      const blur = CK.ImageFilter.MakeBlur(16, 16, CK.TileMode.Decal, null);
      const cf = CK.ColorFilter.MakeMatrix([
        1, 0, 0, 0, 0,
        0, 1, 0, 0, 0,
        0, 0, 1, 0, 0,
        0, 0, 0, 30, -3.75,
      ]);
      const filter = CK.ImageFilter.MakeColorFilter(cf, blur);
      const lp = new CK.Paint();
      lp.setImageFilter(filter);
      skc.saveLayer(lp);
      for (const g of gooGroups.get(c.goo)) drawOne(CK, skc, paint, g, images);
      skc.restore();
      lp.delete(); filter.delete(); cf.delete(); blur.delete();
      continue;
    }
    drawOne(CK, skc, paint, c, images);
  }
}

// parsed-path cache: glyph outlines and big static paths repeat every
// frame, and MakeFromSVGString is the hottest call in the painter. morphing
// paths churn, so the cache is bounded and evicts oldest-first.
const pathCache = new Map();
function cachedPath(CK, d) {
  if (!d) return null;
  let p = pathCache.get(d);
  if (p) return p;
  p = CK.Path.MakeFromSVGString(d);
  if (!p) return null;
  if (pathCache.size > 800) {
    let drop = pathCache.size - 400;
    for (const [k, v] of pathCache) {
      v.delete();
      pathCache.delete(k);
      if (--drop <= 0) break;
    }
  }
  pathCache.set(d, p);
  return p;
}
