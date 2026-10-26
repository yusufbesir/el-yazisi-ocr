# yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
# SAHTE OCR servisi: motor/PROTOKOL.md'ye uyar, gerçek OCR yapmaz. Yalnız Electron entegrasyon testi içindir.
# Kullanım: python sahte_motor.py --servis   (stdin/stdout, satır başına bir JSON)
# Ortam: TUTANAK_SAHTE_PID=<dosya> verilirse süreç kimliği oraya yazılır (test servisi öldürebilsin).
import json, os, sys, time

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")


def yaz(o):
    sys.stdout.write(json.dumps(o, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def satir(sira, ham, kod, durum, adaylar, guven):
    y = 300 + (sira - 1) * 150
    return {
        "sira": sira,
        "stok": {"ham": ham, "secilen": kod if durum == "kabul" else None,
                 "aday": [{"kod": k, "mesafe": m} for k, m in adaylar], "guven": guven, "durum": durum},
        "adet": {"ham": "1", "deger": 1, "guven": 0.98, "durum": "kabul"},
        "hucreKutusu": [100, y, 700, y + 120], "adetKutusu": [720, y, 820, y + 120],
    }


SATIRLAR = [
    satir(1, "T14525", "T14525", "kabul", [("T14525", 0), ("T14575", 1)], 0.93),
    satir(2, "T14522", "T14522", "kabul", [("T14522", 0), ("T14572", 2)], 0.95),
    satir(3, "T20191-08", "T20191-08", "kabul", [("T20191-08", 0), ("T20191-06", 2)], 0.91),
    satir(4, "T2OO97-O1", None, "sor", [("T20097-01", 2), ("T20099-01", 2), ("T20091-01", 3)], 0.55),
    satir(5, "T20236-02", "T20236-02", "kabul", [("T20236-02", 0), ("T20236-01", 1)], 0.88),
    satir(6, "T20236-01", "T20236-01", "kabul", [("T20236-01", 0), ("T20236-02", 1)], 0.90),
    satir(7, "T2O136-02", None, "sor", [("T20136-02", 1), ("T20136-01", 2), ("T20138-02", 2)], 0.62),
    satir(8, "T20178-0l", None, "sor", [("T20178-01", 1), ("T20178-02", 1), ("T20176-01", 3)], 0.70),
]


def main():
    if "--servis" not in sys.argv:
        print("kullanım: sahte_motor.py --servis", file=sys.stderr)
        return 1
    pidyol = os.environ.get("TUTANAK_SAHTE_PID")
    if pidyol:
        with open(pidyol, "w") as f:
            f.write(str(os.getpid()))
    t0 = time.time()
    yaz({"olay": "hazir", "surum": "1.0", "motor": "SAHTE-MOTOR 0.1", "sure_ms": int((time.time() - t0) * 1000)})
    kok = None
    for h in sys.stdin:
        h = h.strip()
        if not h:
            continue
        try:
            i = json.loads(h)
        except ValueError:
            print("geçersiz json", file=sys.stderr)
            continue
        islem, rid = i.get("islem"), i.get("id")
        if islem == "kapat":
            return 0
        if islem == "kok":
            kok = os.path.realpath(i.get("yol", ""))
            continue
        if islem == "durum":
            yaz({"id": rid, "tamam": True, "motor": "SAHTE-MOTOR 0.1", "bekleyen": 0})
        elif islem == "oku":
            foto = os.path.realpath(i.get("foto", ""))
            if not kok or os.path.commonpath([kok, foto]) != kok or not os.path.isfile(foto):
                yaz({"id": rid, "tamam": False, "hata": "foto yolu izinli klasörde değil ya da yok"})
                continue
            time.sleep(0.2)
            yaz({"id": rid, "tamam": True, "sure_ms": 200, "yontem": "hucre", "goruntu": {"w": 1424, "h": 2000},
                 "satirlar": SATIRLAR, "uyari": ["sahte motor"]})
        else:
            yaz({"id": rid, "tamam": False, "hata": "bilinmeyen işlem"})
    return 0


sys.exit(main())
