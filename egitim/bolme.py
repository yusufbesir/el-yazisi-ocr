# -*- coding: utf-8 -*-
# 2026-10-25 [Claude#RKxwbX devralan] iade formu: yedek 'gevsek' tablo yolu (tablo_bul_gevsek, SON); eski tablo_bul ve eski formlarin sonucu DEGISMEDI
# 2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: stok hucresi hedef kutu sayilari 6,9 AYNEN KALDI ([5,6,8,9] denendi, tutanak-3 yanlis kabul artti)
"""
bolme.py - Tutanak fotoğrafından Stok Kodu ve Adet hücrelerini kırpar,
hücreyi karakterlere böler ve her karakteri MNIST biçimine (28x28) getirir.

Tasarım notu: mantık saf JS'e (ES5) taşınacak şekilde basit tutuldu:
yalnız numpy dizileri, döngüler ve toplamlar. OpenCV yalnız bağlı bileşen
etiketleme için (cv2.connectedComponentsWithStats); JS'te bu iki geçişli
birleştirme (union-find) ile yazılabilir.
Çıkış biçimi: 28x28, siyah zemin (0.0), beyaz mürekkep (1.0), MNIST gibi.
"""
import sys
import numpy as np
from PIL import Image, ImageOps
import cv2  # yalnız bağlı bileşenler için

# ---------------------------------------------------------------- ayarlar
AYAR = {
    "stok_sutun": 1,      # 0 tabanlı: Sıra=0, Stok Kodu=1
    "adet_sutun": 3,      # Adet = 4. sütun
    "esik_yaricap": 25,   # uyarlamalı eşik pencere yarıçapı (piksel)
    "esik_fark": 12,      # yerel ortalamadan en az bu kadar koyu
    "satir_oran": 0.30,   # yatay çizgi: satır koyu sayısı / genişlik
    "sutun_oran": 0.40,   # dikey çizgi: sütun koyu sayısı / tablo yüksekliği
    "murekkep_mutlak": 130,  # mürekkep gri değeri bu değerden koyu olmalı
    "murekkep_fark": 25,  # ve yerel ortalamadan bu kadar koyu
    "hucre_ic_pay": 7,    # hücre çizgisinden içeri pay (piksel)
}


# ------------------------------------------------------- temel yardımcılar
def gri_yukle(yol):
    """JPEG'i EXIF yönüne göre döndürüp gri (uint8) dizi olarak yükler."""
    im = ImageOps.exif_transpose(Image.open(yol))
    return np.array(im.convert("L"))


def kutu_ortalama(a, r):
    """(2r+1)^2 pencere ortalaması; integral görüntü ile (JS'te aynı)."""
    k = 2 * r + 1
    p = np.pad(a.astype(np.float64), ((r + 1, r), (r + 1, r)), mode="edge")
    I = p.cumsum(0).cumsum(1)
    return (I[k:, k:] - I[:-k, k:] - I[k:, :-k] + I[:-k, :-k]) / (k * k)


def kumeler(profil, esik):
    """profil > esik olan ardışık aralıkları (bas, son, tepe) olarak verir."""
    sonuc = []
    bas = None
    for i in range(len(profil)):
        if profil[i] > esik and bas is None:
            bas = i
        elif profil[i] <= esik and bas is not None:
            sonuc.append((bas, i - 1, float(max(profil[bas:i]))))
            bas = None
    if bas is not None:
        sonuc.append((bas, len(profil) - 1, float(max(profil[bas:]))))
    return sonuc


def duzenli_dizi(merkezler, tol=0.08):
    """Aralıkları birbirine benzer (referans aralığın +-%8'i) en uzun ardışık
    çizgi dizisini bulur; tablo dışındaki rastgele çizgileri eler."""
    if len(merkezler) < 3:
        return list(merkezler)
    ara = [merkezler[i + 1] - merkezler[i] for i in range(len(merkezler) - 1)]
    en_iyi = []
    for ref in ara:
        blok = []
        for i in range(len(ara) + 1):
            if i < len(ara) and abs(ara[i] - ref) <= tol * ref:
                blok.append(i)
                continue
            if blok and len(blok) + 1 > len(en_iyi):
                en_iyi = [merkezler[blok[0]]] + [merkezler[j + 1] for j in blok]
            blok = []
    return en_iyi


