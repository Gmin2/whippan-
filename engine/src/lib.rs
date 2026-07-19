use serde::{Deserialize, Serialize};
use std::collections::HashMap;

mod text;
pub use text::{init_font, register_font};

#[derive(Deserialize)]
pub struct Stage {
    pub fps: f32,
    pub size: [f32; 2],
    pub scenes: Vec<Scene>,
    /// music bed mixed in at export
    #[serde(default)]
    pub audio: Option<Audio>,
}

#[derive(Deserialize, Clone)]
pub struct Audio {
    pub src: String,
    #[serde(default = "d_gain")]
    pub gain: f32,
    #[serde(default = "d_fade_out")]
    pub fade_out: f32,
}
fn d_gain() -> f32 {
    0.8
}
fn d_fade_out() -> f32 {
    0.6
}

#[derive(Deserialize)]
pub struct Scene {
    pub id: String,
    #[serde(default)]
    pub bg: Option<String>,
    /// seconds this scene owns on the timeline
    #[serde(default = "d_dur_scene")]
    pub dur: f32,
    /// how this scene enters (from the previous one)
    #[serde(default)]
    pub transition: Option<Transition>,
    pub nodes: Vec<Node>,
    /// camera keys (cam_x, cam_y, cam_zoom) attached by overlay tracks
    /// that target the scene id
    #[serde(skip)]
    keys: HashMap<String, Vec<Key>>,
}
fn d_dur_scene() -> f32 {
    5.0
}

#[derive(Deserialize, Clone)]
pub struct Transition {
    #[serde(default = "d_trans_kind")]
    pub kind: String,
    #[serde(default = "d_trans_dur")]
    pub dur: f32,
    /// push direction: which way the incoming scene travels from
    #[serde(default = "d_trans_dir")]
    pub dir: String,
    #[serde(default)]
    pub ease: Option<Ease>,
    /// magic move: nodes sharing an id across the cut glide as one object
    /// while unmatched nodes ride the crossfade
    #[serde(default)]
    pub morph: bool,
    #[serde(default)]
    pub morph_dur: Option<f32>,
    #[serde(default)]
    pub morph_ease: Option<Ease>,
}
fn d_trans_kind() -> String {
    "fade".into()
}
fn d_trans_dur() -> f32 {
    0.4
}
fn d_trans_dir() -> String {
    "left".into()
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
    /// image nodes: name the painter resolves to a loaded bitmap
    #[serde(default)]
    pub src: Option<String>,
    #[serde(default)]
    pub font: Option<Font>,
    #[serde(default)]
    pub color: Option<String>,
    #[serde(default)]
    pub keys: HashMap<String, Vec<Key>>,
    #[serde(default)]
    pub glow: Option<Glow>,
    #[serde(default)]
    pub gradient: Option<Gradient>,
    /// named property overrides the overlay can flip to (button pressed,
    /// panel open...). unknown names mean "back to base".
    #[serde(default)]
    pub states: HashMap<String, StateDef>,
    #[serde(skip)]
    flips: Vec<(f32, String)>,
    #[serde(skip)]
    reveal: Option<(f32, Reveal)>,
    /// property name -> (loop start, loop period), set by looped overlay tracks
    #[serde(skip)]
    loops: HashMap<String, (f32, f32)>,
    /// morph continuity: this node starts as the named node from the
    /// previous scene and interpolates into its own geometry
    #[serde(default)]
    pub morph: Option<Morph>,
    /// gooey group: shapes sharing a group render through a blur +
    /// alpha-threshold layer, fusing into metaballs
    #[serde(default)]
    pub goo: Option<String>,
    /// multi-exposure trail while the node moves
    #[serde(default)]
    pub streak: Option<Streak>,
}

#[derive(Deserialize, Clone)]
pub struct Streak {
    #[serde(default = "d_streak_samples")]
    pub samples: u32,
    #[serde(default = "d_streak_window")]
    pub window: f32,
    #[serde(default = "d_streak_gain")]
    pub gain: f32,
}
fn d_streak_samples() -> u32 {
    4
}
fn d_streak_window() -> f32 {
    0.08
}
fn d_streak_gain() -> f32 {
    0.5
}

#[derive(Deserialize, Clone)]
pub struct Morph {
    pub from: String,
    #[serde(default = "d_morph_dur")]
    pub dur: f32,
    #[serde(default)]
    pub ease: Option<Ease>,
}
fn d_morph_dur() -> f32 {
    0.5
}

struct MorphSrc {
    x: f32,
    y: f32,
    w: f32,
    h: f32,
    radius: f32,
    fill: String,
    dur: f32,
    ease: Option<Ease>,
    tsrc: Option<TextSrc>,
}

/// the frozen source side of a text morph: its glyphs get drawn under a
/// uniform scale toward the target size, colors lerping (open-slide model)
struct TextSrc {
    text: String,
    size: f32,
    weight: f32,
    family: String,
    color: String,
}

#[derive(Deserialize, Clone, Default)]
pub struct StateDef {
    #[serde(default)]
    pub fill: Option<String>,
    #[serde(default)]
    pub scale: Option<f32>,
    #[serde(default)]
    pub opacity: Option<f32>,
    #[serde(default)]
    pub dy: Option<f32>,
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
    /// displaces the echo, e.g. negative dy for a top-heavy bloom
    #[serde(default)]
    pub dx: f32,
    #[serde(default)]
    pub dy: f32,
}
fn d_sigma() -> f32 {
    32.0
}
fn d_glow_opacity() -> f32 {
    0.85
}

/// linear gradient fill. angle in degrees: 0 = left to right, 90 = top to
/// bottom. the engine projects the node's box onto the angle and hands the
/// painter finished line endpoints.
#[derive(Deserialize, Clone)]
pub struct Gradient {
    #[serde(default = "d_angle")]
    pub angle: f32,
    pub stops: Vec<Stop>,
}
fn d_angle() -> f32 {
    90.0
}

#[derive(Deserialize, Clone)]
pub struct Stop {
    pub at: f32,
    pub color: String,
}

#[derive(Serialize)]
pub struct Grad {
    pub x0: f32,
    pub y0: f32,
    pub x1: f32,
    pub y1: f32,
    pub stops: Vec<(f32, String)>,
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
    Spring { spring: [f32; 2] },
}

/// damped spring normalized to [0,1]: overshoots, oscillates `cycles` times,
/// settled by p=1. damping controls how fast the bounce dies.
fn spring(p: f32, damping: f32, cycles: f32) -> f32 {
    let p = p.clamp(0.0, 1.0);
    let w = cycles * std::f32::consts::PI * 2.0 + std::f32::consts::FRAC_PI_2;
    1.0 - (-damping * p).exp() * (w * p).cos()
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
    /// flip the target node to this named state at `at`
    #[serde(default)]
    pub state: Option<String>,
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
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grad: Option<Grad>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub src: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub goo: Option<String>,
    pub color: String,
    pub opacity: f32,
    pub scale: f32,
}

