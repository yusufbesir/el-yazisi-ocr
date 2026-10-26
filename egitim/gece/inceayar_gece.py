# -*- coding: utf-8 -*-
"""
inceayar_gece.py - Gece kod modelini (gece_egit mimarisi) GERÇEK tutanak kırpıntılarıyla ince ayarlar.
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait, eğitim amaçlı
Yusuf'un isteği (26.10 08:46): ince ayar; kullanılmış el yazısı örneklerinin 2. ve 3. kullanımı için sis, bozukluk, eksiklik.
  Her gerçek kırpıntı: 1 temiz + kopyalar (her kopyada rastgele): sis (kontrast düşük, gri peçe, bulanıklık), bozukluk
  (afin/elastik, kalınlık, gürültü), eksiklik (dikdörtgen silme ya da kenardan kesik). Kopyalar her epoch yeniden üretilir.
  Unutmama karışımı: gece_egit.uret ile arşiv (eğitim bölmeleri) örnekleri, gerçek sayısının --unut katı.
Dürüst ölçüm: --test ile verilen fotoğrafın kırpıntıları eğitime GİRMEZ (dışarıda bırakılan fotoğraf).
Kullanım: python inceayar_gece.py --egit tutanak-1 yeni3 --test tutanak-3 [--taban kod/en-iyi.pt] [--epoch 12] [--kat 30] [--cikis kod/inceayar-t1y3.json]
"""
import os, sys, json, argparse, time
import numpy as np
AD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AD, ".."))
import gece_egit as ge


def sis(a, rng):
    import cv2
    a = cv2.GaussianBlur(a, (0, 0), rng.uniform(0.6, 1.6))
    k = rng.uniform(0.35, 0.75)                           # kontrast kaybı
    return np.clip(a * k + rng.uniform(0.05, 0.3) * (1 - k), 0, 1)   # gri peçe (zemin artık tam siyah değil)


def bozukluk(a, rng):
    import cv2
    n = 28
    t = np.deg2rad(rng.uniform(-12, 12)); sh = rng.uniform(-0.25, 0.25); s = rng.uniform(0.85, 1.12)
    M = np.array([[s * np.cos(t), -np.sin(t) + sh, 0], [np.sin(t), s * np.cos(t), 0]], np.float32)
    M[:, 2] = np.array([n / 2, n / 2]) - M[:, :2] @ np.array([n / 2, n / 2]) + rng.uniform(-1.5, 1.5, 2)
    a = cv2.warpAffine(a, M, (n, n))
    if rng.random() < 0.4:
        ke = np.ones((2, 2), np.uint8)
        a = cv2.dilate(a, ke) if rng.random() < 0.5 else cv2.erode(a, ke)
    return np.clip(a + rng.normal(0, rng.uniform(0.02, 0.1), a.shape), 0, 1)


def eksiklik(a, rng):
    a = a.copy()
    if rng.random() < 0.5:   # dikdörtgen silme (mürekkep atlaması, leke)
        h, w = int(rng.integers(3, 9)), int(rng.integers(3, 9)); y, x = int(rng.integers(4, 24 - h)), int(rng.integers(4, 24 - w))
        a[y:y + h, x:x + w] = 0
    else:                    # kenardan kesik (kutu sıkı kırpılmış)
        f = int(rng.integers(2, 6)); k = int(rng.integers(4))
        if k == 0: a[:f + 4] = 0
        elif k == 1: a[-(f + 4):] = 0
        elif k == 2: a[:, :f + 4] = 0
        else: a[:, -(f + 4):] = 0
    return a


def kopya(a, rng):
    out = a.astype(np.float32)
    secim = [f for f in (sis, bozukluk, eksiklik) if rng.random() < 0.55] or [bozukluk]
    for f in secim:
        out = f(out, rng)
    return out.astype(np.float32)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--egit", nargs="+", required=True); ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--taban", default=os.path.join(AD, "kod", "en-iyi.pt")); ap.add_argument("--epoch", type=int, default=12)
    ap.add_argument("--kat", type=int, default=30); ap.add_argument("--unut", type=float, default=8.0); ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--cikis", default=os.path.join(AD, "kod", "inceayar.json"))
    a = ap.parse_args()
    import torch, torch.nn.functional as F
    torch.set_num_threads(6); torch.manual_seed(0); rng = np.random.default_rng(0)
    ge._KL = os.path.dirname(a.cikis)
    G = ge.gercek_kirpinti("kod")
    Xg = np.concatenate([G[k][0] for k in a.egit]); Yg = np.concatenate([G[k][1] for k in a.egit])
    ag = ge.ag_kur(12); ag.load_state_dict(torch.load(a.taban, weights_only=True))
    ge.isci_baslat("kod", 0)   # unutmama: aynı süreçte küçük üretim
    def dogr(k):
        return ge.dogruluk(ag, G[k][0], G[k][1])
    once = {k: round(dogr(k), 4) for k in G}
    print("taban", os.path.basename(a.taban), "eğitim kırpıntı", len(Yg), "öncesi", once, flush=True)
    opt = torch.optim.AdamW(ag.parameters(), a.lr, weight_decay=1e-4)
    t0 = time.time()
    for e in range(a.epoch):
        Xk = np.stack([kopya(Xg[i % len(Xg)], rng) for i in range(len(Xg) * a.kat)])
        Yk = np.tile(Yg, a.kat)
        Xu, Yu, _ = ge.uret((int(len(Yg) * a.unut), 1000 + e))
        X = np.concatenate([Xg, Xk, Xu.astype(np.float32) / 255.0]).astype(np.float32); Y = np.concatenate([Yg, Yk, Yu])
        ag.train(); p = np.random.permutation(len(X))
        for i in range(0, len(X), 128):
            ii = p[i:i + 128]
            k = F.cross_entropy(ag(torch.from_numpy(X[ii]).unsqueeze(1)), torch.from_numpy(Y[ii]), label_smoothing=0.05)
            opt.zero_grad(); k.backward(); opt.step()
        print("epoch %d | %s | %.0f sn" % (e + 1, " ".join("%s=%.3f" % (k, dogr(k)) for k in G), time.time() - t0), flush=True)
    son = {k: round(dogr(k), 4) for k in G}
    ge.disa_aktar(ag, a.cikis, ge.GOREV["kod"], {"taban": os.path.basename(a.taban), "egit": a.egit, "test": a.test, "once": once, "sonra": son,
                                                "kat": a.kat, "epoch": a.epoch, "artirma": "sis+bozukluk+eksiklik"})
    torch.save(ag.state_dict(), os.path.splitext(a.cikis)[0] + ".pt")
    print("SONUÇ öncesi", once, "sonrası", son, "(eğitime girenler:", a.egit, "| dışarıda:", a.test, ")")
