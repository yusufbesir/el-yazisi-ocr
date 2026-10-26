# -*- coding: utf-8 -*-
# 2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: stok kodu deseni T+4/5 rakam
"""
coz.py - Kısıtlı çözümleme: hücrenin karakter olasılık matrisini P (n x 12) ve
geçerli stok kodu listesini birleştirir.
Her aday kod için log-puan = Σ log P[i][kod_i]. Uzunluk eşleşmezse (±1) bir
kutu fazla/eksik sayılır ve sabit ceza uygulanır (kutu bölme hatası payı).
Çıktı: en iyi 3 aday, güven (en iyi - ikinci, log farkı) ve durum:
"tamam" (fark >= eşik) ya da "sor" (kullanıcıya göster).
JS portu için: yalnız döngü, toplama, log; vektörleştirme gerekmiyor.
"""
import json
import re
import numpy as np

SINIFLAR = "0123456789T-"
EPS = 1e-6
CEZA_KUTU = 6.0     # fazladan kutu (kod harfine eşlenmedi): log ceza
CEZA_HARF = 6.0     # kodun bir harfi için kutu yok: log ceza
CEZA_T = 1.0        # yalnız baştaki 'T' yazılmamışsa hafif ceza (T'siz yazan yazarlar; JS ile aynı)
TIRE_IPUCU = 1.0    # geometri "tire" dediyse '-' log-puanına eklenen
TAU = 1.5          # sıcaklık: log-olasılıklar bölünür (aşırı güveni yumuşatır)
ESIK = 2.0          # en iyi - ikinci farkı (nat) bunun altındaysa "sor"
ESIK_MUTLAK = 3.0   # kısıtsız en iyi okuma ile seçilen kod arasındaki log fark (nat) bunu aşarsa "sor"
                    # (kapalı liste koruması: listede olmayan kod komşu koda oturmasın; JS ile aynı, 2026-10-25)


def ham_oku(P):
    """Kısıtsız en olası dizi."""
    return "".join(SINIFLAR[int(np.argmax(p))] for p in P)


def log_matris(P, tire_ipucu=None):
    lp = np.log(np.maximum(np.asarray(P, dtype=np.float64), EPS)) / TAU
    if tire_ipucu is not None:
        for i, t in enumerate(tire_ipucu):
            if t:
                lp[i, 11] += TIRE_IPUCU
    return lp


def kod_dizinleri(kodlar):
    """Uzunluğa göre gruplanmış (kod listesi, sınıf indeksi matrisi)."""
    gruplar = {}
    for k in kodlar:
        gruplar.setdefault(len(k), []).append(k)
    sonuc = {}
    for L, liste in gruplar.items():
        idx = np.array([[SINIFLAR.index(c) for c in k] for k in liste], dtype=np.int64)
        sonuc[L] = (liste, idx)
    return sonuc


def puanla(lp, grup):
    """lp: (n,12) log olasılık. Tüm adayların puanı: {kod: puan} dizisi olarak
    (kodlar listesi, puan vektörü)."""
    n = lp.shape[0]
    kodlar, puanlar, cezalar = [], [], []
    for L, (liste, idx) in grup.items():
        if abs(L - n) > 1:
            continue
        m = len(liste)
        ceza = 0.0
        if L == n:
            p = lp[np.arange(n)[None, :], idx].sum(1)
        elif L == n + 1:
            # kodun bir harfi için kutu yok: j. harfi atla
            en = np.full(m, -1e18)          # cezalı en iyi
            en_ceza = np.full(m, CEZA_HARF)  # o seçimin cezası
            for j in range(L):
                sol = lp[np.arange(j)[None, :], idx[:, :j]].sum(1) if j > 0 else 0.0
                sag = lp[np.arange(j, n)[None, :], idx[:, j + 1:]].sum(1) if j < n else 0.0
                # j=0 ve atlanan harf 'T' (sınıf 10) ise hafif ceza
                cz = np.where((j == 0) & (idx[:, 0] == 10), CEZA_T, CEZA_HARF)
                aday = sol + sag - cz
                daha_iyi = aday > en
                en = np.where(daha_iyi, aday, en)
                en_ceza = np.where(daha_iyi, cz, en_ceza)
            p = en
            ceza = en_ceza
        else:
            # L == n-1: bir kutu fazla: k. kutuyu atla
            en = np.full(m, -1e18)
            for k in range(n):
                sol = lp[np.arange(k)[None, :], idx[:, :k]].sum(1) if k > 0 else 0.0
                sag = lp[np.arange(k + 1, n)[None, :], idx[:, k:]].sum(1) if k < n - 1 else 0.0
                en = np.maximum(en, sol + sag)
            p = en - CEZA_KUTU
            ceza = CEZA_KUTU
        kodlar.extend(liste)
        puanlar.append(p)
        cezalar.append(np.broadcast_to(np.asarray(ceza, dtype=np.float64), (m,)).copy())
    if not puanlar:
        return [], np.zeros(0), np.zeros(0)
    return kodlar, np.concatenate(puanlar), np.concatenate(cezalar)


def stok_coz(P, grup, tire_ipucu=None, esik=ESIK):
    """P: (n,12) olasılıklar. Dönüş: sözlük
    {ham, adaylar:[(kod,puan)x3], guven, durum}."""
    ham = ham_oku(P)
    if len(P) == 0:
        return {"ham": "", "adaylar": [], "guven": 0.0, "durum": "sor"}
    lp = log_matris(P, tire_ipucu)
    kodlar, puan, ceza = puanla(lp, grup)
    if len(kodlar) == 0:
        return {"ham": ham, "adaylar": [], "guven": 0.0, "acik": 0.0, "durum": "sor"}
    ust = float(lp.max(1).sum())          # kısıtsız üst sınır (JS: ust)
    sira = np.argsort(-puan)[:3]
    adaylar = [(kodlar[i], float(puan[i])) for i in sira]
    guven = float(puan[sira[0]] - puan[sira[1]]) if len(sira) > 1 else 99.0
    acik = ust - float(puan[sira[0]] + ceza[sira[0]])
    # iki koşul birden: ikinci adaydan ayrılmış VE CNN'in kendi okumasına yakın (kapalı liste koruması)
    # Üçüncü koşul (2026-10-25, T+4 deseni sonrası): cezalı (uzunluğu tutmayan) eşleşme otomatik kabul edilmez; JS ile aynı
    durum = "tamam" if (guven >= esik and acik <= ESIK_MUTLAK and not (float(ceza[sira[0]]) > 0)) else "sor"
    return {"ham": ham, "adaylar": adaylar, "guven": guven, "acik": acik, "durum": durum}


def adet_coz(P):
    """Adet: yalnız rakamlar (T ve '-' dışlanır). Boşsa 1."""
    if len(P) == 0:
        return {"adet": 1, "ham": "", "guven": 0.0}
    P = np.asarray(P, dtype=np.float64)[:, :10]
    s = "".join(str(int(np.argmax(p))) for p in P)
    pr = P / np.maximum(P.sum(1, keepdims=True), EPS)
    guven = float(np.mean([np.max(p) for p in pr]))
    return {"adet": int(s), "ham": s, "guven": guven}


def kod_yukle(yol):
    k = json.load(open(yol, encoding="utf-8"))
    if isinstance(k, dict):
        k = k.get("kodlar") or list(k.keys())
    # yalnız biçime uyanlar: T + 4 veya 5 rakam, isteğe bağlı -2 rakam (model alfabesi)
    desen = re.compile(r"^T\d{4,5}(-\d{2})?$")
    return kod_dizinleri(sorted(set(x for x in k if desen.match(x))))
