# -*- coding: utf-8 -*-
"""
veri.py - Eğitim verisi: MNIST rakamları + sentetik "T" + sentetik "-".
Sınıflar: "0123456789T-" (indeks 0-9 rakam, 10 = T, 11 = tire).
Her örnek bolme.mnist_normalle ile aynı biçime getirilir (gerçek hücre
kırpıntıları da aynı işlemden geçtiği için eğitim/test dağılımı yakın olur).

Kullanım: python veri.py <MNIST klasörü> <çıkış.npz> [tohum]
"""
import sys, gzip, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import bolme

SINIFLAR = "0123456789T-"
FONTLAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf",
]
TUVAL = 64  # sentetik çizim tuvali


def mnist_oku(klasor, ad):
    with gzip.open(os.path.join(klasor, ad + "-images-idx3-ubyte.gz")) as f:
        x = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1, 28, 28)
    with gzip.open(os.path.join(klasor, ad + "-labels-idx1-ubyte.gz")) as f:
        y = np.frombuffer(f.read(), np.uint8, offset=8)
    return x, y


# ------------------------------------------------------------ bozulmalar
def afin(a, rng, aci=15.0, kayma=0.3, olcek=(0.8, 1.2)):
    """a: kare 2B dizi (0..1). Merkez etrafında dönme + kayma + ölçek."""
    n = a.shape[0]
    t = np.deg2rad(rng.uniform(-aci, aci))
    sx, sy = rng.uniform(*olcek), rng.uniform(*olcek)
    k = rng.uniform(-kayma, kayma)
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    M = R.dot(np.array([[sx, k], [0, sy]]))
    c = np.array([n / 2.0, n / 2.0])
    ofs = c - M.dot(c)
    A = np.hstack([M, ofs.reshape(2, 1)]).astype(np.float32)
    return cv2.warpAffine(a.astype(np.float32), A, (n, n), flags=cv2.INTER_LINEAR)


def kalinlik(a, rng):
    """Rastgele kalınlaştır / incelt (3x3 elips çekirdek)."""
    r = rng.random()
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    if r < 0.25:
        return cv2.dilate(a, k)
    if r < 0.40:
        return cv2.erode(a, k)
    return a


def kirp(a, rng, p=0.25):
    """Bazen karakterin bir kenarından %5-15'ini kes (kutu sıkı kesilmiş gibi)."""
    if rng.random() > p:
        return a
    ys, xs = np.nonzero(a > 0.05)
    if len(ys) == 0:
        return a
    a = a.copy()
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    f = rng.uniform(0.05, 0.15)
    yon = rng.integers(4)
    if yon == 0: a[:, :x0 + int((x1 - x0) * f)] = 0
    elif yon == 1: a[:, x1 - int((x1 - x0) * f):] = 0
    elif yon == 2: a[:y0 + int((y1 - y0) * f), :] = 0
    else: a[y1 - int((y1 - y0) * f):, :] = 0
    return a


def son_gurultu(c, rng):
    """28x28 normalleşmiş görüntüye hafif gürültü ve kontrast oynaması."""
    c = c * rng.uniform(0.8, 1.0)
    if rng.random() < 0.5:
        c = c + rng.normal(0, 0.04, c.shape)
    return np.clip(c, 0, 1).astype(np.float32)


def normalle(tuval, rng):
    return bolme.mnist_normalle(tuval)


# ------------------------------------------------------------- sınıf üretimi
def rakam_bozuk(a28, rng):
    """MNIST rakamını 56x56 tuvale koyup bozar, sonra normalleştirir."""
    t = np.zeros((56, 56), np.float32)
    t[14:42, 14:42] = a28.astype(np.float32) / 255.0
    t = afin(t, rng, aci=15, kayma=0.35, olcek=(0.75, 1.25))
    t = kalinlik(t, rng)
    t = kirp(t, rng, 0.1)
    return son_gurultu(normalle(t, rng), rng)


