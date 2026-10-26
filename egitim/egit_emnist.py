# -*- coding: utf-8 -*-
"""
egit_emnist.py - egit.py ile AYNI mimari (egit.Ag), EMNIST + T-H-E verisiyle eğitim.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
Kullanım: python egit_emnist.py [epoch=8]
Çıktı: model-emnist.json, model-emnist.pt, ../js/model-emnist.js (window.ELYAZISI_MODEL); eski model.json/model.js değişmez.
"""
import sys, os, json, time
import numpy as np
import torch
import torch.nn.functional as F
import egit

AD = os.path.dirname(os.path.abspath(__file__))


def js_yaz(json_yol, js_yol):
    d = open(json_yol, encoding="utf-8").read()
    open(js_yol, "w", encoding="utf-8").write(
        "/* El yazısı CNN ağırlıkları (egitim/model-emnist.json; EMNIST + T-H-E ile eğitildi). Otomatik üretildi (egit_emnist.py); elle değiştirmeyin.\n"
        "   yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı */\n"
        '(typeof window !== "undefined" ? window : global).ELYAZISI_MODEL = ' + d + ";\n")


if __name__ == "__main__":
    epoch = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    torch.set_num_threads(14)
    torch.manual_seed(0)
    t0 = time.time()
    npz = os.path.join(AD, "..", "veri", "emnist", "egitim-verisi.npz")
    if not os.path.exists(npz):   # veri üretimi ayrı süreçte (torch'suz çalışanlar bellek tasarrufu)
        import subprocess
        subprocess.check_call([sys.executable, "-X", "utf8", os.path.join(AD, "veri_emnist.py"), npz])
    d = np.load(npz)
    Xn = d["x"].astype(np.float32) / 255.0; Yn = d["y"]
    bilgi = json.load(open(npz + ".bilgi.json", encoding="utf-8"))
    testler = {k[3:]: (d[k].astype(np.float32) / 255.0, d["ty_" + k[3:]]) for k in d.files if k.startswith("tx_")}
    print("veri hazır %.0f sn; toplam %s sınıf sayıları %s" % (time.time() - t0, Xn.shape, np.bincount(Yn).tolist()))
    print("kaynak dökümü:", bilgi)
    X = torch.from_numpy(Xn).unsqueeze(1); Y = torch.from_numpy(Yn)
    TT = {k: (torch.from_numpy(x.astype(np.float32)).unsqueeze(1), torch.from_numpy(y)) for k, (x, y) in testler.items()}
    ag = egit.Ag()
    B = 256
    opt = torch.optim.Adam(ag.parameters(), 2e-3)
    adim = epoch * ((len(X) + B - 1) // B)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, 6e-3, total_steps=adim)
    t1 = time.time()
    for e in range(epoch):
        ag.train()
        perm = torch.randperm(len(X)); top = 0.0
        for i in range(0, len(X), B):
            ii = perm[i:i + B]
            k = F.cross_entropy(ag(X[ii]), Y[ii])
            opt.zero_grad(); k.backward(); opt.step(); sch.step()
            top += float(k.detach()) * len(ii)
        print("epoch %d kayıp %.4f | %s (%.0f sn)" % (e + 1, top / len(X), " ".join(
            "%s %.4f" % (k, egit.dogruluk(ag, x, y)) for k, (x, y) in TT.items()), time.time() - t1), flush=True)
    yol = os.path.join(AD, "model-emnist.json")
    egit.disa_aktar(ag, yol)
    torch.save(ag.state_dict(), yol.replace(".json", ".pt"))
    js_yaz(yol, os.path.join(AD, "..", "js", "model-emnist.js"))
    sonuc = {k: egit.dogruluk(ag, x, y) for k, (x, y) in TT.items()}
    json.dump({"egitim_sure_sn": time.time() - t1, "epoch": epoch, "ornek": int(len(X)), "siniflar": np.bincount(Yn).tolist(),
               "kaynak": bilgi, "test": sonuc}, open(os.path.join(AD, "model-emnist-egitim.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("TEST:", sonuc)
