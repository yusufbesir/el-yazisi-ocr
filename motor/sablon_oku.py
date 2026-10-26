# -*- coding: utf-8 -*-
"""
sablon_oku.py - Tablo çizgisi bulunamayan tutanak fotoğraflarını FORM ŞABLONUNA göre okur (çizgisiz yedek yol).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait; değiştirme: yalnız bu iş parçacığı

Neden: eğik/gölgeli çekimlerde (yeni5 sponsorluk tutanakları) bolme.py tablo çizgilerini bulamıyor ve hiç satır okunmuyordu.
Yöntem: tam sayfa PaddleOCR metin kutuları -> başlık satırı (Sıra, Stok Kodu, Ürün Açıklaması, Renk, Beden, Adet, Fiyat, Tutar)
  bulunur -> eğiklik başlık kutularından düzeltilir -> sütun sınırları başlık merkezlerinin ortası -> başlık altındaki kutular
  satırlara kümelenir ("toplam / teslim eden / imza" satırında durur).
Form tanımı (Yusuf kuralı, TAARNAK web/uygulama.js TESLIM_SUTUNLARI / IADE_SUTUNLARI): renk ve beden AYRI alan.
Güvenlik: bu yolda CNN uzlaşması yok; stok kodu yalnız listedekiyle BİREBİR (mesafe 0) ve güven >= 0.90 ise kabul, aksi "sor".
"""
import re
import numpy as np

SUTUN_ANAHTAR = [  # (alan, eşleşen sözcük kökleri) — sıra önemli değil, eşleşme başlık metninde aranır
    ("sira", ("sira",)), ("stok", ("stok", "kod")), ("aciklama", ("aciklama", "urun")), ("renk", ("renk",)),
    ("beden", ("beden",)), ("teslim_no", ("teslim no",)), ("teslim_tarihi", ("teslim tarih",)),
    ("adet", ("adet", "miktar")), ("fiyat", ("fiyat",)), ("tutar", ("tutar",)),
]
BITIS = re.compile(r"toplam|teslim eden|teslim alan|imza|kase|onay", re.I)


