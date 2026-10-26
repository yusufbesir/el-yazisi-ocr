# -*- coding: utf-8 -*-
"""
commons_topla.py - Wikimedia Commons'tan açık lisanslı Türkçe el yazısı görselleri toplar (resmî API, yavaş ve nazik).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait, eğitim amaçlı
Yusuf'un isteği (26.10 03:21): "siteleri kazı ve verileri al, her şey eğitim için".
- Yalnız MediaWiki API (robots.txt'e uygun, oturum yok); istek arası >= 1 sn; 1600 px küçük resim.
- Yalnız özgür lisanslar (CC0, CC BY, CC BY-SA, kamu malı); lisans, yazar, kaynak sayfası her dosya için kaynak.jsonl'ye.
- Görseller ETİKETSİZ: eğitimde doğrudan kullanılmaz; etiketleme/sınama arşivi. Osmanlıca (Arap harfli) belgeler ayrıca elenmeli.
Kullanım: python commons_topla.py "<arama>" [en_cok=300]
"""
import os, sys, json, time, hashlib, re, urllib.request, urllib.parse

KOK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CIK = os.path.join(KOK, "veri", "commons-tr-el-yazisi")
UA = "TAARNAK-OCR-egitim/0.1 (yerel egitim arsivi)"
API = "https://commons.wikimedia.org/w/api.php?"
IZIN = re.compile(r"^(cc0|cc[- ]by(-sa)?[- ]?\d|public domain|pd)", re.I)


def al(url):
    time.sleep(1.0)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return r.read()


if __name__ == "__main__":
    arama = sys.argv[1]; en_cok = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    os.makedirs(CIK, exist_ok=True)
    kayit = os.path.join(CIK, "kaynak.jsonl")
    var = set()
    if os.path.exists(kayit):
        var = {json.loads(s)["baslik"] for s in open(kayit, encoding="utf-8")}
    devam, say, alinan = {}, 0, 0
    while say < en_cok:
        p = {"action": "query", "format": "json", "generator": "search", "gsrsearch": arama, "gsrnamespace": 6, "gsrlimit": 50,
             "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size", "iiurlwidth": 1600}
        p.update(devam)
        d = json.loads(al(API + urllib.parse.urlencode(p)))
        for sf in (d.get("query", {}).get("pages", {}) or {}).values():
            say += 1
            t = sf.get("title", "")
            ii = (sf.get("imageinfo") or [{}])[0]
            if t in var or ii.get("mime") not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
                continue
            em = ii.get("extmetadata", {})
            lis = (em.get("LicenseShortName", {}) or {}).get("value", "")
            if not IZIN.match(lis.strip()):
                continue
            url = ii.get("thumburl") or ii.get("url")
            try:
                b = al(url)
            except Exception as e:
                print("indirilemedi", t, e); continue
            sha = hashlib.sha256(b).hexdigest()
            uz = ".png" if url.lower().endswith(".png") else ".jpg"
            ad = sha[:16] + uz
            open(os.path.join(CIK, ad), "wb").write(b)
            rec = {"baslik": t, "dosya": ad, "sha256": sha, "lisans": lis, "yazar": re.sub("<[^>]+>", "", (em.get("Artist", {}) or {}).get("value", ""))[:200],
                   "sayfa": ii.get("descriptionurl"), "arama": arama, "tarih": time.strftime("%Y-%m-%d %H:%M")}
            open(kayit, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
            var.add(t); alinan += 1
        if "continue" not in d:
            break
        devam = d["continue"]
    print("taranan", say, "alınan", alinan)
