# -*- coding: utf-8 -*-
"""
paketle.py - veri\ altındaki çok sayıda küçük dosyayı tek büyük paket dosyasına toplar (kopyalama hızlansın).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait
Yusuf'un isteği (26.10 09:09): küçük dosyalar kopyalamayı yavaşlatıyor; klasör klasör büyük paketler.
- Görseller zaten sıkıştırılmış olduğu için ZIP_STORED (hızlı, kayıpsız). Paket yanına <ad>.zip.sha256.
- Doğrulama: paketteki her dosya yeniden okunup CRC ve boyutu kaynakla karşılaştırılır.
- Kaynak dosyalar SİLİNMEZ; doğrulanan klasörlerin listesi PAKETLER.md'ye yazılır, Geri Dönüşüm Kutusu'na taşıma Yusuf'un onayıyla.
Kullanım: python paketle.py <klasör> [<klasör> ...]   (veri\ içine göre)
"""
import os, sys, zipfile, zlib, hashlib, json, time

V = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "veri"))


def paketle(goreli):
    kok = os.path.join(V, goreli)
    hedef = kok.rstrip("\\/") + ".zip"
    dosyalar = []
    for d, _, fs in os.walk(kok):
        for f in sorted(fs):
            dosyalar.append(os.path.join(d, f))
    with zipfile.ZipFile(hedef + ".yeni", "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for p in dosyalar:
            z.write(p, os.path.relpath(p, os.path.dirname(kok)))
    hata = 0
    with zipfile.ZipFile(hedef + ".yeni") as z:
        bilgi = {i.filename.replace("/", os.sep): i for i in z.infolist()}
        for p in dosyalar:
            i = bilgi.get(os.path.relpath(p, os.path.dirname(kok)))
            b = open(p, "rb").read()
            if i is None or i.file_size != len(b) or i.CRC != (zlib.crc32(b) & 0xFFFFFFFF):
                hata += 1
        if z.testzip() is not None:
            hata += 1
    if hata:
        print(goreli, "DOĞRULAMA HATASI", hata, "- paket .yeni olarak bırakıldı"); return None
    os.replace(hedef + ".yeni", hedef)
    h = hashlib.sha256()
    with open(hedef, "rb") as f:
        for parca in iter(lambda: f.read(1 << 22), b""):
            h.update(parca)
    open(hedef + ".sha256", "w").write(h.hexdigest() + "  " + os.path.basename(hedef) + "\n")
    r = {"klasor": goreli, "paket": os.path.relpath(hedef, V), "dosya": len(dosyalar), "bayt": os.path.getsize(hedef), "sha256": h.hexdigest(),
         "dogrulama": "her dosya CRC+boyut eşleşti", "tarih": time.strftime("%Y-%m-%d %H:%M")}
    print(json.dumps(r, ensure_ascii=False)); return r


if __name__ == "__main__":
    out = [r for r in (paketle(g) for g in sys.argv[1:]) if r]
    with open(os.path.join(V, "PAKETLER.md"), "a", encoding="utf-8") as f:
        for r in out:
            f.write("- %s -> %s : %d dosya, %.1f MB, SHA-256 %s, %s (%s). Kaynak klasör duruyor; Yusuf onaylarsa Geri Dönüşüm Kutusu'na.\n" % (
                r["klasor"], r["paket"], r["dosya"], r["bayt"] / 1e6, r["sha256"], r["dogrulama"], r["tarih"]))
