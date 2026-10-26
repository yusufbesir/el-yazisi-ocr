# -*- coding: utf-8 -*-
"""
olc.py - tutanak-1.jpg üzerinde uçtan uca ölçüm; OLCUM.md üretir.
Kullanım: python olc.py <foto> <dogru.json> <stok-kodlari.json> <model.json> <çıkış.md> <ara klasör> [etiket]
"""
import sys, os, json, subprocess, time
import numpy as np
from PIL import Image
import bolme, coz, cikarim_numpy as cn


def tesseract(png):
    try:
        r = subprocess.run(["tesseract", png, "stdout", "--psm", "7", "-l", "eng",
                            "-c", "tessedit_char_whitelist=T0123456789-"],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip().replace(" ", "")
    except Exception as e:
        return "?"


def kenarli(a, pay=20):
    """Beyaz kenar payı ekler (tesseract kenara yapışık yazıyı sevmez)."""
    return np.pad(a, pay, constant_values=255)


def main(foto, dogru_yol, kod_yol, model_yol, cikis, ara, etiket=""):
    os.makedirs(ara, exist_ok=True)
    dogru = json.load(open(dogru_yol, encoding="utf-8"))["satirlar"]
    grup = coz.kod_yukle(kod_yol)
    model = cn.model_yukle(model_yol)
    t0 = time.time()
    g, satirlar, sutunlar, sonuc = bolme.sayfa_isle(foto)
    veri = [s for s in sonuc if s["stok"]["maske"].sum() > 50][:len(dogru)]
    t_bolme = time.time() - t0
    try:
        import easyocr
        okuyucu = easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception as e:
        okuyucu = None
        print("EasyOCR yok:", e)
    satir_md, ist = [], {"ham": 0, "kod": 0, "yanlis_kabul": 0, "sor": 0, "tess": 0, "tess2": 0, "easy": 0, "adet": 0, "karakter": 0, "karakter_top": 0}
    t1 = time.time()
    for i, s in enumerate(veri):
        d = dogru[i]
        st = s["stok"]
        P = np.array([cn.ileri(model, c) for c in st["karakterler"]]) if len(st["karakterler"]) else np.zeros((0, 12))
        tire = [k[4] for k in st["kutular"]]
        r = coz.stok_coz(P, grup, tire)
        # adet
        Pa = np.array([cn.ileri(model, c) for c in s["adet"]["karakterler"]]) if len(s["adet"]["karakterler"]) else np.zeros((0, 12))
        a = coz.adet_coz(Pa)
        # karşılaştırma okuyucuları: aynı hücre kırpıntısı
        yol_maske = os.path.join(ara, "olc_s%d_maske.png" % (i + 1))
        yol_gri = os.path.join(ara, "olc_s%d_gri.png" % (i + 1))
        Image.fromarray(kenarli((~st["maske"]).astype(np.uint8) * 255)).save(yol_maske)
        Image.fromarray(kenarli(st["gri"])).save(yol_gri)
        tess_temiz, tess_gri = tesseract(yol_maske), tesseract(yol_gri)
        if okuyucu is not None:
            try:
                easy = "".join(okuyucu.readtext(yol_gri, allowlist="T0123456789-", detail=0))
            except Exception as e:
                easy = "hata"
        else:
            easy = "-yok-"
        iyi = r["adaylar"][0][0] if r["adaylar"] else ""
        kod_dogru = iyi == d["stok"]
        kabul = r["durum"] == "tamam"
        yk = kabul and not kod_dogru
        ist["ham"] += r["ham"] == d["stok"]; ist["kod"] += kod_dogru; ist["yanlis_kabul"] += yk
        ist["sor"] += not kabul; ist["tess"] += tess_temiz == d["stok"]; ist["tess2"] += tess_gri == d["stok"]
        ist["easy"] += easy == d["stok"]; ist["adet"] += a["adet"] == d["adet"]
        if len(r["ham"]) == len(d["stok"]):
            ist["karakter_top"] += len(d["stok"]); ist["karakter"] += sum(x == y for x, y in zip(r["ham"], d["stok"]))
        aday = ", ".join("%s (%.1f)" % (k, p) for k, p in r["adaylar"])
        satir_md.append("| %d | %s | %s | %s%s | %.1f | %s | %s | %s | %s |" % (
            i + 1, d["stok"], r["ham"], iyi, "" if kod_dogru else " (X)", r["guven"],
            "tamam" if kabul else "sor", tess_temiz, tess_gri, easy))
        print(satir_md[-1], "| adet=%s" % a["adet"], "| adaylar:", aday)
    t_cnn = time.time() - t1
    n = len(veri)
    md = ["# Ölçüm: tutanak-1.jpg %s" % etiket, "",
          "Tablo: %d veri satırı. CNN = `%s`; çözümleme = `coz.py` (13.127 koddan biçime uyan %d aday)." % (
              n, os.path.basename(model_yol), sum(len(v[0]) for v in grup.values())), "",
          "| Satır | Doğru | CNN ham | Kısıtlı en iyi | Güven (nat) | Durum | Tesseract (temiz maske) | Tesseract (ham gri) | EasyOCR |",
          "|---|---|---|---|---|---|---|---|---|"] + satir_md + ["",
          "## Özet", "",
          "- Kod doğruluğu (kısıtlı, en iyi aday): **%d/%d**" % (ist["kod"], n),
          "- Ham CNN tam eşleşme: %d/%d; uzunluğu doğru satırlarda karakter doğruluğu: %d/%d" % (ist["ham"], n, ist["karakter"], ist["karakter_top"]),
          "- Yanlış-kabul (durum=tamam ama kod yanlış): **%d**; 'sor' durumuna düşen: %d" % (ist["yanlis_kabul"], ist["sor"]),
          "- Adet doğru: %d/%d" % (ist["adet"], n),
          "- Tesseract tam eşleşme: temiz maske %d/%d, ham gri %d/%d; EasyOCR %d/%d" % (ist["tess"], n, ist["tess2"], n, ist["easy"], n),
          "- Süre: bölme %.1f sn (tam sayfa, numpy), CNN+çözümleme %.1f sn (numpy referans, JS'e göre yavaş)" % (t_bolme, t_cnn), ""]
    if os.path.exists(cikis):
        base, ext = os.path.splitext(cikis)
        cikis = base + "_" + (etiket or time.strftime("%H%M%S")) + ext
    open(cikis, "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md[-12:]))
    return ist


if __name__ == "__main__":
    main(*sys.argv[1:8])
