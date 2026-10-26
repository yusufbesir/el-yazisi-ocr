# -*- coding: utf-8 -*-
"""
egit.py - Küçük CNN eğitimi (PyTorch, CPU) ve model.json dışa aktarımı.
Kullanım: python egit.py <MNIST klasörü> <egitim.npz> <model.json> [epoch]
Mimari: conv(1->16,3x3) ReLU maxpool2 -> conv(16->32,3x3) ReLU maxpool2
        -> düzleştir (32*5*5=800) -> FC 64 ReLU -> FC 12 -> softmax
"""
import sys, json, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import veri

SINIFLAR = "0123456789T-"


class Ag(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = nn.Conv2d(1, 16, 3)
        self.c2 = nn.Conv2d(16, 32, 3)
        self.f1 = nn.Linear(32 * 5 * 5, 64)
        self.f2 = nn.Linear(64, 12)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.c1(x)), 2)   # 28 -> 26 -> 13
        x = F.max_pool2d(F.relu(self.c2(x)), 2)   # 13 -> 11 -> 5
        x = x.flatten(1)                           # (C,H,W) sırası
        x = F.relu(self.f1(x))
        return self.f2(x)


def duz(t):
    return [round(float(v), 5) for v in t.detach().cpu().numpy().ravel()]


def disa_aktar(ag, yol):
    k = [
        {"tip": "conv", "w": duz(ag.c1.weight), "b": duz(ag.c1.bias), "giris": 1, "cikis": 16, "k": 3, "aktivasyon": "relu"},
        {"tip": "maxpool", "k": 2},
        {"tip": "conv", "w": duz(ag.c2.weight), "b": duz(ag.c2.bias), "giris": 16, "cikis": 32, "k": 3, "aktivasyon": "relu"},
        {"tip": "maxpool", "k": 2},
        {"tip": "duzlestir"},
        {"tip": "fc", "w": duz(ag.f1.weight), "b": duz(ag.f1.bias), "giris": 800, "cikis": 64, "aktivasyon": "relu"},
        {"tip": "fc", "w": duz(ag.f2.weight), "b": duz(ag.f2.bias), "giris": 64, "cikis": 12, "aktivasyon": "yok"},
    ]
    json.dump({"katmanlar": k, "siniflar": SINIFLAR, "giris": [28, 28], "not": "çıkışa softmax uygula"},
              open(yol, "w"), separators=(",", ":"))


def dogruluk(ag, x, y):
    ag.eval()
    with torch.no_grad():
        tahmin = torch.cat([ag(x[i:i + 2000]).argmax(1) for i in range(0, len(x), 2000)])
    return float((tahmin == y).float().mean())


if __name__ == "__main__":
    mnist, npz, cikis = sys.argv[1], sys.argv[2], sys.argv[3]
    epoch = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    torch.set_num_threads(4)
    torch.manual_seed(0)
    d = np.load(npz)
    X = torch.from_numpy(d["x"].astype(np.float32) / 255.0).unsqueeze(1)
    Y = torch.from_numpy(d["y"])
    xt, yt = veri.mnist_oku(mnist, "t10k")
    Xt = torch.from_numpy(xt.astype(np.float32) / 255.0).unsqueeze(1); Yt = torch.from_numpy(yt.astype(np.int64))
    xs, ys = veri.sentetik_test(mnist)
    Xs = torch.from_numpy(xs).unsqueeze(1); Ys = torch.from_numpy(ys)
    ag = Ag()
    print("parametre sayısı:", sum(p.numel() for p in ag.parameters()))
    opt = torch.optim.Adam(ag.parameters(), 2e-3)
    adim = epoch * ((len(X) + 127) // 128)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, 4e-3, total_steps=adim)
    t0 = time.time()
    for e in range(epoch):
        ag.train()
        perm = torch.randperm(len(X))
        toplam = 0.0
        for i in range(0, len(X), 128):
            ii = perm[i:i + 128]
            kayip = F.cross_entropy(ag(X[ii]), Y[ii])
            opt.zero_grad(); kayip.backward(); opt.step(); sch.step()
            toplam += float(kayip.detach()) * len(ii)
        print("epoch %d kayıp %.4f mnist-test %.4f sentetik T/- test %.4f (%.0f sn)" % (
            e + 1, toplam / len(X), dogruluk(ag, Xt, Yt), dogruluk(ag, Xs, Ys), time.time() - t0))
    disa_aktar(ag, cikis)
    torch.save(ag.state_dict(), cikis.replace(".json", ".pt"))
    print("MNIST test doğruluğu: %.4f" % dogruluk(ag, Xt, Yt))
