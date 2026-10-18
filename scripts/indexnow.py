#!/usr/bin/env python3
"""Notifica IndexNow (Bing, Yandex, Seznam, Naver) de les URLs de producció."""
import glob, json, re, sys, urllib.request

KEY = "0e7f48253f9aaf1e81d0b90ed90c146a"
HOST = "ivankovacevic.com"

urls = []
for f in ["public/sitemap.xml"] + glob.glob("public/*/sitemap.xml"):
    try:
        xml = open(f, encoding="utf-8").read()
    except OSError:
        continue
    urls += re.findall(r"<loc>(.*?)</loc>", xml)
urls = sorted(set(u for u in urls if u.startswith("https://" + HOST)))
if not urls:
    print("IndexNow: cap URL al sitemap")
    sys.exit(0)
payload = json.dumps({"host": HOST, "key": KEY, "keyLocation": "https://%s/%s.txt" % (HOST, KEY), "urlList": urls}).encode("utf-8")
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    r = urllib.request.urlopen(req, timeout=30)
    print("IndexNow: %d URLs enviades (HTTP %s)" % (len(urls), r.status))
except Exception as e:
    print("IndexNow: error %s" % e, file=sys.stderr)
