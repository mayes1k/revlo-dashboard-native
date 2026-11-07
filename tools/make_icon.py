# -*- coding: utf-8 -*-
"""
Genere assets/revlo-logo.ico a partir de revlo-logo.svg (necessite Pillow : pip install pillow).
Le logo fourni est blanc sur fond transparent : il est place sur un carre arrondi sombre
pour rester lisible dans la barre des taches Windows (clair ou sombre).
Parseur SVG minimal : chemins absolus M, L, H, V, Z uniquement.
"""
import os
import re
import sys

from PIL import Image, ImageDraw

BG = (15, 23, 42, 255)        # #0F172A
FG = (255, 255, 255, 255)
SUPER = 2048
SIZES = [16, 24, 32, 48, 64, 128, 256]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_polygons(svg_text):
    polygons = []
    for d in re.findall(r'<path[^>]*\sd="([^"]+)"', svg_text):
        tokens = re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", d)
        pts, cur, cmd, i = [], (0.0, 0.0), None, 0
        while i < len(tokens):
            t = tokens[i]
            if t.isalpha():
                if t not in "MLHVZ":
                    raise ValueError("Commande SVG non geree : " + t)
                cmd = t
                i += 1
                if cmd == "Z":
                    polygons.append(pts)
                    pts = []
                continue
            if cmd in ("M", "L"):
                cur = (float(tokens[i]), float(tokens[i + 1]))
                i += 2
                cmd = "L"
            elif cmd == "H":
                cur = (float(tokens[i]), cur[1])
                i += 1
            elif cmd == "V":
                cur = (cur[0], float(tokens[i]))
                i += 1
            else:
                raise ValueError("Donnees SVG inattendues")
            pts.append(cur)
        if pts:
            polygons.append(pts)
    return polygons


def main():
    svg_path = os.path.join(ROOT, "revlo-logo.svg")
    ico_path = os.path.join(ROOT, "assets", "revlo-logo.ico")
    with open(svg_path, "r", encoding="utf-8") as f:
        polygons = parse_polygons(f.read())

    xs = [p[0] for poly in polygons for p in poly]
    ys = [p[1] for poly in polygons for p in poly]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    scale = 0.62 * SUPER / max(w, h)
    ox = SUPER / 2 - (min(xs) + w / 2) * scale
    oy = SUPER / 2 - (min(ys) + h / 2) * scale

    img = Image.new("RGBA", (SUPER, SUPER), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, SUPER - 1, SUPER - 1), radius=int(SUPER * 0.22), fill=BG)
    for poly in polygons:
        draw.polygon([(x * scale + ox, y * scale + oy) for x, y in poly], fill=FG)

    base = img.resize((256, 256), Image.LANCZOS)
    os.makedirs(os.path.dirname(ico_path), exist_ok=True)
    base.save(ico_path, format="ICO", sizes=[(s, s) for s in SIZES])
    print("Icone creee :", ico_path)


if __name__ == "__main__":
    sys.exit(main())