# ------------------------------------------------------------ tablo bulma
def tablo_bul(g, ayar=AYAR):
    """Gri görüntüden satır (y) ve sütun (x) çizgi merkezlerini bulur."""
    h, w = g.shape
    koyu = g < kutu_ortalama(g, ayar["esik_yaricap"]) - ayar["esik_fark"]
    satir_profil = koyu.sum(1)
    k = kumeler(satir_profil, ayar["satir_oran"] * w)
    # sayfa kenarındaki (0-10) kümeleri at
    satirlar = [(a + b) / 2.0 for a, b, _ in k if a > 15 and b < h - 15]
    satirlar = duzenli_dizi(satirlar)
    if len(satirlar) < 3:
        raise RuntimeError("tablo satır çizgileri bulunamadı")
    y0, y1 = int(satirlar[0]), int(satirlar[-1])
    sutun_profil = koyu[y0:y1].sum(0)
    k2 = kumeler(sutun_profil, ayar["sutun_oran"] * (y1 - y0))
    sutunlar = [(a + b) / 2.0 for a, b, _ in k2 if a > 15 and b < w - 15 and b - a < 15]
    return satirlar, sutunlar


# ---------------------------------------- gevşek tablo bulma (2026-10-25, iade formu)
# Açık gri ince çizgili, hafif eğik fotoğraflar (İade ve Değişim Tutanağı: 5 sütun, 4 satır) için YEDEK yol.
# Eski tablo_bul sonuç vermezse (sütun < 5) devreye girer; eski formların sonucunu değiştirmez.
GEVSEK = {
    "esik_fark": 8,        # yerel ortalamadan en az bu kadar koyu (açık gri çizgi için 12'den düşük)
    "aci_max": 5.0,        # eğiklik taraması +-derece
    "aci_adim": 0.25,
    "cizgi_fark": 4,       # çizgi pikseli, 1B komşu ortalamasından en az bu kadar koyu
    "dikey_fark": 3,
    "form_satir": 4,
    "sablon": [0.066, 0.257, 0.320, 0.216, 0.141],   # iade formu sütun genişlikleri / tablo genişliği (ornek-6..8 ölçümü)
    "sablon_tol": 0.03,       # iade formunda 4 veri satırı
    "yatay_oran": 0.20,    # yatay çizgi: kesintisiz koyu koşu >= oran * genişlik
    "kume_oran": 0.20,     # satır kümesi: koşu piksel sayısı >= oran * genişlik
    "kalin_maks": 9,       # satır çizgisi kümesi bu kadar pikselden kalın olamaz (siyah bölüm başlığı bandı elenir)
    "sutun_oran": 0.85,    # iç dikey çizgiler: alt dizi yüksekliğinin bu oranı kadar koyu
    "kenar_oran": 0.60,    # sol/sağ kenar çizgisi (sağ kenar sık soluk)
    "min_sutun_cizgisi": 5,
    "murekkep_oran": 0.80,  # gevşek yolda mürekkep mutlak eşiği = oran * tablo ortanca parlaklığı
    "murekkep_fark": 15,
        "tol": 0.12,
}


def _kosu_filtre(maske, uzunluk, eksen, bosluk=0):
    """Bir eksen boyunca (1: yatay, 0: dikey) ardışık `uzunluk` pikselden kısa koşuları siler (morfolojik açma).
    bosluk: en çok bu kadar piksellik kopukluk önce kapatılır (JPEG gürültüsüyle kopan açık gri çizgi için).
    JS'te aynı sonuç koşu taraması döngüsüyle (kopukluk birleştirme + uzunluk süzgeci) yazılır."""
    m = maske.astype(np.uint8)
    if eksen == 0:
        m = m.T.copy()
    if bosluk > 0:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((1, bosluk + 1), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((1, max(1, int(uzunluk))), np.uint8))
    m = m.astype(bool)
    return m if eksen == 1 else m.T