/// gradient line for a node's box at the given angle, endpoints relative to
/// the node origin
fn grad_for(g: &Gradient, w: f32, h: f32) -> Grad {
    let a = g.angle.to_radians();
    let (dx, dy) = (a.cos(), a.sin());
    let r = (w * dx.abs() + h * dy.abs()) / 2.0;
    Grad {
        x0: -r * dx,
        y0: -r * dy,
        x1: r * dx,
        y1: r * dy,
        stops: g.stops.iter().map(|s| (s.at, s.color.clone())).collect(),
    }
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
        Some(Ease::Spring { spring: s }) => spring(p, s[0], s[1]),
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
            "spring" => spring(p, 6.0, 1.0),
            _ => p,
        },
        None => p,
    }
}

const STATE_DUR: f32 = 0.12;

struct StateBlend {
    from_fill: Option<String>,
    to_fill: Option<String>,
    p: f32,
    scale: f32,
    opacity: f32,
    dy: f32,
}

/// resolve the node's latest state flip at time t, easing the overridden
/// props from the previous state's values over STATE_DUR
fn state_blend(node: &Node, t: f32) -> StateBlend {
    let neutral = StateBlend {
        from_fill: None,
        to_fill: None,
        p: 1.0,
        scale: 1.0,
        opacity: 1.0,
        dy: 0.0,
    };
    let mut cur: Option<(f32, &str)> = None;
    let mut prev: Option<&str> = None;
    for (at, name) in &node.flips {
        if *at <= t {
            prev = cur.map(|c| c.1);
            cur = Some((*at, name));
        } else {
            break;
        }
    }
    let Some((at, name)) = cur else {
        return neutral;
    };
    let lookup = |n: &str| node.states.get(n).cloned().unwrap_or_default();
    let to = lookup(name);
    let from = prev.map(lookup).unwrap_or_default();
    let p = out_cubic(((t - at) / STATE_DUR).clamp(0.0, 1.0));
    let lerp = |a: f32, b: f32| a + (b - a) * p;
    StateBlend {
        from_fill: from.fill.clone(),
        to_fill: to.fill.clone(),
        p,
        scale: lerp(from.scale.unwrap_or(1.0), to.scale.unwrap_or(1.0)),
        opacity: lerp(from.opacity.unwrap_or(1.0), to.opacity.unwrap_or(1.0)),
        dy: lerp(from.dy.unwrap_or(0.0), to.dy.unwrap_or(0.0)),
    }
}

fn arrow_path(s: f32) -> String {
    let pts = [
        (0.0, 0.0),
        (0.0, 18.4),
        (4.6, 14.1),
        (7.2, 20.4),
        (10.0, 19.2),
        (7.5, 13.0),
        (13.2, 13.0),
    ];
    let mut d = String::new();
    for (i, (x, y)) in pts.iter().enumerate() {
        let cmd = if i == 0 { 'M' } else { 'L' };
        let _ =
            std::fmt::Write::write_fmt(&mut d, format_args!("{}{:.1} {:.1}", cmd, x * s, y * s));
    }
    d.push('Z');
    d
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
            if scene.id == track.target {
                for (prop, keys) in &track.keys {
                    let shifted = keys
                        .iter()
                        .map(|k| Key {
                            t: k.t + track.at,
                            v: k.v,
                            ease: k.ease.clone(),
                        })
                        .collect();
                    scene.keys.insert(prop.clone(), shifted);
                }
                continue;
            }
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
                if let Some(s) = &track.state {
                    node.flips.push((track.at, s.clone()));
                    node.flips
                        .sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
                }
            }
        }
    }
}

/// evaluate stage + overlay at time `t` into a flat list of draw commands.
/// deterministic: same inputs always yield the same output.
pub fn render_frame(stage_json: &str, overlay_json: &str, t: f32) -> String {
    match render_cmds(stage_json, overlay_json, t) {
        Ok(cmds) => serde_json::to_string(&cmds).unwrap_or_else(|_| "[]".into()),
        Err(e) => format!("{{\"error\":{:?}}}", e),
    }
}

