# -*- coding: utf-8 -*-
"""
veri_emnist.py - EMNIST (+ T-H-E Dataset) tabanlı eğitim verisi.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

Sınıflar "0123456789T-" (veri.py ile aynı). Kaynaklar:
  rakam   : emnist-digits train (EMNIST görüntüleri transpoze -> .T), mnist_normalle ile
            MNIST biçimine (20x20 kutu + kütle merkezi) getirilir; bir kısmı veri.rakam_bozuk ile bozulur.
  "1"     : 7k bayraklı sentetik (veri.bir_uret) korunur.
  T       : EMNIST byclass T (etiket 29) + t (55), T-H-E Dataset version6 T(59)/t(20) (varsa),
            eksik kalırsa veri.t_uret sentetiği.
  "-"     : veri.tire_uret sentetik.
Kullanım: python veri_emnist.py <çıkış.npz>
"""
import sys, os, gzip, time
import numpy as np
from multiprocessing import Pool
import veri, bolme

KOK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EMNIST = os.path.join(KOK, "veri", "emnist", "gzip")
THE = os.path.join(KOK, "veri", "the-dataset", "version6.csv")

# veri.py Linux font yollarını kullanıyor; bu makinede Windows fontları
_W = "C:/Windows/Fonts/"
veri.FONTLAR = [_W + f for f in ("arial.ttf", "arialbd.ttf", "ariali.ttf", "times.ttf", "timesi.ttf", "calibri.ttf",
                                  "verdana.ttf", "tahoma.ttf", "comic.ttf", "cour.ttf", "segoeui.ttf")
                if os.path.exists(_W + f)]


def idx(bol, ad):
    """EMNIST idx oku. Görüntüler transpoze saklanır: (N,28,28) -> her biri .T"""
    with gzip.open(os.path.join(EMNIST, "emnist-%s-%s-images-idx3-ubyte.gz" % (bol, ad))) as f:
        x = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1, 28, 28)
    with gzip.open(os.path.join(EMNIST, "emnist-%s-%s-labels-idx1-ubyte.gz" % (bol, ad))) as f:
        y = np.frombuffer(f.read(), np.uint8, offset=8)
    return np.ascontiguousarray(x.transpose(0, 2, 1)), y


def the_oku(sinif_etiketleri=(59, 20)):
    """T-H-E version6.csv: ilk sütun etiket (1..78), sonra 784 piksel. Yalnız istenen etiketler."""
    if not os.path.exists(THE) or os.path.getsize(THE) < 119_387_000:
        return np.zeros((0, 28, 28), np.uint8)
    out = []
    with open(THE, "r") as f:
        for ln in f:
            i = ln.find(",")
            if int(float(ln[:i])) in sinif_etiketleri:
                out.append(np.array(ln[i + 1:].strip().split(","), dtype=np.float32))
    a = np.stack(out)
    if a.max() <= 1.0:
        a = a * 255
    return np.ascontiguousarray(a.reshape(-1, 28, 28).transpose(0, 2, 1)).astype(np.uint8)  # PNG ile doğrulandı: ham satır/sütun yer değişik -> .T


def norm(a):
    """uint8 28x28 -> mnist_normalle -> float32 0..1"""
    return bolme.mnist_normalle(a.astype(np.float32) / 255.0)


def _norm_toplu(arr):
    return np.stack([norm(a) for a in arr])


def _bozuk_toplu(args):
    arr, tohum = args
    rng = np.random.default_rng(tohum)
    return np.stack([veri.rakam_bozuk(a, rng) for a in arr])


def _bozuk_t_toplu(args):
    arr, tohum = args
    rng = np.random.default_rng(tohum)
    # T: ham 28x28 -> 56 tuval -> afin (rakam_bozuk ile aynı işlem)
    return np.stack([veri.rakam_bozuk(a, rng) for a in arr])


def _sent_t(args):
    n, tohum, birler = args
    rng = np.random.default_rng(tohum)
    return np.stack([veri.t_uret(birler, rng) for _ in range(n)])


def _sent_tire(args):
    n, tohum = args
    rng = np.random.default_rng(tohum)
    return np.stack([veri.tire_uret(rng) for _ in range(n)])


def _sent_bir(args):
    n, tohum = args
    rng = np.random.default_rng(tohum)
    return np.stack([veri.bir_uret(rng) for _ in range(n)])


def parcala(a, n):
    return np.array_split(a, n)


