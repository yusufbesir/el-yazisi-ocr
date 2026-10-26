# -*- coding: utf-8 -*-
"""model_kaynak_kaydi.py - İndirilen hazır modellerin kaynak, sürüm (HF commit) ve SHA-256 kaydını üretir.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait; değiştirme: yalnız bu iş parçacığı."""
import os, hashlib, json, glob, sys
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
kayit = {"not": "SHA-256 bu makinedeki dosyalar üzerinden hesaplandı; kaynak adresleri HF/Paddle resmi depoları.", "modeller": []}
hf = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
for ad in ["microsoft/trocr-small-handwritten", "microsoft/trocr-base-handwritten", "microsoft/trocr-small-printed"]:
    kl = os.path.join(hf, "models--" + ad.replace("/", "--"))
    ref = os.path.join(kl, "refs", "main")
    commit = open(ref).read().strip() if os.path.exists(ref) else None
    dosyalar = []
    snap = os.path.join(kl, "snapshots", commit) if commit else None
    if snap and os.path.isdir(snap):
        for p in sorted(glob.glob(os.path.join(snap, "*"))):
            rp = os.path.realpath(p)
            if os.path.isfile(rp): dosyalar.append({"dosya": os.path.basename(p), "bayt": os.path.getsize(rp), "sha256": sha(rp)})
    kayit["modeller"].append({"ad": ad, "kaynak": "https://huggingface.co/" + ad, "lisans": "MIT", "hf_commit": commit, "yukleme": "transformers from_pretrained (safetensors; torch.load ile dış .pt açılmadı)", "dosyalar": dosyalar})
px = os.path.join(os.path.expanduser("~"), ".paddlex", "official_models")
if os.path.isdir(px):
    for m in sorted(os.listdir(px)):
        dosyalar = []
        for p in sorted(glob.glob(os.path.join(px, m, "*"))):
            if os.path.isfile(p): dosyalar.append({"dosya": os.path.basename(p), "bayt": os.path.getsize(p), "sha256": sha(p)})
        kayit["modeller"].append({"ad": "PaddleOCR/" + m, "kaynak": "https://paddleocr.bj.bcebos.com (PaddleX official_models)", "lisans": "Apache-2.0", "paddleocr_surum": "3.7.0", "paddlepaddle_surum": "3.3.1", "dosyalar": dosyalar})
eo = os.path.join(os.path.expanduser("~"), ".EasyOCR", "model")
if os.path.isdir(eo):
    dosyalar = [{"dosya": f, "bayt": os.path.getsize(os.path.join(eo, f)), "sha256": sha(os.path.join(eo, f))} for f in sorted(os.listdir(eo)) if os.path.isfile(os.path.join(eo, f))]
    kayit["modeller"].append({"ad": "EasyOCR (en)", "kaynak": "https://github.com/JaidedAI/EasyOCR (model indirme easyocr 1.7.2)", "lisans": "Apache-2.0", "yukleme": "easyocr kendi torch.load'u ile kendi indirdiği .pth dosyalarını açar (kaynak EasyOCR resmi sürüm)", "dosyalar": dosyalar})
# bizim model
for p in ["egitim/model.json", "js/model.js", "js/elyazisi-ocr.js"]:
    kayit["modeller"].append({"ad": "bizim/" + p, "kaynak": "bu proje (bulutta eğitildi, MNIST + sentetik)", "dosyalar": [{"dosya": p, "bayt": os.path.getsize(p), "sha256": sha(p)}]})
json.dump(kayit, open("cihaz/model-kaynak-kaydi.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for m in kayit["modeller"]:
    print(m["ad"], "|", m.get("hf_commit", ""), "|", len(m["dosyalar"]), "dosya |", sum(d["bayt"] for d in m["dosyalar"]) // 1024 // 1024, "MB")
