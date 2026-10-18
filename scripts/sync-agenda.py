#!/usr/bin/env python3
"""
sync-agenda.py
Agrega els calendaris iCal definits a data/sources.yaml i genera:
  - static/data/concerts.txt          (un sol VCALENDAR vàlid, per al JS client)
  - data/concerts-schema.json         (JSON-LD MusicEvent, per a Hugo)

Cada esdeveniment porta el nom del projecte (font) com a artista/origen.
"""
import json
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
    import requests
except ImportError as e:
    print(f"Falta dependència: {e}. Instal·la requirements.txt", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.yaml"
ICAL_OUT = ROOT / "static" / "data" / "concerts.txt"
SCHEMA_OUT = ROOT / "data" / "concerts-schema.json"
PRICES = ROOT / "data" / "concert-prices.yaml"
BASE_URL = "https://ivankovacevic.com"
BANDSINTOWN_APP_ID = "js_ivankovacevic.com"


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


AVAILABILITY = {
    "in-stock": "https://schema.org/InStock",
    "sold-out": "https://schema.org/SoldOut",
    "pre-order": "https://schema.org/PreOrder",
    "presale": "https://schema.org/PreSale",
}


def parse_price(value):
    """Retorna el preu com a número o None si no és vàlid."""
    try:
        price = float(str(value).replace("€", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    return int(price) if price.is_integer() else price


def to_schema_date(value):
    """Accepta data iCal (20260901T100000) o ISO 8601 i retorna ISO 8601."""
    value = (value or "").strip()
    if not value:
        return ""
    if re.fullmatch(r"\d{8}(T\d{6}Z?)?", value):
        return parse_ical_date(value)
    return value


def unescape_ical(text):
    text = text.replace("\\n", "\n").replace("\\,", ",")
    text = text.replace("\\;", ";").replace("\\\\", "\\")
    return text.strip()


def unfold_ical(lines):
    result = []
    for line in lines:
        if line.startswith((" ", "\t")) and result:
            result[-1] = result[-1].rstrip("\r\n") + line.lstrip()
        else:
            result.append(line)
    return result


def parse_ical(content):
    lines = unfold_ical(content.splitlines(keepends=True))
    events, current, in_event = [], {}, False
    for line in lines:
        line = line.rstrip("\r\n")
        if line == "BEGIN:VEVENT":
            in_event, current = True, {}
        elif line == "END:VEVENT":
            in_event = False
            if current:
                events.append(current)
        elif in_event and ":" in line:
            key, _, value = line.partition(":")
            key = key.split(";")[0].strip()
            current[key] = unescape_ical(value)
    return events


def parse_ical_date(dtstr):
    dtstr = dtstr.strip()
    try:
        if "T" in dtstr:
            if dtstr.endswith("Z"):
                dt = datetime.strptime(dtstr, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(dtstr, "%Y%m%dT%H%M%S")
        else:
            dt = datetime.strptime(dtstr, "%Y%m%d")
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    except ValueError:
        return dtstr


def to_schema(event, performer, base_url=BASE_URL):
    summary = event.get("SUMMARY", "")
    location = event.get("LOCATION", "")
    dtstart = event.get("DTSTART", "")
    dtend = event.get("DTEND", "")
    desc = event.get("DESCRIPTION", "")
    url = event.get("URL", base_url)

    schema = {
        "@type": "MusicEvent",
        "name": summary,
        "startDate": parse_ical_date(dtstart),
        "performer": {"@type": "MusicGroup", "name": performer},
    }
    if dtend:
        schema["endDate"] = parse_ical_date(dtend)

    if location:
        parts = [p.strip() for p in location.split(",")]
        schema["location"] = {
            "@type": "Place",
            "name": parts[0],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": parts[1] if len(parts) > 1 else "",
                "addressLocality": parts[-1] if len(parts) > 1 else parts[0],
                "addressCountry": "ES",
            },
        }
    else:
        schema["location"] = {
            "@type": "Place",
            "name": "Barcelona",
            "address": {"@type": "PostalAddress", "addressLocality": "Barcelona", "addressCountry": "ES"},
        }

    if desc:
        schema["description"] = desc[:200]
    if url and url != base_url:
        schema["url"] = url
    schema["eventStatus"] = "https://schema.org/EventScheduled"
    schema["organizer"] = {"@type": "MusicGroup", "name": performer}

    # Oferta d'entrades: només si el preu és conegut. Google Validation
    # (Search Console) exigeix price i priceCurrency dins d'«offers».
    price = parse_price(event.get("X-PRICE", ""))
    if price is not None:
        offer = {"@type": "Offer", "price": price}
        offer["priceCurrency"] = (event.get("X-PRICE-CURRENCY") or "EUR").strip().upper() or "EUR"
        ticket_url = event.get("URL", "")
        if ticket_url and ticket_url != base_url:
            offer["url"] = ticket_url
        availability = (event.get("X-AVAILABILITY") or "").strip().lower()
        if availability:
            offer["availability"] = AVAILABILITY.get(availability, availability)
        valid_from = to_schema_date(event.get("X-VALID-FROM", ""))
        if valid_from:
            offer["validFrom"] = valid_from
        schema["offers"] = offer
    return schema


def fetch(url):
    resp = requests.get(url, timeout=30, headers={"User-Agent": "ivankovacevic.com/1.0"})
    resp.raise_for_status()
    return resp.text


def fetch_bandsintown(artist_id):
    url = f"https://rest.bandsintown.com/artists/id_{artist_id}/events?app_id={BANDSINTOWN_APP_ID}"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "ivankovacevic.com/1.0"})
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        raise RuntimeError(data.get("Message", "resposta inesperada de Bandsintown"))
    return data


def bandsintown_to_event(ev, name):
    """Converteix un esdeveniment de Bandsintown al format VEVENT intern."""
    dt_raw = (ev.get("datetime") or "").strip()
    if not dt_raw:
        return None
    try:
        start = datetime.fromisoformat(dt_raw)
    except ValueError:
        return None
    end = start + timedelta(hours=2)

    venue = ev.get("venue") or {}
    vname = (venue.get("name") or "").strip()
    vcity = (venue.get("city") or "").strip()
    vcountry = (venue.get("country") or "").strip()
    location = ", ".join(x for x in (vname, vcity, vcountry) if x)

    title = (ev.get("title") or "").strip()
    if title and vname:
        summary = f"{title}, {vname}"
    else:
        summary = title or vname or name

    url = ""
    for offer in ev.get("offers") or []:
        if offer.get("url"):
            url = offer["url"]
            break
    if not url:
        url = ev.get("url") or ""

    internal = {
        "SUMMARY": summary,
        "DTSTART": start.strftime("%Y%m%dT%H%M%S"),
        "DTEND": end.strftime("%Y%m%dT%H%M%S"),
        "LOCATION": location,
        "DESCRIPTION": (ev.get("description") or "").strip(),
        "URL": url,
        "X-PERFORMER": name,
    }

    # Dades de l'oferta que Bandsintown sí que publica (preu no).
    if ev.get("free"):
        internal["X-PRICE"] = "0"
        internal["X-PRICE-CURRENCY"] = "EUR"
    if ev.get("sold_out"):
        internal["X-AVAILABILITY"] = "sold-out"
    on_sale = (ev.get("on_sale_datetime") or "").strip()
    if on_sale:
        internal["X-VALID-FROM"] = on_sale
    return internal


def price_key(ev):
    """Clau de data/concert-prices.yaml: YYYY-MM-DD + slug del lloc."""
    day = ev.get("DTSTART", "")[:8]
    if len(day) == 8:
        day = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
    venue = (ev.get("LOCATION") or ev.get("SUMMARY") or "").split(",")[0].strip()
    return f"{day}-{slugify(venue)}"


def event_key(ev):
    venue = (ev.get("LOCATION") or ev.get("SUMMARY") or "").split(",")[0].strip().lower()
    return (ev.get("DTSTART", "")[:8], venue)


def escape_ical(text):
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def main():
    sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    gigs = sources.get("gigs") or []
    if not gigs:
        print("Cap font de gigs a data/sources.yaml", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    vervevents = []
    report = []

    for src in gigs:
        name, ical_url = src.get("name", "?"), src.get("ical")
        if not ical_url:
            continue
        try:
            content = fetch(ical_url)
        except Exception as e:
            print(f"AVÍS: no s'ha pogut descarregar «{name}»: {e}", file=sys.stderr)
            continue

        events = parse_ical(content)
        kept = 0
        for ev in events:
            dtstart = ev.get("DTSTART", "")
            if not dtstart:
                continue
            try:
                iso = parse_ical_date(dtstart)
                dt = datetime.fromisoformat(iso)
                if dt.timestamp() <= now.timestamp() - 86400:
                    continue
            except Exception:
                pass
            ev["X-PERFORMER"] = name
            vervevents.append(ev)
            kept += 1
        report.append(f"  {name} (iCal): {kept} esdeveniments propers")

    bandsintown = sources.get("bandsintown") or []
    for src in bandsintown:
        name, artist_id = src.get("name", "?"), src.get("id")
        if not artist_id:
            continue
        try:
            raw_events = fetch_bandsintown(artist_id)
        except Exception as e:
            print(f"AVÍS: Bandsintown «{name}» ha fallat: {e}", file=sys.stderr)
            continue
        kept = 0
        for raw in raw_events:
            ev = bandsintown_to_event(raw, name)
            if ev:
                vervevents.append(ev)
                kept += 1
        report.append(f"  {name} (Bandsintown): {kept} esdeveniments propers")

    deduped, seen = [], set()
    for ev in sorted(vervevents, key=lambda e: e.get("DTSTART", "")):
        key = event_key(ev)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)
    vervevents = deduped

    # Preus manuals (data/concert-prices.yaml), per als esdeveniments en què
    # ni l'iCal ni Bandsintown no publiquen l'import de l'entrada.
    overrides = {}
    if PRICES.exists():
        overrides = yaml.safe_load(PRICES.read_text(encoding="utf-8")) or {}
    for ev in vervevents:
        override = overrides.get(price_key(ev)) or {}
        if override.get("price") is not None:
            ev["X-PRICE"] = str(override["price"])
        if override.get("priceCurrency"):
            ev["X-PRICE-CURRENCY"] = str(override["priceCurrency"])
        if override.get("availability"):
            ev["X-AVAILABILITY"] = str(override["availability"])
        if override.get("validFrom"):
            ev["X-VALID-FROM"] = str(override["validFrom"])

    schema_events = [to_schema(ev, ev.get("X-PERFORMER", "")) for ev in vervevents]
    SCHEMA_OUT.write_text(
        json.dumps({"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "events": schema_events}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ivankovacevic.com//agenda//CA",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Ivan Kovačević",
    ]
    for ev in vervevents:
        lines.append("BEGIN:VEVENT")
        for key in ("SUMMARY", "DTSTART", "DTEND", "LOCATION", "DESCRIPTION", "URL", "X-PERFORMER"):
            if ev.get(key):
                lines.append(f"{key}:{escape_ical(ev[key])}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    ICAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    ICAL_OUT.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")

    print("Agenda sincronitzada:")
    print("\n".join(report))
    print(f"Total: {len(schema_events)} esdeveniments propers de {len(gigs) + len(bandsintown)} fonts")


if __name__ == "__main__":
    main()
