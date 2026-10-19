#!/usr/bin/env python3
"""Genera static/llms-full.txt a partir del contingut de Hugo (index complet per a IA)."""
import re, glob, os, html

LANGS = [
    ("en", {"biography": "biography", "discography": "discography", "agenda": "agenda",
            "videos": "videos", "photos": "photos", "press": "press",
            "booking": "booking", "contact": "contact"}),
    ("ca", {"biography": "biografia", "discography": "discografia", "agenda": "agenda",
            "videos": "videos", "photos": "fotos", "press": "premsa",
            "booking": "contractacio", "contact": "contacte"}),
    ("es", {"biography": "biografia", "discography": "discografia", "agenda": "agenda",
            "videos": "videos", "photos": "fotos", "press": "prensa",
            "booking": "contratacion", "contact": "contacto"}),
]
BASE = "https://barcelonabigbluesband.com"
LABELS = {
    "en": ("Biography", "Discography", "Agenda", "Videos", "Photos", "Press", "Booking", "Contact"),
    "ca": ("Biografia", "Discografia", "Agenda", "Vídeos", "Fotos", "Premsa", "Contractació", "Contacte"),
    "es": ("Biografía", "Discografía", "Agenda", "Vídeos", "Fotos", "Prensa", "Contratación", "Contacto"),
}

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

lines = []
lines.append("# Barcelona Big Blues Band - full site index (llms-full.txt)")
lines.append("")
lines.append("> Official website of the Barcelona Big Blues Band, a rhythm & blues big band")
lines.append("> from Barcelona (Spain) led by double bassist Ivan Kovacevic. Concerts, discography,")
lines.append("> videos, press and booking. Complete citable index of the site for AI systems and")
lines.append("> search engines.")
lines.append("")
lines.append("## Canonical site")
lines.append("- URL: " + BASE + "/")
lines.append("- Languages: en, ca, es")
lines.append("- Sitemap: " + BASE + "/sitemap.xml")
lines.append("- Short summary: " + BASE + "/llms.txt")
lines.append("- Contact / booking: bookingb4@gmail.com")
lines.append("")

for lg, slugs in LANGS:
    L = LABELS[lg]
    lines.append("## " + lg.upper() + " (" + lg + ")")
    lines.append("")

    # biography (section with description)
    b = "content/%s/%s/_index.md" % (lg, slugs["biography"])
    if os.path.exists(b):
        f = fm_of(b)
        lines.append("### " + L[0])
        lines.append("- " + f.get("title", "") + " - " + BASE + "/" + lg + "/" + slugs["biography"] + "/")
        if f.get("description"):
            lines.append("  " + f["description"])
        lines.append("")

    # discography (itemised)
    lines.append("### " + L[1])
    for p in sorted(glob.glob("content/%s/%s/*.md" % (lg, slugs["discography"]))):
        if p.endswith("_index.md"):
            continue
        f = fm_of(p)
        if not f.get("title"):
            continue
        slug = os.path.basename(p)[:-3]
        meta = ", ".join(x for x in (f.get("year", ""), f.get("type_release", "")) if x)
        lines.append("- " + f["title"] + (" (" + meta + ")" if meta else "") +
                     " - " + BASE + "/" + lg + "/" + slugs["discography"] + "/" + slug + "/")
        links = []
        for key, lbl in (("spotify", "Spotify"), ("apple_music", "Apple Music"),
                         ("youtube", "YouTube"), ("smartlink", "All platforms")):
            if f.get(key):
                links.append(lbl + ": " + f[key])
        if links:
            lines.append("  Links: " + " | ".join(links))
        if f.get("description"):
            lines.append("  " + f["description"])
    lines.append("")

    # remaining sections (agenda/videos/photos/press/booking/contact)
    for key, idx in (("agenda", 2), ("videos", 3), ("photos", 4), ("press", 5), ("booking", 6), ("contact", 7)):
        b = "content/%s/%s/_index.md" % (lg, slugs[key])
        if os.path.exists(b):
            f = fm_of(b)
            lines.append("### " + L[idx])
            lines.append("- " + f.get("title", "") + " - " + BASE + "/" + lg + "/" + slugs[key] + "/")
            if f.get("description"):
                lines.append("  " + f["description"])
            lines.append("")

out = "\n".join(lines).rstrip() + "\n"
os.makedirs("static", exist_ok=True)
open("static/llms-full.txt", "w", encoding="utf-8").write(out)
print("llms-full.txt generat:", len(out), "bytes")
