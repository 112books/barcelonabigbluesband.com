#!/usr/bin/env python3
"""Genera static/llms-full.txt a partir del contingut de Hugo (index complet per a IA)."""
import re, glob, os, html

LANGS = [
    ("en", {"biography": "biography", "projects": "projects", "discography": "discography",
             "gigs": "gigs", "videos": "videos", "photos": "photos", "press": "press", "contact": "contact"}),
    ("ca", {"biography": "biografia", "projects": "projectes", "discography": "discografia",
             "gigs": "concerts", "videos": "videos", "photos": "fotografies", "press": "premsa", "contact": "contacte"}),
    ("es", {"biography": "biografia", "projects": "proyectos", "discography": "discografia",
             "gigs": "conciertos", "videos": "videos", "photos": "fotografias", "press": "prensa", "contact": "contacto"}),
    ("sr", {"biography": "biografija", "projects": "projekti", "discography": "diskografija",
             "gigs": "koncerti", "videos": "video", "photos": "fotografije", "press": "stampa", "contact": "kontakt"}),
]
BASE = "https://ivankovacevic.com"
LABELS = {"en": ("Biography", "Projects", "Discography", "Gigs", "Videos", "Photos", "Press"),
          "ca": ("Biografia", "Projectes", "Discografia", "Concerts", "Videos", "Fotografies", "Premsa"),
          "es": ("Biografia", "Proyectos", "Discografia", "Conciertos", "Videos", "Fotografías", "Prensa"),
          "sr": ("Biografija", "Projekti", "Diskografija", "Koncerti", "Video", "Fotografije", "Štampa")}

def fm_of(p):
    t = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    fm = {}
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm

def clean(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or ""))).strip()

def artist_of(p):
    t = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n.*?\n---\n?(.*)$", t, re.S)
    body = m.group(1) if m else ""
    first = re.split(r"(?<=[.!?])\s+", body.strip(), maxsplit=1)[0]
    return clean(first).rstrip(".")

lines = []
lines.append("# Ivan Kovacevic - full site index (llms-full.txt)")
lines.append("")
lines.append("> Official website of Serbian double bassist, bandleader and arranger Ivan Kovacevic")
lines.append("> (Belgrade 1977, based in Barcelona). Balkan, jazz and rhythm & blues. Complete citable")
lines.append("> index of the site for AI systems and search engines.")
lines.append("")
lines.append("## Canonical site")
lines.append("- URL: " + BASE + "/")
lines.append("- Languages: en, ca, es, sr")
lines.append("- Sitemap: " + BASE + "/sitemap.xml")
lines.append("- Short summary: " + BASE + "/llms.txt")
lines.append("- Contact / booking: ivandoublebass@gmail.com")
lines.append("")

for lg, slugs in LANGS:
    L = LABELS[lg]
    lines.append("## " + lg.upper() + " (" + lg + ")")
    lines.append("")
    # biography
    b = "content/%s/%s/_index.md" % (lg, slugs["biography"])
    if os.path.exists(b):
        f = fm_of(b)
        lines.append("### " + L[0])
        lines.append("- " + f.get("title", "") + " - " + BASE + "/" + lg + "/" + slugs["biography"] + "/")
        if f.get("description"): lines.append("  " + f["description"])
        lines.append("")
    # projects
    lines.append("### " + L[1])
    for p in sorted(glob.glob("content/%s/%s/*.md" % (lg, slugs["projects"]))):
        if p.endswith("_index.md"): continue
        f = fm_of(p)
        if not f.get("title"): continue
        slug = os.path.basename(p)[:-3]
        lines.append("- " + f["title"] + " - " + BASE + "/" + lg + "/" + slugs["projects"] + "/" + slug + "/")
        if f.get("description"): lines.append("  " + f["description"])
    lines.append("")
    # discography
    lines.append("### " + L[2])
    for p in sorted(glob.glob("content/%s/%s/*.md" % (lg, slugs["discography"]))):
        if p.endswith("_index.md"): continue
        f = fm_of(p)
        if not f.get("title"): continue
        slug = os.path.basename(p)[:-3]
        year = f.get("year", "")
        tr = f.get("type_release", "")
        meta = ", ".join([x for x in (year, tr) if x])
        artist = artist_of(p)
        lines.append("- " + f["title"] + (" (" + meta + ")" if meta else "") + " - " + artist + " - " + BASE + "/" + lg + "/" + slugs["discography"] + "/" + slug + "/")
        links = []
        for key, lbl in (("apple_music", "Apple Music"), ("spotify", "Spotify"), ("youtube", "YouTube"), ("smartlink", "All platforms")):
            if f.get(key): links.append(lbl + ": " + f[key])
        if links: lines.append("  Links: " + " | ".join(links))
        if f.get("description"): lines.append("  " + f["description"])
    lines.append("")
    # gigs / videos / photos / press (summary)
    for key, idx in (("gigs", 3), ("videos", 4), ("photos", 5), ("press", 6)):
        b = "content/%s/%s/_index.md" % (lg, slugs[key])
        if os.path.exists(b):
            f = fm_of(b)
            lines.append("### " + L[idx])
            lines.append("- " + f.get("title", "") + " - " + BASE + "/" + lg + "/" + slugs[key] + "/")
            if f.get("description"): lines.append("  " + f["description"])
            lines.append("")

out = "\n".join(lines).rstrip() + "\n"
os.makedirs("static", exist_ok=True)
open("static/llms-full.txt", "w", encoding="utf-8").write(out)
print("llms-full.txt generat:", len(out), "bytes")
