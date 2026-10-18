#!/usr/bin/env python3
"""
gen-sections.py — Genera l'esquelet de seccions de contingut per als 4 idiomes.

Crea content/{lang}/{dir}/_index.md per a cada seccio, amb `type` (compartit
entre idiomes) i `cascade.type` per als fills. Tambe genera la portada _index.md.
No sobreescriu fitxers existents.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# type -> layout
LAYOUT = {
    "biography": "single", "projects": "list", "discography": "list",
    "gigs": "list", "videos": "list", "photos": "list", "news": "list",
    "contact": "list", "search": "list",
}

# lang -> { type: (dir, title, description) }
L = {
    "en": {
        "home": ("", "Ivan Kovačević – Double Bass · Balkan · Jazz · Rhythm & Blues",
                 "Official website of double bassist Ivan Kovačević: Balkan, jazz, rhythm & blues from Barcelona."),
        "biography": ("biography", "Biography",
                      "The musical career of double bassist Ivan Kovačević: from Belgrade to Barcelona, Balkan, jazz and rhythm & blues."),
        "projects": ("projects", "Projects", "Bands and projects of double bassist Ivan Kovačević."),
        "discography": ("discography", "Discography", "Albums and recordings featuring Ivan Kovačević."),
        "gigs": ("gigs", "Gigs", "Upcoming concerts and performances by Ivan Kovačević."),
        "videos": ("videos", "Videos", "Live performances and videos."),
        "photos": ("photos", "Photos", "Photo galleries."),
        "news": ("news", "News", "News and press about Ivan Kovačević."),
        "contact": ("contact", "Contact", "Contact and booking for double bassist Ivan Kovačević."),
        "search": ("search", "Search", "Search the Ivan Kovačević website."),
    },
    "ca": {
        "home": ("", "Ivan Kovačević – Contrabaix · Balcànic · Jazz · Rhythm & Blues",
                 "Web oficial del contrabaixista Ivan Kovačević: balcànic, jazz i rhythm & blues des de Barcelona."),
        "biography": ("biografia", "Biografia", "La trajectòria musical del contrabaixista Ivan Kovačević: de Belgrad a Barcelona, balcànic, jazz i rhythm & blues."),
        "projects": ("projectes", "Projectes", "Bandes i projectes del contrabaixista Ivan Kovačević."),
        "discography": ("discografia", "Discografia", "Discos i gravacions amb Ivan Kovačević."),
        "gigs": ("concerts", "Concerts", "Propers concerts i actuacions d'Ivan Kovačević."),
        "videos": ("videos", "Vídeos", "Actuacions en directe i vídeos."),
        "photos": ("fotografies", "Fotografies", "Galeries de fotografies."),
        "news": ("noticies", "Notícies", "Notícies i premsa sobre Ivan Kovačević."),
        "contact": ("contacte", "Contacte", "Contacte i contractació del contrabaixista Ivan Kovačević."),
        "search": ("cerca", "Cerca", "Cerca al web d'Ivan Kovačević."),
    },
    "es": {
        "home": ("", "Ivan Kovačević – Contrabajo · Balcánico · Jazz · Rhythm & Blues",
                 "Web oficial del contrabajista Ivan Kovačević: balcánico, jazz y rhythm & blues desde Barcelona."),
        "biography": ("biografia", "Biografía", "La trayectoria musical del contrabajista Ivan Kovačević: de Belgrado a Barcelona, balcánico, jazz y rhythm & blues."),
        "projects": ("proyectos", "Proyectos", "Bandas y proyectos del contrabajista Ivan Kovačević."),
        "discography": ("discografia", "Discografía", "Discos y grabaciones con Ivan Kovačević."),
        "gigs": ("conciertos", "Conciertos", "Próximos conciertos y actuaciones de Ivan Kovačević."),
        "videos": ("videos", "Vídeos", "Actuaciones en directo y vídeos."),
        "photos": ("fotografias", "Fotografías", "Galerías de fotografías."),
        "news": ("noticias", "Noticias", "Noticias y prensa sobre Ivan Kovačević."),
        "contact": ("contacto", "Contacto", "Contacto y contratación del contrabajista Ivan Kovačević."),
        "search": ("buscar", "Buscar", "Buscar en la web de Ivan Kovačević."),
    },
    "sr": {
        "home": ("", "Ivan Kovačević – Kontrabas · Balkan · Džez · Rhythm & Blues",
                 "Zvanični sajt kontrabasiste Ivana Kovačevića: balkanska muzika, džez i rhythm & blues iz Barselone."),
        "biography": ("biografija", "Biografija", "Muzička karijera kontrabasiste Ivana Kovačevića: od Beograda do Barselone, balkan, džez i rhythm & blues."),
        "projects": ("projekti", "Projekti", "Bendovi i projekti kontrabasiste Ivana Kovačevića."),
        "discography": ("diskografija", "Diskografija", "Albumi i snimci sa Ivanom Kovačevićem."),
        "gigs": ("koncerti", "Koncerti", "Predstojeći koncerti i nastupi Ivana Kovačevića."),
        "videos": ("video", "Video", "Nastupi uživo i video snimci."),
        "photos": ("fotografije", "Fotografije", "Galerije fotografija."),
        "news": ("vesti", "Vesti", "Vesti i mediji o Ivanu Kovačeviću."),
        "contact": ("kontakt", "Kontakt", "Kontakt i rezervacije kontrabasiste Ivana Kovačevića."),
        "search": ("pretraga", "Pretraga", "Pretraži sajt Ivana Kovačevića."),
    },
}


def write_if_absent(path, content):
    full = os.path.join(ROOT, path)
    if os.path.exists(full):
        print(f"  = existeix, salto: {path}")
        return
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  + {path}")


def fm(d):
    out = ["---"]
    for k, v in d.items():
        if isinstance(v, bool):
            out.append(f"{k}: {'true' if v else 'false'}")
        else:
            out.append(f'{k}: "{v}"')
    out.append("---\n")
    return "\n".join(out)


for lang, secs in L.items():
    print(f"== {lang}")
    # portada
    hdir, htitle, hdesc = secs["home"]
    write_if_absent(f"content/{lang}/_index.md", fm({"title": htitle, "description": hdesc}))
    for typ, (d, title, desc) in secs.items():
        if typ == "home":
            continue
        extra = {"title": title, "description": desc, "type": typ, "layout": LAYOUT[typ], "translationKey": typ}
        body = ""
        lines = ["---"]
        for k, v in extra.items():
            lines.append(f'{k}: "{v}"')
        if typ == "search":
            lines.append("noindex: true")
        if typ in ("projects", "news"):
            lines.append("cascade:")
            lines.append(f"  type: {typ}")
        lines.append("---\n")
        write_if_absent(f"content/{lang}/{d}/_index.md", "\n".join(lines) + body)
