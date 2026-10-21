#!/usr/bin/env python3
# pip install --break-system-packages fonttools requests
import os, subprocess, requests
from urllib.parse import quote
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

REPO_URL = "https://github.com/mc20000-01/font.git"
BASE = "https://raw.githubusercontent.com/google/fonts/main/"
FILL = "#ffffff"  # <img>/URL use ignores currentColor, so set a real color

FONTS = {
    # normal
    "inter":           "ofl/inter/Inter[opsz,wght].ttf",
    "roboto":          "ofl/roboto/Roboto[wdth,wght].ttf",
    "open-sans":       "ofl/opensans/OpenSans[wdth,wght].ttf",
    "lato":            "ofl/lato/Lato-Regular.ttf",
    "montserrat":      "ofl/montserrat/Montserrat[wght].ttf",
    # small / en-only
    "press-start-2p":  "ofl/pressstart2p/PressStart2P-Regular.ttf",
    "vt323":           "ofl/vt323/VT323-Regular.ttf",
    "silkscreen":      "ofl/silkscreen/Silkscreen-Regular.ttf",
    "share-tech-mono": "ofl/sharetechmono/ShareTechMono-Regular.ttf",
    "pixelify-sans":   "ofl/pixelifysans/PixelifySans[wght].ttf",
}

def glyph_filename(ch):
    if ch.islower() or ch.isdigit():
        return ch
    if ch.isupper():
        return f"upper-{ch.lower()}"
    return f"u{ord(ch):04x}"  # punctuation, e.g. u0021 = !

def convert(ttf_path, out_dir):
    font = TTFont(ttf_path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    asc, desc = font["hhea"].ascent, font["hhea"].descent
    h = asc - desc
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for code in range(33, 127):
        if code not in cmap:
            continue
        g = gs[cmap[code]]
        pen = SVGPathPen(gs)
        g.draw(pen)
        d = pen.getCommands()
        if not d:
            continue
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {g.width} {h}">'
               f'<g transform="translate(0,{asc}) scale(1,-1)">'
               f'<path fill="{FILL}" d="{d}"/></g></svg>')
        with open(os.path.join(out_dir, glyph_filename(chr(code)) + ".svg"), "w") as f:
            f.write(svg)
        n += 1
    return n

def sh(*cmd):
    return subprocess.run(cmd, check=False).returncode

os.makedirs("_tmp", exist_ok=True)
for name, path in FONTS.items():
    try:
        r = requests.get(BASE + quote(path), timeout=60)
        r.raise_for_status()
        tmp = f"_tmp/{name}.ttf"
        with open(tmp, "wb") as f:
            f.write(r.content)
        print(f"{name}: {convert(tmp, name)} glyphs")
    except Exception as e:
        print(f"{name}: FAILED ({e})")

for f in os.listdir("_tmp"):
    os.remove(os.path.join("_tmp", f))
os.rmdir("_tmp")

# git
if not os.path.isdir(".git"):
    sh("git", "init", "-b", "main")
if sh("git", "remote", "get-url", "origin") == 0:
    sh("git", "remote", "set-url", "origin", REPO_URL)
else:
    sh("git", "remote", "add", "origin", REPO_URL)

sh("git", "add", ".")
sh("git", "commit", "-m", "add font svgs")
if sh("git", "push", "-u", "origin", "main") != 0:
    sh("git", "pull", "--rebase", "origin", "main")
    sh("git", "push", "-u", "origin", "main")
