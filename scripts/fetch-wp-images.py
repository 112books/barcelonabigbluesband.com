#!/usr/bin/env python3
"""
fetch-wp-images.py — Desa les imatges del WordPress a static/images/wp/ i
reescriu les referencies dins content/*.md a rutes locals.

- Detecta URLs de wp-content/uploads (host antic o nou).
- Baixa l'original (sense sufix -WxH).
- Reescriu qualsevol aparicio de la URL (Markdown o HTML) cap a /images/wp/.
- Neteja atributs srcset i sizes del HTML.
"""
import glob
import os
import re
import urllib.parse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "static", "images", "wp")
os.makedirs(IMG_DIR, exist_ok=True)

UPLOAD_RE = re.compile(r"https?://[^\s\"')<>]*wp-content/uploads/[^\s\"')<>]+")
SIZE_RE = re.compile(r"-\d+x\d+(\.\w+)$")


def original_name(url):
    path = urllib.parse.urlparse(url).path
    base = os.path.basename(path)
    base = SIZE_RE.sub(r"\1", base)
    return base


def main():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (compatible; IvanImport/1.0)"
    files = glob.glob(os.path.join(ROOT, "content", "**", "*.md"), recursive=True)
    downloaded = {}
    for fp in files:
        text = open(fp, encoding="utf-8").read()
        urls = set(UPLOAD_RE.findall(text))
        if not urls:
            continue
        # agrupa per nom original: tria la URL sense sufix de mida (original)
        by_name = {}
        for u in urls:
            name = original_name(u)
            # preferim la URL que ja es l'original (sense -WxH)
            if name not in by_name or SIZE_RE.search(os.path.basename(urllib.parse.urlparse(by_name[name]).path)):
                if SIZE_RE.search(os.path.basename(urllib.parse.urlparse(u).path)):
                    continue
                by_name[name] = u
        for name, url in by_name.items():
            dest = os.path.join(IMG_DIR, name)
            if name not in downloaded and not os.path.exists(dest):
                try:
                    r = s.get(url, timeout=30)
                    if r.status_code == 200 and r.content:
                        with open(dest, "wb") as f:
                            f.write(r.content)
                        print(f"  + {name} ({len(r.content)//1024} KB)")
                    else:
                        print(f"  ! {url} -> HTTP {r.status_code}")
                except Exception as e:
                    print(f"  ! {url}: {e}")
            downloaded[name] = f"/images/wp/{name}"
        # reescriu totes les URLs (originals o miniatures) cap al nom local
        def repl(m):
            name = original_name(m.group(0))
            return f"/images/wp/{name}"
        text = UPLOAD_RE.sub(repl, text)
        # neteja srcset i sizes del HTML
        text = re.sub(r'\s+srcset="[^"]*"', "", text)
        text = re.sub(r"\s+sizes=\"[^\"]*\"", "", text)
        open(fp, "w", encoding="utf-8").write(text)
        print(f"  ~ {os.path.relpath(fp, ROOT)}")

    print(f"\n{len(downloaded)} imatges a static/images/wp/")


if __name__ == "__main__":
    main()
