use serde::{Deserialize, Serialize};
use std::collections::HashMap;

mod text;
pub use text::init_font;

#[derive(Deserialize)]
pub struct Stage {
    pub fps: f32,
    pub size: [f32; 2],
    pub scenes: Vec<Scene>,
}

#[derive(Deserialize)]
pub struct Scene {
    pub id: String,
    #[serde(default)]
    pub bg: Option<String>,
    pub nodes: Vec<Node>,
}

#[derive(Deserialize)]
pub struct Node {
    pub id: String,
    #[serde(rename = "type")]
    pub kind: String,
    #[serde(default)]
    pub text: Option<String>,
    #[serde(default)]
    pub x: f32,
    #[serde(default)]
    pub y: f32,
    #[serde(default)]
    pub w: Option<f32>,
    #[serde(default)]
    pub h: Option<f32>,
    #[serde(default)]
    pub radius: Option<f32>,
    #[serde(default)]
    pub fill: Option<String>,
    #[serde(default)]
    pub font: Option<Font>,
    #[serde(default)]
    pub color: Option<String>,
    #[serde(default)]
    pub keys: HashMap<String, Vec<Key>>,
    #[serde(default)]
    pub glow: Option<Glow>,
    #[serde(skip)]
    reveal: Option<(f32, Reveal)>,
    /// property name -> (loop start, loop period), set by looped overlay tracks
    #[serde(skip)]
    loops: HashMap<String, (f32, f32)>,
}

/// a soft emission behind the node: a gaussian-blurred copy of the shape,
/// drawn first. sigma and opacity are overridable per-frame through the
/// keyed properties `glow_sigma` and `glow_opacity`.
#[derive(Deserialize, Clone)]
pub struct Glow {
    #[serde(default = "d_sigma")]
    pub sigma: f32,
    #[serde(default = "d_glow_opacity")]
    pub opacity: f32,
    #[serde(default)]
    pub color: Option<String>,
}
fn d_sigma() -> f32 {
    32.0
}
fn d_glow_opacity() -> f32 {
    0.85
}

#[derive(Deserialize)]
pub struct Font {
    #[serde(default = "default_family")]
    pub family: String,
    #[serde(default = "default_weight")]
    pub weight: u32,
    #[serde(default = "default_size")]
    pub size: f32,
}
fn default_family() -> String {
    "sans-serif".into()
}
fn default_weight() -> u32 {
    400
}
fn default_size() -> f32 {
    48.0
}

#[derive(Deserialize)]
pub struct Key {
    pub t: f32,
    pub v: f32,
    #[serde(default)]
    pub ease: Option<Ease>,
}

#[derive(Deserialize, Clone)]
#[serde(untagged)]
pub enum Ease {
    Named(String),
    Bezier([f32; 4]),
}

/// word-by-word entrance: each word rises in from below, opacity leading the
/// move, flashes in the accent color and tempers to the node's ink. defaults
/// are the measured numbers from the ai-1 teardown.
#[derive(Deserialize, Clone)]
pub struct Reveal {
    #[serde(default = "d_unit")]
    pub unit: String,
    #[serde(default = "d_stagger")]
    pub stagger: f32,
    #[serde(default = "d_dur")]
    pub dur: f32,
    #[serde(default = "d_rise")]
    pub rise: f32,
    #[serde(default = "d_accent")]
    pub accent: String,
    #[serde(default)]
    pub keep: Vec<String>,
    #[serde(default = "d_cdelay")]
    pub color_delay: f32,
    #[serde(default = "d_cdur")]
    pub color_dur: f32,
}
fn d_unit() -> String {
    "word".into()
}
fn d_stagger() -> f32 {
    0.05
}
fn d_dur() -> f32 {
    0.27
}
fn d_rise() -> f32 {
    40.0
}
fn d_accent() -> String {
    "#e8671f".into()
}
fn d_cdelay() -> f32 {
    0.16
}
fn d_cdur() -> f32 {
    0.3
}

#[derive(Deserialize)]
pub struct Overlay {
    pub tracks: Vec<Track>,
}

#[derive(Deserialize)]
pub struct Track {
    pub target: String,
    #[serde(default)]
    pub at: f32,
    #[serde(default)]
    pub keys: HashMap<String, Vec<Key>>,
    #[serde(default)]
    pub reveal: Option<Reveal>,
    /// repeat this track's keys forever from `at`
    #[serde(rename = "loop", default)]
    pub looped: bool,
}

