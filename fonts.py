#!/usr/bin/env python3
# pip install --break-system-packages fonttools requests
import os, subprocess, requests
from urllib.parse import quote
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

REPO_URL = "https://github.com/mc20000-01/font.git"
BASE = "https://raw.githubusercontent.com/google/fonts/main/"
FILL = "#ffffff"
SIZE = 24  # native size, like lucide

FONTS = {
    "inter":           "ofl/inter/Inter[opsz,wght].ttf",
    "roboto":          "ofl/roboto/Roboto[wdth,wght].ttf",
    "open-sans":       "ofl/opensans/OpenSans[wdth,wght].ttf",
    "lato":            "ofl/lato/Lato-Regular.ttf",
    "montserrat":      "ofl/montserrat/Montserrat[wght].ttf",
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
    return f"u{ord(ch):04x}"

def convert(ttf_path, out_dir):
    font = TTFont(ttf_path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    upm = font["head"].unitsPerEm
    cap = getattr(font["OS/2"], "sCapHeight", 0) or upm * 0.7
    s = 16 / cap          # capital letters are 16 units tall (Lucide's 2px padding)
    base = 19.5           # baseline y, so caps span 3.5-19.5 and descenders fit below
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
        k = min(s, 20 / g.width) if g.width else s   # shrink only if too wide
        tx = (SIZE - g.width * k) / 2
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
               f'viewBox="0 0 {SIZE} {SIZE}">'
               f'<g transform="translate({tx:.3f},{base}) scale({k:.6f},{-k:.6f})">'
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

if not os.path.isdir(".git"):
    sh("git", "init", "-b", "main")
if sh("git", "remote", "get-url", "origin") == 0:
    sh("git", "remote", "set-url", "origin", REPO_URL)
else:
    sh("git", "remote", "add", "origin", REPO_URL)

sh("git", "add", ".")
sh("git", "commit", "-m", "20x20 glyph svgs")
if sh("git", "push", "-u", "origin", "main") != 0:
    sh("git", "pull", "--rebase", "origin", "main")
    sh("git", "push", "-u", "origin", "main")
