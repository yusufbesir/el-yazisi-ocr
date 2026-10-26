# -*- coding: utf-8 -*-
"""
yon_test.py - motor/paddle_motor.yon_bul_hizli testi (plan: docs/planlar/2026-10-26-yon-tespiti.md).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait
Çalıştırma: venv\Scripts\python.exe test\yon_test.py   (PaddleOCR gerekir; ağ kullanmaz, model yerel önbellekte)
Beklenen: "YON TEST GECTI".
"""
import os, sys
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
KOK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path[:0] = [os.path.join(KOK, "motor"), os.path.join(KOK, "egitim")]
from PIL import Image
import paddle_motor as pm

ORN = os.path.join(KOK, "ornekler")


def main():
    m = pm.Motor()
    hata = []
    t1 = Image.open(os.path.join(ORN, "tutanak-1.jpg")).convert("RGB")
    # düz görüntüyü d derece döndürünce düzeltme açısı (360-d)%360 olmalı (PIL.rotate saat yönünün tersine)
    durumlar = [("tutanak-1 %d" % d, t1.rotate(d, expand=True), (360 - d) % 360) for d in (0, 90, 180, 270)]
    for ad, beklenen in (("yeni2/ornek-4.jpg", 270), ("yeni5/y5-02.jpg", 90), ("yeni5/y5-07.jpg", 0)):
        durumlar.append((ad, Image.open(os.path.join(ORN, ad)).convert("RGB"), beklenen))
    for ad, im, beklenen in durumlar:
        r = pm.yon_bul_hizli(m, im)
        if r is None or r[0] != beklenen:
            hata.append("%s: beklenen %d, bulunan %s" % (ad, beklenen, None if r is None else r))
        else:
            print("tamam", ad, r[0], r[1].get("guven"))
    eski = pm.YON_MODELI_ACIK
    pm.YON_MODELI_ACIK = False
    if pm.yon_bul_hizli(m, t1) is not None:
        hata.append("YON_MODELI_ACIK=False iken None dönmeli")
    pm.YON_MODELI_ACIK = eski
    kucuk = Image.new("RGB", (8, 8), "white")
    try:
        pm.yon_bul_hizli(m, kucuk)   # hata fırlatmamalı (None ya da bir açı)
    except Exception as e:
        hata.append("küçük görüntü hata verdi: %r" % e)
    print("\n".join(hata) if hata else "YON TEST GECTI")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())
