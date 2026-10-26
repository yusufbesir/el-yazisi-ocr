# -*- coding: utf-8 -*-
"""test_servis.py - paddle_motor.py --servis protokol testi (alt süreç, stdout yalnız JSON mu, yanlış kabul 0 mu).
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
Çalıştır: venv\\Scripts\\python.exe motor\\test_servis.py"""
import json, os, shutil, subprocess, sys, tempfile, time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = json.load(open(os.path.join(KOK, "motor", "motor.json"), encoding="utf-8"))["python"]
dogru = json.load(open(os.path.join(KOK, "ornekler", "tutanak-1.dogru.json"), encoding="utf-8"))["satirlar"]
kodlar = json.load(open(os.path.join(KOK, "ornekler", "stok-kodlari.json"), encoding="utf-8"))
if not isinstance(kodlar, list):
    kodlar = kodlar.get("kodlar")
hatalar, jdisi = [], []


def kontrol(ad, kosul, ek=""):
    print(("TAMAM " if kosul else "HATA  ") + ad + (" " + str(ek) if ek else ""), flush=True)
    if not kosul:
        hatalar.append(ad)


gecici = tempfile.mkdtemp(prefix="ocrtest_")
dis = tempfile.mkdtemp(prefix="ocrdis_")
shutil.copy(os.path.join(KOK, "ornekler", "tutanak-1.jpg"), os.path.join(gecici, "x.jpg"))
shutil.copy(os.path.join(KOK, "ornekler", "tutanak-1.jpg"), os.path.join(dis, "y.jpg"))
t0 = time.time()
p = subprocess.Popen([PY, os.path.join(KOK, "motor", "paddle_motor.py"), "--servis"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=open(os.path.join(KOK, "motor", "gunluk", "_servis_stderr.txt"), "w"), cwd=KOK)


def oku():
    b = p.stdout.readline()
    if not b:
        return None
    s = b.decode("utf-8").rstrip("\r\n")
    try:
        return json.loads(s)
    except Exception:
        jdisi.append(s)
        return {"_json_degil": s}


def gonder(o):
    p.stdin.write((json.dumps(o, ensure_ascii=False) + "\n").encode("utf-8"))
    p.stdin.flush()


try:
    h = oku()
    kontrol("hazir olayı", h and h.get("olay") == "hazir", f"{h} (bekleme {time.time() - t0:.1f}s)")
    gonder({"id": "k", "islem": "kok", "yol": gecici})
    r = oku(); kontrol("kok", r and r.get("tamam"), r)
    t1 = time.time()
    gonder({"id": "i1", "islem": "oku", "foto": os.path.join(gecici, "x.jpg"), "kodlar": kodlar, "en_buyuk_kenar": 2000})
    r = oku(); sure = time.time() - t1
    kontrol("oku tamam", r and r.get("tamam") is True and r.get("yontem") == "sayfa+hucre", f"süre {sure:.1f}s (motor {r.get('sure_ms')}ms)")
    sat = r.get("satirlar", [])
    kontrol("satır sayısı 8", len(sat) == len(dogru), len(sat))
    yanlis = sum(1 for s, d in zip(sat, dogru) if s["stok"]["durum"] == "kabul" and s["stok"]["secilen"] != d["stok"])
    kabul = sum(1 for s in sat if s["stok"]["durum"] == "kabul")
    kontrol("yanlış kabul 0", yanlis == 0, f"kabul {kabul}, yanlış {yanlis}")
    kontrol("satırlarda kaynak alanı", all(s.get("kaynak") in ("sayfa", "hucre") for s in sat))
    kontrol("goruntu w/h", r["goruntu"]["w"] > 0 and r["goruntu"]["h"] > 0, r["goruntu"])
    gonder({"id": "i2", "islem": "oku", "foto": os.path.join(dis, "y.jpg"), "kodlar": kodlar})
    r = oku(); kontrol("kök dışı foto reddedildi", r and r.get("tamam") is False, r.get("hata") if r else r)
    gonder({"id": "i3", "islem": "oku", "foto": os.path.join(gecici, "..", os.path.basename(dis), "y.jpg"), "kodlar": kodlar})
    r = oku(); kontrol("..\\ ile kaçış reddedildi", r and r.get("tamam") is False)
    gonder("bozuk json değil ama dizgi")
    r = oku(); kontrol("geçersiz istek hata döndü, servis ayakta", r and r.get("tamam") is False, r)
    gonder({"id": "i4", "islem": "durum"})
    r = oku(); kontrol("durum", r and r.get("tamam") is True and r.get("bekleyen") == 0, r)
    gonder({"islem": "kapat"})
    try:
        kod = p.wait(timeout=20)
    except Exception:
        kod = None
    kontrol("temiz çıkış (kod 0)", kod == 0, kod)
    kontrol("stdout'ta JSON dışı satır yok", not jdisi, jdisi[:3])
finally:
    if p.poll() is None:
        p.kill()
    shutil.rmtree(gecici, ignore_errors=True)  # kendi ürettiğim geçici klasörler
    shutil.rmtree(dis, ignore_errors=True)
print(f"toplam {time.time() - t0:.1f}s; {'BAŞARILI' if not hatalar else 'BAŞARISIZ: ' + ', '.join(hatalar)}")
sys.exit(1 if hatalar else 0)
