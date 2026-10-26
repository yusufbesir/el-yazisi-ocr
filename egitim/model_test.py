# -*- coding: utf-8 -*-
"""
model_test.py - model.json dosyalarını (eski / emnist) aynı test kümelerinde ölçer (egitim-verisi.npz içindeki test_* dizileri + EMNIST mnist bölmesi normallenmiş hali).
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
Kullanım: python model_test.py model.json model-emnist.json
"""
import sys, json, numpy as np, torch, egit, veri_emnist as ve


def yukle(yol):
    k = json.load(open(yol, encoding="utf-8"))["katmanlar"]
    ag = egit.Ag()
    with torch.no_grad():
        for m, d in ((ag.c1, k[0]), (ag.c2, k[2]), (ag.f1, k[5]), (ag.f2, k[6])):
            m.weight.copy_(torch.tensor(d["w"]).view_as(m.weight)); m.bias.copy_(torch.tensor(d["b"]))
    return ag.eval()


if __name__ == "__main__":
    d = np.load(ve.os.path.join(ve.KOK, "veri", "emnist", "egitim-verisi.npz"))
    mx, my = ve.idx("mnist", "test")
    T = {k[3:]: (d[k].astype(np.float32) / 255.0, d["ty_" + k[3:]]) for k in d.files if k.startswith("tx_")}
    T["mnist (EMNIST bölmesi, ham)"] = T.pop("mnist")
    T["mnist (EMNIST bölmesi, mnist_normalle ile)"] = (np.stack([ve.norm(a) for a in mx]), my.astype(np.int64))
    sonuc = {}
    for yol in sys.argv[1:]:
        ag = yukle(yol)
        sonuc[yol] = {k: egit.dogruluk(ag, torch.from_numpy(x).unsqueeze(1), torch.from_numpy(y)) for k, (x, y) in T.items()}
    print(json.dumps(sonuc, ensure_ascii=False, indent=1))