def uret(pool, tohum=1, rakam_basina=30000, bir_sent=7000, t_hedef=18000, tire_say=16000, log=print):
    rng = np.random.default_rng(tohum)
    X, Y = idx("digits", "train")
    log("digits train:", X.shape)
    xs, ys, bilgi = [], [], {}
    NP = 12
    birler_ham = X[Y == 1]
    for c in range(10):
        ii = np.nonzero(Y == c)[0]
        rng.shuffle(ii)
        hedef = rakam_basina - (bir_sent if c == 1 else 0)
        ii = ii[:hedef]
        n_boz = int(len(ii) * 0.35)
        temiz, boz = X[ii[n_boz:]], X[ii[:n_boz]]
        xs.append(np.concatenate(pool.map(_norm_toplu, parcala(temiz, NP))))
        ys.append(np.full(len(temiz), c, np.int64))
        xs.append(np.concatenate(pool.map(_bozuk_toplu, [(p, tohum * 1000 + c * 50 + k) for k, p in enumerate(parcala(boz, NP))])))
        ys.append(np.full(len(boz), c, np.int64))
        bilgi["rakam%d" % c] = len(ii) + (bir_sent if c == 1 else 0)
    xs.append(np.concatenate(pool.map(_sent_bir, [(bir_sent // NP + 1, tohum * 7 + k) for k in range(NP)]))[:bir_sent])
    ys.append(np.full(bir_sent, 1, np.int64))
    # T: gerçek
    bx, by = idx("byclass", "train")
    gercek = [("emnist T", bx[by == 29]), ("emnist t", bx[by == 55])]
    th = the_oku()
    if len(th):
        gercek.append(("the T/t", th))
    tg = []
    for ad, a in gercek:
        bilgi[ad] = len(a)
        t_ = np.concatenate(pool.map(_norm_toplu, parcala(a, NP)))
        tg.append(t_)
        # bozulmuş kopya (aynı sayıda yarı)
    tg = np.concatenate(tg)
    allr = np.concatenate([a for _, a in gercek])
    boz = np.concatenate(pool.map(_bozuk_t_toplu, [(p, tohum * 31 + k) for k, p in enumerate(parcala(allr[rng.permutation(len(allr))[:len(allr) // 2]], NP))]))
    xs += [tg, boz]; ys += [np.full(len(tg) + len(boz), 10, np.int64)]
    eksik = max(0, t_hedef - len(tg) - len(boz))
    bilgi["T sentetik"] = eksik
    if eksik:
        xs.append(np.concatenate(pool.map(_sent_t, [(eksik // NP + 1, tohum * 11 + k, birler_ham) for k in range(NP)]))[:eksik])
        ys.append(np.full(eksik, 10, np.int64))
    xs.append(np.concatenate(pool.map(_sent_tire, [(tire_say // NP + 1, tohum * 13 + k) for k in range(NP)]))[:tire_say])
    ys.append(np.full(tire_say, 11, np.int64))
    bilgi["tire sentetik"] = tire_say
    return np.concatenate(xs).astype(np.float32), np.concatenate(ys), bilgi


def test_kumeleri(pool):
    """Eğitime girmeyen test kümeleri: dict ad -> (x float32 0..1 N,28,28 ; y)"""
    T = {}
    x, y = idx("digits", "test")
    T["emnist-digits"] = (np.concatenate(pool.map(_norm_toplu, parcala(x, 12))), y.astype(np.int64))
    x, y = idx("mnist", "test")   # EMNIST'in 'mnist' bölmesi = MNIST 70k (test 10k)
    # MNIST ham biçim (zaten 20x20 + kütle merkezi): normallemeden
    T["mnist"] = (x.astype(np.float32) / 255.0, y.astype(np.int64))
    x, y = idx("byclass", "test")
    m = (y == 29) | (y == 55)
    T["emnist-T/t"] = (np.concatenate(pool.map(_norm_toplu, parcala(x[m], 12))), np.full(int(m.sum()), 10, np.int64))
    return T


if __name__ == "__main__":
    import json
    t0 = time.time()
    with Pool(6) as p:
        X, Y, b = uret(p)
        T = test_kumeleri(p)
    rng = np.random.default_rng(999)
    d = idx("digits", "train")
    birler = d[0][d[1] == 1][::-1]
    xs = [veri.t_uret(birler, rng) for _ in range(500)] + [veri.tire_uret(rng) for _ in range(500)]
    T["sentetik T/-"] = (np.stack(xs), np.array([10] * 500 + [11] * 500, np.int64))
    print("toplam", X.shape, np.bincount(Y).tolist(), b, "%.0f sn" % (time.time() - t0))
    kw = {"x": (X * 255).astype(np.uint8), "y": Y}
    for k, (x, y) in T.items():
        kw["tx_" + k] = (x * 255).astype(np.uint8); kw["ty_" + k] = y
    np.savez_compressed(sys.argv[1], **kw)
    json.dump(b, open(sys.argv[1] + ".bilgi.json", "w", encoding="utf-8"), ensure_ascii=False)
