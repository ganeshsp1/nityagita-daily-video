"""Builds the app promo videos (promo/scripts.json) as 1080x1920 Shorts/Reels.

Each video: the spoken lines as large captions over a cream band at the top,
the app's own screen recording of that feature in a phone frame below, and a
closing "download free" card. Captions are HTML rendered by headless Chrome
(like generator/make_video.py), so every Indian script shapes correctly.

  python3 promo/make_promo.py --recordings ~/Personal/promo_clips \\
      --voice ~/nityagita_promo_voice --out work/promo [--langs ml hi] [--videos ask]

--recordings holds <language>.mov with <language>.start (epoch ms when the
recording began) and <language>.marks ("PROMO_MARK <scene> start|end <ms>"),
from the app repo's tool/promo/record.sh. --voice holds <lang>/<video>-<n>.m4a
from promo/make_voiceovers.py; without it, the clips are fetched from the app
storage Worker (GITA_WORKER_URL, GITA_WORKER_TOKEN) at promo/voice/..., and a
video with no voiceover yet is made as a silent draft with estimated timing.
Writes <out>/<video>-<lang>.mp4 and <video>-<lang>.json (caption + hashtags).
Needs ffmpeg/ffprobe and Chrome.
"""
import argparse
import html
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "generator"))
from make_video import find_chrome  # noqa: E402

W, H = 1080, 1920
BAND = 430           # caption band at the top
PHONE_H = 1290       # phone screen height in the frame
END_SECONDS = 3.2
GAP = 0.3
FLAVOR = {"en": "english", "hi": "hindi", "mr": "marathi", "kn": "kannada",
          "ml": "malayalam", "ta": "tamil", "te": "telugu"}
CREAM, NAVY, SAFFRON = "#FAF6F0", "#1A1A2E", "#FF7722"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))[:300]}\n{r.stderr[-1500:]}")
    return r.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip() or 0)


def marks(rec, flavor):
    start = int((rec / f"{flavor}.start").read_text().strip())
    found = {}
    for line in (rec / f"{flavor}.marks").read_text().splitlines():
        _, scene, what, t = line.split()
        found.setdefault(scene, {})[what] = (int(t) - start) / 1000
    return found


def voice_clip(args, lang, video, n, work):
    if args.voice:
        p = Path(args.voice).expanduser() / lang / f"{video}-{n}.m4a"
        return p if p.exists() else None
    base, token = os.environ.get("GITA_WORKER_URL"), os.environ.get("GITA_WORKER_TOKEN")
    if not (base and token):
        return None
    dest = work / f"voice-{lang}-{video}-{n}.m4a"
    if not dest.exists():
        req = urllib.request.Request(f"{base.rstrip('/')}/promo/voice/{lang}/{video}-{n}.m4a",
                                     headers={"X-Gita-Auth": token, "User-Agent": "curl/8"})
        try:
            dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        except Exception:
            return None
    return dest


