# -*- coding: utf-8 -*-
"""
karsilastir.py - model.json dosyalarını gerçek tutanak kırpıntılarında (eğitime girmeyen) numpy çıkarımıyla karşılaştırır.
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait; yalnız ölçüm.
Kullanım: python karsilastir.py model1.json [model2.json ...]
"""
import os, sys, time
import numpy as np
AD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AD, ".."))
import cikarim_numpy as cn
from gece_egit import gercek_kirpinti

if __name__ == "__main__":
    G = gercek_kirpinti("kod")
    for yol in sys.argv[1:]:
        m = cn.model_yukle(yol); t = time.time(); n = 0; sat = []
        for ad, (X, Y) in G.items():
            Pt = cn.ileri_toplu(m, X); n += len(X)
            if "--dongu" in os.environ.get("KARSILASTIR", ""):
                Pd = np.array([cn.ileri(m, x) for x in X]); print("  döngü/toplu en büyük fark %.2e" % np.abs(Pd - Pt).max())
            P = Pt.argmax(1)
            sat.append("%s %d/%d (%.3f)" % (ad, int((P == Y).sum()), len(Y), (P == Y).mean()))
        print(os.path.relpath(yol, os.path.join(AD, "..", "..")), "|", " ".join(sat), "| %.1f ms/karakter" % ((time.time() - t) * 1000 / n))