/// native entry point: the same evaluation returning structured commands
pub fn render_cmds(
    stage_json: &str,
    overlay_json: &str,
    t: f32,
) -> Result<Vec<DrawCmd>, String> {
    let mut stage: Stage =
        serde_json::from_str(stage_json).map_err(|e| e.to_string())?;
    if !overlay_json.trim().is_empty() {
        let o: Overlay =
            serde_json::from_str(overlay_json).map_err(|e| e.to_string())?;
        merge(&mut stage, &o);
    }
    let mut cmds: Vec<DrawCmd> = Vec::new();
    if stage.scenes.is_empty() {
        return Ok(cmds);
    }
    let mut starts = Vec::with_capacity(stage.scenes.len());
    let mut acc = 0.0f32;
    for s in &stage.scenes {
        starts.push(acc);
        acc += s.dur;
    }
    let mut active = stage.scenes.len() - 1;
    for (i, start) in starts.iter().enumerate() {
        if t < start + stage.scenes[i].dur {
            active = i;
            break;
        }
    }
    let scene = &stage.scenes[active];
    let tl = (t - starts[active]).max(0.0);
    let scene_bg = |s: &Scene| s.bg.clone().unwrap_or_else(|| "#ffffff".into());
    let mut clear_color = scene_bg(scene);
    // magic-move pairing: explicit node.morph, or same-id auto pairs when the
    // incoming transition asks for morph
    let mut morphs: HashMap<String, MorphSrc> = HashMap::new();
    let mut sources: std::collections::HashSet<String> = std::collections::HashSet::new();
    if active > 0 {
        let prev = &stage.scenes[active - 1];
        let auto = scene.transition.as_ref().filter(|tr| tr.morph);
        for node in &scene.nodes {
            let (from, dur, ease) = match (&node.morph, auto) {
                (Some(m), _) => (Some(m.from.clone()), m.dur, m.ease.clone()),
                (None, Some(tr)) if prev.nodes.iter().any(|n| n.id == node.id) => (
                    Some(node.id.clone()),
                    tr.morph_dur.unwrap_or(tr.dur * 2.5),
                    tr.morph_ease.clone(),
                ),
                _ => (None, 0.0, None),
            };
            let Some(from) = from else { continue };
            if let Some(srcn) = prev.nodes.iter().find(|n| n.id == from) {
                sources.insert(from.clone());
                morphs.insert(
                    node.id.clone(),
                    MorphSrc {
                        x: srcn.x + node_prop(srcn, "x", 0.0, prev.dur),
                        y: srcn.y + node_prop(srcn, "y", 0.0, prev.dur),
                        w: srcn.w.unwrap_or(0.0),
                        h: srcn.h.unwrap_or(0.0),
                        radius: srcn.radius.unwrap_or(0.0),
                        fill: srcn.fill.clone().unwrap_or_else(|| "#000000".into()),
                        dur,
                        ease,
                        tsrc: if srcn.kind == "text" {
                            srcn.text.as_ref().map(|txt| {
                                let (size, weight, family) = srcn
                                    .font
                                    .as_ref()
                                    .map(|f| (f.size, f.weight as f32, f.family.clone()))
                                    .unwrap_or((48.0, 400.0, "inter".into()));
                                TextSrc {
                                    text: txt.clone(),
                                    size,
                                    weight,
                                    family,
                                    color: srcn.color.clone().unwrap_or_else(|| "#000000".into()),
                                }
                            })
                        } else {
                            None
                        },
                    },
                );
            }
        }
    }
    let none: HashMap<String, MorphSrc> = HashMap::new();
    let no_skip: std::collections::HashSet<String> = std::collections::HashSet::new();

    // transition dispatch: a draw pass per scene plus the frame clear color
    let mut prev_pass: Option<Pass> = None;
    let mut cur_pass = Pass::plain(tl);
    if let Some(tr) = &scene.transition {
        if active > 0 && tl < tr.dur {
            let prev_bg = scene_bg(&stage.scenes[active - 1]);
            let p = (tl / tr.dur).clamp(0.0, 1.0);
            let prev_tl = t - starts[active - 1];
            match tr.kind.as_str() {
                "fade" => {
                    clear_color = mix_hex(&prev_bg, &clear_color, p);
                    let mut pp = Pass::plain(prev_tl);
                    pp.fade = 1.0 - p;
                    prev_pass = Some(pp);
                    cur_pass.fade = p;
                }
                "push" | "whip" => {
                    let whip = tr.kind == "whip";
                    let default_ease = if whip { "inOutCubic" } else { "outCubic" };
                    let e = ease(
                        p,
                        &tr.ease.clone().or(Some(Ease::Named(default_ease.into()))),
                    );
                    let (w, h) = (stage.size[0], stage.size[1]);
                    let (odx, ody, idx, idy) = match tr.dir.as_str() {
                        "right" => (e * w, 0.0, (e - 1.0) * w, 0.0),
                        "up" => (0.0, -e * h, 0.0, (1.0 - e) * h),
                        "down" => (0.0, e * h, 0.0, (e - 1.0) * h),
                        _ => (-e * w, 0.0, (1.0 - e) * w, 0.0),
                    };
                    clear_color = mix_hex(&prev_bg, &clear_color, p);
                    let blur = if whip {
                        // blur follows the slide's instantaneous speed
                        let dp = 0.01f32;
                        let e2 = ease(
                            (p + dp).min(1.0),
                            &tr.ease.clone().or(Some(Ease::Named(default_ease.into()))),
                        );
                        ((e2 - e).abs() / dp * 18.0).min(60.0)
                    } else {
                        0.0
                    };
                    let mut pp = Pass::plain(prev_tl);
                    pp.ox = odx;
                    pp.oy = ody;
                    pp.add_blur = blur;
                    prev_pass = Some(pp);
                    cur_pass.ox = idx;
                    cur_pass.oy = idy;
                    cur_pass.add_blur = blur;
                }
                "dip" => {
                    // out through a solid color, then in from it. dir doubles
                    // as the dip color when it holds a hex
                    let dip = if tr.dir.starts_with('#') {
                        tr.dir.clone()
                    } else {
                        "#000000".into()
                    };
                    if p < 0.5 {
                        let q = p * 2.0;
                        clear_color = mix_hex(&prev_bg, &dip, q);
                        let mut pp = Pass::plain(prev_tl);
                        pp.fade = 1.0 - q;
                        prev_pass = Some(pp);
                        cur_pass.fade = 0.0;
                    } else {
                        let q = (p - 0.5) * 2.0;
                        clear_color = mix_hex(&dip, &clear_color, q);
                        cur_pass.fade = q;
                    }
                }
                "zoom" => {
                    let e = ease(
                        p,
                        &tr.ease.clone().or(Some(Ease::Named("inOutCubic".into()))),
                    );
                    clear_color = mix_hex(&prev_bg, &clear_color, e);
                    let mut pp = Pass::plain(prev_tl);
                    pp.tzoom = 1.0 + e * 0.7;
                    pp.fade = 1.0 - e;
                    prev_pass = Some(pp);
                    cur_pass.tzoom = 1.14 - 0.14 * e;
                    cur_pass.fade = e;
                }
                "rise" | "dissolve" | "settle" | "bloom" => {
                    // open-slide phase choreography: exit ease-in through the
                    // first ~44%, enter ease-out from ~22%, always overlapped
                    let qe = (p / 0.44).clamp(0.0, 1.0);
                    let qn = ((p - 0.22) / 0.78).clamp(0.0, 1.0);
                    let ein = qe * qe * qe;
                    let eout = out_cubic(qn);
                    clear_color = mix_hex(&prev_bg, &clear_color, p);
                    let mut pp = Pass::plain(prev_tl);
                    pp.fade = 1.0 - ein;
                    cur_pass.fade = eout;
                    match tr.kind.as_str() {
                        "rise" => {
                            pp.oy = -10.0 * ein;
                            cur_pass.oy = 14.0 * (1.0 - eout);
                        }
                        "settle" => {
                            pp.oy = -8.0 * ein;
                            cur_pass.oy = 16.0 * (1.0 - eout);
                            cur_pass.add_blur = 5.0 * (1.0 - eout);
                        }
                        "bloom" => {
                            pp.tzoom = 1.0 + 0.012 * ein;
                            cur_pass.tzoom = 0.97 + 0.03 * eout;
                        }
                        _ => {}
                    }
                    prev_pass = Some(pp);
                }
                "wipe" => {
                    let e = ease(
                        p,
                        &tr.ease.clone().or(Some(Ease::Named("inOutCubic".into()))),
                    );
                    let (w, h) = (stage.size[0], stage.size[1]);
                    let clip = match tr.dir.as_str() {
                        "right" => [w * (1.0 - e), 0.0, w * e, h],
                        "up" => [0.0, h * (1.0 - e), w, h * e],
                        "down" => [0.0, 0.0, w, h * e],
                        _ => [0.0, 0.0, w * e, h],
                    };
                    prev_pass = Some(Pass::plain(prev_tl));
                    cur_pass.clip = Some(clip);
                }
                _ => {}
            }
        }
    }
    cmds.push(DrawCmd {
        op: "clear".into(),
        x: 0.0,
        y: 0.0,
        w: None,
        h: None,
        radius: None,
        d: None,
        blur: None,
        grad: None,
        src: None,
        goo: None,
        color: clear_color,
        opacity: 1.0,
        scale: 1.0,
    });
    if let Some(pp) = prev_pass {
        let prev = &stage.scenes[active - 1];
        render_scene(
            prev,
            &pp,
            stage.size[0],
            stage.size[1],
            &none,
            &sources,
            &mut cmds,
        );
    }
    render_scene(
        scene,
        &cur_pass,
        stage.size[0],
        stage.size[1],
        &morphs,
        &no_skip,
        &mut cmds,
    );
    Ok(cmds)
}

