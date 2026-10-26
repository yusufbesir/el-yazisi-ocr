# -*- coding: utf-8 -*-
"""
hiz_profil.py - paddle_motor.sayfa_oku süresini aşamalara böler (yön bulma, tablo det+rec, hücre tanıma, CNN, bölme).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait; yalnız ölçüm, motoru değiştirmez.
Kullanım: python hiz_profil.py foto.jpg [foto2 ...]   (çıktı: konsol + gece/hiz-profil.json)
"""
import os, sys, json, time, functools
AD = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.normpath(os.path.join(AD, "..", ".."))
sys.path[:0] = [os.path.join(KOK, "motor"), os.path.join(KOK, "egitim")]
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
import paddle_motor as pm, bolme

SAY = {}


def sar(nesne, ad, etiket):
    asil = getattr(nesne, ad)

    @functools.wraps(asil)
    def f(*a, **k):
        t = time.time()
        try:
            return asil(*a, **k)
        finally:
            s = SAY.setdefault(etiket, [0, 0.0]); s[0] += 1; s[1] += time.time() - t
    setattr(nesne, ad, f)


if __name__ == "__main__":
    t = time.time(); m = pm.Motor(); yukle = time.time() - t
    sar(pm.Motor, "sayfa", "paddle det+rec (sayfa)"); sar(pm.Motor, "tani", "paddle rec (hücre)")
    sar(pm, "cnn_oku", "cnn (numpy)"); sar(bolme, "sayfa_isle", "tablo bölme"); sar(pm, "yon_bul", "yön bulma (toplam)")
    kodlar = json.load(open(os.path.join(KOK, "ornekler", "stok-kodlari.json"), encoding="utf-8"))
    if isinstance(kodlar, dict):
        kodlar = list(kodlar.get("kodlar", kodlar))
    sonuc = {"yukleme_sn": round(yukle, 1), "foto": {}}
    for foto in sys.argv[1:]:
        SAY.clear(); t = time.time()
        y, _ = pm.sayfa_oku(m, foto, kodlar)
        top = time.time() - t
        sonuc["foto"][os.path.basename(foto)] = {"toplam_sn": round(top, 1), "satir": len(y["satirlar"]),
                                                 "asamalar": {k: {"adet": v[0], "sn": round(v[1], 1)} for k, v in SAY.items()},
                                                 "durumlar": [(s["stok"]["secilen"], s["stok"]["durum"]) for s in y["satirlar"]]}
        print(os.path.basename(foto), json.dumps(sonuc["foto"][os.path.basename(foto)], ensure_ascii=False), flush=True)
    json.dump(sonuc, open(os.path.join(AD, "hiz-profil.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
