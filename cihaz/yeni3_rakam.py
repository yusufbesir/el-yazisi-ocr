# -*- coding: utf-8 -*-
r"""yeni3_rakam.py - ornekler/yeni3 serbest metin fotoğraflarından, Yusuf'un okuduğu SAYILARIN kutularını (PaddleOCR satır kutusu içinde bölge)
karakterlere bölüp etiketli 28x28 rakam kırpıntıları üretir: veri/yeni3-rakam/<sınıf>/*.png, etiketler.csv, eslesmedi.txt, gozden-gecir.html.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı.
Girdi: cihaz/yeni3-kutular.json (cihaz/yeni3_kutular.py çıktısı). Bölme: egitim/bolme.py (karakter_kutulari/genis_bol/mnist_normalle);
yalnız maske serbest yazı için uyarlamalı eşik (cv2.adaptiveThreshold) + PaddleOCR satır çokgeni ile sınırlanır (tablo eşiği küçük fotoğrafta işlemiyor).
Etiket kuralı: bölge içi karakter kutusu sayısı doğru rakam sayısına EŞİTSE etiketlenir, değilse atlanır (eslesmedi.txt).
Kullanım: venv\Scripts\python.exe cihaz\yeni3_rakam.py [--debug]"""
import os, sys, json, html, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "egitim"))
import bolme

# (foto, paddle satır no, x0, x1 [orijinal piksel], doğru rakamlar, not)   -- doğru değerler Yusuf'un okuması
TOKENLER = [
    ("15.jpg", 0, 283, 405, "20062026", "tarih 20.06.2026"),
    ("15.jpg", 2, 345, 410, "2200", "Saat 22:00"),
    ("15.jpg", 12, 18, 46, "81", "81'"),
    ("14.webp", 2, 212, 252, "146", "(146. gün)"),
    ("16.jpg", 10, 394, 420, "10", "10 yaşında"),
    ("16.jpg", 18, 159, 234, "2900000", "2.900.000"),
    ("16.jpg", 18, 283, 330, "29", "2.9 milyon"),
    ("18.jpg", 4, 62, 84, "3", "3 yaşında"),
    ("18.jpg", 4, 112, 136, "7", "7 yaşında (1)"),
    ("18.jpg", 4, 214, 240, "7", "7 yaşında (2)"),
    ("18.jpg", 4, 420, 482, "2023", "2023"),
    ("18.jpg", 5, 160, 196, "95", "yüzde 95"),
]
SINIF = "0123456789"
CIKIS = os.environ.get("YENI3_CIKIS") or os.path.join(KOK, "veri", "yeni3-rakam")


def maske(g, poly, C=14, blok=31, pad=3):
    m = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, blok, C) > 0
    pm = np.zeros(g.shape, np.uint8)
    cv2.fillPoly(pm, [np.array(poly, np.int32)], 1)
    return m & (cv2.dilate(pm, np.ones((2 * pad + 1, 2 * pad + 1), np.uint8)) > 0)


def isle(foto, satir, x0, x1, dogru, kutular, C=14):
    g = bolme.gri_yukle(os.path.join(KOK, "ornekler", "yeni3", foto))
    poly = kutular[foto][satir]["poly"]
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    if x1 <= x0:
        x0, x1 = min(xs), max(xs)
    y0, y1 = max(0, min(ys) - 4), min(g.shape[0], max(ys) + 4)
    xa, xb = max(0, min(xs) - 4), min(g.shape[1], max(xs) + 4)
    satir_m = bolme.cizgi_temizle(maske(g, poly, C)[y0:y1, xa:xb])      # cetvel çizgisi tüm satır genişliğinde silinir
    n, et, ist, _ = cv2.connectedComponentsWithStats(satir_m.astype(np.uint8), connectivity=8)
    for i in range(1, n):                                                # üst/alt kenara değen = komşu satır taşması
        bx, by, bw, bh, al = ist[i]
        if by <= 0 or by + bh >= satir_m.shape[0]:
            satir_m[et == i] = False
    if x1 <= x0:
        x0, x1 = xa, xb
    x0, x1 = max(xa, x0), min(xb, x1)
    m = satir_m[:, x0 - xa:x1 - xa]
    gri = g[y0:y1, x0:x1]
    kut = bolme.karakter_kutulari(m, (len(dogru),))
    kut = [k for k in kut if k[3] - k[1] >= 0.35 * m.shape[0] or (k[3] - k[1]) >= 8]
    return gri, m, kut, (x0, y0)


