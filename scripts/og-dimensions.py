#!/usr/bin/env python3
"""Genera data/og-dimensions.yaml amb ample/alçada de les imatges emprades com a OG image."""
import re, os, glob, struct

def size_of(path):
    with open(path, "rb") as f:
        d = f.read()
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", d[16:24])
        return w, h
    if d[:2] == b"\xff\xd8":
        i = 2
        while i < len(d) - 9:
            if d[i] != 0xFF:
                i += 1
                continue
            m = d[i + 1]
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            seg = struct.unpack(">H", d[i + 2:i + 4])[0]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", d[i + 5:i + 9])
                return w, h
            i += 2 + seg
    return None

def fm(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    out = {}
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip('"')
    return out

paths = set()
t = open("hugo.toml", encoding="utf-8").read()
m = re.search(r'og_image\s*=\s*"([^"]+)"', t)
if m:
    paths.add(m.group(1))

for p in glob.glob("content/**/*.md", recursive=True):
    for key in ("og_image", "cover", "photo"):
        v = fm(p).get(key)
        if v:
            paths.add(v if v.startswith("/") else "/" + v)

lines = ["# Generat per scripts/og-dimensions.py — NO editar a mà.",
         "# Clau = ruta relativa a static/, valor = {width, height}"]
missing = []
for path in sorted(paths):
    rel = path.lstrip("/")
    full = os.path.join("static", rel)
    if not os.path.exists(full):
        missing.append(rel)
        continue
    dim = size_of(full)
    if not dim:
        missing.append(rel)
        continue
    lines.append('"%s": {width: %d, height: %d}' % (rel, dim[0], dim[1]))

os.makedirs("data", exist_ok=True)
open("data/og-dimensions.yaml", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("OG dimensions:", len(paths) - len(missing), "registrades")
for x in missing:
    print("  sense dimensió:", x)
