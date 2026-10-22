"""Builds the Nitya Gita "verse of the day" status video outside the app.

Mirrors lib/utils/VideoGenerator.dart in the app: the same verse-of-the-day
pick, card layout, audio (sloka recitation + meaning) and ffmpeg filter graph.
Text cards are HTML rendered by headless Chrome so Indic scripts shape
correctly.

All verse data, audio and background videos are downloaded from the Worker at
run time into the output folder; nothing from the app is stored in this repo.

usage: python3 generator/make_video.py --date 2026-10-21 --lang ml --out work/ml
env:   GITA_WORKER_URL, GITA_WORKER_TOKEN (required)
       CHROME (optional, path to Chrome), DART (optional, path to dart)
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Cloudflare's bot filter rejects Python's default User-Agent.
USER_AGENT = "Dart/3.12 (dart:io)"

DIGIT_ZEROS = [0x0966, 0x09E6, 0x0A66, 0x0AE6, 0x0B66, 0x0BE6, 0x0C66, 0x0CE6,
               0x0D66, 0xABF0, 0x0660, 0x06F0]


def to_ascii_digits(text):
    out = []
    for ch in text:
        cp = ord(ch)
        for zero in DIGIT_ZEROS:
            if zero <= cp <= zero + 9:
                ch = chr(0x30 + cp - zero)
                break
        out.append(ch)
    return "".join(out)


def find_chrome():
    for candidate in (os.environ.get("CHROME"), "google-chrome", "chromium",
                      "chromium-browser",
                      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if candidate and (shutil.which(candidate) or os.path.exists(candidate)):
            return shutil.which(candidate) or candidate
    sys.exit("Chrome not found; set CHROME")


def verse_of_the_day(date):
    """Same number the app shows: Dart Random(yyyymd).nextInt(658) + 1."""
    dart = os.environ.get("DART", "dart")
    result = subprocess.run([dart, "run", os.path.join(HERE, "votd.dart"), date],
                            capture_output=True, text=True, check=True)
    return int(result.stdout.strip())


def fetch(base, token, path, dest):
    req = urllib.request.Request(f"{base}/{path}", headers={
        "X-Gita-Auth": token, "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)
    return dest


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def esc(text):
    return html.escape(text).replace("\n", "<br>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--lang", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = os.environ["GITA_WORKER_URL"].rstrip("/")
    token = os.environ["GITA_WORKER_TOKEN"]
    config = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
    lang = config["languages"][args.lang]
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    chrome = find_chrome()

    # ---- Verse ----------------------------------------------------------
    section_count = verse_of_the_day(args.date)
    data_path = fetch(base, token, f"data/{lang['data_file']}", f"{out}/data.json")
    data = json.load(open(data_path, encoding="utf-8"))
    chapter = section = None
    for c in data["Chapters"]:
        for s in c["Sections"]:
            if int(s["SectionCount"]) == section_count:
                chapter, section = c, s
    if section is None:
        sys.exit(f"section {section_count} not found")

    serial = int(chapter["ChapterSerial"])
    gita_chapter = serial - 2
    raw_title = chapter["Title"]
    # Some languages (e.g. Kannada) already include "Chapter N:" in the title.
    has_number = re.search(rf"(?<!\d){gita_chapter}(?!\d)", to_ascii_digits(raw_title))
    title = (lang["chapter_label"].format(number=gita_chapter, title=raw_title)
             if serial > 2 and not has_number else raw_title)
    sloka_no = section["SlokaNumber"]
    speaker = section.get("Speaker") or ""
    content = section["Content"]
    meaning = section.get("Meaning", "")
    verse_nums = re.findall(r"\d+", to_ascii_digits(sloka_no))
    ref = (f"{gita_chapter}.{'-'.join(verse_nums)}" if serial > 2 and verse_nums
           else chapter.get("Name", "intro"))

    font = f"{lang['font_family']}, 'Noto Sans', sans-serif"

    def chrome_run(extra):
        return subprocess.run([chrome, "--headless=new", "--no-sandbox", "--hide-scrollbars",
                               "--default-background-color=00000000",
                               "--force-device-scale-factor=1", "--virtual-time-budget=3000",
                               *extra], capture_output=True, text=True)

    # ---- 1. Verse card (mirrors _renderVerseToPng) ---------------------------
    card_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:transparent;width:1080px;font-family:{font};}}
#card{{position:absolute;left:50px;top:50px;width:980px;box-sizing:border-box;
  padding:100px 30px 360px;text-align:center;background:rgba(0,0,0,.6);
  border:2px solid rgba(255,255,255,.15);border-radius:32px;
  box-shadow:0 15px 30px rgba(0,0,0,.55);}}
.app{{color:rgba(255,255,255,.7);font-size:32px;font-weight:600;letter-spacing:1.2px;margin-bottom:10px}}
.title{{color:#FFD740;font-size:48px;font-weight:700;margin-bottom:10px}}
.no{{color:rgba(255,255,255,.6);font-size:36px;font-weight:500;margin-bottom:{40 if speaker else 80}px}}
.spk{{color:#FF7722;font-size:38px;font-weight:800;margin-bottom:60px}}
.content{{color:#fff;font-size:64px;line-height:1.4;font-weight:500;margin-bottom:80px}}
.meaning{{color:rgba(255,255,255,.7);font-size:48px;line-height:1.4;font-style:italic}}
</style></head><body><div id="card">
<div class="app">{esc(lang['app_title'])}</div><div class="title">{esc(title)}</div>
<div class="no">{esc(sloka_no)}</div>{f'<div class="spk">{esc(speaker)}</div>' if speaker else ''}
<div class="content">{esc(content)}</div><div class="meaning">{esc(meaning)}</div>
</div><script>document.body.setAttribute('data-h',
  Math.ceil(document.getElementById('card').getBoundingClientRect().bottom + 50));</script>
</body></html>"""
    open(f"{out}/card.html", "w", encoding="utf-8").write(card_html)
    dom = chrome_run(["--dump-dom", f"file://{out}/card.html"]).stdout
    total_h = int(re.search(r'data-h="(\d+)"', dom).group(1))
    chrome_run([f"--screenshot={out}/verse.png", f"--window-size=1080,{max(1920, total_h)}",
                f"file://{out}/card.html"])

    # ---- 2. End card (mirrors _renderSignatureToPng) -------------------------
    icon = os.path.join(ROOT, "assets", "app_icon.png")
    lines = "<br>".join(map(esc, [lang["find_your_peace"], lang["app_title"], lang["download_app"]]))
    sig_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:1920px;background:rgba(0,0,0,.85);font-family:{font};overflow:hidden}}
