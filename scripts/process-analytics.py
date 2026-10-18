import json
import sys
from datetime import datetime, timezone

def safe_get(data, key, default=None):
    if data is None:
        return default
    return data.get(key, default)

def main():
    if len(sys.argv) < 5:
        print("Ús: process-analytics.py <input.json> <output.json> <start> <end>")
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2]
    start_date  = sys.argv[3]
    end_date    = sys.argv[4]

    try:
        with open(input_file) as f:
            content = f.read().strip()
        if not content:
            print("⚠️  Fitxer d'entrada buit, generant analytics buit.")
            raw = {}
        else:
            raw = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ JSON invàlid: {e}")
        print(f"   Contingut: {content[:200]}")
        sys.exit(1)

    hits_data = safe_get(raw, "hits_data") or raw
    hits = safe_get(hits_data, "hits") or []

    def extract_stats(obj, key):
        """GoatCounter pot retornar la llista sota el nom de l'endpoint o sota 'stats'"""
        if not obj:
            return []
        items = obj.get(key) or obj.get('stats') or []
        out = []
        for s in items:
            out.append({
                "id":    s.get('id')   or s.get('code') or s.get('name') or '',
                "name":  s.get('name') or s.get('id')   or s.get('code') or '',
                "count": s.get('count', 0),
            })
        return out

    browsers  = extract_stats(safe_get(raw, "browsers")  or {}, "browsers")
    systems   = extract_stats(safe_get(raw, "systems")   or {}, "systems")
    sizes     = extract_stats(safe_get(raw, "sizes")     or {}, "sizes")
    locations = extract_stats(safe_get(raw, "locations") or {}, "locations")

    # Agregar per idioma i secció
    LANGS = {'ca', 'es', 'en'}
    by_lang = {}
    by_section = {}
    for h in hits:
        path = h.get("path", "")
        count = h.get("count", 0)
        parts = [p for p in path.strip("/").split("/") if p]
        lang = parts[0] if parts and parts[0] in LANGS else "other"
        by_lang[lang] = by_lang.get(lang, 0) + count
        if parts and parts[0] in LANGS:
            section = parts[1] if len(parts) > 1 else "home"
        else:
            section = parts[0] if parts else "home"
        by_section[section] = by_section.get(section, 0) + count

    total = sum(h.get("count", 0) for h in hits) if hits else 0

    output = {
        "generated_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "generated":    datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "period":       {"start": start_date, "end": end_date},
        "total":        total,
        "total_pageviews": total,
        "by_lang":      by_lang,
        "by_section":   by_section,
        "hits":         hits,
        "browsers":     browsers,
        "systems":      systems,
        "sizes":        sizes,
        "locations":    locations,
    }

    # Guarda: no sobreescriure dades bones amb un resultat buit (fallada transitòria)
    if total == 0:
        try:
            with open(output_file) as f:
                prev = json.load(f)
            if (prev.get("total") or 0) > 0:
                print("WARN: resultat buit; es conserva analytics.json anterior")
                return
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Analytics processats: {total} pageviews")
    print(f"   Langs: {by_lang} | Seccions: {len(by_section)}")

if __name__ == "__main__":
    main()