def cizgi_t(rng):
    """El çizimi benzeri T: yatay çubuk + dikey gövde, rastgele sapmalar."""
    t = np.zeros((TUVAL, TUVAL), np.uint8)
    kal = int(rng.integers(2, 6))
    cx = 32 + rng.uniform(-3, 3)
    bw = rng.uniform(14, 34)         # çubuk genişliği
    bh = rng.uniform(22, 40)         # gövde yüksekliği
    ust = 32 - bh / 2 + rng.uniform(-2, 2)
    eg = rng.uniform(-0.12, 0.12)    # çubuk eğimi
    xs0, xs1 = cx - bw / 2 + rng.uniform(-4, 4), cx + bw / 2 + rng.uniform(-4, 4)
    p0 = (xs0, ust - eg * bw / 2); p1 = (xs1, ust + eg * bw / 2)
    cv2.line(t, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 255, kal, cv2.LINE_AA)
    # gövde: hafif eğri (2 parça)
    ortay = ust + bh / 2
    sap = rng.uniform(-3, 3)
    gx = cx + rng.uniform(-3, 3)
    pts = np.array([[gx, ust + rng.uniform(-3, 2)], [gx + sap, ortay], [gx + sap * 1.5 + rng.uniform(-3, 3), ust + bh]], np.int32)
    cv2.polylines(t, [pts.reshape(-1, 1, 2)], False, 255, kal, cv2.LINE_AA)
    return t.astype(np.float32) / 255.0


