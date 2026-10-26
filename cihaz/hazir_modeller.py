# -*- coding: utf-8 -*-
# 2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: stok kodu deseni T+4/5 rakam
"""
hazir_modeller.py - Hazır el yazısı OCR modellerini (TrOCR, PaddleOCR, EasyOCR) tutanak hücrelerinde dener.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · eğitim amaçlı, Yusuf'a ait.
Değiştirme kuralı: yalnız bu iş parçacığındaki Claude; ölçüm sonuçları cihaz/HAZIR-MODELLER.md'ye yazılır.

Kullanım (venv içinden):
  python cihaz/hazir_modeller.py ornekler/tutanak-1.jpg ornekler/tutanak-1.dogru.json cihaz/hucreler cihaz/hazir-sonuc.json
Hücre kesimi için egitim/bolme.py kullanılır (aynı hücreler, adil karşılaştırma).
"""
import sys, os, json, time, re
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "egitim"))
import bolme  # noqa: E402

KOD = re.compile(r"T\d{4,5}(-\d{2})?")


def temizle(s):
    s = (s or "").upper().replace(" ", "").replace("—", "-").replace("–", "-")
    s = s.replace("O", "0").replace("I", "1").replace("L", "1").replace("S", "5").replace("B", "8").replace("Z", "2")
    return s


def kenarli(a, pay=24):
    return np.pad(a, pay, constant_values=255)


def hucre_png(ara, sonuc, dogru):
    """Her satır için stok hücresinin ham gri ve temiz maske PNG'lerini yazar."""
    os.makedirs(ara, exist_ok=True)
    cikis = []
    veri = [s for s in sonuc if s["stok"]["maske"].sum() > 50][:len(dogru)]
    for i, s in enumerate(veri, 1):
        gri = s["stok"].get("gri")
        maske = s["stok"]["maske"]
        temiz = (255 - (maske.astype(np.uint8) * 255))  # mürekkep siyah, zemin beyaz
        p_temiz = os.path.join(ara, f"satir{i}-temiz.png")
        Image.fromarray(kenarli(temiz).astype(np.uint8)).save(p_temiz)
        p_gri = None
        if gri is not None:
            p_gri = os.path.join(ara, f"satir{i}-gri.png")
            Image.fromarray(kenarli(np.asarray(gri)).astype(np.uint8)).save(p_gri)
        cikis.append({"sira": i, "temiz": p_temiz, "gri": p_gri})
    return cikis


def trocr_calistir(pngler, model_adi):
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    import torch
    t0 = time.time()
    proc = TrOCRProcessor.from_pretrained(model_adi)
    model = VisionEncoderDecoderModel.from_pretrained(model_adi)
    model.eval()
    yukleme = time.time() - t0
    sonuc, sure = [], 0.0
    for p in pngler:
        im = Image.open(p).convert("RGB")
        t1 = time.time()
        with torch.no_grad():
            px = proc(images=im, return_tensors="pt").pixel_values
            ids = model.generate(px, max_new_tokens=16, num_beams=3)
        metin = proc.batch_decode(ids, skip_special_tokens=True)[0]
        sure += time.time() - t1
        sonuc.append(metin)
    return sonuc, yukleme, sure / max(1, len(pngler))


def paddle_calistir(pngler):
    from paddleocr import PaddleOCR
    t0 = time.time()
    try:
        ocr = PaddleOCR(lang="en", use_textline_orientation=False, use_doc_orientation_classify=False, use_doc_unwarping=False)
        yeni = True
    except TypeError:
        ocr = PaddleOCR(lang="en", use_angle_cls=False, show_log=False)
        yeni = False
    yukleme = time.time() - t0
    sonuc, sure = [], 0.0
    for p in pngler:
        t1 = time.time()
        metin = ""
        try:
            if yeni:
                r = ocr.predict(p)
                parcalar = []
                for sayfa in r:
                    d = sayfa if isinstance(sayfa, dict) else getattr(sayfa, "json", {}).get("res", {})
                    parcalar += list(d.get("rec_texts", []))
                metin = "".join(parcalar)
            else:
                r = ocr.ocr(p, cls=False)
                metin = "".join(x[1][0] for x in (r[0] or []))
        except Exception as e:
            metin = "HATA:" + type(e).__name__
        sure += time.time() - t1
        sonuc.append(metin)
    return sonuc, yukleme, sure / max(1, len(pngler))