def egiklik_bul(koyu, ay=GEVSEK):
    """Koyu piksellerin satır profili en keskin olan açı (derece). Pozitif: görüntü saat yönü tersine döndürülür."""
    ys, xs = np.nonzero(koyu)
    if len(ys) > 300000:
        i = np.random.RandomState(0).choice(len(ys), 300000, replace=False)
        ys, xs = ys[i], xs[i]
    w = koyu.shape[1]
    en_iyi = (-1.0, 0.0)
    for a in np.arange(-ay["aci_max"], ay["aci_max"] + 1e-9, ay["aci_adim"]):
        t = np.tan(np.radians(a))
        yy = np.round(ys - xs * t).astype(np.int64) + int(abs(w * t)) + 1
        p = np.bincount(yy).astype(np.float64)
        s = float((p * p).sum())
        if s > en_iyi[0] + 1e-9:
            en_iyi = (s, float(a))
    return en_iyi[1]


def dondur_gri(g, aci, bos=255):
    """Gri (ya da RGB) görüntüyü merkez etrafında `aci` derece döndürür (cv2 yönü). aci=0 ise aynen."""
    if abs(aci) < 1e-9:
        return g
    h, w = g.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), aci, 1.0)
    return cv2.warpAffine(g, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(bos if g.ndim == 2 else (bos,) * g.shape[2]))


def kutu_ort_1d(a, r, eksen):
    """Tek eksende (2r+1) pencere ortalaması (eksen 0: dikey, 1: yatay). Açık gri çizgi, KOMŞULARINA göre koyu aranır."""
    k = 2 * r + 1
    pad = [(r + 1, r) if i == eksen else (0, 0) for i in range(2)]
    I = np.pad(a.astype(np.float64), pad, mode="edge").cumsum(eksen)
    n = a.shape[eksen]
    ust = [slice(k, k + n) if i == eksen else slice(None) for i in range(2)]
    alt = [slice(0, n) if i == eksen else slice(None) for i in range(2)]
    return (I[tuple(ust)] - I[tuple(alt)]) / k


def zincirler(merkez, tol, min_aralik):
    """Düzenli aralıklı çizgi zincirleri; en çok 1 eksik çizgi arka arkaya araya konabilir. [(gözlenen_sayı, [konumlar])] çoktan aza."""
    sonuc = {}
    n = len(merkez)
    refler = set()
    for i in range(n - 1):
        d = merkez[i + 1] - merkez[i]
        if d >= min_aralik:
            refler.add(round(d, 1))
        if i + 2 < n and (merkez[i + 2] - merkez[i]) / 2.0 >= min_aralik:
            refler.add(round((merkez[i + 2] - merkez[i]) / 2.0, 1))
    for ref in refler:
        for i in range(n):
            zin, gozlem, son = [merkez[i]], 1, merkez[i]
            while True:
                bulundu = None
                for c in merkez:
                    if c > son + 0.5 * ref and abs(c - son - ref) <= tol * ref:
                        bulundu = (c, False); break
                    if c > son + 0.5 * ref and abs(c - son - 2 * ref) <= tol * ref:
                        bulundu = (c, True); break
                if not bulundu:
                    break
                c, atla = bulundu
                if atla:
                    zin.append(son + (c - son) / 2.0)
                zin.append(c); gozlem += 1; son = c
            if gozlem >= 3:
                sonuc[tuple(round(z, 1) for z in zin)] = gozlem
    return sorted(((g, list(z)) for z, g in sonuc.items()), key=lambda t: (-t[0], -len(t[1])))


