#!/usr/bin/env python3
"""
Conformance: how close a rendered film is to the video it reproduces.

Renders a doc at the reference video's OWN presentation timestamps, then scores
two independent things:

  timing      pearson correlation of the two motion-energy curves. this asks
              "do we move when they move". it is brutally sensitive: on claude,
              aligned scores r=0.62 and a ONE frame offset collapses it to 0.00.

  appearance  mean absolute pixel error over the whole frame, 0-255. this asks
              "does it look like theirs". monotonic in misalignment: 3.3 aligned,
              6.5 at ten frames out, 17.0 at sixty.

Both are needed. Neither alone is enough, and a single blended percentage would
hide which one moved, so this never reports one.

Whole-frame SSIM was tried first and is useless here: on `terminal` it scored
0.877 aligned, 0.878 offset by a second, and 0.877 against the reference played
backwards. It is dominated by the static majority of the frame. Do not put it
back without a control run proving it discriminates.

Energy is measured exactly the way analysis/extract.sh measured it (160x90
greyscale, mean abs diff between consecutive frames) so our numbers and the
stored motion-energy.txt are comparable. That is asserted, not assumed: see
--selftest.
"""

import argparse, json, math, subprocess, sys, time
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("conform needs numpy and pillow.  see conform/README.md")

ROOT = Path(__file__).resolve().parent.parent      # whippan/
REPO = ROOT.parent                                  # json-edit/
ANALYSIS = REPO / "analysis"
DOCS = ROOT / "docs"
OUT = ROOT / "out" / "conform"
EXPORT = ROOT / "target" / "release" / "export"

# the size the reference pipeline measured energy at; kept identical so our
# numbers and the stored motion-energy.txt can be compared directly
GRID = (160, 90)


def films():
    """analysis dirs paired with the doc they reproduce, if there is one"""
    docs = {p.name[: -len(".stage.json")] for p in DOCS.glob("*.stage.json")}
    found = {}
    for d in sorted(ANALYSIS.iterdir()):
        if not (d.is_dir() and (d / "frames").is_dir() and (d / "pts.txt").exists()):
            continue
        # analysis dirs were named after the source video, which does not always
        # match the doc slug
        for cand in (d.name, d.name.replace("-video", "").replace("-main", "").replace("-figma", "")):
            if cand in docs:
                found[cand] = d
                break
    return found


def load(paths, size=GRID):
    return np.stack(
        [np.asarray(Image.open(p).convert("L").resize(size), dtype=np.float32) for p in paths]
    )


def energy(seq):
    """mean abs difference between consecutive frames, one value per gap"""
    return np.abs(np.diff(seq, axis=0)).mean(axis=(1, 2))


def pearson(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / d) if d else 0.0


def best_lag(ours, ref, span=12):
    """
    The lag that would score best, and its score.

    A film can be right but late. Reporting only the zero-lag number would call
    that a failure without saying it is fixable by shifting one `at`.
    """
    best = (0, pearson(ours, ref))
    for k in range(-span, span + 1):
        if k == 0:
            continue
        a, b = (ours[: len(ours) - k], ref[k:]) if k > 0 else (ours[-k:], ref[: len(ref) + k])
        if len(a) < 8:
            continue
        r = pearson(a, b)
        if r > best[1]:
            best = (k, r)
    return best


def scene_spans(slug, times):
    """frame index ranges per scene, so a failure names the beat it is in"""
    stage = json.loads((DOCS / f"{slug}.stage.json").read_text())
    spans, acc = [], 0.0
    for sc in stage["scenes"]:
        dur = sc.get("dur", 3)
        lo = next((i for i, t in enumerate(times) if t >= acc), len(times))
        hi = next((i for i, t in enumerate(times) if t >= acc + dur), len(times))
        spans.append((sc["id"], lo, hi))
        acc += dur
    return spans