#[derive(Serialize)]
pub struct DrawCmd {
    pub op: String,
    pub x: f32,
    pub y: f32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub w: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub h: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub radius: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub d: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub blur: Option<f32>,
    pub color: String,
    pub opacity: f32,
    pub scale: f32,
}

fn bezier_sample(a: f32, b: f32, u: f32) -> f32 {
    let inv = 1.0 - u;
    3.0 * inv * inv * u * a + 3.0 * inv * u * u * b + u * u * u
}

fn bezier_slope(a: f32, b: f32, u: f32) -> f32 {
    let inv = 1.0 - u;
    3.0 * inv * inv * a + 6.0 * inv * u * (b - a) + 3.0 * u * u * (1.0 - b)
}

/// css-style cubic bezier: find the curve parameter whose x equals `p`
/// (newton, bisection fallback), then return the y there.
fn bezier(p: f32, pts: &[f32; 4]) -> f32 {
    let [x1, y1, x2, y2] = *pts;
    let mut u = p;
    for _ in 0..8 {
        let err = bezier_sample(x1, x2, u) - p;
        let d = bezier_slope(x1, x2, u);
        if d.abs() < 1e-6 {
            break;
        }
        u = (u - err / d).clamp(0.0, 1.0);
    }
    if (bezier_sample(x1, x2, u) - p).abs() > 1e-4 {
        let (mut lo, mut hi) = (0.0f32, 1.0f32);
        for _ in 0..32 {
            u = (lo + hi) / 2.0;
            let x = bezier_sample(x1, x2, u);
            if (x - p).abs() < 1e-5 {
                break;
            }
            if x < p {
                lo = u;
            } else {
                hi = u;
            }
        }
    }
    bezier_sample(y1, y2, u)
}

fn out_cubic(p: f32) -> f32 {
    1.0 - (1.0 - p.clamp(0.0, 1.0)).powi(3)
}

fn ease(p: f32, kind: &Option<Ease>) -> f32 {
    let p = p.clamp(0.0, 1.0);
    match kind {
        Some(Ease::Bezier(pts)) => bezier(p, pts),
        Some(Ease::Named(name)) => match name.as_str() {
            "outCubic" => out_cubic(p),
            "inCubic" => p * p * p,
            "inOutCubic" => {
                if p < 0.5 {
                    4.0 * p * p * p
                } else {
                    1.0 - (-2.0 * p + 2.0).powi(3) / 2.0
                }
            }
            _ => p,
        },
        None => p,
    }
}

/// property lookup with loop support: looped tracks wrap time inside their
/// window so the keys repeat forever from the track start.
fn node_prop(node: &Node, name: &str, default: f32, t: f32) -> f32 {
    let t = match node.loops.get(name) {
        Some((at, period)) if t > *at => at + (t - at) % period,
        _ => t,
    };
    eval_prop(&node.keys, name, default, t)
}

fn eval_prop(keys: &HashMap<String, Vec<Key>>, name: &str, default: f32, t: f32) -> f32 {
    let track = match keys.get(name) {
        Some(k) if !k.is_empty() => k,
        _ => return default,
    };
    if t <= track[0].t {
        return track[0].v;
    }
    let last = &track[track.len() - 1];
    if t >= last.t {
        return last.v;
    }
    for w in track.windows(2) {
        let (a, b) = (&w[0], &w[1]);
        if t >= a.t && t <= b.t {
            let span = (b.t - a.t).max(1e-6);
            let p = (t - a.t) / span;
            return a.v + (b.v - a.v) * ease(p, &b.ease);
        }
    }
    last.v
}

fn parse_hex(c: &str) -> [f32; 3] {
    let h = c.trim_start_matches('#');
    let n = u32::from_str_radix(h, 16).unwrap_or(0);
    [
        ((n >> 16) & 0xff) as f32,
        ((n >> 8) & 0xff) as f32,
        (n & 0xff) as f32,
    ]
}

fn mix_hex(a: &str, b: &str, p: f32) -> String {
    let (ca, cb) = (parse_hex(a), parse_hex(b));
    let p = p.clamp(0.0, 1.0);
    format!(
        "#{:02x}{:02x}{:02x}",
        (ca[0] + (cb[0] - ca[0]) * p) as u8,
        (ca[1] + (cb[1] - ca[1]) * p) as u8,
        (ca[2] + (cb[2] - ca[2]) * p) as u8,
    )
}