/// total timeline length of a stage doc in seconds
pub fn doc_duration(stage_json: &str) -> Result<f32, String> {
    let stage: Stage = serde_json::from_str(stage_json).map_err(|e| e.to_string())?;
    Ok(stage.scenes.iter().map(|s| s.dur).sum())
}

/// canvas size of a stage doc
pub fn doc_size(stage_json: &str) -> Result<(f32, f32), String> {
    let stage: Stage = serde_json::from_str(stage_json).map_err(|e| e.to_string())?;
    Ok((stage.size[0], stage.size[1]))
}

/// draw one scene's nodes at scene-local time `tl`, all opacities scaled by
/// `fade` (crossfades hand in a partial fade); ox/oy shift the whole scene
/// (push transitions)
/// per-scene draw parameters a transition hands to render_scene
struct Pass {
    tl: f32,
    fade: f32,
    ox: f32,
    oy: f32,
    /// extra zoom about canvas center on top of the scene camera
    tzoom: f32,
    /// blur added to every command (whip pans)
    add_blur: f32,
    /// clip rect [x, y, w, h] wrapped around the scene (wipes)
    clip: Option<[f32; 4]>,
}

impl Pass {
    fn plain(tl: f32) -> Self {
        Pass {
            tl,
            fade: 1.0,
            ox: 0.0,
            oy: 0.0,
            tzoom: 1.0,
            add_blur: 0.0,
            clip: None,
        }
    }
}

