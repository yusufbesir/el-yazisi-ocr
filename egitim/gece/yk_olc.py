# -*- coding: utf-8 -*-
"""
yk_olc.py - Ayrı doğrulama kümesinde YANLIŞ KABUL ölçümü (denetmen, 26.10).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait; yalnız ölçüm.
Yöntem: eğitime ve seçime girmeyen arşiv TEST bölmelerinden (EMNIST rakam test, EMNIST/T-H-E test 'T') karakterler, tutanak
benzetimiyle bozulup (gece_egit.boz, sabit tohum) stok kodu dizisine dizilir; coz.stok_coz ile çözülür.
  listede   : listeden rastgele kod -> doğru kabul / sor / YANLIŞ KABUL (başka koda)
  liste-dışı: listede olmayan, aynı desende rastgele kod -> her kabul YANLIŞ KABUL
Kullanım: python yk_olc.py model1.json [model2.json ...] [--n 600]
"""
import os, sys, json, re
import numpy as np
AD = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.normpath(os.path.join(AD, "..", ".."))
sys.path.insert(0, os.path.join(AD, ".."))
import cikarim_numpy as cn, coz
from gece_egit import boz, OB


def havuz():
    hv = {}
    for ad in ("emnist-digits-test", "emnist-harf-test", "the-test"):
        x = np.load(os.path.join(OB, ad + "_x.npy"), mmap_mode="r"); y = np.load(os.path.join(OB, ad + "_y.npy"))
        for c in "0123456789Tt":
            ii = np.nonzero(y == c)[0]
            if len(ii):
                hv.setdefault("T" if c in "Tt" else c, []).append((x, ii))
    return hv


def ciz(kod, hv, rng):
    out = []
    for c in kod:
        if c == "-":
            import veri
            out.append(veri.tire_uret(rng)); continue
        x, ii = hv[c][int(rng.integers(len(hv[c])))]
        out.append(boz(np.asarray(x[ii[int(rng.integers(len(ii)))]]), rng))
    return np.stack(out)


if __name__ == "__main__":
    a = [s for s in sys.argv[1:] if not s.startswith("--")]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 600
    kodlar = json.load(open(os.path.join(KOK, "ornekler", "stok-kodlari.json"), encoding="utf-8"))
    if isinstance(kodlar, dict):
        kodlar = list(kodlar.get("kodlar", kodlar))
    desen = re.compile(r"^T\d{4,5}(-\d{2})?$")
    kodlar = sorted({k for k in kodlar if desen.match(k)})
    kset = set(kodlar)
    grup = coz.kod_dizinleri(kodlar)
    hv = havuz()
    rng0 = np.random.default_rng(2026)
    liste = [kodlar[int(i)] for i in rng0.integers(0, len(kodlar), n)]
    disi = []
    while len(disi) < n // 2:
        k = "T" + "".join(str(int(v)) for v in rng0.integers(0, 10, int(rng0.choice([4, 5])))) + (("-%02d" % rng0.integers(1, 20)) if rng0.random() < 0.3 else "")
        if k not in kset:
            disi.append(k)
    # aynı görüntüler her model için (sabit tohum)
    rng = np.random.default_rng(7)
    G_l = [ciz(k, hv, rng) for k in liste]; G_d = [ciz(k, hv, rng) for k in disi]
    sonuc = {}
    for yol in a:
        m = cn.model_yukle(yol)
        r = {"listede": {"dogru_kabul": 0, "sor": 0, "yanlis_kabul": 0, "ilk_aday_dogru": 0, "n": n},
             "liste_disi": {"sor": 0, "yanlis_kabul": 0, "n": len(disi)}}
        for k, g in zip(liste, G_l):
            s = coz.stok_coz(cn.ileri_toplu(m, g).astype(np.float64), grup)
            ilk = s["adaylar"][0][0] if s["adaylar"] else None
            r["listede"]["ilk_aday_dogru"] += (ilk == k)
            if s["durum"] == "tamam":
                r["listede"]["dogru_kabul" if ilk == k else "yanlis_kabul"] += 1
            else:
                r["listede"]["sor"] += 1
        for k, g in zip(disi, G_d):
            s = coz.stok_coz(cn.ileri_toplu(m, g).astype(np.float64), grup)
            r["liste_disi"]["yanlis_kabul" if s["durum"] == "tamam" else "sor"] += 1
        sonuc[os.path.relpath(yol, KOK)] = r
        print(os.path.relpath(yol, KOK), json.dumps(r, ensure_ascii=False), flush=True)
    json.dump(sonuc, open(os.path.join(AD, "sabah", "yk-olcum.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