/// resolve each overlay track onto its stage node: shift key times by the
/// track's `at` and attach them. overlay wins over inline stage keys.
fn merge(stage: &mut Stage, overlay: &Overlay) {
    for track in &overlay.tracks {
        for scene in stage.scenes.iter_mut() {
            if let Some(node) = scene.nodes.iter_mut().find(|n| n.id == track.target) {
                for (prop, keys) in &track.keys {
                    let shifted = keys
                        .iter()
                        .map(|k| Key {
                            t: k.t + track.at,
                            v: k.v,
                            ease: k.ease.clone(),
                        })
                        .collect();
                    node.keys.insert(prop.clone(), shifted);
                }
                if let Some(r) = &track.reveal {
                    node.reveal = Some((track.at, r.clone()));
                }
                if track.looped {
                    for (prop, keys) in &track.keys {
                        if let Some(last) = keys.last() {
                            if last.t > 0.0 {
                                node.loops.insert(prop.clone(), (track.at, last.t));
                            }
                        }
                    }
                }
            }
        }
    }
}

/// evaluate stage + overlay at time `t` into a flat list of draw commands.
/// deterministic: same inputs always yield the same output.
pub fn render_frame(stage_json: &str, overlay_json: &str, t: f32) -> String {
    let mut stage: Stage = match serde_json::from_str(stage_json) {
        Ok(s) => s,
        Err(e) => return format!("{{\"error\":{:?}}}", e.to_string()),
    };
    if !overlay_json.trim().is_empty() {
        match serde_json::from_str::<Overlay>(overlay_json) {
            Ok(o) => merge(&mut stage, &o),
            Err(e) => return format!("{{\"error\":{:?}}}", e.to_string()),
        }
    }
    let mut cmds: Vec<DrawCmd> = Vec::new();
    if let Some(scene) = stage.scenes.first() {
        cmds.push(DrawCmd {
            op: "clear".into(),
            x: 0.0,
            y: 0.0,
            w: None,
            h: None,
            radius: None,
            d: None,
            blur: None,
            color: scene.bg.clone().unwrap_or_else(|| "#ffffff".into()),
            opacity: 1.0,
            scale: 1.0,
        });
        for node in &scene.nodes {
            let opacity = node_prop(node, "opacity", 1.0, t);
            let dx = node_prop(node, "x", 0.0, t);
            let dy = node_prop(node, "y", 0.0, t);
            let scale = node_prop(node, "scale", 1.0, t);
            match node.kind.as_str() {
                "text" => {
                    let content = match &node.text {
                        Some(s) if !s.is_empty() => s,
                        _ => continue,
                    };
                    let (size, weight) = node
                        .font
                        .as_ref()
                        .map(|f| (f.size, f.weight as f32))
                        .unwrap_or((48.0, 400.0));
                    let line = match text::shape_line(content, size, weight) {
                        Some(l) => l,
                        None => continue,
                    };
                    let ink = node.color.clone().unwrap_or_else(|| "#000000".into());
                    let left = node.x + dx - line.width / 2.0;
                    let baseline = node.y + dy + line.baseline_shift;
                    // one clock per piece: a word, or a single glyph
                    let piece = |idx: f32, kept: bool| -> (f32, f32, String) {
                        match &node.reveal {
                            Some((at, r)) => {
                                let start = at + idx * r.stagger;
                                let p = ((t - start) / r.dur).clamp(0.0, 1.0);
                                let rise = r.rise * (1.0 - out_cubic(p));
                                let o = out_cubic((p * 2.0).min(1.0));
                                let q =
                                    ((t - start - r.color_delay) / r.color_dur).clamp(0.0, 1.0);
                                let color = if kept {
                                    r.accent.clone()
                                } else {
                                    mix_hex(&r.accent, &ink, out_cubic(q))
                                };
                                (o, rise, color)
                            }
                            None => (1.0, 0.0, ink.clone()),
                        }
                    };
                    let glyph_unit = node
                        .reveal
                        .as_ref()
                        .map(|(_, r)| r.unit == "glyph")
                        .unwrap_or(false);
                    let mut gi = 0usize;
                    for (wi, word) in line.words.iter().enumerate() {
                        let kept = node
                            .reveal
                            .as_ref()
                            .map(|(_, r)| r.keep.iter().any(|k| k == &word.text))
                            .unwrap_or(false);
                        if glyph_unit {
                            for glyph in &word.glyphs {
                                let (o, rise, color) = piece(gi as f32, kept);
                                gi += 1;
                                cmds.push(DrawCmd {
                                    op: "path".into(),
                                    x: left + word.x + glyph.x,
                                    y: baseline + rise,
                                    w: None,
                                    h: None,
                                    radius: None,
                                    d: Some(glyph.path.clone()),
                                    blur: None,
                                    color,
                                    opacity: opacity * o,
                                    scale,
                                });
                            }
                        } else {
                            let (o, rise, color) = piece(wi as f32, kept);
                            cmds.push(DrawCmd {
                                op: "path".into(),
                                x: left + word.x,
                                y: baseline + rise,
                                w: None,
                                h: None,
                                radius: None,
                                d: Some(word.path.clone()),
                                blur: None,
                                color,
                                opacity: opacity * o,
                                scale,
                            });
                        }
                    }
                }
                "rect" => {
                    let fill = node.fill.clone().unwrap_or_else(|| "#000000".into());
                    if let Some(g) = &node.glow {
                        let sigma = node_prop(node, "glow_sigma", g.sigma, t);
                        let glow_opacity = node_prop(node, "glow_opacity", g.opacity, t);
                        cmds.push(DrawCmd {
                            op: "rect".into(),
                            x: node.x + dx,
                            y: node.y + dy,
                            w: node.w,
                            h: node.h,
                            radius: node.radius,
                            d: None,
                            blur: Some(sigma),
                            color: g.color.clone().unwrap_or_else(|| fill.clone()),
                            opacity: opacity * glow_opacity,
                            scale,
                        });
                    }
                    cmds.push(DrawCmd {
                        op: "rect".into(),
                        x: node.x + dx,
                        y: node.y + dy,
                        w: node.w,
                        h: node.h,
                        radius: node.radius,
                        d: None,
                        blur: None,
                        color: fill,
                        opacity,
                        scale,
                    });
                }
                _ => {}
            }
        }
    }
    serde_json::to_string(&cmds).unwrap_or_else(|_| "[]".into())
}

