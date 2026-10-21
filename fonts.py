#!/usr/bin/env python3
# pip install --break-system-packages fonttools requests
import os, json, shutil, subprocess, requests
from urllib.parse import quote
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

REPO_URL = "https://github.com/mc20000-01/font.git"
BASE = "https://raw.githubusercontent.com/google/fonts/main/"
VERSION = "1.0.0"
FILL = "currentColor"   # same as lucide; use "#ffffff" if you load via <img>
SIZE = 24               # lucide canvas
SAFE = 20               # lucide safe area (2px padding)
PAD = (SIZE - SAFE) / 2

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

def glyph_name(ch):
    if ch.islower() or ch.isdigit():
        return ch
    if ch.isupper():
        return f"upper-{ch.lower()}"
    return f"u{ord(ch):04x}"  # punctuation, e.g. u0021 = !

def num(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def bounds(gs, name):
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return bp.bounds

def make_svg(font_name, gname, ch, d):
    return (
        f"<!-- @license font-svg v{VERSION} - OFL-1.1 | {font_name} | char: U+{ord(ch):04X} -->\n"
        f"<svg\n"
        f'  class="font-glyph font-{font_name} font-glyph-{gname}"\n'
        f'  xmlns="http://www.w3.org/2000/svg"\n'
        f'  width="{SIZE}"\n'
        f'  height="{SIZE}"\n'
        f'  viewBox="0 0 {SIZE} {SIZE}"\n'
        f'  fill="{FILL}"\n'
        f'  stroke="none"\n'
        f">\n"
        f'  <path d="{d}" />\n'
        f"</svg>\n"
    )

def convert(ttf_path, font_name, out_dir):
    font = TTFont(ttf_path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()

    # font-wide vertical extent from letters/digits (keeps real proportions)
    bs = [bounds(gs, cmap[c]) for c in range(33, 127)
          if c in cmap and chr(c).isalnum()]
    bs = [b for b in bs if b]
    ymax = max(b[3] for b in bs)
    ymin = min(b[1] for b in bs)
    s = SAFE / (ymax - ymin)      # one scale per font
    base = PAD + ymax * s         # shared baseline

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    files, meta = [], {}
    for code in range(33, 127):
        if code not in cmap:
            continue
        name = cmap[code]
        b = bounds(gs, name)
        if not b:
            continue
        x0, y0, x1, y1 = b
        w, h = x1 - x0, y1 - y0

        k = min(s, SAFE / w, SAFE / h)
        tx = SIZE / 2 - (x0 + w / 2) * k
        ty = SIZE / 2 + (y0 + h / 2) * k if k < s * 0.999 else base

        path = SVGPathPen(gs, ntos=num)
        gs[name].draw(TransformPen(path, (k, 0, 0, -k, tx, ty)))
        d = path.getCommands()
        if not d:
            continue

        ch = chr(code)
        gname = glyph_name(ch)
        fn = gname + ".svg"
        with open(os.path.join(out_dir, fn), "w") as f:
            f.write(make_svg(font_name, gname, ch, d))
        files.append(fn)
        meta[fn] = {"char": ch, "unicode": f"U+{code:04X}"}

    files.sort()
    with open(os.path.join(out_dir, "list.txt"), "w") as f:
        f.write("\n".join(files) + "\n")
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump({
            "font": font_name,
            "license": "OFL-1.1",
            "source": "https://github.com/google/fonts",
            "size": SIZE,
            "glyphs": meta,
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return len(files)

def sh(*cmd):
    return subprocess.run(cmd, check=False).returncode

os.makedirs("_tmp", exist_ok=True)
done = []
for name, path in FONTS.items():
    try:
        r = requests.get(BASE + quote(path), timeout=60)
        r.raise_for_status()
        tmp = f"_tmp/{name}.ttf"
        with open(tmp, "wb") as f:
            f.write(r.content)
        print(f"{name}: {convert(tmp, name, name)} glyphs")
        done.append(name)
    except Exception as e:
        print(f"{name}: FAILED ({e})")
shutil.rmtree("_tmp")

with open("list.txt", "w") as f:
    f.write("\n".join(sorted(done)) + "\n")

if not os.path.isdir(".git"):
    sh("git", "init", "-b", "main")
if sh("git", "remote", "get-url", "origin") == 0:
    sh("git", "remote", "set-url", "origin", REPO_URL)
else:
    sh("git", "remote", "add", "origin", REPO_URL)

sh("git", "add", ".")
sh("git", "commit", "-m", "regenerate font svgs")
if sh("git", "push", "-u", "origin", "main") != 0:
    sh("git", "pull", "--rebase", "origin", "main")
    sh("git", "push", "-u", "origin", "main")
