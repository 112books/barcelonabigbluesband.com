import json
import re
import sys
import os

playlist_file = sys.argv[1]
out_file      = sys.argv[2]

with open(playlist_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

entries = data.get('entries', [])

# Carrega vídeos existents per preservar l'historial
existing = {}
if os.path.exists(out_file):
    try:
        with open(out_file, 'r', encoding='utf-8') as f:
            for v in json.load(f):
                existing[v['id']] = v
    except Exception:
        pass

new_videos = []
for entry in entries:
    if not entry:
        continue

    video_id = entry.get('id') or entry.get('url', '').split('v=')[-1]
    if not video_id:
        continue

    title = entry.get('title', '')
    # Filtra Shorts
    if re.search(r'#[Ss]horts?', title):
        continue
    url = entry.get('url') or entry.get('webpage_url') or f'https://www.youtube.com/watch?v={video_id}'
    if '/shorts/' in url:
        continue

    # Data de publicació: upload_date és 'YYYYMMDD'
    upload_date = entry.get('upload_date', '')
    if len(upload_date) == 8:
        published = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    else:
        published = upload_date[:10] if upload_date else ''

    # Miniatura: agafa la millor disponible o construeix la URL per defecte
    thumbnails = entry.get('thumbnails', [])
    if thumbnails:
        thumb = thumbnails[-1].get('url', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')
    else:
        thumb = f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'

    new_videos.append({
        'id':        video_id,
        'title':     title,
        'published': published,
        'thumb':     thumb,
        'url':       f'https://www.youtube.com/watch?v={video_id}',
        'embed':     f'https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1',
    })

# Fusiona: prioritza dades noves, manté els vídeos antics que no surten al feed
merged = {v['id']: v for v in new_videos}
for vid_id, v in existing.items():
    if vid_id not in merged:
        merged[vid_id] = v

# Ordena per data de publicació descendent
videos = sorted(merged.values(), key=lambda v: v['published'], reverse=True)

with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(videos, f, ensure_ascii=False, indent=2)

print(f"Vídeos guardats: {len(videos)} ({len(new_videos)} nous del feed, {len(existing)} existents)")
