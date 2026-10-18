#!/usr/bin/env python3
"""
process-concerts.py
Converteix concerts.txt (iCal) a static/data/concerts-schema.json
per generar JSON-LD MusicEvent en build time amb Hugo.
"""
import json
import re
import sys
from datetime import datetime, timezone

def parse_ical_date(dtstr):
    """Converteix DTSTART/DTEND de iCal a ISO 8601."""
    dtstr = dtstr.strip()
    try:
        if 'T' in dtstr:
            # Format: 20260419T160000Z o 20260419T160000
            if dtstr.endswith('Z'):
                dt = datetime.strptime(dtstr, '%Y%m%dT%H%M%SZ')
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(dtstr, '%Y%m%dT%H%M%S')
        else:
            # Format: 20260419 (tot el dia)
            dt = datetime.strptime(dtstr, '%Y%m%d')
        return dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    except ValueError:
        return dtstr

def unescape_ical(text):
    """Desescapa caràcters especials d'iCal."""
    text = text.replace('\\n', '\n')
    text = text.replace('\\,', ',')
    text = text.replace('\\;', ';')
    text = text.replace('\\\\', '\\')
    return text.strip()

def unfold_ical(lines):
    """Uneix línies doblegades (continuation lines) de iCal."""
    result = []
    for line in lines:
        if line.startswith((' ', '\t')) and result:
            result[-1] = result[-1].rstrip('\r\n') + line.lstrip()
        else:
            result.append(line)
    return result

def parse_ical(content):
    """Parseja el contingut iCal i retorna llista d'events."""
    lines = unfold_ical(content.splitlines(keepends=True))
    events = []
    current = {}
    in_event = False

    for line in lines:
        line = line.rstrip('\r\n')
        if line == 'BEGIN:VEVENT':
            in_event = True
            current = {}
        elif line == 'END:VEVENT':
            in_event = False
            if current:
                events.append(current)
        elif in_event and ':' in line:
            # Suport per propietats amb paràmetres (ex: DTSTART;TZID=Europe/Madrid:...)
            key, _, value = line.partition(':')
            key = key.split(';')[0].strip()
            value = unescape_ical(value)
            current[key] = value

    return events

def event_to_schema(event, base_url='https://ivankovacevic.com'):
    """Converteix un event iCal a objecte Schema.org MusicEvent."""
    summary  = event.get('SUMMARY', '')
    location = event.get('LOCATION', '')
    dtstart  = event.get('DTSTART', '')
    dtend    = event.get('DTEND', '')
    desc     = event.get('DESCRIPTION', '')
    url      = event.get('URL', base_url)

    schema = {
        '@type': 'MusicEvent',
        'name': summary,
        'startDate': parse_ical_date(dtstart),
        'performer': {
            '@type': 'MusicGroup',
            'name': 'Bratia Music',
            'url': base_url
        }
    }

    if dtend:
        schema['endDate'] = parse_ical_date(dtend)

    if location:
        parts = [p.strip() for p in location.split(',')]
        schema['location'] = {
            '@type': 'Place',
            'name': parts[0],
            'address': {
                '@type': 'PostalAddress',
                'streetAddress': parts[1] if len(parts) > 1 else '',
                'addressLocality': parts[-1] if len(parts) > 1 else parts[0],
                'addressCountry': 'ES'
            }
        }
    else:
        schema['location'] = {
            '@type': 'Place',
            'name': 'Barcelona',
            'address': {
                '@type': 'PostalAddress',
                'addressLocality': 'Barcelona',
                'addressCountry': 'ES'
            }
        }

    if desc:
        schema['description'] = desc[:200]

    if url and url != base_url:
        schema['url'] = url

    schema['eventStatus'] = 'https://schema.org/EventScheduled'
    schema['organizer'] = {
        '@type': 'MusicGroup',
        'name': 'Bratia Music',
        'url': base_url
    }

    return schema

def main():
    if len(sys.argv) < 3:
        print('Ús: python3 process-concerts.py concerts.txt output.json')
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2]
    base_url    = sys.argv[3] if len(sys.argv) > 3 else 'https://ivankovacevic.com'

    with open(input_file, encoding='utf-8') as f:
        content = f.read()

    events   = parse_ical(content)
    now      = datetime.now(timezone.utc)
    upcoming = []

    for ev in events:
        dtstart = ev.get('DTSTART', '')
        if not dtstart:
            continue
        try:
            iso = parse_ical_date(dtstart)
            # Filtra events passats (més de 1 dia enrere)
            dt = datetime.fromisoformat(iso.replace('+00:00', '+00:00'))
            if dt.timestamp() > now.timestamp() - 86400:
                upcoming.append(event_to_schema(ev, base_url))
        except Exception:
            upcoming.append(event_to_schema(ev, base_url))

    # Ordena per data
    upcoming.sort(key=lambda x: x.get('startDate', ''))

    result = {
        'generated': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'events': upcoming
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f'Concerts processats: {len(upcoming)} propers events')

if __name__ == '__main__':
    main()