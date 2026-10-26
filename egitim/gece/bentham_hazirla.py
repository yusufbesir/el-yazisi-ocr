# -*- coding: utf-8 -*-
"""Bentham R0 (Zenodo 44519, CC BY 4.0) kelime/kisa-satir kirpintilari uretir.
Aciklama: PAGE-XML'de Word yoksa TextLine kutusu kullanilir; yalniz 1-2 kelimelik
kisa satirlar alinir. Cikti: veri/onbellek/bentham_kelime_x.npy (N,32,256 uint8,
mürekkep beyaz/zemin siyah) ve bentham_kelime_y.json.
Yazan: [Claude#HtqxxY işçi]. Sahibi: Yusuf (El-Yazisi-OCR). Degistirme: yalniz yazan YZ
veya Yusuf'un izniyle; girdi arsivleri akisla okunur, hicbir sey silinmez/calistirilmaz.
Atif: Sanchez ve ark., tranScriptorium Bentham R0, Zenodo 44519 (CC BY 4.0).
"""
import tarfile, re, json, sys, time
import xml.etree.ElementTree as ET
import numpy as np, cv2

D = r'D:\Programlar\El-Yazisi-OCR\veri'
GT = D + r'\bentham-r0\BenthamDatasetR0-GT.tbz'
IM = D + r'\bentham-r0\BenthamDatasetR0-Images.tbz'
OUT_X = D + r'\onbellek\bentham_kelime_x.npy'
OUT_Y = D + r'\onbellek\bentham_kelime_y.json'
MAXN = 40000
OK = re.compile(r'^[A-Za-z0-9-]{1,24}$')
t0 = time.time()

def pts(el):
    c = el.find('{*}Coords')
    return np.array([[int(p.get('x')), int(p.get('y'))] for p in c.findall('{*}Point')], np.int32)

# 1) GT: sayfa -> [(poligon, metin)]
pages = {}
nword = nline = 0
with tarfile.open(GT, 'r|bz2') as t:
    for m in t:
        if not (m.isfile() and '/PAGE/' in m.name and m.name.endswith('.xml')):
            continue
        root = ET.fromstring(t.extractfile(m).read())
        pg = root.find('{*}Page').get('imageFilename')
        nword += len(root.findall('.//{*}Word'))
        items = []
        for tl in root.findall('.//{*}TextLine'):
            nline += 1
            u = tl.find('{*}TextEquiv/{*}Unicode')
            txt = (u.text or '').strip() if u is not None else ''
            toks = txt.split()
            if not 1 <= len(toks) <= 2 or len(txt) > 24:
                continue
            if not all(OK.match(k) for k in toks):
                continue
            try:
                pp = pts(tl)
                if len(pp) >= 3:
                    items.append((pp, ' '.join(toks)))
            except Exception:
                pass
        if items:
            pages[pg] = items
print('GT: sayfa', len(pages), 'Word', nword, 'TextLine', nline,
      'aday', sum(len(v) for v in pages.values()), flush=True)

# 2) Gorseller
X, Y = [], []
with tarfile.open(IM, 'r|bz2') as t:
    for m in t:
        if len(X) >= MAXN:
            break
        if not m.isfile():
            continue
        name = m.name.split('/')[-1]
        if name not in pages:
            continue
        buf = np.frombuffer(t.extractfile(m).read(), np.uint8)
        g = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
        if g is None:
            continue
        H, W = g.shape
        for poly, txt in pages[name]:
            x0, y0 = poly.min(0); x1, y1 = poly.max(0)
            x0 = max(x0 - 2, 0); y0 = max(y0 - 2, 0); x1 = min(x1 + 3, W); y1 = min(y1 + 3, H)
            if x1 - x0 < 8 or y1 - y0 < 8:
                continue
            crop = g[y0:y1, x0:x1].copy()
            # poligon disindaki komsu murekkebi kagit rengine boya
            mask = np.zeros(crop.shape, np.uint8)
            cv2.fillPoly(mask, [poly - [x0, y0]], 255)
            mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
            paper = int(np.percentile(crop, 90))
            crop[mask == 0] = paper
            inv = 255 - crop
            h, w = inv.shape
            nw = int(round(w * 32.0 / h))
            if nw < 4 or nw > 252:
                continue
            r = cv2.resize(inv, (nw, 32), interpolation=cv2.INTER_AREA)
            cv = np.zeros((32, 256), np.uint8)
            cv[:, 2:2 + nw] = r
            X.append(cv); Y.append(txt)
            if len(X) >= MAXN:
                break
        if len(X) % 500 < 5:
            print(len(X), name, round(time.time() - t0), 's', flush=True)

X = np.stack(X) if X else np.zeros((0, 32, 256), np.uint8)
np.save(OUT_X, X)
with open(OUT_Y, 'w', encoding='utf-8') as f:
    json.dump(Y, f, ensure_ascii=False)
# ornek gorsel
if len(X) >= 12:
    cv2.imwrite(D + r'\bentham-r0\ornek-kelime.png', np.concatenate(list(X[:12]), 0))
print('bitti', len(X), 'Word', nword, 'sure', round(time.time() - t0), 's')
print(Y[:12])
