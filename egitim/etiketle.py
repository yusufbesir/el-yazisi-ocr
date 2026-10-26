# -*- coding: utf-8 -*-
"""
etiketle.py - Yarı otomatik etiketleme: tutanak fotoğrafı + doğru değer JSON'u -> etiketli 28x28 karakter kırpıntıları.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

Kullanım: python etiketle.py <foto.jpg> <foto.dogru.json> [çıkış kökü=../veri/tutanak-kirpinti]
Çıktı klasörü: <kök>/<foto-adı>/  (sınıf klasörleri 0..9, T, tire; etiketler.csv; eslesmedi.txt;
gozden-gecir.html; hatalar.txt boş). Ayrıntı: veri/tutanak-kirpinti/BENIOKU.md

Ön işleme olc.py / çıkarım ile AYNI: bolme.sayfa_isle (hücre kesimi, çizgi temizleme, karakter kutuları,
mnist_normalle). Eşleme kuralı: kutu sayısı == kod uzunluğu -> soldan sağa; kutu sayısı == uzunluk-1 ve
kod 'T' ile başlıyorsa (T'siz yazılmış) baştaki T atlanır; aksi halde satır eslesmedi.txt'ye yazılır.
json'da `yazilan` alanı varsa (T'siz yazım) kutular ona göre eşlenir. Adet hücresi: tek rakamlı adet ve tek kutu ise etiketlenir.
Dosya adı: stok  <foto>-s<satır>-k<kutu>.png ; adet <foto>-s<satır>-a<kutu>.png (çakışmayı önlemek için 'a').
"""
import sys, os, json, html, re
import numpy as np
from PIL import Image
import bolme

SINIFLAR = "0123456789T-"


def klasor_adi(c):
    return "tire" if c == "-" else c