def duz(s):
    t = (s or "").lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("i̇", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ç", "c"), ("â", "a")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def baslik_bul(kutular):
    """Başlık kutuları: {alan: (cx, cy, h)}. En az 3 alan aynı yatay bantta olmalı (stok ve adet şart)."""
    aday = []
    for k in kutular:
        m = duz(k[4])
        for alan, kokler in SUTUN_ANAHTAR:
            if any(x in m for x in kokler):
                # "teslim no/tarih" iade sütunu; "teslim eden/alan" imza bölümüdür, başlık değil
                if alan == "stok" and "teslim" in m:
                    continue
                aday.append((alan, (k[0] + k[2]) / 2, (k[1] + k[3]) / 2, k[3] - k[1], k))
                break
    if not aday:
        return None
    en_iyi = None
    for _, _, cy, h, _ in aday:
        bant = [a for a in aday if abs(a[2] - cy) <= max(h, 12) * 1.5]
        alanlar = {}
        for a in bant:
            alanlar.setdefault(a[0], a)
        # stok şart; adet sütunu olmayan sade tutanak (y5-10: Sıra | Stok | Açıklama | Fiyat) için en az 3 başlık yeter
        if "stok" in alanlar and len(alanlar) >= 3:
            if en_iyi is None or len(alanlar) > len(en_iyi):
                en_iyi = alanlar
    return en_iyi


def oku(motor, rgb, kodlar, stok_karar, adet_karar, lev, temizle):
    """Dönüş (satirlar_listesi, ek_listesi, bilgi) ya da None (başlık bulunamadı)."""
    kut = motor.sayfa(rgb)
    bas = baslik_bul(kut)
    if not bas:
        return None
    # eğiklik: başlık merkezlerinden doğru (y = a*x + b); koordinatları -açı kadar döndür
    xs = np.array([v[1] for v in bas.values()]); ys = np.array([v[2] for v in bas.values()])
    a = float(np.polyfit(xs, ys, 1)[0]) if len(xs) >= 2 and np.ptp(xs) > 50 else 0.0
    c, s = 1 / np.sqrt(1 + a * a), a / np.sqrt(1 + a * a)

    def dondur(x, y):
        return x * c + y * s, -x * s + y * c
    sut = sorted(((dondur(v[1], v[2])[0], alan) for alan, v in bas.items()))
    sinir = [(sut[i][0] + sut[i + 1][0]) / 2 for i in range(len(sut) - 1)]
    bas_y = float(np.median([dondur(v[1], v[2])[1] for v in bas.values()]))
    bas_h = float(np.median([v[3] for v in bas.values()]))
    baslik_kutulari = {id(v[4]) for v in bas.values()}
    govde = []
    for k in kut:
        if id(k) in baslik_kutulari:
            continue
        x, y = dondur((k[0] + k[2]) / 2, (k[1] + k[3]) / 2)
        if y > bas_y + bas_h * 0.6:
            govde.append((y, x, k))
    govde.sort(key=lambda t: t[0])
    # satır kümeleme
    hs = [g[2][3] - g[2][1] for g in govde] or [bas_h]
    tol = max(8.0, float(np.median(hs)) * 0.6)
    satirlar, son_y = [], None
    for y, x, k in govde:
        if son_y is None or y - son_y > tol:
            satirlar.append([])
        satirlar[-1].append((x, k)); son_y = y
    liste, ek, sira = [], [], 0
    for sat in satirlar:
        metin_satir = " ".join(k[4] for _, k in sat)
        if BITIS.search(duz(metin_satir)):
            break
        hucre = {}
        for x, k in sorted(sat, key=lambda t: t[0]):
            i = sum(1 for b in sinir if x > b)
            hucre.setdefault(sut[i][1], []).append(k)
        def metin(alan):
            L = hucre.get(alan, [])
            return (" ".join(k[4] for k in L), min((k[5] for k in L), default=0.0))
        sm, sg = metin("stok")
        if sum(ch.isdigit() for ch in sm) < 2:
            continue   # stok hücresinde kod yok: boş satır ya da tablo dışı yazı
        sira += 1
        stok, d1, d2 = stok_karar(sm, sg, kodlar)
        stok["kaynak"] = "sablon"
        stok["cnn"] = {"secilen": None, "guven": 0.0}
        stok["uzlasma"] = False
        if stok["durum"] == "kabul" and not (d1 == 0 and sg >= 0.90):
            stok["durum"] = "sor"   # CNN uzlaşması olmayan yolda yalnız birebir ve yüksek güvenli kabul
        am, ag = metin("adet")
        adet = adet_karar(am, ag) if am.strip() else adet_karar("", 1.0)
        adet["kaynak"] = "sablon"; adet["cnn"] = {"deger": None, "guven": 0.0}; adet["uzlasma"] = False
        if adet["durum"] == "kabul" and ag < 0.90:
            adet["durum"] = "sor"
        satir = {"sira": sira, "kaynak": "sablon", "stok": stok, "adet": adet,
                 "aciklama": metin("aciklama")[0], "renk": metin("renk")[0], "beden": metin("beden")[0]}
        for ekalan in ("teslim_no", "teslim_tarihi", "fiyat", "tutar"):
            if ekalan in bas:
                satir[ekalan] = metin(ekalan)[0]
        L = hucre.get("stok", [])
        satir["hucreKutusu"] = [int(min(k[0] for k in L)), int(min(k[1] for k in L)), int(max(k[2] for k in L)), int(max(k[3] for k in L))]
        A = hucre.get("adet", [])
        satir["adetKutusu"] = [int(min(k[0] for k in A)), int(min(k[1] for k in A)), int(max(k[2] for k in A)), int(max(k[3] for k in A))] if A else None
        liste.append(satir)
        ek.append({"cnn": stok["cnn"], "uzlasma": False, "adet_murekkep": 100 if am.strip() else 0, "gri": None, "temiz": None,
                   "sayfa": (sm, sg), "kaynak": "sablon", "d1": d1, "d2": d2})
    return liste, ek, {"egiklik": round(float(np.degrees(np.arctan(a))), 2), "basliklar": [al for _, al in sut]}
