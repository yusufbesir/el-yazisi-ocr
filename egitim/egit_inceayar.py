# -*- coding: utf-8 -*-
"""
egit_inceayar.py - Gerçek tutanak kırpıntılarıyla ince ayar (egit.Ag mimarisi, düşük öğrenme hızı, kısa eğitim).
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

Kullanım (egitim/ klasöründen):
  python egit_inceayar.py --foto tutanak-1 [--foto tutanak-3 ...] [--taban model.json|model-emnist.json]
         [--cikis model-inceayar.json] [--js ../js/model-inceayar.js | --js-yok] [--epoch 12] [--lr 3e-4]
Veri: ../veri/tutanak-kirpinti/<foto>/ (etiketle.py çıktısı; hatalar.txt'deki dosyalar dışlanır).
  gerçek kırpıntılar afin/kalınlık/gürültü bozulmasıyla 20 kat çoğaltılır + gerçek sayısının ~5 katı "unutmama"
  karışımı (MNIST rakamları [EMNIST 'mnist' bölmesi] + veri.py sentetik T, '-', bayraklı '1').
Başlangıç ağırlığı: taban .pt dosyası varsa o, yoksa taban JSON'daki ağırlıklar Ag'ye yüklenir.
Varsayılan model dosyalarına (model.json, js/model.js) dokunmaz.
"""
import sys, os, json, time, argparse
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import egit, veri, veri_emnist, bolme

AD = os.path.dirname(os.path.abspath(__file__))
KIRPINTI = os.path.normpath(os.path.join(AD, "..", "veri", "tutanak-kirpinti"))
SINIFLAR = "0123456789T-"


def ag_yukle(taban):
    ag = egit.Ag()
    pt = os.path.splitext(taban)[0] + ".pt"
    if os.path.exists(pt):
        ag.load_state_dict(torch.load(pt)); kaynak = pt
    else:
        m = json.load(open(taban, encoding="utf-8"))["katmanlar"]
        K = [k for k in m if k["tip"] in ("conv", "fc")]
        with torch.no_grad():
            for modul, k in zip((ag.c1, ag.c2, ag.f1, ag.f2), K):
                modul.weight.copy_(torch.tensor(k["w"], dtype=torch.float32).reshape(modul.weight.shape))
                modul.bias.copy_(torch.tensor(k["b"], dtype=torch.float32))
        kaynak = taban
    return ag, kaynak


def gercek_yukle(fotolar):
    """(X (N,28,28) float32, Y (N,) int64, dışlanan sayısı). hatalar.txt: satır başına dosya adı (klasörlü ya da yalnız ad)."""
    xs, ys, dis = [], [], 0
    for f in fotolar:
        kl = os.path.join(KIRPINTI, f)
        hata = set()
        hy = os.path.join(kl, "hatalar.txt")
        if os.path.exists(hy):
            hata = {os.path.basename(s.strip().replace("\\", "/")) for s in open(hy, encoding="utf-8") if s.strip() and not s.startswith("#")}
        for i, ln in enumerate(open(os.path.join(kl, "etiketler.csv"), encoding="utf-8")):
            if i == 0 or not ln.strip():
                continue
            dosya, sinif = ln.split(",")[:2]
            if os.path.basename(dosya) in hata:
                dis += 1; continue
            xs.append(np.array(Image.open(os.path.join(kl, dosya)), np.float32) / 255.0)
            ys.append(SINIFLAR.index(sinif))
    return np.stack(xs), np.array(ys, np.int64), dis


def bozuk_kopya(a28, rng):
    """veri.rakam_bozuk ile aynı işlem, 0..1 girdi: 56 tuval -> afin -> kalınlık -> mnist_normalle -> gürültü."""
    t = np.zeros((56, 56), np.float32)
    t[14:42, 14:42] = a28
    t = veri.afin(t, rng, aci=10, kayma=0.25, olcek=(0.85, 1.15))
    t = veri.kalinlik(t, rng)
    return veri.son_gurultu(bolme.mnist_normalle(t), rng)


def unutmama(n, rng):
    X, Y = veri_emnist.idx("mnist", "train")
    birler = X[Y == 1]
    nd, nt, nr, nb = int(n * 0.55), int(n * 0.15), int(n * 0.15), n - int(n * 0.55) - 2 * int(n * 0.15)
    ii = rng.choice(len(X), nd, replace=False)
    xs = [X[ii].astype(np.float32) / 255.0]; ys = [Y[ii].astype(np.int64)]
    xs.append(np.stack([veri.t_uret(birler, rng) for _ in range(nt)])); ys.append(np.full(nt, 10, np.int64))
    xs.append(np.stack([veri.tire_uret(rng) for _ in range(nr)])); ys.append(np.full(nr, 11, np.int64))
    xs.append(np.stack([veri.bir_uret(rng) for _ in range(nb)])); ys.append(np.full(nb, 1, np.int64))
    return np.concatenate(xs), np.concatenate(ys)