fn render_scene(
    scene: &Scene,
    pass: &Pass,
    cw: f32,
    ch: f32,
    morphs: &HashMap<String, MorphSrc>,
    skip: &std::collections::HashSet<String>,
    cmds: &mut Vec<DrawCmd>,
) {
    let t = pass.tl;
    let fade = pass.fade;
    let (ox, oy) = (pass.ox, pass.oy);
    let first = cmds.len();
    if let Some(c) = pass.clip {
        cmds.push(DrawCmd {
            op: "clip".into(),
            x: c[0],
            y: c[1],
            w: Some(c[2]),
            h: Some(c[3]),
            radius: None,
            d: None,
            blur: None,
            grad: None,
            src: None,
            goo: None,
            color: "#000000".into(),
            opacity: 1.0,
            scale: 1.0,
        });
    }
    {
        for node in &scene.nodes {
            if skip.contains(&node.id) {
                continue;
            }
            let sb = state_blend(node, t);
            // a morphing clone is a solid object: it never rides the crossfade
            let node_fade = if morphs.contains_key(&node.id) {
                1.0
            } else {
                fade
            };
            let opacity = node_prop(node, "opacity", 1.0, t) * node_fade * sb.opacity;
            let dx = node_prop(node, "x", 0.0, t);
            let dy = node_prop(node, "y", 0.0, t) + sb.dy;
            let scale = node_prop(node, "scale", 1.0, t) * sb.scale;
            match node.kind.as_str() {
                "text" => {
                    if let Some(src) = morphs.get(&node.id) {
                        if let Some(ts) = &src.tsrc {
                            if t < src.dur {
                                let p = ease(
                                    t / src.dur,
                                    &src.ease.clone().or(Some(Ease::Named("outCubic".into()))),
                                );
                                let (to_size, _, _) = node
                                    .font
                                    .as_ref()
                                    .map(|f| (f.size, 0.0, 0.0))
                                    .unwrap_or((48.0, 0.0, 0.0));
                                let k = 1.0 + (to_size / ts.size - 1.0) * p;
                                let line = match text::shape_line(
                                    &ts.text, ts.size, ts.weight, &ts.family,
                                ) {
                                    Some(l) => l,
                                    None => continue,
                                };
                                let ink = node.color.clone().unwrap_or_else(|| "#000000".into());
                                let color = mix_hex(&ts.color, &ink, p);
                                let l = |a: f32, b: f32| a + (b - a) * p;
                                let cx = l(src.x, node.x + dx);
                                let cy = l(src.y, node.y + dy);
                                let left = cx - line.width * k / 2.0;
                                let baseline = cy + line.baseline_shift * k;
                                for word in &line.words {
                                    cmds.push(DrawCmd {
                                        op: "path".into(),
                                        x: left + word.x * k,
                                        y: baseline,
                                        w: None,
                                        h: None,
                                        radius: None,
                                        d: Some(word.path.clone()),
                                        blur: None,
                                        grad: None,
                                        src: None,
                                        goo: None,
                                        color: color.clone(),
                                        opacity,
                                        scale: scale * k,
                                    });
                                }
                                continue;
                            }
                        }
                    }
                    let content = match &node.text {
                        Some(s) if !s.is_empty() => s,
                        _ => continue,
                    };
                    let (size, weight, family) = node
                        .font
                        .as_ref()
                        .map(|f| (f.size, f.weight as f32, f.family.clone()))
                        .unwrap_or((48.0, 400.0, "inter".into()));
                    let line = match text::shape_line(content, size, weight, &family) {
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
                                let q = ((t - start - r.color_delay) / r.color_dur).clamp(0.0, 1.0);
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
                                    grad: None,
                                    src: None,
                                    goo: None,
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
                                grad: None,
                                src: None,
                                goo: None,
                                color,
                                opacity: opacity * o,
                                scale,
                            });
                        }
                    }
                }
                "rect" => {
                    let base = node.fill.clone().unwrap_or_else(|| "#000000".into());
                    let fill = if node.flips.is_empty() {
                        base
                    } else {
                        mix_hex(
                            sb.from_fill.as_deref().unwrap_or(&base),
                            sb.to_fill.as_deref().unwrap_or(&base),
                            sb.p,
                        )
                    };
                    let mut gx = node.x + dx;
                    let mut gy = node.y + dy;
                    let mut gw = node.w.map(|base| node_prop(node, "w", base, t)).or(node.w);
                    let mut gh = node.h.map(|base| node_prop(node, "h", base, t)).or(node.h);
                    let mut gr = node.radius;
                    let mut fill = fill;
                    if let Some(src) = morphs.get(&node.id) {
                        {
                            if t < src.dur {
                                let p = ease(
                                    t / src.dur,
                                    &src.ease.clone().or(Some(Ease::Named("outCubic".into()))),
                                );
                                let l = |a: f32, b: f32| a + (b - a) * p;
                                gx = l(src.x, gx);
                                gy = l(src.y, gy);
                                gw = Some(l(src.w, gw.unwrap_or(0.0)));
                                gh = Some(l(src.h, gh.unwrap_or(0.0)));
                                gr = Some(l(src.radius, gr.unwrap_or(0.0)));
                                fill = mix_hex(&src.fill, &fill, p);
                            }
                        }
                    }
                    if let Some(st) = &node.streak {
                        for i in (1..=st.samples).rev() {
                            let back = st.window * i as f32 / st.samples as f32;
                            let ti = t - back;
                            if ti < 0.0 {
                                continue;
                            }
                            let ex = node.x + node_prop(node, "x", 0.0, ti);
                            let ey = node.y + node_prop(node, "y", 0.0, ti);
                            let dist = ((ex - gx).powi(2) + (ey - gy).powi(2)).sqrt();
                            if dist < 2.0 {
                                continue;
                            }
                            let fadeout = 1.0 - i as f32 / (st.samples + 1) as f32;
                            cmds.push(DrawCmd {
                                op: "rect".into(),
                                x: ex,
                                y: ey,
                                w: gw,
                                h: gh,
                                radius: gr,
                                d: None,
                                blur: None,
                                grad: None,
                                src: None,
                                goo: None,
                                color: fill.clone(),
                                opacity: opacity * st.gain * fadeout,
                                scale,
                            });
                        }
                    }
                    if let Some(g) = &node.glow {
                        let sigma = node_prop(node, "glow_sigma", g.sigma, t);
                        let glow_opacity = node_prop(node, "glow_opacity", g.opacity, t);
                        let echo_color = g.color.clone().unwrap_or_else(|| {
                            node.gradient
                                .as_ref()
                                .and_then(|gr| gr.stops.get(gr.stops.len() / 2))
                                .map(|s| s.color.clone())
                                .unwrap_or_else(|| fill.clone())
                        });
                        cmds.push(DrawCmd {
                            op: "rect".into(),
                            x: gx + g.dx,
                            y: gy + g.dy,
                            w: gw,
                            h: gh,
                            radius: gr,
                            d: None,
                            blur: Some(sigma),
                            grad: None,
                            src: None,
                            goo: None,
                            color: echo_color,
                            opacity: opacity * glow_opacity,
                            scale,
                        });
                    }
                    let grad = node
                        .gradient
                        .as_ref()
                        .map(|g| grad_for(g, gw.unwrap_or(0.0), gh.unwrap_or(0.0)));
                    cmds.push(DrawCmd {
                        op: "rect".into(),
                        x: gx,
                        y: gy,
                        w: gw,
                        h: gh,
                        radius: gr,
                        d: None,
                        blur: None,
                        grad,
                        src: None,
                        goo: node.goo.clone(),
                        color: fill,
                        opacity,
                        scale,
                    });
                }
                "cursor" => {
                    let s = node.w.unwrap_or(26.0) / 13.2;
                    let cx = node.x + dx;
                    let cy = node.y + dy;
                    let layers: [(f32, f32, f32, String, Option<f32>, f32); 3] = [
                        (2.0, 3.0, s, "#000000".into(), Some(5.0), 0.3),
                        (0.0, 0.0, s * 1.22, "#ffffff".into(), None, 1.0),
                        (
                            0.0,
                            0.0,
                            s,
                            node.fill.clone().unwrap_or_else(|| "#111111".into()),
                            None,
                            1.0,
                        ),
                    ];
                    for (lx, ly, ps, color, blur, alpha) in layers {
                        cmds.push(DrawCmd {
                            op: "path".into(),
                            x: cx + lx,
                            y: cy + ly,
                            w: None,
                            h: None,
                            radius: None,
                            d: Some(arrow_path(ps)),
                            blur,
                            grad: None,
                            src: None,
                            goo: None,
                            color,
                            opacity: opacity * alpha,
                            scale,
                        });
                    }
                }
                "image" => {
                    cmds.push(DrawCmd {
                        op: "image".into(),
                        x: node.x + dx,
                        y: node.y + dy,
                        w: node.w,
                        h: node.h,
                        radius: node.radius,
                        d: None,
                        blur: None,
                        grad: None,
                        src: node.src.clone(),
                        goo: node.goo.clone(),
                        color: "#000000".into(),
                        opacity,
                        scale,
                    });
                }
                _ => {}
            }
        }
    }
    let zoom = eval_prop(&scene.keys, "cam_zoom", 1.0, t);
    let cam_x = eval_prop(&scene.keys, "cam_x", 0.0, t);
    let cam_y = eval_prop(&scene.keys, "cam_y", 0.0, t);
    for c in &mut cmds[first..] {
        if c.op == "clip" {
            continue;
        }
        if zoom != 1.0 || cam_x != 0.0 || cam_y != 0.0 {
            c.x = (c.x - cam_x - cw / 2.0) * zoom + cw / 2.0;
            c.y = (c.y - cam_y - ch / 2.0) * zoom + ch / 2.0;
            c.scale *= zoom;
            if let Some(b) = c.blur.as_mut() {
                *b *= zoom;
            }
        }
        if pass.tzoom != 1.0 {
            c.x = (c.x - cw / 2.0) * pass.tzoom + cw / 2.0;
            c.y = (c.y - ch / 2.0) * pass.tzoom + ch / 2.0;
            c.scale *= pass.tzoom;
            if let Some(b) = c.blur.as_mut() {
                *b *= pass.tzoom;
            }
        }
        if pass.add_blur > 0.1 {
            c.blur = Some(c.blur.unwrap_or(0.0) + pass.add_blur);
        }
        c.x += ox;
        c.y += oy;
    }
    if pass.clip.is_some() {
        cmds.push(DrawCmd {
            op: "unclip".into(),
            x: 0.0,
            y: 0.0,
            w: None,
            h: None,
            radius: None,
            d: None,
            blur: None,
            grad: None,
            src: None,
            goo: None,
            color: "#000000".into(),
            opacity: 1.0,
            scale: 1.0,
        });
    }
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
    #[wasm_bindgen]
    pub fn register_font(name: &str, bytes: &[u8]) {
        super::register_font(name, bytes.to_vec());
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
            "/../assets/fonts/Inter-Variable.ttf"
        );
        let _ = init_font(std::fs::read(path).expect("font file"));
    }

    fn frame(t: f32) -> Vec<Value> {
        load_font();
        serde_json::from_str(&render_frame(STAGE, OVERLAY, t)).unwrap()
    }

    #[test]
    fn camera_zooms_about_center_and_pans() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"s1","bg":"#ffffff","dur":2.0,"nodes":[
            {"id":"r","type":"rect","x":300,"y":350,"w":100,"h":100,"fill":"#ea752f"}]}
        ]}"##;
        let overlay = r##"{"tracks":[
          {"target":"s1","keys":{
            "cam_zoom":[{"t":0,"v":1},{"t":1,"v":2}],
            "cam_x":[{"t":0,"v":0},{"t":1,"v":50}]}}
        ]}"##;
        let f = |t: f32| -> Value {
            let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, overlay, t)).unwrap();
            cmds.iter().find(|c| c["op"] == "rect").unwrap().clone()
        };
        let start = f(0.0);
        assert_eq!(start["x"], 300.0);
        assert_eq!(start["scale"], 1.0);
        // zoom 2, pan 50: x' = (300 - 50 - 500)*2 + 500 = 0
        let end = f(1.5);
        assert_eq!(end["x"], 0.0);
        assert_eq!(end["scale"], 2.0);
    }

    #[test]
    fn streak_emits_decaying_echoes_only_in_motion() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"s","bg":"#ffffff","dur":2.0,"nodes":[
            {"id":"r","type":"rect","x":100,"y":350,"w":80,"h":80,"fill":"#ea752f",
             "streak":{"samples":3,"window":0.09}}]}
        ]}"##;
        let overlay = r##"{"tracks":[
          {"target":"r","keys":{"x":[{"t":0,"v":0},{"t":0.3,"v":600}]}}
        ]}"##;
        let mid: Vec<Value> = serde_json::from_str(&render_frame(stage, overlay, 0.2)).unwrap();
        let rects: Vec<&Value> = mid.iter().filter(|c| c["op"] == "rect").collect();
        assert_eq!(rects.len(), 4, "3 echoes + body");
        let xs: Vec<f64> = rects.iter().map(|r| r["x"].as_f64().unwrap()).collect();
        assert!(
            xs.windows(2).all(|w| w[0] < w[1]),
            "trail behind motion: {xs:?}"
        );
        let os: Vec<f64> = rects
            .iter()
            .map(|r| r["opacity"].as_f64().unwrap())
            .collect();
        assert!(
            os.windows(2).all(|w| w[0] < w[1]),
            "opacity ramps to body: {os:?}"
        );

        let settled: Vec<Value> = serde_json::from_str(&render_frame(stage, overlay, 1.0)).unwrap();
        assert_eq!(
            settled.iter().filter(|c| c["op"] == "rect").count(),
            1,
            "no echoes at rest"
        );
    }

    #[test]
    fn spring_overshoots_and_settles() {
        assert!(spring(0.0, 6.0, 1.0).abs() < 1e-4, "starts at rest");
        let mut peak = 0.0f32;
        for i in 1..100 {
            peak = peak.max(spring(i as f32 / 100.0, 6.0, 1.0));
        }
        assert!(peak > 1.05, "overshoots: peak {peak}");
        assert!((spring(1.0, 6.0, 1.0) - 1.0).abs() < 0.01, "settled by end");
    }

    #[test]
    fn push_slides_both_scenes() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"a","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"r1","type":"rect","x":500,"y":350,"w":100,"h":100,"fill":"#ea752f"}]},
          {"id":"b","bg":"#000000","dur":1.0,
           "transition":{"kind":"push","dur":0.4,"dir":"left"},"nodes":[
            {"id":"r2","type":"rect","x":500,"y":350,"w":100,"h":100,"fill":"#4a21d5"}]}
        ]}"##;
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 1.2)).unwrap();
        let rects: Vec<&Value> = cmds.iter().filter(|c| c["op"] == "rect").collect();
        assert_eq!(rects.len(), 2, "both scenes drawn in the window");
        let out_x = rects[0]["x"].as_f64().unwrap();
        let in_x = rects[1]["x"].as_f64().unwrap();
        assert!(out_x < 200.0, "outgoing pushed off left: {out_x}");
        assert!(in_x > 500.0 && in_x < 1400.0, "incoming arriving: {in_x}");
        let settled: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 1.9)).unwrap();
        let r: Vec<&Value> = settled.iter().filter(|c| c["op"] == "rect").collect();
        assert_eq!(r.len(), 1);
        assert_eq!(r[0]["x"], 500.0);
    }

    #[test]
    fn text_morph_scales_source_glyphs() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"a","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"hero","type":"text","text":"whippan","x":500,"y":200,
             "font":{"weight":600,"size":120},"color":"#161616"}]},
          {"id":"b","bg":"#ffffff","dur":1.0,
           "transition":{"kind":"fade","dur":0.3,"morph":true},"nodes":[
            {"id":"hero","type":"text","text":"whippan","x":300,"y":600,
             "font":{"weight":600,"size":40},"color":"#e8671f"}]}
        ]}"##;
        let f = |t: f32| -> Vec<Value> {
            serde_json::from_str(&render_frame(stage, "", t)).unwrap()
        };
        // mid-morph: one path per source word, uniform scale between 1.0
        // and 40/120, color between ink and accent, full opacity
        let mid = f(1.3);
        let paths: Vec<&Value> = mid.iter().filter(|c| c["op"] == "path").collect();
        assert_eq!(paths.len(), 1, "one word, one clone");
        let sc = paths[0]["scale"].as_f64().unwrap();
        assert!(sc < 1.0 && sc > 40.0 / 120.0, "uniform scale mid-lerp: {sc}");
        assert_eq!(paths[0]["opacity"], 1.0);
        assert_ne!(paths[0]["color"], "#161616");
        assert_ne!(paths[0]["color"], "#e8671f");
        // past the window: target text at scale 1
        let done = f(1.9);
        let p2: Vec<&Value> = done.iter().filter(|c| c["op"] == "path").collect();
        assert_eq!(p2[0]["scale"], 1.0);
        assert_eq!(p2[0]["color"], "#e8671f");
    }

    #[test]
    fn rise_family_choreographs_phases() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"a","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"r1","type":"rect","x":500,"y":350,"w":100,"h":100,"fill":"#111111"}]},
          {"id":"b","bg":"#ffffff","dur":1.0,
           "transition":{"kind":"rise","dur":0.36},"nodes":[
            {"id":"r2","type":"rect","x":500,"y":350,"w":100,"h":100,"fill":"#e8671f"}]}
        ]}"##;
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 1.1)).unwrap();
        let outr = cmds.iter().find(|c| c["color"] == "#111111").unwrap();
        let inr = cmds.iter().find(|c| c["color"] == "#e8671f").unwrap();
        let oo = outr["opacity"].as_f64().unwrap();
        let io = inr["opacity"].as_f64().unwrap();
        assert!(oo < 1.0, "outgoing fading: {oo}");
        assert!(io > 0.0 && io < 1.0, "incoming entering: {io}");
        assert!(outr["y"].as_f64().unwrap() < 350.0, "outgoing lifted");
        assert!(inr["y"].as_f64().unwrap() > 350.0, "incoming rising from below");
    }

    #[test]
    fn magic_move_pairs_by_id_and_fades_the_rest() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"a","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"pill","type":"rect","x":300,"y":300,"w":300,"h":80,"radius":40,"fill":"#ea752f"},
            {"id":"old","type":"rect","x":700,"y":500,"w":100,"h":100,"fill":"#111111"}]},
          {"id":"b","bg":"#ffffff","dur":1.0,
           "transition":{"kind":"fade","dur":0.3,"morph":true},"nodes":[
            {"id":"pill","type":"rect","x":700,"y":300,"w":180,"h":100,"radius":20,"fill":"#4a21d5"},
            {"id":"new","type":"rect","x":300,"y":500,"w":100,"h":100,"fill":"#222222"}]}
        ]}"##;
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 1.1)).unwrap();
        let rects: Vec<&Value> = cmds.iter().filter(|c| c["op"] == "rect").collect();
        assert_eq!(
            rects.len(),
            3,
            "leaver + joiner + one clone, no double pill"
        );

        let leaver = rects.iter().find(|r| r["color"] == "#111111").unwrap();
        let lo = leaver["opacity"].as_f64().unwrap();
        assert!(lo > 0.5 && lo < 0.8, "leaver fading out: {lo}");

        let joiner = rects.iter().find(|r| r["color"] == "#222222").unwrap();
        let jo = joiner["opacity"].as_f64().unwrap();
        assert!(jo > 0.2 && jo < 0.5, "joiner fading in: {jo}");

        let clone = rects
            .iter()
            .find(|r| r["color"] != "#111111" && r["color"] != "#222222")
            .unwrap();
        assert_eq!(clone["opacity"], 1.0, "clone is a solid object");
        let cx = clone["x"].as_f64().unwrap();
        assert!(cx > 320.0 && cx < 680.0, "clone mid-glide: {cx}");
        assert_ne!(clone["color"], "#ea752f");
        assert_ne!(clone["color"], "#4a21d5");

        // past the morph window (0.3 * 2.5 = 0.75) the pill is the target
        let done: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 1.9)).unwrap();
        let pill = done
            .iter()
            .find(|c| c["op"] == "rect" && c["color"] == "#4a21d5")
            .unwrap();
        assert_eq!(pill["x"], 700.0);
        assert_eq!(pill["radius"], 20.0);
    }

    #[test]
    fn morph_carries_geometry_across_the_cut() {
        load_font();
        let stage = r##"{"fps":30,"size":[1000,700],"scenes":[
          {"id":"a","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"pill","type":"rect","x":300,"y":200,"w":400,"h":80,"radius":40,"fill":"#ea752f"}]},
          {"id":"b","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"btn","type":"rect","x":700,"y":500,"w":200,"h":100,"radius":16,"fill":"#4a21d5",
             "morph":{"from":"pill","dur":0.5,"ease":"outCubic"}}]}
        ]}"##;
        let f = |t: f32| -> Value {
            let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, "", t)).unwrap();
            cmds.iter().find(|c| c["op"] == "rect").unwrap().clone()
        };
        // just after the cut: still nearly the pill
        let early = f(1.01);
        let ex = early["x"].as_f64().unwrap();
        assert!(ex < 380.0, "starts near source: {ex}");
        assert_ne!(early["color"], "#4a21d5");
        // midway: strictly between
        let mid = f(1.15);
        let mx = mid["x"].as_f64().unwrap();
        assert!(mx > 320.0 && mx < 690.0, "mid morph: {mx}");
        // after the window: exactly the target
        let done = f(1.6);
        assert_eq!(done["x"], 700.0);
        assert_eq!(done["w"], 200.0);
        assert_eq!(done["radius"], 16.0);
        assert_eq!(done["color"], "#4a21d5");
    }

    #[test]
    fn mono_family_shapes_monospaced() {
        load_font();
        let mono_path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../assets/fonts/JetBrainsMono-Regular.ttf"
        );
        register_font("mono", std::fs::read(mono_path).expect("mono font"));
        let narrow = text::shape_line("iiii", 40.0, 400.0, "mono").unwrap();
        let wide = text::shape_line("wwww", 40.0, 400.0, "mono").unwrap();
        assert!(
            (narrow.width - wide.width).abs() < 0.01,
            "mono advances equal: {} vs {}",
            narrow.width,
            wide.width
        );
        let inter_narrow = text::shape_line("iiii", 40.0, 400.0, "inter").unwrap();
        let inter_wide = text::shape_line("wwww", 40.0, 400.0, "inter").unwrap();
        assert!(
            (inter_narrow.width - inter_wide.width).abs() > 5.0,
            "inter is proportional"
        );
    }

    #[test]
    fn cursor_glides_and_states_flip() {
        load_font();
        let stage = r##"{"fps":30,"size":[1920,1080],"scenes":[{"id":"s","bg":"#fafafa",
          "nodes":[
            {"id":"btn","type":"rect","x":960,"y":540,"w":320,"h":90,"radius":45,
             "fill":"#ea752f","states":{"pressed":{"fill":"#c85a1a","scale":0.96}}},
            {"id":"cur","type":"cursor","x":700,"y":700}
          ]}]}"##;
        let overlay = r##"{"tracks":[
          {"target":"cur","at":0.2,"keys":{
            "x":[{"t":0,"v":0},{"t":0.6,"v":250,"ease":"inOutCubic"}],
            "y":[{"t":0,"v":0},{"t":0.6,"v":-150,"ease":"inOutCubic"}]}},
          {"target":"btn","at":0.9,"state":"pressed"},
          {"target":"btn","at":1.05,"state":"base"}
        ]}"##;
        let f = |t: f32| -> Vec<Value> {
            serde_json::from_str(&render_frame(stage, overlay, t)).unwrap()
        };

        // cursor: three layered arrow paths, gliding
        let mid = f(0.5);
        let arrows: Vec<&Value> = mid.iter().filter(|c| c["op"] == "path").collect();
        assert_eq!(arrows.len(), 3, "shadow + outline + arrow");
        let x = arrows[2]["x"].as_f64().unwrap();
        assert!(x > 700.0 && x < 950.0, "mid-glide x {x}");

        // pressed: fill lerps toward the pressed color, scale dips
        let pressed = f(1.02);
        let btn = pressed.iter().find(|c| c["op"] == "rect").unwrap();
        assert_ne!(btn["color"], "#ea752f", "fill left base during press");
        assert!(btn["scale"].as_f64().unwrap() < 1.0, "pressed scale dip");

        // released: back to base
        let released = f(1.5);
        let btn2 = released.iter().find(|c| c["op"] == "rect").unwrap();
        assert_eq!(btn2["color"], "#ea752f");
        assert_eq!(btn2["scale"], 1.0);
    }

    #[test]
    fn image_nodes_carry_src_and_animate() {
        load_font();
        let stage = r##"{"fps":30,"size":[1920,1080],"scenes":[{"id":"s","bg":"#fafafa",
          "nodes":[{"id":"shot","type":"image","src":"assets/demo/mark.png",
                    "x":960,"y":540,"w":300,"h":300,"radius":40}]}]}"##;
        let overlay = r##"{"tracks":[{"target":"shot","at":0.1,"keys":{
          "opacity":[{"t":0,"v":0},{"t":0.2,"v":1}],
          "scale":[{"t":0,"v":0.9},{"t":0.25,"v":1,"ease":"outCubic"}]}}]}"##;
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, overlay, 1.0)).unwrap();
        let img = cmds.iter().find(|c| c["op"] == "image").unwrap();
        assert_eq!(img["src"], "assets/demo/mark.png");
        assert_eq!(img["w"], 300.0);
        assert_eq!(img["radius"], 40.0);
        assert_eq!(img["opacity"], 1.0);
        assert_eq!(img["scale"], 1.0);
        let early: Vec<Value> = serde_json::from_str(&render_frame(stage, overlay, 0.1)).unwrap();
        assert_eq!(
            early.iter().find(|c| c["op"] == "image").unwrap()["opacity"],
            0.0
        );
    }

    #[test]
    fn scenes_timeline_and_crossfade() {
        load_font();
        let stage = r##"{"fps":30,"size":[1920,1080],"scenes":[
          {"id":"a","bg":"#fafafa","dur":1.0,"nodes":[
            {"id":"t1","type":"text","text":"hello there","x":960,"y":500,
             "font":{"weight":600,"size":72},"color":"#161616"}]},
          {"id":"b","bg":"#050505","dur":1.0,"transition":{"kind":"fade","dur":0.4},"nodes":[
            {"id":"p1","type":"rect","x":960,"y":540,"w":400,"h":100,"radius":50,"fill":"#4a21d5"}]},
          {"id":"c","bg":"#ffffff","dur":1.0,"nodes":[
            {"id":"p2","type":"rect","x":960,"y":540,"w":100,"h":100,"radius":10,"fill":"#e8671f"}]}
        ]}"##;
        let overlay = r##"{"tracks":[
          {"target":"p2","at":0.05,"keys":{"opacity":[{"t":0,"v":0},{"t":0.3,"v":1}]}}
        ]}"##;
        let f = |t: f32| -> Vec<Value> {
            serde_json::from_str(&render_frame(stage, overlay, t)).unwrap()
        };

        // scene a alone
        let a = f(0.5);
        assert_eq!(a[0]["color"], "#fafafa");
        assert!(a.iter().any(|c| c["op"] == "path"));
        assert!(!a.iter().any(|c| c["op"] == "rect"));

        // mid-crossfade: mixed bg, both scenes present at half strength
        let mid = f(1.2);
        assert_eq!(mid[0]["color"], "#7f7f7f");
        let path_op = mid.iter().find(|c| c["op"] == "path").unwrap()["opacity"]
            .as_f64()
            .unwrap();
        let rect_op = mid.iter().find(|c| c["op"] == "rect").unwrap()["opacity"]
            .as_f64()
            .unwrap();
        assert!((path_op - 0.5).abs() < 1e-3, "outgoing at {path_op}");
        assert!((rect_op - 0.5).abs() < 1e-3, "incoming at {rect_op}");

        // after the window: scene b alone
        let b = f(1.9);
        assert_eq!(b[0]["color"], "#050505");
        assert!(!b.iter().any(|c| c["op"] == "path"));

        // scene c: local clock restarted, overlay mid-ramp
        let c = f(2.2);
        assert_eq!(c[0]["color"], "#ffffff");
        let o = c.iter().find(|x| x["op"] == "rect").unwrap()["opacity"]
            .as_f64()
            .unwrap();
        assert!(o > 0.0 && o < 1.0, "scene-local ramp mid-flight: {o}");

        // past the end: last scene holds settled
        let hold = f(9.0);
        assert_eq!(hold[0]["color"], "#ffffff");
        assert_eq!(
            hold.iter().find(|x| x["op"] == "rect").unwrap()["opacity"],
            1.0
        );
    }

    #[test]
    fn shapes_words_with_real_metrics() {
        load_font();
        let line = text::shape_line("The fastest way to scale", 72.0, 600.0, "inter").unwrap();
        assert_eq!(line.words.len(), 5);
        assert!(line.width > 400.0, "width {}", line.width);
        for pair in line.words.windows(2) {
            assert!(pair[1].x > pair[0].x + pair[0].width * 0.5);
        }
    }

    #[test]
    fn weight_axis_changes_outlines() {
        load_font();
        let heavy = text::shape_line("The", 72.0, 700.0, "inter").unwrap();
        let light = text::shape_line("The", 72.0, 300.0, "inter").unwrap();
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
            let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, overlay, t)).unwrap();
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
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(STAGE, overlay, 0.5)).unwrap();
        let paths: Vec<&Value> = cmds.iter().filter(|c| c["op"] == "path").collect();
        assert_eq!(paths.len(), 20, "one cmd per glyph");
        let first = paths[0]["opacity"].as_f64().unwrap();
        let last = paths[19]["opacity"].as_f64().unwrap();
        assert!(first > last, "first glyph {first} leads last {last}");

        let done: Vec<Value> = serde_json::from_str(&render_frame(STAGE, overlay, 2.0)).unwrap();
        let settled: Vec<&Value> = done.iter().filter(|c| c["op"] == "path").collect();
        for g in &settled[15..20] {
            assert_eq!(g["color"], "#e8671f", "scale glyphs keep accent");
        }
        assert_eq!(settled[0]["color"], "#161616");
    }

    #[test]
    fn gradient_line_and_offset_echo() {
        load_font();
        let stage = r##"{"fps":30,"size":[1920,1080],"scenes":[{"id":"s","bg":"#050505",
          "nodes":[{"id":"pill","type":"rect","x":960,"y":520,"w":760,"h":116,"radius":58,
            "fill":"#4a21d5",
            "gradient":{"angle":90,"stops":[
              {"at":0,"color":"#6a44f0"},{"at":0.55,"color":"#4a21d5"},{"at":1,"color":"#341786"}]},
            "glow":{"sigma":46,"opacity":0.9,"dy":-18}}]}]}"##;
        let cmds: Vec<Value> = serde_json::from_str(&render_frame(stage, "", 0.0)).unwrap();
        let echo = &cmds[1];
        let shape = &cmds[2];
        assert_eq!(echo["y"], 502.0, "echo displaced up by dy");
        assert_eq!(shape["y"], 520.0, "crisp shape stays put");
        assert_eq!(echo["color"], "#4a21d5", "echo takes the middle stop");
        let g = &shape["grad"];
        assert!((g["y0"].as_f64().unwrap() + 58.0).abs() < 1e-3);
        assert!((g["y1"].as_f64().unwrap() - 58.0).abs() < 1e-3);
        assert!((g["x0"].as_f64().unwrap()).abs() < 1e-3);
        assert_eq!(g["stops"][0][1], "#6a44f0");
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
