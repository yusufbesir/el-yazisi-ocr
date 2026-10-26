# -*- coding: utf-8 -*-
"""yeni3_kutular.py - ornekler/yeni3 fotoğraflarında PaddleOCR satır kutularını (dt_polys) ve metinlerini cihaz/yeni3-kutular.json'a yazar.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı."""
import os, sys, json, glob
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang="en", use_textline_orientation=False, use_doc_orientation_classify=False, use_doc_unwarping=False, enable_mkldnn=False)
cikti = {}
for p in sorted(glob.glob("ornekler/yeni3/*")):
    ad = os.path.basename(p); sat = []
    for s in ocr.predict(p):
        d = s if isinstance(s, dict) else getattr(s, "json", {}).get("res", {})
        for m, sc, poly in zip(d.get("rec_texts", []), d.get("rec_scores", []), d.get("dt_polys", [])):
            sat.append({"metin": m, "guven": round(float(sc), 2), "poly": [[int(x), int(y)] for x, y in poly]})
    cikti[ad] = sat; print(ad, len(sat), flush=True)
json.dump(cikti, open("cihaz/yeni3-kutular.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