def easy_calistir(pngler):
    import easyocr
    t0 = time.time()
    r = easyocr.Reader(["en"], gpu=False, verbose=False)
    yukleme = time.time() - t0
    sonuc, sure = [], 0.0
    for p in pngler:
        t1 = time.time()
        try:
            metin = "".join(r.readtext(p, detail=0, allowlist="T0123456789-"))
        except Exception as e:
            metin = "HATA:" + type(e).__name__
        sure += time.time() - t1
        sonuc.append(metin)
    return sonuc, yukleme, sure / max(1, len(pngler))


def puanla(cikti, dogru):
    tam = sum(1 for c, d in zip(cikti, dogru) if temizle(c) == d["stok"])
    # karakter doğruluğu: Levenshtein
    def lev(a, b):
        dp = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            yeni = [i]
            for j, cb in enumerate(b, 1):
                yeni.append(min(dp[j] + 1, yeni[j - 1] + 1, dp[j - 1] + (ca != cb)))
            dp = yeni
        return dp[-1]
    top = sum(len(d["stok"]) for d in dogru)
    hata = sum(lev(temizle(c), d["stok"]) for c, d in zip(cikti, dogru))
    return tam, 1 - hata / top


def main(foto, dogru_yol, ara, cikis_json):
    dogru = json.load(open(dogru_yol, encoding="utf-8"))["satirlar"]
    t0 = time.time()
    g, satirlar, sutunlar, sonuc = bolme.sayfa_isle(foto)
    t_bolme = time.time() - t0
    hucreler = hucre_png(ara, sonuc, dogru)
    kume = {"temiz": [h["temiz"] for h in hucreler]}
    if all(h["gri"] for h in hucreler):
        kume["gri"] = [h["gri"] for h in hucreler]
    rapor = {"foto": foto, "bolme_sn": round(t_bolme, 2), "satir": len(hucreler), "modeller": {}}
    denemeler = [
        ("TrOCR small handwritten", lambda p: trocr_calistir(p, "microsoft/trocr-small-handwritten")),
        ("TrOCR base handwritten", lambda p: trocr_calistir(p, "microsoft/trocr-base-handwritten")),
        ("TrOCR small printed", lambda p: trocr_calistir(p, "microsoft/trocr-small-printed")),
        ("PaddleOCR (en)", paddle_calistir),
        ("EasyOCR (en, whitelist)", easy_calistir),
    ]
    for ad, fn in denemeler:
        for giris, pngler in kume.items():
            anahtar = f"{ad} / {giris}"
            try:
                cikti, yukleme, ort = fn(pngler)
                tam, kar = puanla(cikti, dogru)
                rapor["modeller"][anahtar] = {"cikti": cikti, "tam": tam, "karakter": round(kar, 3),
                                              "yukleme_sn": round(yukleme, 1), "hucre_sn": round(ort, 2)}
                print(f"{anahtar}: tam {tam}/{len(dogru)} karakter {kar:.3f} yukleme {yukleme:.1f}s hucre {ort:.2f}s -> {cikti}", flush=True)
            except Exception as e:
                rapor["modeller"][anahtar] = {"hata": f"{type(e).__name__}: {e}"[:300]}
                print(f"{anahtar}: HATA {type(e).__name__}: {e}"[:400], flush=True)
            json.dump(rapor, open(cikis_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("BITTI", cikis_json)


if __name__ == "__main__":
    main(*sys.argv[1:5])