.glow{{position:absolute;left:780px;top:1580px;width:200px;height:200px;border-radius:50%;
  background:rgba(255,215,64,.3);filter:blur(20px)}}
img{{position:absolute;left:820px;top:1640px;width:220px;height:220px}}
.txt{{position:absolute;right:40px;top:1500px;max-width:800px;text-align:right;color:#fff;
  font-size:40px;font-weight:700;line-height:1.4;letter-spacing:1.1px}}
.url{{position:absolute;top:1840px;width:1080px;text-align:center;color:rgba(255,255,255,.38);
  font-size:28px;font-weight:500;letter-spacing:1.5px}}
</style></head><body><div class="glow"></div><img src="file://{icon}">
<div class="txt">{lines}</div><div class="url">{esc(config['website'])}</div></body></html>"""
    open(f"{out}/sig.html", "w", encoding="utf-8").write(sig_html)
    chrome_run([f"--screenshot={out}/sig.png", "--window-size=1080,1920", f"file://{out}/sig.html"])

    # ---- 3. Watermark + small logo ----------------------------------------------
    wm_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:100px;background:transparent;font-family:{font}}}
div{{position:absolute;top:30px;width:1080px;text-align:center;color:rgba(255,255,255,.24);
  font-size:32px;font-weight:500;letter-spacing:2px}}</style></head>
<body><div>{esc(config['website'])}</div></body></html>"""
    open(f"{out}/wm.html", "w", encoding="utf-8").write(wm_html)
    chrome_run([f"--screenshot={out}/wm.png", "--window-size=1080,100", f"file://{out}/wm.html"])
    run(["ffmpeg", "-v", "error", "-y", "-i", icon, "-vf",
         "scale=140:140,format=rgba,pad=200:200:0:0:color=0x00000000", f"{out}/logo.png"])

    # ---- 4. Audio: sloka recitation + meaning (same paths as the app) ---------
    fname = f"{serial}-{section['SectionSerial']}.opus"
    sloka = fetch(base, token, f"sa/{fname}", f"{out}/sloka.opus")
    meaning_audio = fetch(base, token, f"{args.lang}/{fname}", f"{out}/meaning.opus")
    run(["ffmpeg", "-v", "error", "-y", "-i", sloka, "-i", meaning_audio, "-filter_complex",
         "[0:a]aresample=44100[a0];[1:a]aresample=44100[a1];[a0][a1]concat=n=2:v=0:a=1[outa]",
         "-map", "[outa]", "-c:a", "aac", "-b:a", "128k", f"{out}/voice.m4a"])
    T = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", f"{out}/voice.m4a"],
                             capture_output=True, text=True, check=True).stdout)

    # ---- 5. Assembly: same filter graph as VideoGenerator._generateVideo ------
    videos = config["background_videos"]
    bg_name = videos[section_count % len(videos)]
    bg = fetch(base, token, f"video/{bg_name}", f"{out}/bg.mp4")
    final_dur = max(T + 3.0, 6.0)
    if total_h > 1500:
        start_y, total_scroll = 250, total_h - 1500 + 500
        scroll_start, scroll_dur = 1.5, max(2.0, (T - 0.5) - 1.5)
        overlay = (f"overlay=x=0:y='{start_y}-max(0, min({total_scroll}, "
                   f"(t-{scroll_start})*({total_scroll}/{scroll_dur})))'")
    else:
        overlay = f"overlay=x=0:y={(1920 - total_h) / 2}"
    fc = (f"[0:v]scale=1080:1920,format=rgba[bg];"
          f"[2:v]format=rgba,fade=out:st={T}:d=0.2:alpha=1[v_fade];"
          f"[3:v]format=rgba,fade=in:st=1.5:d=1.5:alpha=1,fade=out:st={T}:d=0.1:alpha=1[logo_faded];"
          f"[5:v]format=rgba[wm_static];"
          f"[4:v]format=rgba,fade=in:st={T}:d=0.5:alpha=1[sig_fade];"
          f"[bg][v_fade]{overlay}[v1];[v1][logo_faded]overlay=880:1680[v2];"
          f"[v2][wm_static]overlay=0:1820[v3];[v3][sig_fade]overlay=0:0[outv]")
    video_path = f"{out}/video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", bg, "-i", f"{out}/voice.m4a",
         "-f", "image2", "-loop", "1", "-i", f"{out}/verse.png",
         "-f", "image2", "-loop", "1", "-i", f"{out}/logo.png",
         "-f", "image2", "-loop", "1", "-i", f"{out}/sig.png",
         "-f", "image2", "-loop", "1", "-i", f"{out}/wm.png",
         "-filter_complex", fc, "-map", "[outv]", "-map", "1:a",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-t", str(final_dur), video_path])

    # ---- 6. Post text (localized title, caption, hashtags) --------------------
    link = f"{config['play_store_url']}&referrer=utm_source%3Dshorts_{args.lang}"
    fields = dict(lang, ref=ref, title=title, sloka_no=sloka_no, content=content,
                  meaning=meaning, link=link)
    caption = config["templates"]["caption"].format(**fields)
    yt_title = lang.get("youtube_title", config["templates"]["youtube_title"]).format(**fields)
    if len(yt_title) > 100:  # YouTube limit; drop the English tail first
        yt_title = yt_title.split(" | Bhagavad Gita")[0] + " #shorts"
    meta = {
        "date": args.date,
        "lang": args.lang,
        "section_count": section_count,
        "ref": ref,
        "duration": round(final_dur, 1),
        "youtube_title": yt_title[:100],
        # YouTube rejects '<' and '>' in descriptions.
        "description": caption.replace("<", "‹").replace(">", "›")[:4900],
        "instagram_caption": caption[:2150],
        "tags": lang["tags"],
    }
    json.dump(meta, open(f"{out}/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{args.lang}: Gita {ref} (section {section_count}), {final_dur:.1f}s -> {video_path}")


if __name__ == "__main__":
    main()