def sablon_sutun(cl, gv=GEVSEK):
    """cl: [(x, destek)] dikey çizgi adayları (destek: çizgi koyu oranı 0..1). İade formunun 6 sütun çizgisini (5 sütun)
    göreli genişlik şablonuna göre seçer: iç 4 çizgi tam (>= sutun_oran), kenar 2 çizgi >= kenar_oran destekli olmalı. Yoksa None."""
    sb = gv["sablon"]
    for i in range(len(cl) - len(sb)):
        pencere = cl[i:i + len(sb) + 1]
        xs = [c[0] for c in pencere]
        gen = xs[-1] - xs[0]
        if gen < 300:
            continue
        if not all(abs((xs[k + 1] - xs[k]) / gen - sb[k]) <= gv["sablon_tol"] for k in range(len(sb))):
            continue
        if all(c[1] >= gv["sutun_oran"] for c in pencere[1:-1]):
            return xs
    return None


def tablo_bul_gevsek(g, ayar=AYAR, gv=GEVSEK):
    """Dönüş: (döndürülmüş gri, aci, satirlar, sutunlar). Bulunamazsa RuntimeError.
    Adımlar: eğiklik düzelt; çizgileri komşu piksele göre (1B) koyu ara; yatay koşu süzgeci + düzenli aralıklı zincirler;
    zincirin DİKEY çizgilerle desteklenen alt dizisi tablodur (paragraf satırlarından oluşan sahte zincirleri eler)."""
    h, w = g.shape
    ort = kutu_ortalama(g, ayar["esik_yaricap"])
    aci = egiklik_bul(g < ort - gv["esik_fark"], gv)
    r = dondur_gri(g, aci)
    cy = r < kutu_ort_1d(r, 6, 0) - gv["cizgi_fark"]
    cx = r < kutu_ort_1d(r, 6, 1) - gv["dikey_fark"]
    cx = cx | np.roll(cx, 1, 1) | np.roll(cx, -1, 1)          # dalgalı dikey çizgi: +-1 px tolerans
    yat = _kosu_filtre(cy, int(gv["yatay_oran"] * w), 1, 3)
    profil = yat.sum(1)
    k = [(a, b) for a, b, _ in kumeler(profil, gv["kume_oran"] * w) if b - a + 1 <= gv["kalin_maks"] and a > 15 and b < h - 15]
    merkez = [(a + b) / 2.0 for a, b in k]
    zs = zincirler(merkez, gv["tol"], 0.012 * h)
    if not zs:
        raise RuntimeError("tablo satır çizgileri bulunamadı (gevşek)")
    en_iyi = None   # (destek, zincir, aralik, sutunlar)
    for gozlem, z in zs[:12]:
        aralik = (z[-1] - z[0]) / (len(z) - 1)
        if aralik < 0.012 * h:
            continue
        dik = _kosu_filtre(cx, max(8, int(0.8 * aralik)), 0, 3)
        for i in range(len(z) - 2):
            for j in range(i + 2, len(z)):
                y0, y1 = int(z[i]), int(z[j])
                cp = dik[y0:y1].sum(0)
                cl = [((a_ + b_) / 2.0, t_ / float(y1 - y0)) for a_, b_, t_ in kumeler(cp, gv["kenar_oran"] * (y1 - y0)) if b_ - a_ < 12 and a_ > 0.04 * w]
                sut = sablon_sutun(cl, gv)
                if sut is None:
                    continue
                dest = min(c[1] for c in cl if c[0] in sut[1:-1])
                if en_iyi is None or (dest, j - i) > en_iyi[:1] + (en_iyi[4],):
                    en_iyi = (dest, z, aralik, sut, j - i)
    if en_iyi is None:
        raise RuntimeError("tablo sütunları bulunamadı (gevşek)")
    _, z, aralik, sutunlar, _ = en_iyi
    # tablonun üst/alt sınırı: iç dikey çizgilerin en uzun kesintisiz koşusunun ortancası (başlık satırı dahil)
    dik = _kosu_filtre(cx, max(8, int(0.8 * aralik)), 0, 3)
    ust, alt = [], []
    for x in sutunlar[1:-1]:
        ys = np.nonzero(dik[:, max(0, int(x) - 2):int(x) + 3].any(1))[0]
        if len(ys) == 0:
            continue
        bol = np.split(ys, np.nonzero(np.diff(ys) > 6)[0] + 1)
        en = max(bol, key=len)
        ust.append(en.min()); alt.append(en.max())
    if not ust:
        raise RuntimeError("tablo sınırı bulunamadı (gevşek)")
    ytop, ybot = float(np.median(ust)), float(np.median(alt))
    gozlenen = sorted(set(list(merkez) + list(z)))
    sat = [ytop]
    for c in gozlenen:
        if ytop + 0.5 * aralik < c < ybot - 0.5 * aralik and c - sat[-1] > 0.6 * aralik:
            sat.append(c)
    if ybot - sat[-1] > 0.6 * aralik:
        sat.append(ybot)
    else:
        sat[-1] = ybot
    if len(sat) < 3:
        raise RuntimeError("tablo satır sayısı yetersiz (gevşek)")
    return r, aci, sat, sutunlar