#[cfg(target_arch = "wasm32")]
mod wasm {
    use wasm_bindgen::prelude::*;
    #[wasm_bindgen]
    pub fn render(stage_json: &str, overlay_json: &str, t: f32) -> String {
        super::render_frame(stage_json, overlay_json, t)
    }
    #[wasm_bindgen]
    pub fn init_font(bytes: &[u8]) -> bool {
        super::init_font(bytes.to_vec())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;

    const STAGE: &str = r##"{
      "fps":30,"size":[1920,1080],
      "scenes":[{"id":"s1","bg":"#fafafa","nodes":[
        {"id":"title","type":"text","text":"The fastest way to scale","x":960,"y":500,
         "font":{"family":"inter","weight":600,"size":72},"color":"#161616"},
        {"id":"pill","type":"rect","x":960,"y":660,"w":480,"h":96,"radius":48,"fill":"#ea752f"}
      ]}]
    }"##;

    const OVERLAY: &str = r##"{
      "tracks":[
        {"target":"title","at":0.2,"reveal":{"unit":"word","keep":["scale"]}},
        {"target":"pill","at":1.1,"keys":{
          "opacity":[{"t":0,"v":0},{"t":0.05,"v":1}],
          "scale":[{"t":0,"v":0.96},{"t":0.17,"v":1,"ease":[0.22,1.0,0.36,1.0]}]}}
      ]
    }"##;

    fn load_font() {
        let path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../editor/assets/fonts/Inter-Variable.ttf"
        );
        let _ = init_font(std::fs::read(path).expect("font file"));
    }

    fn frame(t: f32) -> Vec<Value> {
        load_font();
        serde_json::from_str(&render_frame(STAGE, OVERLAY, t)).unwrap()
    }

    #[test]
    fn shapes_words_with_real_metrics() {
        load_font();
        let line = text::shape_line("The fastest way to scale", 72.0, 600.0).unwrap();
        assert_eq!(line.words.len(), 5);
        assert!(line.width > 400.0, "width {}", line.width);
        for pair in line.words.windows(2) {
            assert!(pair[1].x > pair[0].x + pair[0].width * 0.5);
        }
    }

    #[test]
    fn weight_axis_changes_outlines() {
        load_font();
        let heavy = text::shape_line("The", 72.0, 700.0).unwrap();
        let light = text::shape_line("The", 72.0, 300.0).unwrap();
        assert_ne!(heavy.words[0].path, light.words[0].path);
    }

    #[test]
    fn reveal_staggers_and_settles() {
        // before the track starts every word is hidden
        let f0 = frame(0.0);
        assert_eq!(f0.len(), 7, "clear + 5 words + pill");
        assert_eq!(f0[0]["op"], "clear");
        assert_eq!(f0[1]["opacity"], 0.0);

        // mid-reveal the first word leads the last
        let mid = frame(0.35);
        let first = mid[1]["opacity"].as_f64().unwrap();
        let last = mid[5]["opacity"].as_f64().unwrap();
        assert!(first > last, "stagger: first {first} last {last}");

        // settled: full opacity, ink color, except the kept accent word
        let done = frame(1.0);
        for w in &done[1..5] {
            assert_eq!(w["opacity"], 1.0);
            assert_eq!(w["color"], "#161616");
        }
        assert_eq!(done[5]["color"], "#e8671f", "scale keeps the accent");
    }

    #[test]
    fn looped_track_wraps_time() {
        load_font();
        let stage = r##"{"fps":30,"size":[1920,1080],"scenes":[{"id":"s","bg":"#050505",
          "nodes":[{"id":"pill","type":"rect","x":960,"y":540,"w":700,"h":110,
                    "radius":55,"fill":"#4a21d5","glow":{"sigma":40,"opacity":0.9}}]}]}"##;
        let overlay = r##"{"tracks":[{"target":"pill","loop":true,"keys":{
          "glow_opacity":[{"t":0,"v":0.8},{"t":0.725,"v":1.0,"ease":"inOutCubic"},
                          {"t":1.45,"v":0.8,"ease":"inOutCubic"}]}}]}"##;
        let probe = |t: f32| -> f64 {
            let cmds: Vec<Value> =
                serde_json::from_str(&render_frame(stage, overlay, t)).unwrap();
            cmds[1]["opacity"].as_f64().unwrap()
        };
        let a = probe(0.3);
        let b = probe(0.3 + 1.45);
        let c = probe(0.3 + 2.0 * 1.45);
        assert!((a - b).abs() < 1e-5 && (b - c).abs() < 1e-5, "{a} {b} {c}");
        assert!(probe(0.725) > probe(0.05), "breath peaks mid-cycle");
    }

    #[test]
    fn glow_emits_echo_before_shape() {
        load_font();
        let stage = r##"{"fps":30,"size":[1920,1080],"scenes":[{"id":"s","bg":"#050505",
          "nodes":[{"id":"pill","type":"rect","x":960,"y":540,"w":700,"h":110,
                    "radius":55,"fill":"#4a21d5","glow":{"sigma":40,"opacity":0.9}}]}]}"##;
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 0.5)).unwrap();
        assert_eq!(cmds[0]["op"], "clear");
        assert_eq!(cmds[0]["color"], "#050505");
        assert_eq!(cmds[1]["blur"], 40.0, "echo first, blurred");
        assert_eq!(cmds[1]["opacity"], 0.9);
        assert!(cmds[2]["blur"].is_null(), "crisp shape second");
    }

    #[test]
    fn glyph_unit_gives_each_letter_its_own_clock() {
        load_font();
        let overlay = r##"{"tracks":[
          {"target":"title","at":0.2,
           "reveal":{"unit":"glyph","stagger":0.03,"keep":["scale"]}}
        ]}"##;
        let cmds: Vec<Value> =
            serde_json::from_str(&render_frame(STAGE, overlay, 0.5)).unwrap();
        let paths: Vec<&Value> = cmds.iter().filter(|c| c["op"] == "path").collect();
        assert_eq!(paths.len(), 20, "one cmd per glyph");
        let first = paths[0]["opacity"].as_f64().unwrap();
        let last = paths[19]["opacity"].as_f64().unwrap();
        assert!(first > last, "first glyph {first} leads last {last}");

        let done: Vec<Value> =
            serde_json::from_str(&render_frame(STAGE, overlay, 2.0)).unwrap();
        let settled: Vec<&Value> = done.iter().filter(|c| c["op"] == "path").collect();
        for g in &settled[15..20] {
            assert_eq!(g["color"], "#e8671f", "scale glyphs keep accent");
        }
        assert_eq!(settled[0]["color"], "#161616");
    }

    #[test]
    fn pill_still_pops() {
        let f = frame(1.4);
        let pill = f.iter().find(|c| c["op"] == "rect").unwrap();
        assert_eq!(pill["opacity"], 1.0);
        assert_eq!(pill["scale"], 1.0);
    }

    #[test]
    fn deterministic() {
        load_font();
        assert_eq!(
            render_frame(STAGE, OVERLAY, 0.8),
            render_frame(STAGE, OVERLAY, 0.8)
        );
    }
}
