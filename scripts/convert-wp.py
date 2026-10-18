#!/usr/bin/env python3
"""
convert-wp.py — Converteix el contingut importat de WordPress (_import/) a
fitxers Markdown de Hugo (content/{lang}/...).

- Converteix HTML -> Markdown amb pandoc.
- Descarrega els originals de /wp-content/uploads/ a static/images/wp/.
- Genera EN i ES (idiomes originals del WordPress). CA i SR es tradueixen a part.

Us:
    python3 scripts/convert-wp.py
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMP = os.path.join(ROOT, "_import")
IMG_DIR = os.path.join(ROOT, "static", "images", "wp")
SITE = "https://ivankovacevic.com"

try:
    import requests
except ImportError:
    sys.exit("Cal el paquet requests")


# ── Mapatge explicit dels items del WordPress ────────────────────────────────
# clau: id del WP -> (lang, tipus, ruta destí relativa a content/, titol, translationKey)
PAGES = {
    167: ("en", "biography", "content/en/biography/_index.md", "Biography", "biography", "single"),
    153: ("es", "biography", "content/es/biografia/_index.md", "Biografía", "biography", "single"),
    746: ("es", "legal", "content/es/legal/politica-cookies.md", "Política de cookies", None, "single"),
    362: ("es", "legal", "content/es/legal/politica-privacidad.md", "Política de privacidad", None, "single"),
    745: ("es", "legal", "content/es/legal/aviso-legal.md", "Aviso legal", None, "single"),
}

# Posts -> projectes (una fitxa per banda). id ES / id EN
PROJECTS = [
    ("bratia",        "Bratia",                           768, None),
    ("barcelona-big-blues-band", "Barcelona Big Blues Band", 82, 286),
    ("barcelona-gipsy-balkan-orchestra", "Barcelona Gipsy balKan Orchestra", 79, 278),
    ("bernat-font-trio", "Bernat Font Trio",              88, 307),
    ("los-mambo-jambo", "Los Mambo Jambo",                64, 267),
    ("5-spots",       "Ivan Kovačević 5 Spots",           84, 171),
    ("lazy-jumpers",  "Lazy Jumpers",                     92, 169),
    ("the-nu-niles",  "The Nu Niles",                     90, 333),
    ("down-home",     "Down Home",                        86, None),
]

# Posts -> noticies
NEWS = [
    ("2016-ruta-66-meeting-point", "Ruta 66 – Meeting Point", 345, "2016-09-27"),
    ("2020-daddario-strings", "Ivan Kovačević sobre D'Addario", 723, "2020-04-08"),
]


def wp_slug_to_local(path):
    """Retorna el nom local d'un fitxer de /wp-content/uploads/."""
    base = os.path.basename(urllib.parse.urlparse(path).path)
    base = re.sub(r"-\d+x\d+(\.\w+)$", r"\1", base)  # treu mides -1024x852
    return base


def download_image(url, session):
    if "wp-content/uploads" not in url:
        return None
    name = wp_slug_to_local(url)
    dest = os.path.join(IMG_DIR, name)
    if os.path.exists(dest):
        return name
    os.makedirs(IMG_DIR, exist_ok=True)
    try:
        r = session.get(url, timeout=30)
        if r.status_code == 200 and r.content:
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"    imatge: {name} ({len(r.content)//1024} KB)")
            return name
    except Exception as e:
        print(f"    ! imatge {url}: {e}")
    return None


def clean_html(html):
    # treu el paràgraf de widgets [do_widget ...]
    html = re.sub(r"\[do_widget[^\]]*\]", "", html)
    return html


def html_to_md(html):
    html = clean_html(html)
    try:
        out = subprocess.run(
            ["pandoc", "-f", "html", "-t", "gfm", "--wrap=none"],
            input=html.encode("utf-8"), capture_output=True, check=True,
        )
        return out.stdout.decode("utf-8").strip()
    except Exception as e:
        print(f"    ! pandoc: {e}")
        return re.sub(r"<[^>]+>", "", html).strip()


def rewrite_media(md, session):
    """Descarrega imatges i reescriu URLs de wp-content/uploads."""
    def repl_img(m):
        alt, url = m.group(1), m.group(2)
        name = download_image(url, session)
        if name:
            return f"![{alt}](/images/wp/{name})"
        return m.group(0)

    md = re.sub(r"!\[([^\]]*)\]\((https?://[^)]+)\)", repl_img, md)
    # enllaços interns antics -> absoluts al domini nou
    md = md.replace("http://ivankovacevic.vl22684.dinaserver.com", SITE)
    return md


def front_matter(fields):
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        else:
            v = str(v).replace('"', '\\"')
            lines.append(f'{k}: "{v}"')
    lines.append("---\n")
    return "\n".join(lines)


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  escrit {path}")


def main():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (compatible; IvanImport/1.0)"
    pages = {p["id"]: p for p in json.load(open(f"{IMP}/pages.json"))}
    posts = {p["id"]: p for p in json.load(open(f"{IMP}/posts.json"))}

    # ── Pagines de seccio ──
    print("== Pagines de seccio")
    for pid, (lang, typ, dest, title, tkey, layout) in PAGES.items():
        p = pages.get(pid)
        if not p:
            print(f"  ! id {pid} no trobat")
            continue
        body = rewrite_media(html_to_md(p["content"]["rendered"]), s)
        fm = {"title": title, "type": typ, "layout": layout, "translationKey": tkey}
        write(dest, front_matter(fm) + body + "\n")

    # ── Projectes (bandes) ──
    print("== Projectes")
    for slug, title, es_id, en_id in PROJECTS:
        weight = PROJECTS.index((slug, title, es_id, en_id)) + 1
        for lang, pid, tdir, tlang in (
            ("es", es_id, "es/proyectos", "es"),
            ("en", en_id, "en/projects", "en"),
        ):
            if not pid or pid not in posts:
                continue
            p = posts[pid]
            body = rewrite_media(html_to_md(p["content"]["rendered"]), s)
            fm = {
                "title": title, "type": "projects", "translationKey": slug,
                "weight": weight, "layout": "single",
            }
            write(f"content/{tdir}/{slug}.md", front_matter(fm) + body + "\n")

    # ── Noticies ──
    print("== Noticies")
    for slug, title, pid, date in NEWS:
        p = posts.get(pid)
        if not p:
            continue
        lang = "en" if "/en/" in p["link"] else "es"
        tdir = "en/news" if lang == "en" else "es/noticias"
        body = rewrite_media(html_to_md(p["content"]["rendered"]), s)
        fm = {"title": title, "type": "news", "layout": "single", "date": date}
        write(f"content/{tdir}/{slug}.md", front_matter(fm) + body + "\n")

    print("\nFet. Revisa content/ i les imatges a static/images/wp/")


if __name__ == "__main__":
    main()
