#!/usr/bin/env python3
"""Obté els propers concerts de Bandsintown i genera data/events.json.

Font: https://www.bandsintown.com/a/3540917-barcelona-big-blues-band
API:  https://rest.bandsintown.com/artists/id_<id>/events?app_id=js_<domini>

Ús:
    python3 scripts/fetch-bandsintown.py

Genera data/events.json amb:
    { "updated": ISO8601, "source": URL, "upcoming": [ ... ] }
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ARTIST_ID = 3540917
APP_ID = "js_barcelonabigbluesband.com"
SOURCE_URL = "https://www.bandsintown.com/a/3540917-barcelona-big-blues-band"
OUT = Path(__file__).resolve().parent.parent / "data" / "events.json"


def fetch_events():
    url = f"https://rest.bandsintown.com/artists/id_{ARTIST_ID}/events?app_id={APP_ID}"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "barcelonabigbluesband.com/1.0"})
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        raise RuntimeError(data.get("Message", "resposta inesperada de Bandsintown"))
    return data


def normalize(ev):
    dt_raw = (ev.get("datetime") or "").strip()
    if not dt_raw:
        return None
    try:
        start = datetime.fromisoformat(dt_raw)
    except ValueError:
        return None

    venue = ev.get("venue") or {}
    ticket_url = ""
    for offer in ev.get("offers") or []:
        if offer.get("url"):
            ticket_url = offer["url"]
            break

    return {
        "date": start.strftime("%Y-%m-%d"),
        "time": start.strftime("%H:%M"),
        "title": (ev.get("title") or "").strip(),
        "venue": (venue.get("name") or "").strip(),
        "city": (venue.get("city") or "").strip(),
        "country": (venue.get("country") or "").strip(),
        "url": (ev.get("url") or "").strip(),
        "ticket_url": ticket_url,
    }


def main():
    try:
        events = fetch_events()
    except Exception as exc:  # noqa: BLE001 — volem continuar si Bandsintown cau
        print(f"AVISA: no s'han pogut obtenir esdeveniments ({exc})", file=sys.stderr)
        if OUT.exists():
            print("Es manté l'events.json existent.")
            sys.exit(0)
        sys.exit(1)

    upcoming = [e for e in (normalize(ev) for ev in events) if e]
    upcoming.sort(key=lambda e: e["date"])

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": SOURCE_URL,
        "upcoming": upcoming,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(upcoming)} concerts propers escrits a {OUT}")


if __name__ == "__main__":
    main()
