# -*- coding: utf-8 -*-
"""paddle_dene.py - PaddleOCR'ı oneDNN kapalı (enable_mkldnn=False) çalıştırır; hazir-sonuc.json'a ekler.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı."""
import json, time, sys, os, traceback
sys.path.insert(0, "cihaz")
from hazir_modeller import puanla
dogru = json.load(open("ornekler/tutanak-1.dogru.json", encoding="utf-8"))["satirlar"]
r = json.load(open("cihaz/hazir-sonuc.json", encoding="utf-8"))
from paddleocr import PaddleOCR
t0 = time.time()
secenekler = [dict(enable_mkldnn=False), dict(enable_mkldnn=False, cpu_threads=4, text_detection_model_name="PP-OCRv5_mobile_det", text_recognition_model_name="PP-OCRv5_mobile_rec")]
ocr = None; kullanilan = None
for sec in secenekler:
    try:
        ocr = PaddleOCR(lang="en", use_textline_orientation=False, use_doc_orientation_classify=False, use_doc_unwarping=False, **sec)
        ocr.predict("cihaz/hucreler/satir2-temiz.png"); kullanilan = sec; break
    except Exception as e:
        print("secenek basarisiz", sec, type(e).__name__, str(e)[:160]); ocr = None
yukleme = time.time() - t0
if ocr is None:
    r["modeller"]["PaddleOCR (en)"] = {"hata": "oneDNN/PIR uyumsuzlugu (NotImplementedError ConvertPirAttribute2RuntimeAttribute); enable_mkldnn=False ile de calismadi"}
else:
    for giris in ("temiz", "gri"):
        pngler = [f"cihaz/hucreler/satir{i}-{giris}.png" for i in range(1, 9)]
        cikti = []; sure = 0.0
        for p in pngler:
            t1 = time.time()
            try:
                parca = []
                for s in ocr.predict(p):
                    dd = s if isinstance(s, dict) else getattr(s, "json", {}).get("res", {})
                    parca += list(dd.get("rec_texts", []))
                cikti.append("".join(parca))
            except Exception as e:
                cikti.append("HATA:" + type(e).__name__)
            sure += time.time() - t1
        tam, kar = puanla(cikti, dogru)
        ad = f"PaddleOCR (en, oneDNN kapalı) / {giris}"
        r["modeller"][ad] = {"cikti": cikti, "tam": tam, "karakter": round(kar, 3), "yukleme_sn": round(yukleme, 1), "hucre_sn": round(sure / 8, 2), "secenek": {k: str(v) for k, v in kullanilan.items()}}
        print(f"{ad}: tam {tam}/8 karakter {kar:.3f} hucre {sure/8:.2f}s -> {cikti}")
json.dump(r, open("cihaz/hazir-sonuc.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BITTI")
