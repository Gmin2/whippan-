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
    shader = CK.Shader.MakeLinearGradient(
      [c.grad.x0, c.grad.y0], [c.grad.x1, c.grad.y1],
      colors, c.grad.stops.map(([at]) => at), CK.TileMode.Clamp);
    paint.setShader(shader);
  } else {
    const col = CK.parseColorString(c.color);
    col[3] = c.opacity;
    paint.setColor(col);
    paint.setShader(null);
  }
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
    const p = CK.Path.MakeFromSVGString(c.d);
    if (p) { skc.drawPath(p, paint); p.delete(); }
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