def font_t(rng):
    f = ImageFont.truetype(FONTLAR[int(rng.integers(len(FONTLAR)))], int(rng.integers(30, 52)))
    im = Image.new("L", (TUVAL, TUVAL), 0)
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), "T", font=f)
    d.text(((TUVAL - (bb[2] - bb[0])) // 2 - bb[0], (TUVAL - (bb[3] - bb[1])) // 2 - bb[1]), "T", fill=255, font=f)
    return np.array(im, np.float32) / 255.0


def mnist_bir_t(birler, rng):
    """MNIST '1' örneğinin üstüne yatay çubuk ekler (rakamın gövdesi kalır)."""
    a = birler[int(rng.integers(len(birler)))].astype(np.float32) / 255.0
    t = np.zeros((TUVAL, TUVAL), np.float32)
    t[18:46, 18:46] = a
    ys, xs = np.nonzero(t > 0.3)
    y0, x0, x1 = ys.min(), xs.min(), xs.max()
    cx = (x0 + x1) / 2.0
    bw = (ys.max() - y0) * rng.uniform(0.5, 1.1)
    kal = int(rng.integers(2, 5))
    ey = rng.uniform(-0.1, 0.1)
    p0 = (int(cx - bw / 2), int(y0 + 1 - ey * bw / 2)); p1 = (int(cx + bw / 2), int(y0 + 1 + ey * bw / 2))
    u8 = (t * 255).astype(np.uint8)
    cv2.line(u8, p0, p1, 255, kal, cv2.LINE_AA)
    return u8.astype(np.float32) / 255.0


def bayrakli_bir(rng):
    """Avrupa tipi '1': gövde + üstte sola inen diyagonal bayrak (7'ye benzer,
    ama bayrak kısa ve eğik); bazen alt çizgi. MNIST'te az bulunur."""
    t = np.zeros((TUVAL, TUVAL), np.uint8)
    kal = int(rng.integers(2, 6))
    h = rng.uniform(26, 44)
    cx = 32 + rng.uniform(-3, 3)
    ust = 32 - h / 2
    alt = ust + h
    sap = rng.uniform(-3, 3)
    pts = np.array([[cx, ust], [cx + sap, ust + h / 2], [cx + sap * 1.3, alt]], np.int32)
    cv2.polylines(t, [pts.reshape(-1, 1, 2)], False, 255, kal, cv2.LINE_AA)
    bl = rng.uniform(6, 16)            # bayrak uzunluğu
    ba = rng.uniform(0.3, 1.0)         # bayrak eğimi (dy/dx)
    cv2.line(t, (int(cx), int(ust)), (int(cx - bl), int(ust + bl * ba)), 255, kal, cv2.LINE_AA)
    if rng.random() < 0.15:            # alt çizgi
        cv2.line(t, (int(cx - 6), int(alt)), (int(cx + 6), int(alt)), 255, kal, cv2.LINE_AA)
    return t.astype(np.float32) / 255.0


def bir_uret(rng):
    a = afin(bayrakli_bir(rng), rng, aci=12, kayma=0.25, olcek=(0.85, 1.15))
    a = kalinlik(a, rng)
    return son_gurultu(normalle(a, rng), rng)


def t_uret(birler, rng):
    r = rng.random()
    if r < 0.35: a = mnist_bir_t(birler, rng)
    elif r < 0.75: a = cizgi_t(rng)
    else: a = font_t(rng)
    a = afin(a, rng, aci=15, kayma=0.3, olcek=(0.8, 1.2))
    a = kalinlik(a, rng)
    a = kirp(a, rng, 0.25)
    return son_gurultu(normalle(a, rng), rng)


def tire_uret(rng):
    t = np.zeros((TUVAL, TUVAL), np.uint8)
    kal = int(rng.integers(1, 6))
    uz = rng.uniform(14, 52)
    cx, cy = 32 + rng.uniform(-4, 4), 32 + rng.uniform(-6, 6)
    eg = rng.uniform(-0.2, 0.2)
    p = [(cx - uz / 2, cy - eg * uz / 2), (cx, cy + rng.uniform(-2, 2)), (cx + uz / 2, cy + eg * uz / 2)]
    cv2.polylines(t, [np.array(p, np.int32).reshape(-1, 1, 2)], False, 255, kal, cv2.LINE_AA)
    a = afin(t.astype(np.float32) / 255.0, rng, aci=8, kayma=0.15, olcek=(0.85, 1.15))
    a = kalinlik(a, rng)
    a = kirp(a, rng, 0.15)
    return son_gurultu(normalle(a, rng), rng)


def uret(klasor, tohum=1, mnist_aug=60000, t_say=7000, tire_say=7000, bir_say=7000):
    rng = np.random.default_rng(tohum)
    X, Y = mnist_oku(klasor, "train")
    birler = X[Y == 1]
    xs, ys = [], []
    # MNIST ham: zaten 20x20 kutu + kütle merkezi
    xs.append(X.astype(np.float32) / 255.0); ys.append(Y.astype(np.int64))
    # MNIST bozulmuş kopyalar
    idx = rng.integers(len(X), size=mnist_aug)
    xs.append(np.stack([rakam_bozuk(X[i], rng) for i in idx])); ys.append(Y[idx].astype(np.int64))
    xs.append(np.stack([t_uret(birler, rng) for _ in range(t_say)])); ys.append(np.full(t_say, 10, np.int64))
    xs.append(np.stack([tire_uret(rng) for _ in range(tire_say)])); ys.append(np.full(tire_say, 11, np.int64))
    xs.append(np.stack([bir_uret(rng) for _ in range(bir_say)])); ys.append(np.full(bir_say, 1, np.int64))
    return np.concatenate(xs), np.concatenate(ys)


def sentetik_test(klasor, tohum=999, n=1000):
    """Eğitimde görülmeyen tohumla T ve '-' sınama kümesi."""
    rng = np.random.default_rng(tohum)
    Xt, Yt = mnist_oku(klasor, "train")
    birler = Xt[Yt == 1][::-1]
    x = [t_uret(birler, rng) for _ in range(n)] + [tire_uret(rng) for _ in range(n)]
    y = [10] * n + [11] * n
    return np.stack(x), np.array(y, np.int64)


if __name__ == "__main__":
    kl, cikis = sys.argv[1], sys.argv[2]
    tohum = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    X, Y = uret(kl, tohum)
    print("toplam:", X.shape, "sınıf sayıları:", np.bincount(Y).tolist())
    np.savez_compressed(cikis, x=(X * 255).astype(np.uint8), y=Y)
    # örnek ızgara: her sınıftan 12
    satirlar = []
    for c in range(12):
        ii = np.nonzero(Y == c)[0][-12:]
        satirlar.append(np.hstack([X[i] for i in ii]))
    Image.fromarray((np.vstack(satirlar) * 255).astype(np.uint8)).save(os.path.splitext(cikis)[0] + "_ornek.png")