class Painter:
    """HTML -> transparent PNG with headless Chrome."""

    def __init__(self, work):
        self.chrome, self.work, self.n = find_chrome(), work, 0

    def png(self, body_css, body, width=W, height=H):
        self.n += 1
        page = self.work / f"p{self.n}.html"
        out = self.work / f"p{self.n}.png"
        page.write_text(f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:transparent}}
{body_css}</style></head><body>{body}</body></html>""", encoding="utf-8")
        subprocess.run([self.chrome, "--headless=new", "--no-sandbox", "--hide-scrollbars",
                        "--default-background-color=00000000", "--force-device-scale-factor=1",
                        "--virtual-time-budget=2000", f"--screenshot={out}",
                        f"--window-size={width},{height}", f"file://{page}"],
                       capture_output=True, text=True)
        return out


def build(args, config, spec, video, lang, painter, work):
    flavor = FLAVOR[lang]
    rec = Path(args.recordings).expanduser()
    scene = marks(rec, flavor).get(video)
    if not scene or "end" not in scene:
        print(f"skip {video}-{lang}: no recording")
        return
    lines = spec["videos"][video]["lines"][lang]
    font = f"{config['languages'].get(lang, {}).get('font_family', 'Inter')}, 'Noto Sans', sans-serif"

    # Timeline: each line from its voice clip (or an estimate for a draft).
    clips, t, timeline = [], 0.35, []
    for n, text in enumerate(lines, 1):
        clip = voice_clip(args, lang, video, n, work)
        d = duration(clip) if clip else max(1.3, 0.07 * len(text))
        timeline.append((t, t + d, text))
        clips.append((clip, t))
        t += d + GAP
    talk_end = t
    total = talk_end + END_SECONDS
    draft = any(c is None for c, _ in clips)

    # Pictures: background, phone mask, captions, end card.
    bg = painter.png(f"""body{{background:linear-gradient(180deg,{CREAM} 0%,#F6EBDA 60%,#F1DFC3 100%);
font-family:{font}}}
.foot{{position:absolute;bottom:52px;width:100%;text-align:center;color:{NAVY};opacity:.75;
font-size:34px;font-weight:700;letter-spacing:1px}}
.om{{position:absolute;right:-60px;bottom:120px;font-size:520px;color:{SAFFRON};opacity:.06}}""",
        f"""<div class="om">ॐ</div><div class="foot">{html.escape(config['languages'].get(lang, {}).get('app_title', 'Nitya Gita'))}</div>""")
    phone_w = round(PHONE_H * 1320 / 2868)
    mask = painter.png("body{background:#000}div{width:100%;height:100%;background:#fff;border-radius:58px}",
                       "<div></div>", phone_w, PHONE_H)
    caps = []
    for i, (a, b, text) in enumerate(timeline):
        size = 76 if i == 0 else 60
        caps.append((painter.png(f"""body{{font-family:{font};display:flex;align-items:center;justify-content:center;
height:{BAND}px}}
div{{width:940px;text-align:center;font-size:{size}px;line-height:1.3;font-weight:800;color:{NAVY}}}
b{{color:{SAFFRON}}}""", f"<div>{html.escape(text)}</div>", W, BAND), a, b))
    end_text = spec["end_card"][lang]
    app_title = config["languages"].get(lang, {}).get("app_title", "Nitya Gita")
    icon = (ROOT / "assets" / "app_icon.png").resolve()
    end = painter.png(f"""body{{background:linear-gradient(180deg,#FFF6E9,#F6D9A8);font-family:{font};
display:flex;flex-direction:column;align-items:center;justify-content:center}}
img{{width:300px;height:300px;border-radius:66px;box-shadow:0 18px 50px rgba(255,119,34,.35)}}
h1{{margin:56px 0 18px;font-size:92px;color:{NAVY}}}
p{{margin:0;font-size:56px;font-weight:700;color:{SAFFRON}}}
small{{margin-top:40px;font-size:38px;color:{NAVY};opacity:.7}}""",
        f"""<img src="file://{icon}"><h1>{html.escape(app_title)}</h1><p>{html.escape(end_text)}</p>
<small>Google Play · App Store</small>""")

    # Video: the scene cut, fitted to the narration (sped up at most 2.2x,
    # or held on its last frame).
    seg = scene["end"] - scene["start"]
    speed = min(2.2, max(1.0, seg / talk_end))
    hold = max(0.0, talk_end - seg / speed)
    out = Path(args.out) / f"{video}-{lang}.mp4"
    inputs = ["-ss", f"{scene['start']:.3f}", "-t", f"{seg:.3f}", "-i", str(rec / f"{flavor}.mov"),
              "-loop", "1", "-t", f"{total:.2f}", "-i", str(bg),
              "-loop", "1", "-t", f"{total:.2f}", "-i", str(mask)]
    for png, _, _ in caps:
        inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", str(png)]
    inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", str(end)]
    first_cap, end_idx = 3, 3 + len(caps)
    audio_inputs = [(c, s) for c, s in clips if c]
    for c, _ in audio_inputs:
        inputs += ["-i", str(c)]
    top = BAND + 10
    f = [f"[0:v]setpts=PTS/{speed:.4f},fps=30,scale={phone_w}:{PHONE_H},"
         f"tpad=stop_mode=clone:stop_duration={hold + END_SECONDS:.2f},trim=0:{total:.2f}[scr]",
         "[2:v]format=gray,scale=%d:%d[m]" % (phone_w, PHONE_H),
         "[scr][m]alphamerge[ph]",
         f"[1:v]scale={W}:{H},fps=30[bg]",
         f"[bg][ph]overlay=x=(W-w)/2:y={top}[v0]"]
    last = "v0"
    for i, (_, a, b) in enumerate(caps):
        # Each caption stays until the next one starts (the last until the end card).
        until = caps[i + 1][1] if i + 1 < len(caps) else talk_end
        f.append(f"[{first_cap + i}:v]fade=t=in:st={a:.2f}:d=0.25:alpha=1[c{i}]")
        f.append(f"[{last}][c{i}]overlay=0:0:enable='between(t,{a:.2f},{until:.2f})'[v{i + 1}]")
        last = f"v{i + 1}"
    f.append(f"[{end_idx}:v]fade=t=in:st={talk_end:.2f}:d=0.4:alpha=1[e]")
    f.append(f"[{last}][e]overlay=0:0:enable='gte(t,{talk_end:.2f})',format=yuv420p[vout]")
    amap = []
    if audio_inputs:
        base = end_idx + 1
        for k, (_, s) in enumerate(audio_inputs):
            f.append(f"[{base + k}:a]adelay={int(s * 1000)}|{int(s * 1000)},apad[a{k}]")
        f.append("".join(f"[a{k}]" for k in range(len(audio_inputs)))
                 + f"amix=inputs={len(audio_inputs)}:normalize=0,atrim=0:{total:.2f}[aout]")
        amap = ["-map", "[aout]", "-c:a", "aac", "-b:a", "160k"]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
         "-filter_complex", ";".join(f), "-map", "[vout]", *amap,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", "30",
         "-t", f"{total:.2f}", "-movflags", "+faststart", str(out)])

    tags = config["languages"].get(lang, {}).get("hashtags", "#BhagavadGita #NityaGita")
    caption = " ".join(lines) + f"\n\n{end_text}\nhttps://thenityagita.com/app/?ref=promo_{video}_{lang}\n\n{tags}"
    (Path(args.out) / f"{video}-{lang}.json").write_text(json.dumps(
        {"video": video, "lang": lang, "title": lines[0], "caption": caption, "draft": draft,
         "seconds": round(total, 1)}, ensure_ascii=False, indent=1), encoding="utf-8")
    # What promo/post.py hands to the platform posters.
    lang_cfg = config["languages"].get(lang, {})
    title = lines[0].rstrip(".?!।")
    meta = {"lang": lang, "video": video,
            "youtube_title": f"{title} | {lang_cfg.get('app_title', 'Nitya Gita')}"[:95] + " #shorts",
            "description": caption, "instagram_caption": caption, "threads_text": caption[:480],
            "tags": list(dict.fromkeys(lang_cfg.get("tags", []) + ["Nitya Gita", "Bhagavad Gita app", "Gita app"]))[:15]}
    (HERE / "meta").mkdir(exist_ok=True)
    (HERE / "meta" / f"{video}-{lang}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.name}: {total:.1f}s{' (draft: no voiceover yet)' if draft else ''}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--recordings", required=True)
    p.add_argument("--voice")
    p.add_argument("--out", default="work/promo")
    p.add_argument("--langs", nargs="*")
    p.add_argument("--videos", nargs="*")
    args = p.parse_args()
    spec = json.load(open(HERE / "scripts.json", encoding="utf-8"))
    config = json.load(open(ROOT / "generator" / "config.json", encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    work = Path(args.out) / ".work"
    work.mkdir(exist_ok=True)
    painter = Painter(work.resolve())
    for video in spec["videos"]:
        if args.videos and video not in args.videos:
            continue
        for lang in spec["videos"][video]["lines"]:
            if args.langs and lang not in args.langs:
                continue
            build(args, config, spec, video, lang, painter, work)


if __name__ == "__main__":
    main()