def main(debug=False):
    kutular = json.load(open(os.path.join(KOK, "cihaz", "yeni3-kutular.json"), encoding="utf-8"))
    if os.path.isdir(CIKIS):
        print("HATA: %s zaten var; silme yok, elle başka ada taşıyın" % CIKIS); sys.exit(1)
    for s in SINIF:
        os.makedirs(os.path.join(CIKIS, s))
    kayit, es = [], []
    dbg = os.environ.get("YENI3_DEBUG")
    for n, (foto, satir, x0, x1, dogru, aciklama) in enumerate(TOKENLER):
        ad = os.path.splitext(foto)[0]
        gri, m, kut, (ox, oy) = isle(foto, satir, x0, x1, dogru, kutular)
        if dbg:
            S = 5
            im = Image.fromarray(gri).convert("RGB").resize((gri.shape[1] * S, gri.shape[0] * S), Image.LANCZOS)
            mk = Image.fromarray(((~m) * 255).astype(np.uint8)).convert("RGB").resize(im.size, Image.NEAREST)
            d = ImageDraw.Draw(mk)
            for j, (a, b, c, e, t) in enumerate(kut):
                d.rectangle([a * S, b * S, c * S, e * S], outline=(255, 0, 0)); d.text((a * S, max(0, b * S - 10)), str(j), fill=(0, 0, 255))
            W = Image.new("RGB", (im.width, im.height * 2)); W.paste(im, (0, 0)); W.paste(mk, (0, im.height))
            W.save(os.path.join(dbg, "t%02d_%s_%s.png" % (n, ad, dogru)))
        if len(kut) != len(dogru):
            es.append("%s satır %d '%s' (%s): kutu sayısı %d != %d, atlandı" % (foto, satir, dogru, aciklama, len(kut), len(dogru))); continue
        kar = []
        for (a, b, c, e, t) in kut:
            sub = m[b:e, a:c].astype(np.uint8)
            nn, ee, ii, _ = cv2.connectedComponentsWithStats(sub, connectivity=8)
            if nn > 2:                                                   # kutudaki küçük parçalar (nokta, çizgi kırıntısı) atılır
                mx = max(ii[i, 4] for i in range(1, nn))
                for i in range(1, nn):
                    if ii[i, 4] < 0.2 * mx:
                        sub[ee == i] = 0
            kar.append(bolme.mnist_normalle(sub.astype(np.float32)))
        for j, c in enumerate(kar):
            dosya = "%s-t%02d-k%d.png" % (ad, n, j)
            Image.fromarray((c * 255).astype(np.uint8)).save(os.path.join(CIKIS, dogru[j], dosya))
            kayit.append((dogru[j] + "/" + dosya, dogru[j], ad, n, j, aciklama))
    with open(os.path.join(CIKIS, "etiketler.csv"), "w", encoding="utf-8") as f:
        f.write("dosya,sinif,foto,belirteç,kutu,not\n")
        for r in kayit:
            f.write(",".join(str(x) for x in r) + "\n")
    open(os.path.join(CIKIS, "eslesmedi.txt"), "w", encoding="utf-8").write("\n".join(es) + "\n")
    open(os.path.join(CIKIS, "hatalar.txt"), "w", encoding="utf-8").write("# gözden geçirmede yanlış çıkan dosyalar (satır başına bir ad)\n")
    p = ["<!doctype html><meta charset=utf-8><title>yeni3-rakam</title><style>body{font:14px sans-serif}figure{display:inline-block;margin:3px;text-align:center}img{width:84px;height:84px;image-rendering:pixelated;background:#000}figcaption{font-size:10px}</style>",
         "<!-- yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı. Yanlış kırpıntıyı hatalar.txt'ye yaz -->"]
    for s in SINIF:
        l = [r for r in kayit if r[1] == s]
        p.append("<h3>%s (%d)</h3>" % (s, len(l)))
        for r in l:
            p.append('<figure><img src="%s"><figcaption>%s</figcaption></figure>' % (html.escape(r[0]), html.escape(os.path.basename(r[0]))))
    open(os.path.join(CIKIS, "gozden-gecir.html"), "w", encoding="utf-8").write("\n".join(p))
    print("etiketli", len(kayit), {s: sum(1 for r in kayit if r[1] == s) for s in SINIF}); print("\n".join(es))


if __name__ == "__main__":
    main()
