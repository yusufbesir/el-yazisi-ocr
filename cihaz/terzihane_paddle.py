# -*- coding: utf-8 -*-
"""terzihane_paddle.py - Tadilat fişlerini (serbest el yazısı alanları) PaddleOCR ile tam sayfa okur; ham satırları kaydeder.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait; değiştirme: yalnız bu iş parçacığı."""
import sys, os, json, time, glob
from paddleocr import PaddleOCR
cikti = {}
ocr = None
for lang in ("en",):
    try:
        ocr = PaddleOCR(lang=lang, use_textline_orientation=False, use_doc_orientation_classify=False, use_doc_unwarping=False, enable_mkldnn=False)
        ocr.predict(sys.argv[1]); print("dil:", lang); break
    except Exception as e:
        print("dil basarisiz", lang, type(e).__name__, str(e)[:120]); ocr = None
for p in sys.argv[1:]:
    t = time.time(); satirlar = []
    try:
        for s in ocr.predict(p):
            d = s if isinstance(s, dict) else getattr(s, "json", {}).get("res", {})
            for m, sc in zip(d.get("rec_texts", []), d.get("rec_scores", [])):
                satirlar.append({"metin": m, "guven": round(float(sc), 2)})
    except Exception as e:
        satirlar = [{"hata": type(e).__name__ + ": " + str(e)[:200]}]
    cikti[os.path.basename(p)] = {"sure_sn": round(time.time() - t, 1), "satirlar": satirlar}
    print("==", os.path.basename(p), round(time.time() - t, 1), "sn")
    for r in satirlar: print("  ", r)
yol=os.environ.get("FIS_JSON","cihaz/terzihane-paddle.json"); eski=json.load(open(yol,encoding="utf-8")) if os.path.exists(yol) else {}; eski.update(cikti); json.dump(eski, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BITTI")



