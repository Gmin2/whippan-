#![allow(clippy::too_many_arguments)]
#[cfg(not(target_arch = "wasm32"))]
mod app {
use skia_safe::image_filters;
use skia_safe::utils::parse_path::from_svg;
use skia_safe::{
    surfaces, AlphaType, BlurStyle, Color, ColorType, Data, ImageInfo, MaskFilter, Paint, Point,
    RRect, Rect, Shader, TileMode,
};
use std::collections::HashMap;
use std::io::Write;
use std::process::{Command, Stdio};
use whippan_engine::{doc_duration, doc_size, register_font, render_cmds, DrawCmd};

fn hex_color(c: &str, alpha: f32) -> Color {
    let h = c.trim_start_matches('#');
    let n = u32::from_str_radix(h, 16).unwrap_or(0);
    Color::from_argb(
        (alpha.clamp(0.0, 1.0) * 255.0) as u8,
        ((n >> 16) & 0xff) as u8,
        ((n >> 8) & 0xff) as u8,
        (n & 0xff) as u8,
    )
}

fn draw_one(canvas: &skia_safe::Canvas, c: &DrawCmd, images: &HashMap<String, skia_safe::Image>) {
    let mut paint = Paint::default();
    paint.set_anti_alias(true);
    if let Some(g) = &c.grad {
        let colors: Vec<Color> = g.stops.iter().map(|(_, hex)| hex_color(hex, c.opacity)).collect();
        let pos: Vec<f32> = g.stops.iter().map(|(at, _)| *at).collect();
        paint.set_shader(Shader::linear_gradient(
            (Point::new(g.x0, g.y0), Point::new(g.x1, g.y1)),
            colors.as_slice(),
            Some(pos.as_slice()),
            TileMode::Clamp,
            None,
            None,
        ));
    } else {
        paint.set_color(hex_color(&c.color, c.opacity));
    }
    if let Some(b) = c.blur {
        paint.set_mask_filter(MaskFilter::blur(BlurStyle::Normal, b, true));
    }
    canvas.save();
    canvas.translate((c.x, c.y));
    canvas.scale((c.scale, c.scale));
    match c.op.as_str() {
        "path" => {
            if let Some(d) = &c.d {
                if let Some(path) = from_svg(d) {
                    canvas.draw_path(&path, &paint);
                }
            }
        }
        "rect" => {
            let (w, h) = (c.w.unwrap_or(0.0), c.h.unwrap_or(0.0));
            let r = c.radius.unwrap_or(0.0);
            let rect = Rect::from_xywh(-w / 2.0, -h / 2.0, w, h);
            canvas.draw_rrect(RRect::new_rect_xy(rect, r, r), &paint);
        }
        "image" => {
            if let Some(img) = c.src.as_ref().and_then(|s| images.get(s)) {
                let (w, h) = (c.w.unwrap_or(0.0), c.h.unwrap_or(0.0));
                let dst = Rect::from_xywh(-w / 2.0, -h / 2.0, w, h);
                let mut ip = Paint::default();
                ip.set_alpha_f(c.opacity);
                if let Some(r) = c.radius.filter(|r| *r > 0.0) {
                    canvas.save();
                    canvas.clip_rrect(RRect::new_rect_xy(dst, r, r), None, true);
                    canvas.draw_image_rect(img, None, dst, &ip);
                    canvas.restore();
                } else {
                    canvas.draw_image_rect(img, None, dst, &ip);
                }
            }
        }
        _ => {}
    }
    canvas.restore();
}

fn paint_frame(
    canvas: &skia_safe::Canvas,
    cmds: &[DrawCmd],
    images: &HashMap<String, skia_safe::Image>,
) {
    let mut goo_groups: HashMap<&str, Vec<&DrawCmd>> = HashMap::new();
    for c in cmds {
        if let Some(g) = &c.goo {
            goo_groups.entry(g).or_default().push(c);
        }
    }
    let mut goo_done: Vec<&str> = Vec::new();
    for c in cmds {
        match c.op.as_str() {
            "clear" => {
                canvas.clear(hex_color(&c.color, 1.0));
            }
            "clip" => {
                canvas.save();
                canvas.clip_rect(
                    Rect::from_xywh(c.x, c.y, c.w.unwrap_or(0.0), c.h.unwrap_or(0.0)),
                    None,
                    true,
                );
            }
            "unclip" => {
                canvas.restore();
            }
            _ => {
                if let Some(g) = &c.goo {
                    let g = g.as_str();
                    if goo_done.contains(&g) {
                        continue;
                    }
                    goo_done.push(g);
                    // blur then re-sharpen alpha, same numbers as the web painter
                    let blur = image_filters::blur((16.0, 16.0), TileMode::Decal, None, None);
                    let cf = skia_safe::color_filters::matrix_row_major(
                        &[
                            1.0, 0.0, 0.0, 0.0, 0.0, //
                            0.0, 1.0, 0.0, 0.0, 0.0, //
                            0.0, 0.0, 1.0, 0.0, 0.0, //
                            0.0, 0.0, 0.0, 30.0, -3.75,
                        ],
                        None,
                    );
                    let chain = image_filters::color_filter(cf, blur, None);
                    let mut lp = Paint::default();
                    lp.set_image_filter(chain);
                    let rec = skia_safe::canvas::SaveLayerRec::default().paint(&lp);
                    canvas.save_layer(&rec);
                    for gc in &goo_groups[g] {
                        draw_one(canvas, gc, images);
                    }
                    canvas.restore();
                } else {
                    draw_one(canvas, c, images);
                }
            }
        }
    }
}

pub fn run() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        eprintln!("usage: export <stage.json> <anim.json> <out.mp4> [fps]");
        std::process::exit(1);
    }
    let stage = std::fs::read_to_string(&args[1]).expect("stage json");
    let anim = std::fs::read_to_string(&args[2]).expect("anim json");
    let out = args[3].clone();
    let fps: f32 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(30.0);

    let root = std::env::current_dir().unwrap();
    for (name, file) in [
        ("inter", "assets/fonts/Inter-Variable.ttf"),
        ("mono", "assets/fonts/JetBrainsMono-Regular.ttf"),
    ] {
        let path = root.join(file);
        register_font(name, std::fs::read(&path).unwrap_or_else(|_| panic!("font {file}")));
    }

    // preload every bitmap the stage references; doc paths are server-absolute
    let mut images: HashMap<String, skia_safe::Image> = HashMap::new();
    let parsed: serde_json::Value = serde_json::from_str(&stage).unwrap();
    if let Some(scenes) = parsed["scenes"].as_array() {
        for sc in scenes {
            for node in sc["nodes"].as_array().into_iter().flatten() {
                if node["type"] == "image" {
                    if let Some(src) = node["src"].as_str() {
                        let path = root.join(src.trim_start_matches('/'));
                        if let Ok(bytes) = std::fs::read(&path) {
                            if let Some(img) =
                                skia_safe::Image::from_encoded(Data::new_copy(&bytes))
                            {
                                images.insert(src.to_string(), img);
                            }
                        }
                    }
                }
            }
        }
    }

    let (w, h) = doc_size(&stage).expect("size");
    let (wi, hi) = (w as i32, h as i32);
    let dur = doc_duration(&stage).expect("duration");
    let frames = (dur * fps).round() as u32;

    let audio = parsed.get("audio").filter(|a| !a.is_null()).map(|a| {
        (
            a["src"].as_str().unwrap_or("").to_string(),
            a["gain"].as_f64().unwrap_or(0.8) as f32,
            a["fade_out"].as_f64().unwrap_or(0.6) as f32,
        )
    });
    let video_out = if audio.is_some() {
        format!("{out}.video.mp4")
    } else {
        out.clone()
    };

    let mut ffmpeg = Command::new("ffmpeg")
        .args([
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgba",
            "-s", &format!("{wi}x{hi}"),
            "-r", &fps.to_string(),
            "-i", "-",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            &video_out,
        ])
        .stdin(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("ffmpeg");
    let mut pipe = ffmpeg.stdin.take().unwrap();

    let mut surface = surfaces::raster_n32_premul((wi, hi)).expect("surface");
    let info = ImageInfo::new((wi, hi), ColorType::RGBA8888, AlphaType::Unpremul, None);
    let row = (wi as usize) * 4;
    let mut buf = vec![0u8; row * hi as usize];

    let start = std::time::Instant::now();
    for i in 0..frames {
        let t = i as f32 / fps;
        let cmds = render_cmds(&stage, &anim, t).expect("render");
        paint_frame(surface.canvas(), &cmds, &images);
        if !surface.read_pixels(&info, &mut buf, row, (0, 0)) {
            panic!("readback failed at frame {i}");
        }
        pipe.write_all(&buf).expect("pipe");
    }
    drop(pipe);
    let status = ffmpeg.wait().expect("ffmpeg wait");
    let secs = start.elapsed().as_secs_f32();

    if let Some((src, gain, fade)) = audio {
        let bed = root.join(src.trim_start_matches('/'));
        let filter = format!(
            "[1:a]atrim=0:{dur},volume={gain},afade=t=out:st={}:d={fade}[a]",
            (dur - fade).max(0.0)
        );
        let mux = Command::new("ffmpeg")
            .args([
                "-y",
                "-i", &video_out,
                "-i", bed.to_str().unwrap(),
                "-filter_complex", &filter,
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                &out,
            ])
            .stderr(Stdio::null())
            .status()
            .expect("mux");
        let _ = std::fs::remove_file(&video_out);
        println!(
            "{out}: {frames} frames + audio in {secs:.1}s ({:.0} fps), mux {mux}",
            frames as f32 / secs
        );
    } else {
        println!(
            "{out}: {frames} frames at {wi}x{hi} in {secs:.1}s ({:.0} fps), ffmpeg {status}",
            frames as f32 / secs
        );
    }
}

}

#[cfg(not(target_arch = "wasm32"))]
fn main() {
    app::run();
}

#[cfg(target_arch = "wasm32")]
fn main() {}
