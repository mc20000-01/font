#!/usr/bin/env python3
# pip install fonttools requests
import os, subprocess, requests
from urllib.parse import quote
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

REPO_URL = "https://github.com/mc20000-01/fonts.git"
BASE = "https://raw.githubusercontent.com/google/fonts/main/"

# folder name -> path in google/fonts
FONTS = {
    # normal
    "inter":        "ofl/inter/Inter[opsz,wght].ttf",
    "roboto":       "ofl/roboto/Roboto[wdth,wght].ttf",
    "open-sans":    "ofl/opensans/OpenSans[wdth,wght].ttf",
    "lato":         "ofl/lato/Lato-Regular.ttf",
    "montserrat":   "ofl/montserrat/Montserrat[wght].ttf",
    # small / en-only
    "press-start-2p": "ofl/pressstart2p/PressStart2P-Regular.ttf",
    "vt323":          "ofl/vt323/VT323-Regular.ttf",
    "silkscreen":     "ofl/silkscreen/Silkscreen-Regular.ttf",
    "share-tech-mono":"ofl/sharetechmono/ShareTechMono-Regular.ttf",
    "pixelify-sans":  "ofl/pixelifysans/PixelifySans[wght].ttf",
}

def glyph_filename(ch):
    if ch.islower() or ch.isdigit():
        return ch
    if ch.isupper():
        return f"upper-{ch.lower()}"   # avoids a.svg / A.svg collision
    return f"u{ord(ch):04x}"           # punctuation: u0021 = !

def convert(ttf_path, out_dir):
    font = TTFont(ttf_path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    asc, desc = font["hhea"].ascent, font["hhea"].descent
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for code in range(33, 127):  # printable ASCII
        if code not in cmap:
            continue
        g = gs[cmap[code]]
        pen = SVGPathPen(gs)
        g.draw(pen)
        d = pen.getCommands()
        if not d:
            continue
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-asc} {g.width} {asc - desc}">'
               f'<path transform="scale(1,-1)" fill="currentColor" d="{d}"/></svg>')
        with open(os.path.join(out_dir, glyph_filename(chr(code)) + ".svg"), "w") as f:
            f.write(svg)
        n += 1
    return n

def sh(*cmd):
    return subprocess.run(cmd, check=False)

os.makedirs("_tmp", exist_ok=True)
for name, path in FONTS.items():
    try:
        r = requests.get(BASE + quote(path), timeout=60)
        r.raise_for_status()
        tmp = f"_tmp/{name}.ttf"
        open(tmp, "wb").write(r.content)
        print(f"{name}: {convert(tmp, name)} glyphs")
    except Exception as e:
        print(f"{name}: FAILED ({e})")

# cleanup + git
for f in os.listdir("_tmp"):
    os.remove(os.path.join("_tmp", f))
os.rmdir("_tmp")

if not os.path.isdir(".git"):
    sh("git", "init", "-b", "main")
    sh("git", "remote", "add", "origin", REPO_URL)
sh("git", "add", ".")
sh("git", "commit", "-m", "add font svgs")
sh("git", "push", "-u", "origin", "main")