def sutun_ata(n_cizgi, ayar=AYAR):
    """Sütun çizgisi sayısına göre (stok, adet) sütun indisi. 6 çizgi = iade formu (Sıra|Barkod|Ürün|Beden/Renk|Miktar)."""
    if n_cizgi == 6:
        return 1, 4
    return ayar["stok_sutun"], ayar["adet_sutun"]


# Son sayfa_isle çağrısının bilgisi (motor, rengi aynı açıyla döndürmek ve sütunları bilmek için)
SON = {"baslik": False, "aci": 0.0, "stok_sutun": AYAR["stok_sutun"], "adet_sutun": AYAR["adet_sutun"], "yol": "eski"}


def murekkep_maskesi(g, ayar=AYAR):
    """Mürekkep: hem mutlak koyu hem yerel ortalamadan belirgin koyu.
    Gri ince tablo çizgileri ve açık gri filigran bu eşikte elenir."""
    yerel = kutu_ortalama(g, ayar["esik_yaricap"])
    return (g < ayar["murekkep_mutlak"]) & (g < yerel - ayar["murekkep_fark"])


def hucre_kirp(g, satirlar, sutunlar, satir_no, sutun_no, ayar=AYAR):
    """satir_no, sutun_no (0 tabanlı, başlık satırı dahil değil: satir_no=0
    ilk veri satırı). Hücrenin gri kırpıntısını ve mürekkep maskesini verir."""
    pay = ayar["hucre_ic_pay"]
    y0 = int(satirlar[satir_no]) + pay
    y1 = int(satirlar[satir_no + 1]) - pay
    x0 = int(sutunlar[sutun_no]) + pay
    x1 = int(sutunlar[sutun_no + 1]) - pay
    return g[y0:y1, x0:x1]


def cizgi_temizle(m):
    """Maskeden uzun yatay/dikey koşuları siler (kalan tablo çizgisi parçaları).
    Yatay koşu > genişliğin %55'i, dikey koşu > yüksekliğin %85'i."""
    h, w = m.shape
    m = m.copy()
    for y in range(h):
        x = 0
        while x < w:
            if m[y, x]:
                s = x
                while x < w and m[y, x]:
                    x += 1
                if x - s > 0.55 * w:
                    m[y, s:x] = False
            else:
                x += 1
    for x in range(w):
        y = 0
        while y < h:
            if m[y, x]:
                s = y
                while y < h and m[y, x]:
                    y += 1
                if y - s > 0.85 * h:
                    m[s:y, x] = False
            else:
                y += 1
    return m


