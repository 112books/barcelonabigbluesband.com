#!/usr/bin/env python3
"""
import-wp.py — Descarrega el contingut del WordPress d'ivankovacevic.com
via l'API REST i el desa a _import/ per a la seva conversio a Markdown.

Us:
    python3 scripts/import-wp.py
    python3 scripts/import-wp.py --base https://ivankovacevic.com

Requereix: requests (a requirements.txt)
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("Cal el paquet requests: pip install requests")


def fetch_paginated(session, url, params=None, max_pages=50, label=""):
    """Descarrega totes les pagines d'un endpoint REST de WordPress."""
    params = dict(params or {})
    params.setdefault("per_page", 100)
    items = []
    page = 1
    while page <= max_pages:
        p = dict(params)
        p["page"] = page
        try:
            r = session.get(url, params=p, timeout=30)
        except requests.RequestException as e:
            print(f"  ! Error de xarxa ({label} pag {page}): {e}")
            break
        if r.status_code == 400 and page > 1:
            break  # passat l'ultima pagina
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        items.extend(data)
        total_pages = int(r.headers.get("X-WP-TotalPages", "1") or "1")
        print(f"  {label}: pagina {page}/{total_pages} ({len(data)} items)")
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.3)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://ivankovacevic.com")
    ap.add_argument("--out", default="_import")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    api = f"{base}/wp-json/wp/v2"
    out = args.out
    os.makedirs(out, exist_ok=True)

    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (compatible; IvanKovacevicImport/1.0)"

    jobs = [
        ("pages", f"{api}/pages", {"_embed": 1}),
        ("posts", f"{api}/posts", {"_embed": 1}),
        ("categories", f"{api}/categories", {}),
        ("tags", f"{api}/tags", {}),
    ]

    summary = {}
    for name, url, params in jobs:
        print(f"==> {name}")
        try:
            items = fetch_paginated(s, url, params, label=name)
        except Exception as e:
            print(f"  ! {name} ha fallat: {e}")
            items = []
        summary[name] = len(items)
        with open(os.path.join(out, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    # Esdeveniments (The Events Calendar)
    print("==> events")
    try:
        url = f"{base}/wp-json/tribe/events/v1/events"
        items = fetch_paginated(
            s, url, {"start_date": "2000-01-01", "per_page": 100}, label="events"
        )
    except Exception as e:
        print(f"  ! events ha fallat: {e}")
        items = []
    summary["events"] = len(items)
    with open(os.path.join(out, "events.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # Media: nomes metadades (les imatges es descarreguen a part)
    print("==> media")
    try:
        items = fetch_paginated(s, f"{api}/media", {"per_page": 100}, label="media")
    except Exception as e:
        print(f"  ! media ha fallat: {e}")
        items = []
    summary["media"] = len(items)
    with open(os.path.join(out, "media.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print("\n=== RESUM ===")
    for k, v in summary.items():
        print(f"  {k:12s} {v}")
    print(f"\nDesat a {out}/")


if __name__ == "__main__":
    main()