def etiketle(foto, dogru_yol, kok):
    ad = os.path.splitext(os.path.basename(foto))[0]
    cikis = os.path.join(kok, ad)
    os.makedirs(cikis, exist_ok=True)
    dogru = json.load(open(dogru_yol, encoding="utf-8"))["satirlar"]
    g, satirlar, sutunlar, sonuc = bolme.sayfa_isle(foto)
    veri = [s for s in sonuc if s["stok"]["maske"].sum() > 50][:len(dogru)]   # olc.py ile aynı eşleme
    kayit, eslesmedi = [], []
    for i, s in enumerate(veri):
        d = dogru[i]
        sira = d.get("sira", i + 1)
        if d.get("belirsiz"):
            eslesmedi.append("satır %s: atlandı (belirsiz:true)" % sira); continue
        kod = (d.get("stok") or "").strip()
        if not kod:
            eslesmedi.append("satır %s: atlandı (stok boş)" % sira); continue
        st = s["stok"]
        n = len(st["kutular"])
        yz = (d.get("yazilan") or "").strip()
        if re.fullmatch(r"[T0-9-]+", yz) and yz != kod:
            # json'da fiilen yazılan metin varsa (T'siz yazım) ona göre eşle
            if n == len(yz):
                harfler = list(yz)
            else:
                eslesmedi.append("satır %s: %s (yazılan %s) -> kutu sayısı %d, yazılan uzunluğu %d (eşleşmedi)" % (sira, kod, yz, n, len(yz)))
                harfler = None
        elif n == len(kod):
            harfler = list(kod); ofs = 0
        elif n == len(kod) - 1 and kod[0] == "T":
            harfler = list(kod[1:]); ofs = 1
        else:
            eslesmedi.append("satır %s: %s -> kutu sayısı %d, kod uzunluğu %d (eşleşmedi)" % (sira, kod, n, len(kod)))
            harfler = None
        if harfler is not None:
            for k, (h, c28) in enumerate(zip(harfler, st["karakterler"])):
                kayit.append((h, "stok", sira, k, c28))
        # adet
        a = str(d.get("adet", "")).strip()
        ak = s["adet"]["kutular"]
        if len(a) == 1 and a.isdigit() and len(ak) == 1:
            kayit.append((a, "adet", sira, 0, s["adet"]["karakterler"][0]))
        elif a:
            eslesmedi.append("satır %s: adet '%s' -> kutu sayısı %d (tek rakam/tek kutu değil)" % (sira, a, len(ak)))
    for h, kay, sira, k, c in kayit:
        os.makedirs(os.path.join(cikis, klasor_adi(h)), exist_ok=True)
    csv = ["dosya,sinif,foto,satir,kutu,kaynak"]
    sayim = {}
    for h, kay, sira, k, c in kayit:
        dosya = "%s/%s-%s%s-%s%d.png" % (klasor_adi(h), ad, "s", sira, "k" if kay == "stok" else "a", k)
        Image.fromarray((c * 255).round().astype(np.uint8)).save(os.path.join(cikis, dosya))
        csv.append("%s,%s,%s,%s,%d,%s" % (dosya, h, ad, sira, k, kay))
        sayim[h] = sayim.get(h, 0) + 1
    open(os.path.join(cikis, "etiketler.csv"), "w", encoding="utf-8", newline="").write("\n".join(csv) + "\n")
    open(os.path.join(cikis, "eslesmedi.txt"), "w", encoding="utf-8").write("\n".join(eslesmedi) + ("\n" if eslesmedi else ""))
    if not os.path.exists(os.path.join(cikis, "hatalar.txt")):
        open(os.path.join(cikis, "hatalar.txt"), "w", encoding="utf-8").write("")
    # gozden-gecir.html: saf HTML, betiksiz
    p = ["<!DOCTYPE html><html lang=\"tr\"><head><meta charset=\"utf-8\"><title>Gözden geçir: %s</title>" % html.escape(ad),
         "<!-- yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; etiketle.py üretir, elle değiştirme. -->",
         "<style>body{font-family:sans-serif;background:#eee;margin:16px}h2{margin-top:28px}"
         ".k{display:inline-block;margin:4px;text-align:center;font-size:11px;width:92px}"
         ".k img{width:84px;height:84px;image-rendering:pixelated;background:#000;display:block}</style></head><body>",
         "<h1>%s</h1><p>Yanlış etiketlenen kırpıntıların dosya adını (ör. <code>7/%s-s3-k2.png</code>) <code>hatalar.txt</code> içine satır satır yaz; eğitim bunları dışlar. Bir sınıfta o sınıfa ait olmayan kırpıntı varsa o yanlıştır.</p>" % (html.escape(ad), html.escape(ad))]
    for h in sorted(sayim, key=lambda c: SINIFLAR.index(c)):
        p.append("<h2>Sınıf %s (%d)</h2><div>" % (html.escape(h), sayim[h]))
        for hh, kay, sira, k, c in kayit:
            if hh != h:
                continue
            dosya = "%s/%s-s%s-%s%d.png" % (klasor_adi(h), ad, sira, "k" if kay == "stok" else "a", k)
            p.append("<div class=\"k\"><img src=\"%s\" alt=\"%s\">%s</div>" % (dosya, html.escape(h), html.escape(os.path.basename(dosya))))
        p.append("</div>")
    p.append("</body></html>")
    open(os.path.join(cikis, "gozden-gecir.html"), "w", encoding="utf-8").write("\n".join(p))
    print("%s: %d karakter etiketlendi; %d uyarı/atlanan; sınıf dağılımı %s" % (
        ad, len(kayit), len(eslesmedi), {c: sayim[c] for c in sorted(sayim, key=SINIFLAR.index)}))
    for e in eslesmedi:
        print("  ", e)
    return len(kayit), eslesmedi, sayim


if __name__ == "__main__":
    kok = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "tutanak-kirpinti")
    etiketle(sys.argv[1], sys.argv[2], os.path.normpath(kok))
