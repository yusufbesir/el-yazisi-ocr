# -*- coding: utf-8 -*-
# Açıklama: RIMES imagettes_mots_cursif.zip -> 32x256 uint8 kırpıntı önbelleği (kelime tanıyıcı eğitimi).
# yazan: [Claude#HtqxxY işçi]  | Sahip: Yusuf (El-Yazisi-OCR). Yalnız yazan yapay zeka değiştirir.
# Zip diske açılmaz; dosya dosya okunur. Lisans: CC BY-NC 4.0 (ticari olmayan).
import zipfile, io, json, random, re, time, sys
import numpy as np, cv2
from PIL import Image
ROOT = r"D:\Programlar\El-Yazisi-OCR\veri"
ZIP = ROOT + r"\rimes\imagettes_mots_cursif.zip"
OUT = ROOT + r"\onbellek"
OK = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZçÇğĞıİöÖşŞüÜ-")
MAXTR, MAXVA, TIME_LIMIT = 60000, 1500, 33 * 60
t0 = time.time()
z = zipfile.ZipFile(ZIP)
raw = z.read("imagettes_mots_cursif/goodSnippets_total/goodSnippets_total.dat")
txt = raw.decode("utf-8-sig", errors="replace")
names = {n.split("lot_", 1)[1] if False else n for n in z.namelist() if n.endswith(".tiff")}
byfile = {}
for n in names:
    byfile[n.rsplit("/", 1)[1]] = n
items, tot = [], 0
for line in txt.splitlines():
    p = line.strip().split()
    if len(p) < 3: continue
    tot += 1
    path, lab = p[0], p[1] if len(p) == 3 else None
    if lab is None or not (1 <= len(lab) <= 20) or any(c not in OK for c in lab): continue
    fn = path.replace("\\", "/").rsplit("/", 1)[1]
    if fn in byfile:
        items.append((byfile[fn], lab, fn.split("_")[0]))
print("etiket satiri", tot, "suzgecten gecen", len(items), flush=True)
rnd = random.Random(1234)
docs = sorted({d for _, _, d in items}); rnd.shuffle(docs)
valdocs = set(docs[:max(1, len(docs) // 20)])  # %5 belge, sizinti olmasin
tr = [i for i in items if i[2] not in valdocs]; va = [i for i in items if i[2] in valdocs]
rnd.shuffle(tr); rnd.shuffle(va)
def proc(b):
    g = np.array(Image.open(io.BytesIO(b)).convert("L"))
    if g.mean() > 0: pass
    gf = g.astype(np.float32)
    bg = cv2.medianBlur(g, 0 if False else 51) if min(g.shape) > 51 else None
    if bg is None: bg = np.full_like(g, int(np.median(g)))
    d = np.clip(bg.astype(np.float32) - gf, 0, 255)  # mürekkep koyu -> beyaz
    m = d.max()
    if m < 20: return None
    d = np.clip(d * (255.0 / m), 0, 255).astype(np.uint8)
    ys, xs = np.where(d > 40)
    if len(ys) == 0: return None
    d = d[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = d.shape
    nw = max(1, round(w * 28 / h))
    if nw > 252: return None
    d = cv2.resize(d, (nw, 28), interpolation=cv2.INTER_AREA)
    c = np.zeros((32, 256), np.uint8); c[2:30, 2:2 + nw] = d
    return c
def build(lst, mx, tlim):
    X, Y = [], []
    for n, lab, _ in lst:
        if len(X) >= mx or time.time() - t0 > tlim: break
        try: c = proc(z.read(n))
        except Exception: continue
        if c is None: continue
        X.append(c); Y.append(lab)
        if len(X) % 5000 == 0: print(len(X), round(time.time() - t0), flush=True)
    return np.stack(X), Y
Xv, Yv = build(va, MAXVA, 10 * 60)
Xt, Yt = build(tr, MAXTR, TIME_LIMIT)
for nm, X, Y in (("rimes-train", Xt, Yt), ("rimes-val", Xv, Yv)):
    np.save(f"{OUT}\{nm}_x.npy", X)
    json.dump(Y, open(f"{OUT}\{nm}_y.json", "w", encoding="utf-8"), ensure_ascii=False)
Image.fromarray(np.concatenate(list(Xt[:12]), 0)).save(ROOT + r"\rimes\ornek-kelime.png")
print("ornek etiketler:", Yt[:12])
open(ROOT + r"\rimes\HAZIRLAMA.md", "w", encoding="utf-8").write(f"""---
description: RIMES kelime kırpıntı önbelleği hazırlama notu
yazan: [Claude#HtqxxY işçi]
---
# RIMES kelime önbelleği
- Kaynak: imagettes_mots_cursif.zip (goodSnippets_total.dat etiketleri; resmi train/val bölmesi yok).
- Lisans: CC BY-NC 4.0 (yalnız ticari olmayan kullanım). Atıf: RIMES, Zenodo 10812725.
- Süzgeç: yalnız 0-9 a-z A-Z çÇğĞıİöÖşŞüÜ '-' ve 1-20 karakter (Fransızca aksanlı/boşluklu/diğer elenir). Dat'ta {tot} satır, süzgeçten sonra {len(items)}.
- Görüntü: gri, zemin medyan-blur(51) ile çıkarıldı, mürekkep beyaz/siyah zemin, ink kutusuna kırpıldı, yükseklik 28, 32x256 tuval (y=2,x=2), genişlik>252 atıldı.
- Bölme: belgeye (00001_L gibi) göre sabit tohum 1234 ile %5 belge val (sızıntı yok). Kullanılan: train {len(Yt)}, val {len(Yv)} (üst sınır 60000/1500).
- Çıktı: veri\onbellek\rimes-train_x.npy/_y.json, rimes-val_x.npy/_y.json. Betik: egitim\gece\rimes_hazirla.py
- Örnek: ornek-kelime.png (ilk 12 train, alt alta): {Yt[:12]}
""")
print("bitti", len(Yt), len(Yv), round(time.time() - t0))
