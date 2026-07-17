use rustybuzz::ttf_parser::{self, GlyphId, Tag};
use rustybuzz::{shape, Face, UnicodeBuffer, Variation};
use std::collections::HashMap;
use std::fmt::Write;
use std::sync::{Mutex, OnceLock};

static FONT: OnceLock<Vec<u8>> = OnceLock::new();
static CACHE: OnceLock<Mutex<HashMap<String, ShapedLine>>> = OnceLock::new();

pub fn init_font(bytes: Vec<u8>) -> bool {
    FONT.set(bytes).is_ok()
}

#[derive(Clone)]
pub struct ShapedGlyph {
    /// offset from the word's left edge
    pub x: f32,
    /// svg path in pixels, origin at the glyph's own pen position
    pub path: String,
}

#[derive(Clone)]
pub struct ShapedWord {
    pub text: String,
    /// offset from the line's left edge
    pub x: f32,
    pub width: f32,
    /// svg path in pixels, origin at the word's left edge on the baseline
    pub path: String,
    pub glyphs: Vec<ShapedGlyph>,
}

#[derive(Clone)]
pub struct ShapedLine {
    pub width: f32,
    /// add to the node's y to place the baseline so the line looks
    /// vertically centered
    pub baseline_shift: f32,
    pub words: Vec<ShapedWord>,
}

struct PathBuilder {
    d: String,
    scale: f32,
    ox: f32,
}

impl ttf_parser::OutlineBuilder for PathBuilder {
    fn move_to(&mut self, x: f32, y: f32) {
        let _ = write!(
            self.d,
            "M{:.1} {:.1}",
            self.ox + x * self.scale,
            -y * self.scale
        );
    }
    fn line_to(&mut self, x: f32, y: f32) {
        let _ = write!(
            self.d,
            "L{:.1} {:.1}",
            self.ox + x * self.scale,
            -y * self.scale
        );
    }
    fn quad_to(&mut self, x1: f32, y1: f32, x: f32, y: f32) {
        let _ = write!(
            self.d,
            "Q{:.1} {:.1} {:.1} {:.1}",
            self.ox + x1 * self.scale,
            -y1 * self.scale,
            self.ox + x * self.scale,
            -y * self.scale
        );
    }
    fn curve_to(&mut self, x1: f32, y1: f32, x2: f32, y2: f32, x: f32, y: f32) {
        let _ = write!(
            self.d,
            "C{:.1} {:.1} {:.1} {:.1} {:.1} {:.1}",
            self.ox + x1 * self.scale,
            -y1 * self.scale,
            self.ox + x2 * self.scale,
            -y2 * self.scale,
            self.ox + x * self.scale,
            -y * self.scale
        );
    }
    fn close(&mut self) {
        self.d.push('Z');
    }
}

fn shape_word(face: &Face, outline_face: &ttf_parser::Face, word: &str, scale: f32) -> ShapedWord {
    let mut buf = UnicodeBuffer::new();
    buf.push_str(word);
    let glyphs = shape(face, &[], buf);
    let infos = glyphs.glyph_infos();
    let positions = glyphs.glyph_positions();

    let mut pen = 0.0f32;
    let mut d = String::new();
    let mut out_glyphs = Vec::new();
    for (info, pos) in infos.iter().zip(positions) {
        let gx = pen + pos.x_offset as f32 * scale;
        let mut own = PathBuilder {
            d: String::new(),
            scale,
            ox: 0.0,
        };
        outline_face.outline_glyph(GlyphId(info.glyph_id as u16), &mut own);
        let mut in_word = PathBuilder {
            d: String::new(),
            scale,
            ox: gx,
        };
        outline_face.outline_glyph(GlyphId(info.glyph_id as u16), &mut in_word);
        d.push_str(&in_word.d);
        out_glyphs.push(ShapedGlyph { x: gx, path: own.d });
        pen += pos.x_advance as f32 * scale;
    }
    ShapedWord {
        text: word.into(),
        x: 0.0,
        width: pen,
        path: d,
        glyphs: out_glyphs,
    }
}

/// shape one line of text into positioned words with outline paths.
/// cached: shaping runs once per (text, size, weight), not per frame.
pub fn shape_line(text: &str, size: f32, weight: f32) -> Option<ShapedLine> {
    let key = format!("{text}|{size}|{weight}");
    let cache = CACHE.get_or_init(|| Mutex::new(HashMap::new()));
    if let Some(hit) = cache.lock().unwrap().get(&key) {
        return Some(hit.clone());
    }

    let bytes = FONT.get()?;
    let wght = Variation {
        tag: Tag::from_bytes(b"wght"),
        value: weight,
    };
    let mut face = Face::from_slice(bytes, 0)?;
    face.set_variations(&[wght]);
    let mut outline_face = ttf_parser::Face::parse(bytes, 0).ok()?;
    let _ = outline_face.set_variation(Tag::from_bytes(b"wght"), weight);

    let upem = face.units_per_em() as f32;
    let scale = size / upem;
    let space = {
        let mut buf = UnicodeBuffer::new();
        buf.push_str(" ");
        let g = shape(&face, &[], buf);
        g.glyph_positions()
            .first()
            .map(|p| p.x_advance as f32 * scale)
            .unwrap_or(size * 0.3)
    };

    let mut words = Vec::new();
    let mut x = 0.0f32;
    for (i, word) in text.split(' ').filter(|w| !w.is_empty()).enumerate() {
        if i > 0 {
            x += space;
        }
        let mut w = shape_word(&face, &outline_face, word, scale);
        w.x = x;
        x += w.width;
        words.push(w);
    }

    let asc = face.ascender() as f32 * scale;
    let desc = face.descender() as f32 * scale;
    let line = ShapedLine {
        width: x,
        baseline_shift: (asc + desc) / 2.0,
        words,
    };
    cache.lock().unwrap().insert(key, line.clone());
    Some(line)
}
