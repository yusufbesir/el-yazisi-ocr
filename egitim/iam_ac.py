# -*- coding: utf-8 -*-
"""iam_ac.py - veri/iam-line parquet dosyalarını PNG + etiket dosyasına açar (veri/iam-line/goruntu/<bolum>/).
yazan: [Claude#WqTeinGYcW] · [İP:El yazısı OCR#RKxwbX] · 2026-10-26 · Yusuf'a ait; ham parquet'e dokunmaz, yalnız goruntu/ yazar."""
import io, os, csv, pyarrow.parquet as pq
from PIL import Image
KOK = os.path.join(os.path.dirname(__file__), "..", "veri", "iam-line")
for bolum in ("train", "validation", "test"):
    t = pq.read_table(os.path.join(KOK, "data", bolum + ".parquet")).to_pylist()
    d = os.path.join(KOK, "goruntu", bolum); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "etiketler.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["dosya", "metin"])
        for i, r in enumerate(t):
            ad = "%s-%05d.png" % (bolum, i)
            Image.open(io.BytesIO(r["image"]["bytes"])).convert("L").save(os.path.join(d, ad))
            w.writerow([ad, r["text"]])
    print(bolum, len(t))
