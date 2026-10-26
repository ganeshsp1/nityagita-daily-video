"""Renders the three pinned intro posts for each language's Instagram account
(same design as @the_nityagita's), as 1080x1350 JPEGs plus their captions.
Run on your own computer: needs Google Chrome. Text comes from
generator/intro_posts.json and generator/config.json.

usage: python3 tools/make_intro_posts.py [lang ...] [--src DIR] [--out DIR]
       --src: folder with logo.png and krishna_face_4.webp
              (default ~/Desktop/NityaGita_Instagram/src)
       --out: default ~/Desktop/NityaGita_Instagram/<lang>/
writes 1_welcome.jpg, 2_daily.jpg, 3_app.jpg and captions.json per language.
Post them in order 3, 2, 1 and pin 3, 2, 1, so Welcome ends up first.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CONFIG = json.load(open(os.path.join(ROOT, "generator", "config.json"), encoding="utf-8"))
TEXT = json.load(open(os.path.join(ROOT, "generator", "intro_posts.json"), encoding="utf-8"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NAVY, NAVY2, GOLD, SAFFRON, CREAM = "#191E38", "#0F1226", "#DFBA4E", "#FF7722", "#FAF6F0"
POSTS = ["1_welcome", "2_daily", "3_app"]

args = sys.argv[1:]


def option(name, default):
    if name in args:
        i = args.index(name)
        value = args[i + 1]
        del args[i:i + 2]
        return os.path.expanduser(value)
    return os.path.expanduser(default)


SRC = option("--src", "~/Desktop/NityaGita_Instagram/src")
OUT = option("--out", "~/Desktop/NityaGita_Instagram")


def css(lang):
    # Letter-spacing and uppercase (as on the English posts) break Indic shaping, so they're left out.
    fonts = f"{lang['font_family']}, 'Avenir Next', 'Helvetica Neue', sans-serif"
    return f"""
html,body{{margin:0;padding:0;overflow:hidden;width:1080px;height:1350px;font-family:{fonts};color:{CREAM}}}
img.logo{{-webkit-mask-image:radial-gradient(circle,#000 64%,transparent 74%);mask-image:radial-gradient(circle,#000 64%,transparent 74%)}}
.post{{width:1080px;height:1350px;position:relative;background:linear-gradient(180deg,{NAVY} 0%,{NAVY2} 100%)}}
.box{{position:absolute;left:70px;right:70px;text-align:center}}
.kicker{{color:{SAFFRON};font-size:38px;font-weight:600}}
.h1{{font-size:84px;line-height:1.25;color:{GOLD};margin:18px 0 30px;font-weight:700}}
.p{{font-size:40px;line-height:1.55;color:rgba(250,246,240,.88)}}
.row{{font-size:46px;line-height:1.4;margin:22px auto;padding:22px 34px;width:760px;text-align:left;
  border:2px solid rgba(223,186,78,.55);border-radius:28px;background:rgba(255,255,255,.03)}}
.foot{{position:absolute;bottom:56px;left:0;right:0;text-align:center;font-size:30px;color:rgba(250,246,240,.5);
  font-family:'Avenir Next','Helvetica Neue',sans-serif;letter-spacing:3px}}
.button{{margin-top:44px;display:inline-block;padding:22px 46px;border-radius:50px;background:{GOLD};
  color:{NAVY2};font-size:42px;font-weight:700}}
"""


def bodies(code):
    lang, t = CONFIG["languages"][code], TEXT[code]
    face, logo = f"file://{SRC}/krishna_face_4.webp", f"file://{SRC}/logo.png"
    return {
        "1_welcome": f"""
<div class="post">
  <img src="{face}" style="position:absolute;top:100px;left:50%;transform:translateX(-50%);width:540px;height:540px;
    border-radius:50%;border:8px solid {GOLD};object-fit:cover;box-shadow:0 0 80px rgba(223,186,78,.35)">
  <div class="box" style="top:700px">
    <div class="kicker">{t['welcome_kicker']}</div>
    <div class="h1">{t['welcome_title']}</div>
    <div class="p">{t['welcome_text']}</div>
  </div>
  <div class="foot">THENITYAGITA.COM</div>
</div>""",
        "2_daily": f"""
<div class="post">
  <div class="box" style="top:120px">
    <div class="kicker">{lang['today_label']}</div>
    <div class="h1">{t['daily_title']}</div>
    {''.join(f'<div class="row">{item}</div>' for item in t['daily_items'])}
    <div class="p" style="margin-top:40px">{t['follow']}</div>
  </div>
  <img class="logo" src="{logo}" style="position:absolute;bottom:120px;left:50%;transform:translateX(-50%);width:150px">
  <div class="foot">MORE LANGUAGES: @THE_NITYAGITA</div>
</div>""",
        "3_app": f"""
<div class="post">
  <img class="logo" src="{logo}" style="position:absolute;top:100px;left:50%;transform:translateX(-50%);width:380px">
  <div class="box" style="top:540px">
    <div class="kicker">{t['app_kicker']}</div>
    <div class="h1">{t['app_title']}</div>
    <div class="p">{'<br>'.join(t['app_items'])}</div>
    <div class="button">{t['link_in_bio']} 👇</div>
  </div>
  <div class="foot">{lang['app_title']}</div>
</div>""",
    }


def captions(code):
    lang, t = CONFIG["languages"][code], TEXT[code]
    plain = lambda s: s.replace("<br>", " ")
    tags = lang["hashtags"].replace("#shorts", "").strip()
    return {
        "1_welcome": f"🙏 {t['welcome_kicker']}\n{plain(t['welcome_text'])}\n\n{t['follow']}\n\n{tags}",
        "2_daily": f"🌅 {plain(t['daily_title'])}\n{' · '.join(t['daily_items'])}\n\n{t['follow']}\n\n{tags}",
        "3_app": f"📲 {plain(t['app_title'])}\n{' · '.join(t['app_items'])}\n\n"
                 f"{lang['download_app']} – {t['link_in_bio']} 👇\n\n{tags}",
    }


def render(code):
    out = os.path.join(OUT, code)
    os.makedirs(out, exist_ok=True)
    style = css(CONFIG["languages"][code])
    with tempfile.TemporaryDirectory() as tmp:
        for name, body in bodies(code).items():
            html = os.path.join(tmp, f"{name}.html")
            png = os.path.join(tmp, f"{name}.png")
            open(html, "w", encoding="utf-8").write(
                f"<!doctype html><html><head><meta charset='utf-8'><style>{style}</style></head>"
                f"<body>{body}</body></html>")
            subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                            "--allow-file-access-from-files", "--virtual-time-budget=3000",
                            "--window-size=1080,1350", f"--screenshot={png}", f"file://{html}"],
                           capture_output=True, check=True)
            # Instagram's API only accepts JPEG images.
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", png,
                            "--out", os.path.join(out, f"{name}.jpg")], capture_output=True, check=True)
    json.dump(captions(code), open(os.path.join(out, "captions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{code}: {out}")


def main():
    for f in ("logo.png", "krishna_face_4.webp"):
        if not os.path.exists(os.path.join(SRC, f)):
            sys.exit(f"Missing {SRC}/{f} (see --src)")
    codes = args or list(TEXT)
    unknown = [c for c in codes if c not in TEXT]
    if unknown:
        sys.exit(f"No intro post text for: {' '.join(unknown)}")
    for code in codes:
        render(code)


if __name__ == "__main__":
    main()
