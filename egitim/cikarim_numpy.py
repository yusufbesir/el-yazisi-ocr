# -*- coding: utf-8 -*-
"""
cikarim_numpy.py - model.json'u okuyup yalnız numpy ile ileri geçiş yapar.
JS portunun birebir izleyeceği referanstır: padding yok, stride 1, maxpool 2
(taban bölme: 11 -> 5), düzleştirme (kanal, satır, sütun) sırasıyla, softmax.
Girdi: 28x28, siyah zemin, beyaz mürekkep, 0..1.
"""
import json
import numpy as np


def model_yukle(yol):
    return json.load(open(yol, encoding="utf-8"))


def conv(x, w, b, cin, cout, k):
    """x: (cin,H,W); w düz liste [cout][cin][k][k]; sonuç (cout,H-k+1,W-k+1)."""
    h, wd = x.shape[1] - k + 1, x.shape[2] - k + 1
    W = np.asarray(w, dtype=np.float64).reshape(cout, cin, k, k)
    cikis = np.zeros((cout, h, wd))
    for o in range(cout):
        acc = np.full((h, wd), b[o], dtype=np.float64)
        for i in range(cin):
            for dy in range(k):
                for dx in range(k):
                    acc += W[o, i, dy, dx] * x[i, dy:dy + h, dx:dx + wd]
        cikis[o] = acc
    return cikis


def maxpool(x, k=2):
    c, h, w = x.shape
    h2, w2 = h // k, w // k
    cikis = np.zeros((c, h2, w2))
    for y in range(h2):
        for xx in range(w2):
            cikis[:, y, xx] = x[:, y * k:(y + 1) * k, xx * k:(xx + 1) * k].reshape(c, -1).max(1)
    return cikis


def fc(x, w, b, giris, cikis):
    return np.asarray(w, dtype=np.float64).reshape(cikis, giris).dot(x) + np.asarray(b, dtype=np.float64)


def softmax(z):
    e = np.exp(z - z.max())
    return e / e.sum()


def ileri(model, goruntu):
    """goruntu: (28,28) 0..1 -> 12 sınıf olasılığı."""
    x = np.asarray(goruntu, dtype=np.float64).reshape(1, 28, 28)
    for kat in model["katmanlar"]:
        t = kat["tip"]
        if t == "conv":
            x = conv(x, kat["w"], kat["b"], kat["giris"], kat["cikis"], kat["k"])
        elif t == "maxpool":
            x = maxpool(x, kat["k"])
        elif t == "duzlestir":
            x = x.reshape(-1)
        elif t == "fc":
            x = fc(x, kat["w"], kat["b"], kat["giris"], kat["cikis"])
        if kat.get("aktivasyon") == "relu":
            x = np.maximum(x, 0)
    return softmax(x)


def _hazir(model):
    """Ağırlıkları bir kez numpy dizisine çevir (model sözlüğünde önbellek)."""
    if "_np" not in model:
        h = []
        for kat in model["katmanlar"]:
            t = kat["tip"]
            if t == "conv":
                h.append(("conv", np.asarray(kat["w"], np.float32).reshape(kat["cikis"], kat["giris"] * kat["k"] * kat["k"]),
                          np.asarray(kat["b"], np.float32), kat["k"], kat.get("aktivasyon") == "relu"))
            elif t == "fc":
                h.append(("fc", np.asarray(kat["w"], np.float32).reshape(kat["cikis"], kat["giris"]),
                          np.asarray(kat["b"], np.float32), 0, kat.get("aktivasyon") == "relu"))
            else:
                h.append((t, None, None, kat.get("k", 2), False))
        model["_np"] = h
    return model["_np"]


def ileri_toplu(model, goruntuler):
    """[2026-10-26 Claude#HtqxxY] ileri() ile aynı hesap, vektörleştirilmiş ve toplu (N,28,28) -> (N,sınıf).
    Büyük modellerde döngülü sürüm karakter başına ~0,5 sn; bu sürüm ~1 ms. Sonuç float32 yuvarlaması kadar farklı olabilir."""
    from numpy.lib.stride_tricks import sliding_window_view
    x = np.asarray(goruntuler, np.float32).reshape(-1, 1, 28, 28)
    if len(x) == 0:
        return np.zeros((0, len(model.get("siniflar", "0123456789T-"))), np.float32)
    for t, W, b, k, relu in _hazir(model):
        if t == "conv":
            p = sliding_window_view(x, (k, k), axis=(2, 3))            # N,C,H',W',k,k
            n, c, h, w = p.shape[:4]
            p = p.transpose(0, 2, 3, 1, 4, 5).reshape(n * h * w, c * k * k)   # (cin,dy,dx) sırası = ağırlık sırası
            x = (p @ W.T + b).reshape(n, h, w, -1).transpose(0, 3, 1, 2)
        elif t == "maxpool":
            n, c, h, w = x.shape
            h2, w2 = h // k, w // k
            x = x[:, :, :h2 * k, :w2 * k].reshape(n, c, h2, k, w2, k).max((3, 5))
        elif t == "duzlestir":
            x = x.reshape(len(x), -1)
        elif t == "fc":
            x = x @ W.T + b
        if relu:
            x = np.maximum(x, 0)
    z = x - x.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


if __name__ == "__main__":
    # PyTorch ile karşılaştırma: python cikarim_numpy.py model.json model.pt egitim.npz
    import sys, torch
    import egit
    m = model_yukle(sys.argv[1])
    ag = egit.Ag(); ag.load_state_dict(torch.load(sys.argv[2])); ag.eval()
    d = np.load(sys.argv[3])
    en_fark = 0.0
    for i in (0, 5, 50000, 90000, 98000, 103000):
        g = d["x"][i].astype(np.float32) / 255.0
        p1 = ileri(m, g)
        with torch.no_grad():
            p2 = torch.softmax(ag(torch.from_numpy(g).reshape(1, 1, 28, 28)), 1)[0].numpy()
        en_fark = max(en_fark, float(np.abs(p1 - p2).max()))
        print(i, "sınıf", int(d["y"][i]), "numpy", int(p1.argmax()), "torch", int(p2.argmax()), "fark %.2e" % np.abs(p1 - p2).max())
    print("en büyük olasılık farkı: %.2e (5 ondalık yuvarlama etkisi dahil)" % en_fark)