def js_yaz(json_yol, js_yol, taban):
    d = open(json_yol, encoding="utf-8").read()
    open(js_yol, "w", encoding="utf-8").write(
        "/* El yazısı CNN ağırlıkları (egitim/%s; %s tabanından gerçek tutanak kırpıntılarıyla ince ayar). Otomatik üretildi (egit_inceayar.py); elle değiştirmeyin.\n"
        "   yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı */\n"
        '(typeof window !== "undefined" ? window : global).ELYAZISI_MODEL = %s;\n' % (os.path.basename(json_yol), taban, d))


def dogr(ag, X, Y):
    return egit.dogruluk(ag, torch.from_numpy(X).unsqueeze(1), torch.from_numpy(Y))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--foto", action="append", required=True)
    ap.add_argument("--taban", default=os.path.join(AD, "model.json"))
    ap.add_argument("--cikis", default=os.path.join(AD, "model-inceayar.json"))
    ap.add_argument("--js", default=os.path.join(AD, "..", "js", "model-inceayar.js"))
    ap.add_argument("--js-yok", action="store_true")
    ap.add_argument("--epoch", type=int, default=12)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--kat", type=int, default=20, help="gerçek kırpıntı çoğaltma katı")
    ap.add_argument("--unut", type=float, default=5.0, help="unutmama karışımı / gerçek sayısı")
    a = ap.parse_args()
    torch.set_num_threads(8); torch.manual_seed(0)
    rng = np.random.default_rng(0)
    t0 = time.time()
    ag, kaynak = ag_yukle(a.taban)
    Xg, Yg, dis = gercek_yukle(a.foto)
    print("taban: %s | gerçek kırpıntı %d (hatalar.txt ile dışlanan %d) sınıf sayıları %s" % (
        kaynak, len(Xg), dis, np.bincount(Yg, minlength=12).tolist()))
    boz = np.stack([bozuk_kopya(Xg[i % len(Xg)], rng) for i in range(len(Xg) * a.kat)])
    Xu, Yu = unutmama(int(len(Xg) * a.unut), rng)
    X = np.concatenate([Xg, boz, Xu]).astype(np.float32)
    Y = np.concatenate([Yg, np.tile(Yg, a.kat), Yu])
    print("eğitim kümesi %d (gerçek %d + bozuk %d + unutmama %d)" % (len(X), len(Xg), len(boz), len(Xu)))
    # kontrol kümeleri (eğitimde yok): MNIST test + sentetik T/-
    mx, my = veri_emnist.idx("mnist", "test")
    Xm, Ym = mx.astype(np.float32) / 255.0, my.astype(np.int64)
    on_m = dogr(ag, Xm, Ym); on_g = dogr(ag, Xg, Yg)
    print("öncesi: MNIST test %.4f | gerçek kırpıntı (eğitim verisi) %.4f" % (on_m, on_g))
    Xt, Yt = torch.from_numpy(X).unsqueeze(1), torch.from_numpy(Y)
    opt = torch.optim.Adam(ag.parameters(), a.lr)
    B = 64
    for e in range(a.epoch):
        ag.train(); perm = torch.randperm(len(Xt)); top = 0.0
        for i in range(0, len(Xt), B):
            ii = perm[i:i + B]
            k = F.cross_entropy(ag(Xt[ii]), Yt[ii])
            opt.zero_grad(); k.backward(); opt.step(); top += float(k.detach()) * len(ii)
        print("epoch %d kayıp %.4f | gerçek %.4f MNIST test %.4f (%.0f sn)" % (e + 1, top / len(Xt), dogr(ag, Xg, Yg), dogr(ag, Xm, Ym), time.time() - t0), flush=True)
    egit.disa_aktar(ag, a.cikis)
    torch.save(ag.state_dict(), os.path.splitext(a.cikis)[0] + ".pt")
    if not a.js_yok:
        js_yaz(a.cikis, a.js, os.path.basename(a.taban))
    print("SONUÇ: öğrenilen gerçek karakter %d | eğitim doğruluğu %.4f (önce %.4f) | MNIST test %.4f (önce %.4f) | %s | %.0f sn" % (
        len(Xg), dogr(ag, Xg, Yg), on_g, dogr(ag, Xm, Ym), on_m, a.cikis, time.time() - t0))
