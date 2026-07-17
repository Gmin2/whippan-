use serde::{Deserialize, Serialize};
use std::collections::HashMap;

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

/// the animation layer: motion only, joined to stage nodes by id.
/// key times inside a track are relative to `at`.
#[derive(Deserialize)]
pub struct Overlay {
    pub tracks: Vec<Track>,
}

#[derive(Deserialize)]
pub struct Track {
    pub target: String,
    #[serde(default)]
    pub at: f32,
    pub keys: HashMap<String, Vec<Key>>,
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
    pub text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub size: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub weight: Option<u32>,
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

fn ease(p: f32, kind: &Option<Ease>) -> f32 {
    let p = p.clamp(0.0, 1.0);
    match kind {
        Some(Ease::Bezier(pts)) => bezier(p, pts),
        Some(Ease::Named(name)) => match name.as_str() {
            "outCubic" => 1.0 - (1.0 - p).powi(3),
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
        for node in &scene.nodes {
            let opacity = eval_prop(&node.keys, "opacity", 1.0, t);
            let dx = eval_prop(&node.keys, "x", 0.0, t);
            let dy = eval_prop(&node.keys, "y", 0.0, t);
            let scale = eval_prop(&node.keys, "scale", 1.0, t);
            match node.kind.as_str() {
                "text" => {
                    let (size, weight) = node
                        .font
                        .as_ref()
                        .map(|f| (f.size, f.weight))
                        .unwrap_or((48.0, 400));
                    cmds.push(DrawCmd {
                        op: "text".into(),
                        x: node.x + dx,
                        y: node.y + dy,
                        w: None,
                        h: None,
                        radius: None,
                        text: node.text.clone(),
                        size: Some(size),
                        weight: Some(weight),
                        color: node.color.clone().unwrap_or_else(|| "#000000".into()),
                        opacity,
                        scale,
                    });
                }
                "rect" => {
                    cmds.push(DrawCmd {
                        op: "rect".into(),
                        x: node.x + dx,
                        y: node.y + dy,
                        w: node.w,
                        h: node.h,
                        radius: node.radius,
                        text: None,
                        size: None,
                        weight: None,
                        color: node.fill.clone().unwrap_or_else(|| "#000000".into()),
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
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;

    const STAGE: &str = r##"{
      "fps":30,"size":[1920,1080],
      "scenes":[{"id":"s1","bg":"#fafafa","nodes":[
        {"id":"title","type":"text","text":"The fastest way to scale","x":960,"y":540,
         "font":{"family":"grotesk","weight":600,"size":72},"color":"#161616"},
        {"id":"pill","type":"rect","x":960,"y":660,"w":480,"h":96,"radius":48,"fill":"#ea752f"}
      ]}]
    }"##;

    const OVERLAY: &str = r##"{
      "tracks":[
        {"target":"title","at":0,"keys":{
          "opacity":[{"t":0,"v":0},{"t":0.27,"v":1,"ease":"outCubic"}],
          "y":[{"t":0,"v":40},{"t":0.27,"v":0,"ease":"outCubic"}]}},
        {"target":"pill","at":1.1,"keys":{
          "opacity":[{"t":0,"v":0},{"t":0.05,"v":1}],
          "scale":[{"t":0,"v":0.96},{"t":0.17,"v":1,"ease":[0.22,1.0,0.36,1.0]}]}}
      ]
    }"##;

    fn frame(t: f32) -> Vec<Value> {
        serde_json::from_str(&render_frame(STAGE, OVERLAY, t)).unwrap()
    }

    #[test]
    fn overlay_tracks_land_on_their_nodes() {
        let f0 = frame(0.0);
        assert_eq!(f0[0]["opacity"], 0.0, "title hidden at start");
        assert_eq!(f0[0]["y"], 580.0, "title offset below home");
        assert_eq!(f0[1]["opacity"], 0.0, "pill hidden before its track starts");

        let f = frame(0.6);
        assert_eq!(f[0]["opacity"], 1.0, "title settled");
        assert_eq!(f[0]["y"], 540.0);
        assert_eq!(f[1]["opacity"], 0.0, "pill still waiting at 0.6s");

        let f2 = frame(1.4);
        assert_eq!(f2[1]["opacity"], 1.0, "pill visible after its track");
        assert_eq!(f2[1]["scale"], 1.0, "pill settled at full scale");
        assert_eq!(f2[1]["op"], "rect");
    }

    #[test]
    fn track_at_shifts_key_times() {
        // 1.1 + 0.17/2: mid pop, scale strictly between 0.96 and 1
        let f = frame(1.185);
        let s = f[1]["scale"].as_f64().unwrap();
        assert!(s > 0.96 && s < 1.0, "mid-pop scale {s}");
    }

    #[test]
    fn bezier_ease_shape() {
        let sym = [0.42, 0.0, 0.58, 1.0];
        assert!((bezier(0.5, &sym) - 0.5).abs() < 1e-3, "symmetric midpoint");
        assert!(bezier(0.25, &sym) < 0.25, "slow start");
        assert!(bezier(0.75, &sym) > 0.75, "fast end");
        let out = [0.22, 1.0, 0.36, 1.0];
        assert!(bezier(0.3, &out) > 0.7, "strong ease-out front-loads");
    }

    #[test]
    fn deterministic() {
        assert_eq!(render_frame(STAGE, OVERLAY, 1.3), render_frame(STAGE, OVERLAY, 1.3));
    }
}