def render(slug, times_file, out_dir, force=False):
    """render our doc at the reference timestamps, reusing a fresh render"""
    stage = DOCS / f"{slug}.stage.json"
    anim = DOCS / f"{slug}.anim.json"
    stamp = out_dir / ".stamp"
    key = f"{stage.stat().st_mtime_ns}:{anim.stat().st_mtime_ns}:{EXPORT.stat().st_mtime_ns}"
    if not force and stamp.exists() and stamp.read_text() == key:
        return sorted(out_dir.glob("f*.png")), True
    if not EXPORT.exists():
        sys.exit(f"renderer missing at {EXPORT}\n  cargo build --release -p whippan-engine --bin export")
    subprocess.run(
        [str(EXPORT), "frames", str(stage), str(anim), str(out_dir), str(times_file)],
        cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    stamp.write_text(key)
    return sorted(out_dir.glob("f*.png")), False


def heatmap(ours_png, ref_jpg, dest):
    """where the frame is wrong, in red, over a dim copy of ours"""
    a = Image.open(ours_png).convert("RGB")
    b = Image.open(ref_jpg).convert("RGB").resize(a.size)
    d = np.abs(np.asarray(a, np.int16) - np.asarray(b, np.int16)).max(axis=2)
    base = (np.asarray(a.convert("L"), np.float32) * 0.35)[..., None].repeat(3, axis=2)
    base[..., 0] = np.clip(base[..., 0] + d * 1.6, 0, 255)
    Image.fromarray(base.astype(np.uint8)).save(dest)


def run(slug, adir, stride=1, force=False, keep=6):
    times = [float(x) for x in (adir / "pts.txt").read_text().split() if x.strip()]
    ref_files = sorted((adir / "frames").glob("f*.jpg"))
    n = min(len(times), len(ref_files))
    times, ref_files = times[:n], ref_files[:n]

    work = OUT / slug
    work.mkdir(parents=True, exist_ok=True)
    tf = work / "times.txt"
    tf.write_text("\n".join(f"{t:.6f}" for t in times) + "\n")

    t0 = time.time()
    our_files, cached = render(slug, tf, work / "frames", force)
    if len(our_files) < n:
        return {"slug": slug, "error": f"rendered {len(our_files)} frames, expected {n}"}

    sl = slice(None, None, stride)
    ours = load(our_files[:n][sl])
    ref = load(ref_files[sl])

    eo, er = energy(ours), energy(ref)
    lag, lag_r = best_lag(eo, er)
    mae = float(np.abs(ours - ref).mean())
    per_frame = np.abs(ours - ref).mean(axis=(1, 2))

    # a film that renders static against a moving reference is the single most
    # useful thing to surface, and correlation alone cannot say it
    ratio = float(eo.mean() / er.mean()) if er.mean() else 0.0

    scenes = []
    for sid, lo, hi in scene_spans(slug, times):
        lo, hi = lo // stride, hi // stride
        if hi - lo < 3:
            continue
        ro, rr = float(eo[lo:hi].mean()), float(er[lo:hi].mean())
        scenes.append({
            "id": sid,
            "mae": round(float(per_frame[lo:hi].mean()), 2),
            "timing": round(pearson(eo[lo:max(lo + 1, hi - 1)], er[lo:max(lo + 1, hi - 1)]), 3),
            "energy_ratio": round(ro / rr, 2) if rr else 0.0,
        })

    # a film mean can sit at parity while its scenes are wrong in both
    # directions and cancel: `claude` read 1.06 overall while one scene ran at
    # 2.76 and another at 0.46. Carry the spread so that cannot hide.
    off = [sc["energy_ratio"] for sc in scenes
           if sc["energy_ratio"] and not 0.7 <= sc["energy_ratio"] <= 1.4]

    worst_idx = np.argsort(-per_frame)[:keep]
    shots = (work / "worst")
    shots.mkdir(exist_ok=True)
    for f in shots.glob("*.png"):
        f.unlink()
    worst = []
    for i in sorted(int(x) for x in worst_idx):
        real = i * stride
        name = f"f{real + 1:04d}.png"
        heatmap(our_files[real], ref_files[real], shots / name)
        worst.append({"frame": real + 1, "t": round(times[real], 3),
                      "mae": round(float(per_frame[i]), 2), "heatmap": f"worst/{name}"})

    return {
        "slug": slug,
        "frames": len(ours),
        "stride": stride,
        "timing": round(pearson(eo, er), 3),
        "best_lag": lag,
        "timing_at_best_lag": round(lag_r, 3),
        "appearance_mae": round(mae, 2),
        "energy_ratio": round(ratio, 3),
        "scenes_off_energy": len(off),
        "our_energy": round(float(eo.mean()), 3),
        "ref_energy": round(float(er.mean()), 3),
        "scenes": scenes,
        "worst": worst,
        "seconds": round(time.time() - t0, 1),
        "cached": cached,
    }


def selftest():
    """our energy measure must reproduce what analysis/extract.sh recorded"""
    bad = 0
    for slug, adir in list(films().items())[:6]:
        saved = np.loadtxt(adir / "motion-energy.txt")
        ref = load(sorted((adir / "frames").glob("f*.jpg")))
        mine = np.concatenate([[0.0], energy(ref)])
        err = float(np.abs(mine - saved[: len(mine)]).max())
        ok = err < 0.01
        bad += not ok
        print(f"  {slug:<16} max abs err {err:.4f}  {'ok' if ok else 'MISMATCH'}")
    return bad


def main():
    ap = argparse.ArgumentParser(description="score a rendered film against the video it reproduces")
    ap.add_argument("films", nargs="*", help="slugs, or none for all")
    ap.add_argument("--stride", type=int, default=1, help="score every Nth frame (fast pass)")
    ap.add_argument("--force", action="store_true", help="re-render even if cached")
    ap.add_argument("--selftest", action="store_true", help="check our energy measure matches the pipeline")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(1 if selftest() else 0)

    avail = films()
    todo = args.films or sorted(avail)
    unknown = [s for s in todo if s not in avail]
    if unknown:
        sys.exit(f"no reference frames for: {', '.join(unknown)}\navailable: {', '.join(sorted(avail))}")

    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for slug in todo:
        print(f"{slug} ...", end=" ", flush=True)
        try:
            r = run(slug, avail[slug], args.stride, args.force)
        except subprocess.CalledProcessError as e:
            r = {"slug": slug, "error": f"render failed ({e.returncode})"}
        results.append(r)
        print(r.get("error") or f"timing {r['timing']:+.3f}  mae {r['appearance_mae']:.2f}  ({r['seconds']}s)")

    (OUT / "results.json").write_text(json.dumps(results, indent=1))
    report(results)

    ok = [r for r in results if "error" not in r]
    if ok:
        print(f"\n{'film':<16}{'timing':>8}{'lag':>6}{'mae':>8}{'energy':>9}{'off':>5}"
              f"  scenes worth opening")
        for r in sorted(ok, key=lambda r: r["timing"]):
            weak = [s["id"] for s in r["scenes"] if s["timing"] < 0.2][:4]
            print(f"{r['slug']:<16}{r['timing']:>+8.3f}{r['best_lag']:>6}{r['appearance_mae']:>8.2f}"
                  f"{r['energy_ratio']:>9.2f}{r['scenes_off_energy']:>5}  {' '.join(weak)}")
        nsc = sum(len(r["scenes"]) for r in ok)
        noff = sum(r["scenes_off_energy"] for r in ok)
        print(f"\nmean timing {np.mean([r['timing'] for r in ok]):+.3f}   "
              f"mean mae {np.mean([r['appearance_mae'] for r in ok]):.2f}   "
              f"over {len(ok)} films")
        # the honest headline: a film mean can sit at parity while its scenes
        # cancel each other out, so count the scenes that are actually wrong
        print(f"scenes outside 0.7-1.4 energy: {noff} of {nsc} ({100*noff/nsc:.0f}%)")
    print(f"\nreport: {OUT / 'report.html'}")


def report(results):
    rows = []
    for r in sorted(results, key=lambda r: r.get("timing", -9)):
        if "error" in r:
            rows.append(f"<tr class=err><td>{r['slug']}</td><td colspan=5>{r['error']}</td></tr>")
            continue
        shots = "".join(
            f'<a href="{r["slug"]}/{w["heatmap"]}" title="frame {w["frame"]} · {w["t"]}s · mae {w["mae"]}">'
            f'<img src="{r["slug"]}/{w["heatmap"]}"></a>' for w in r["worst"])
        def chip(sc):
            off = not 0.7 <= sc["energy_ratio"] <= 1.4
            cls = "bad" if sc["timing"] < 0.2 or off else ""
            tail = "" if not off else f' {sc["energy_ratio"]}'
            return (f'<span class="{cls}" title="energy {sc["energy_ratio"]} '
                    f'mae {sc["mae"]} timing {sc["timing"]:+.2f}">{sc["id"]}{tail}</span>')
        bad = "".join(chip(sc) for sc in r["scenes"])
        rows.append(
            f"<tr><td><b>{r['slug']}</b><div class=sc>{bad}</div></td>"
            f"<td class=n>{r['timing']:+.3f}</td><td class=n>{r['best_lag']}</td>"
            f"<td class=n>{r['appearance_mae']:.2f}</td><td class=n>{r['energy_ratio']:.2f}</td>"
            f"<td class=shots>{shots}</td></tr>")
    (OUT / "report.html").write_text(f"""<!doctype html><meta charset=utf-8>
<title>whippan conformance</title>
<style>
 body{{font:13px/1.5 ui-monospace,Menlo,monospace;background:#faf9f8;color:#1a1a1a;margin:24px}}
 h1{{font-size:15px;font-weight:600;margin:0 0 4px}}
 p.sub{{color:#888;margin:0 0 18px}}
 table{{border-collapse:collapse;width:100%}}
 th{{text-align:left;font-weight:500;color:#888;padding:6px 10px;border-bottom:1px solid #ddd;font-size:11px;
     text-transform:uppercase;letter-spacing:.08em}}
 td{{padding:8px 10px;border-bottom:1px solid #eee;vertical-align:top}}
 td.n{{text-align:right;font-variant-numeric:tabular-nums}}
 .sc{{color:#aaa;font-size:10px;margin-top:3px}} .sc span{{margin-right:5px}}
 .sc .bad{{color:#c0392b}}
 .shots img{{height:52px;margin-right:4px;border:1px solid #ddd;border-radius:3px}}
 tr.err td{{color:#c0392b}}
</style>
<h1>whippan conformance</h1>
<p class=sub>timing is the correlation of motion-energy curves; one frame of drift takes it to zero.
 mae is mean absolute pixel error, 0-255. energy is ours over theirs: near 0 means we render static.
 red in a heatmap is where the frame is wrong. sorted worst first.</p>
<table><tr><th>film</th><th>timing</th><th>lag</th><th>mae</th><th>energy</th><th>worst frames</th></tr>
{''.join(rows)}</table>""")


if __name__ == "__main__":
    main()