# --------------------------------------------------------- karakter bölme
def karakter_kutulari(m, hedefler=None):
    """Maskeden karakter kutuları: [(x0,y0,x1,y1,tire_mi), ...] soldan sağa.
    1) Bağlı bileşenler (8 komşuluk). 2) Çok küçük gürültü atılır.
    3) Yatayda belirgin örtüşenler birleştirilir. 4) Geniş-basık => tire adayı."""
    h, w = m.shape
    n, etiket, ist, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    kutular = []
    for i in range(1, n):
        x, y, bw, bh, alan = ist[i]
        # gürültü: küçük alan ve küçük boy
        if alan < 0.004 * h * h or (bh < 0.18 * h and bw < 0.18 * h):
            continue
        kutular.append([x, y, x + bw, y + bh, int(alan)])
    # benek: bileşen alanları medyanının %5'inden küçük, tire biçiminde olmayanlar
    if kutular:
        alanlar = sorted(k[4] for k in kutular)
        med = alanlar[len(alanlar) // 2]
        kutular = [k for k in kutular
                   if k[4] >= 0.05 * med or (k[2] - k[0]) >= 1.6 * (k[3] - k[1])]
    kutular = [k[:4] for k in kutular]
    kutular.sort()
    # yatay örtüşenleri birleştir (dar kutunun %50'sinden fazlası örtüşüyorsa)
    birlesik = []
    for k in kutular:
        if birlesik:
            p = birlesik[-1]
            ort = min(p[2], k[2]) - max(p[0], k[0])
            dar = min(p[2] - p[0], k[2] - k[0])
            if ort > 0.5 * dar:
                p[0] = min(p[0], k[0]); p[1] = min(p[1], k[1])
                p[2] = max(p[2], k[2]); p[3] = max(p[3], k[3])
                continue
        birlesik.append(list(k))
    if hedefler:
        birlesik = genis_bol(m, birlesik, hedefler)
    sonuc = []
    for x0, y0, x1, y1 in birlesik:
        bw, bh = x1 - x0, y1 - y0
        tire = bw >= 1.6 * bh and bh < 0.30 * h
        sonuc.append((x0, y0, x1, y1, bool(tire)))
    return sonuc


def genis_bol(m, kutular, hedefler, oran=0.9):
    """Birbirine değen karakterler tek bileşen olur. Kutu genişliği yüksekliğin
    `oran` katından büyükse (ilk kutu 'T' çubuğu geniştir: 1.9 kat) ve toplam
    kutu sayısı hedeflerden (5, 6, 8 veya 9 karakter; 2026-10-25 T+4 rakam deseni [Claude#RKxwbX], eskiden 6/9) birine ulaşmamışsa, ortadaki %35-65 aralığında dikey
    izdüşümün en az olduğu sütundan ikiye böler. Tekrarlanır."""
    kutular = [list(k) for k in kutular]
    degisti = True
    while degisti and len(kutular) not in hedefler and len(kutular) < max(hedefler):
        degisti = False
        # en geniş/yüksek oranlı adayı seç
        en_iyi, en_r = -1, 0.0
        for i, (x0, y0, x1, y1) in enumerate(kutular):
            r = (x1 - x0) / float(max(1, y1 - y0))
            sinir = 1.9 if i == 0 else oran
            if r > sinir and r > en_r and (x1 - x0) >= 24:
                en_iyi, en_r = i, r
        if en_iyi < 0:
            break
        x0, y0, x1, y1 = kutular[en_iyi]
        izd = m[y0:y1, x0:x1].sum(0).astype(np.float64)
        w = x1 - x0
        a, b = int(0.35 * w), max(int(0.35 * w) + 1, int(0.65 * w))
        # 3 sütunluk ortalamayla yumuşat, en az olanı al
        duz = np.convolve(izd, np.ones(3) / 3.0, mode="same")
        kes = a + int(np.argmin(duz[a:b]))
        sol, sag = m[y0:y1, x0:x0 + kes], m[y0:y1, x0 + kes:x1]
        parcalar = []
        for xo, p in ((x0, sol), (x0 + kes, sag)):
            ys = np.nonzero(p.sum(1))[0]
            if len(ys) == 0:
                continue
            parcalar.append([xo, y0 + int(ys.min()), xo + p.shape[1], y0 + int(ys.max()) + 1])
        if len(parcalar) < 2:
            break
        kutular[en_iyi:en_iyi + 1] = parcalar
        degisti = True
    return kutular


# --------------------------------------------- MNIST biçimine normalleştirme
def alan_agirliklari(n_kaynak, n_hedef):
    """Alan ortalamalı yeniden örnekleme ağırlık matrisi (n_hedef x n_kaynak)."""
    A = np.zeros((n_hedef, n_kaynak), dtype=np.float64)
    oran = n_kaynak / float(n_hedef)
    for i in range(n_hedef):
        b, s = i * oran, (i + 1) * oran
        for j in range(int(b), min(int(np.ceil(s)), n_kaynak)):
            A[i, j] = min(s, j + 1) - max(b, j)
        A[i] /= max(A[i].sum(), 1e-9)
    return A


def mnist_normalle(a, kutu=20, tuval=28):
    """a: 2B dizi (0..1, mürekkep yüksek). En-boy korunarak en uzun kenar
    20 piksele ölçeklenir, 28x28'e konur, ağırlık merkezi (28/2, 28/2)'e
    tamsayı kaydırmayla getirilir."""
    ys, xs = np.nonzero(a > 0.05)
    if len(ys) == 0:
        return np.zeros((tuval, tuval), dtype=np.float32)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float64)
    h, w = a.shape
    olcek = float(kutu) / max(h, w)
    h2 = max(1, int(round(h * olcek)))
    w2 = max(1, int(round(w * olcek)))
    k = alan_agirliklari(h, h2).dot(a).dot(alan_agirliklari(w, w2).T)
    cikis = np.zeros((tuval, tuval), dtype=np.float64)
    oy, ox = (tuval - h2) // 2, (tuval - w2) // 2
    cikis[oy:oy + h2, ox:ox + w2] = k
    toplam = cikis.sum()
    if toplam > 0:
        yy, xx = np.mgrid[0:tuval, 0:tuval]
        cy, cx = (cikis * yy).sum() / toplam, (cikis * xx).sum() / toplam
        dy, dx = int(round(tuval / 2.0 - 0.5 - cy)), int(round(tuval / 2.0 - 0.5 - cx))
        yeni = np.zeros_like(cikis)
        # kaydırma: kaynak [y,x] -> hedef [y+dy,x+dx]; taşan kısım kesilir
        ys0, ys1 = max(0, -dy), min(tuval, tuval - dy)
        xs0, xs1 = max(0, -dx), min(tuval, tuval - dx)
        if ys1 > ys0 and xs1 > xs0:
            yeni[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = cikis[ys0:ys1, xs0:xs1]
        cikis = yeni
    return np.clip(cikis, 0, 1).astype(np.float32)


def karakterleri_cikar(m, kutular):
    """Her kutudaki maske parçasını MNIST biçimine getirir: (N,28,28)."""
    cikti = []
    for x0, y0, x1, y1, tire in kutular:
        cikti.append(mnist_normalle(m[y0:y1, x0:x1].astype(np.float32)))
    if not cikti:
        return np.zeros((0, 28, 28), dtype=np.float32)
    return np.stack(cikti)


# ----------------------------------------------------------- uçtan uca
def sayfa_isle(yol, ayar=AYAR):
    """Tüm sayfa: her veri satırı için stok ve adet hücresi sonuçları."""
    g = gri_yukle(yol)
    SON.update({"aci": 0.0, "stok_sutun": ayar["stok_sutun"], "adet_sutun": ayar["adet_sutun"], "yol": "eski"})
    try:
        satirlar, sutunlar = tablo_bul(g, ayar)
        if len(sutunlar) < max(ayar["stok_sutun"], ayar["adet_sutun"]) + 2:
            raise RuntimeError("tablo sütunları bulunamadı (%d çizgi)" % len(sutunlar))
    except RuntimeError as e_eski:
        try:
            g, aci, satirlar, sutunlar = tablo_bul_gevsek(g, ayar)
        except RuntimeError as e_yeni:
            raise RuntimeError("%s | %s" % (e_eski, e_yeni))
        sn_s, sn_a = sutun_ata(len(sutunlar), ayar)
        if max(sn_s, sn_a) + 1 >= len(sutunlar):
            raise RuntimeError("tablo sütun sayısı uyumsuz (%d çizgi)" % len(sutunlar))
        SON.update({"aci": aci, "stok_sutun": sn_s, "adet_sutun": sn_a, "yol": "gevsek"})
        # loş fotoğraf (sayfa ~218) ve açık renk mürekkep: mutlak eşik sayfa parlaklığına göre (%80), fark 15
        sayfa_med = float(np.median(g[int(satirlar[0]):int(satirlar[-1]), int(sutunlar[0]):int(sutunlar[-1])]))
        ayar = dict(ayar, stok_sutun=sn_s, adet_sutun=sn_a, murekkep_mutlak=int(GEVSEK["murekkep_oran"] * sayfa_med), murekkep_fark=GEVSEK["murekkep_fark"])
    mur = murekkep_maskesi(g, ayar)
    pay = ayar["hucre_ic_pay"]
    # ilk aralık başlık satırı olabilir: başlık yüksekliği diğerlerinden büyükse atla
    ara = [satirlar[i + 1] - satirlar[i] for i in range(len(satirlar) - 1)]
    sonuc = []
    baslik = False
    if SON["yol"] == "gevsek" and len(satirlar) >= 4:
        # iade formunda başlık bandı veri satırından ince (~%80): ilk aralık belirgin kısaysa başlıktır, veri satırı sayılmaz
        diger = sorted(ara[1:])
        baslik = ara[0] < 0.92 * diger[len(diger) // 2]
    SON["baslik"] = baslik
    for r in range(len(satirlar) - 1):
        if baslik and r == 0:
            continue
        satir = {"satir": r, "y0": satirlar[r], "y1": satirlar[r + 1]}
        for ad, sn in (("stok", ayar["stok_sutun"]), ("adet", ayar["adet_sutun"])):
            y0 = int(satirlar[r]) + pay; y1 = int(satirlar[r + 1]) - pay
            x0 = int(sutunlar[sn]) + pay; x1 = int(sutunlar[sn + 1]) - pay
            m = cizgi_temizle(mur[y0:y1, x0:x1])
            kut = karakter_kutulari(m, (6, 9) if ad == "stok" else None)
            satir[ad] = {
                "gri": g[y0:y1, x0:x1], "maske": m, "kutular": kut,
                "karakterler": karakterleri_cikar(m, kut),
            }
        sonuc.append(satir)
    return g, satirlar, sutunlar, sonuc


if __name__ == "__main__":
    import json, os
    yol = sys.argv[1]
    cikis = sys.argv[2]
    dogru = json.load(open(sys.argv[3], encoding="utf-8"))["satirlar"] if len(sys.argv) > 3 else None
    os.makedirs(cikis, exist_ok=True)
    g, satirlar, sutunlar, sonuc = sayfa_isle(yol)
    print("satır çizgileri:", [int(s) for s in satirlar])
    print("sütun çizgileri:", [int(s) for s in sutunlar])
    # ilk aralık (başlık) hariç veri satırları: stok sütununda mürekkep olanlar
    veri = [s for s in sonuc if s["stok"]["maske"].sum() > 50]
    print("mürekkepli satır:", len(veri))
    for i, s in enumerate(veri):
        for ad in ("stok", "adet"):
            Image.fromarray((~s[ad]["maske"]).astype(np.uint8) * 255).save("%s/s%d_%s_maske.png" % (cikis, i + 1, ad))
            Image.fromarray(s[ad]["gri"]).save("%s/s%d_%s_gri.png" % (cikis, i + 1, ad))
            for j, c in enumerate(s[ad]["karakterler"]):
                Image.fromarray((c * 255).astype(np.uint8)).save("%s/s%d_%s_k%d.png" % (cikis, i + 1, ad, j))
        bek = len(dogru[i]["stok"]) if dogru else None
        tire = [k[4] for k in s["stok"]["kutular"]]
        print("satır %d: stok kutu=%d beklenen=%s %s | adet kutu=%d tire=%s" % (
            i + 1, len(s["stok"]["kutular"]), bek,
            "OK" if bek == len(s["stok"]["kutular"]) else "YANLIŞ",
            len(s["adet"]["kutular"]), "".join("-" if t else "." for t in tire)))
