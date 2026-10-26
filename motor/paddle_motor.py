# -*- coding: utf-8 -*-
# 2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: stok kodu deseni T+4/5 rakam
# 2026-10-25 [Claude#RKxwbX] (devralan): iade formu için gevşek tablo yolu (bolme.SON), yön düzeltme (ön adım)
"""paddle_motor.py - masaüstü "güçlü OCR motoru": tutanak hücrelerini PaddleOCR ile okur, stok kodunu listeyle kısıtlar.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
Protokol: motor/PROTOKOL.md. Servis: python motor/paddle_motor.py --servis
Ölçüm: python motor/paddle_motor.py --olc foto dogru.json stok-kodlari.json [--json cikti.json]
Fiş (yön düzeltmeli tam sayfa metin): python motor/paddle_motor.py --fis foto... [--json cikti.json]
Not: torch bu süreçte ASLA yüklenmez (Paddle ile çakışır). stdout yalnız JSON satırı (servis modu)."""
import os, sys, json, re, time, tempfile
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("HF_HUB_OFFLINE", "1")  # model yerel önbellekte; ağ yok

# gerçek stdout'u sakla; Paddle'ın kendi print'leri stderr'e gitsin
_STDOUT = sys.stdout
sys.stdout = sys.stderr
try:
    _STDOUT.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
from PIL import Image

SURUM = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "egitim"))

KOD_RE = re.compile(r"^T\d{4,5}(-\d{2})?$")
H = {"O": "0", "I": "1", "L": "1", "S": "5", "B": "8", "Z": "2", "G": "6", "Q": "0", "D": "0", "U": "0", "Y": "7"}


def yaz(o):
    _STDOUT.write(json.dumps(o, ensure_ascii=False) + "\n")
    _STDOUT.flush()


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- eşleme
def temizle(s):
    s = (s or "").upper().replace("—", "-").replace("–", "-")
    s = "".join(H.get(c, c) for c in s)
    return re.sub(r"[^T0-9-]", "", s)


def lev(a, b):
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        yeni = [i]
        for j, cb in enumerate(b, 1):
            yeni.append(min(dp[j] + 1, yeni[j - 1] + 1, dp[j - 1] + (ca != cb)))
        dp = yeni
    return dp[-1]


def adaylar(ham, kodlar):
    """(ilk 3 [(mesafe,kod)], d1, d2). T'siz yazılmışsa başına T eklenmiş hali de denenir; en küçük mesafe kazanır."""
    t = temizle(ham)
    if not t or not kodlar:
        return [], 99, 99
    ts = [t] + (["T" + t] if not t.startswith("T") else [])
    sirali = sorted((min(lev(x, k) for x in ts), k) for k in kodlar)
    d1 = sirali[0][0]
    d2 = sirali[1][0] if len(sirali) > 1 else 99
    return sirali[:3], d1, d2


def stok_karar(ham, guven, kodlar):
    sirali, d1, d2 = adaylar(ham, kodlar)
    if not sirali:
        return {"ham": ham, "secilen": None, "aday": [], "guven": round(float(guven), 3), "durum": "bos"}, 99, 99
    durum = "kabul" if (d1 <= 1 and d2 > d1 and guven >= 0.80) else "sor"
    return {"ham": ham, "secilen": sirali[0][1],
            "aday": [{"kod": k, "mesafe": d} for d, k in sirali],
            "guven": round(float(guven), 3), "durum": durum}, d1, d2


def adet_karar(ham, guven):
    r = re.sub(r"[^0-9]", "", ham or "")
    g = round(float(guven), 3)
    if not r:
        return {"ham": ham, "deger": 1, "guven": g, "durum": "bos"}
    v = int(r)
    esik = 0.6 if re.fullmatch(r"[0-9]", (ham or "").strip()) else 0.8  # yalnız tek karakterli rakam okumasında 0.6
    if v < 1 or v > 99 or guven < esik:
        return {"ham": ham, "deger": v, "guven": g, "durum": "sor"}
    return {"ham": ham, "deger": v, "guven": g, "durum": "kabul"}


# ---------------------------------------------------------------- motor
def motor_ayar():
    """motor.json'dan det_model/rec_model (yoksa PaddleOCR varsayılanı)."""
    try:
        d = json.load(open(os.path.join(HERE, "motor.json"), encoding="utf-8"))
        return d.get("det_model"), d.get("rec_model")
    except Exception:
        return None, None


class Motor:
    def __init__(self, det=None, rec=None):
        t0 = time.time()
        if det is None and rec is None:
            det, rec = motor_ayar()
        self.det, self.rec_ad = det, rec
        import paddleocr
        from paddleocr import TextRecognition, PaddleOCR
        self.surum = "PaddleOCR " + getattr(paddleocr, "__version__", "?")
        self.rec = TextRecognition(model_name="PP-OCRv5_server_rec", enable_mkldnn=False)
        self.tam = None
        try:
            ekstra = {}
            if det:
                ekstra["text_detection_model_name"] = det
            if rec:
                ekstra["text_recognition_model_name"] = rec
            self.tam = PaddleOCR(lang="en", enable_mkldnn=False, use_textline_orientation=False,
                                 use_doc_orientation_classify=False, use_doc_unwarping=False, **ekstra)
        except Exception as e:
            log("tam sayfa motoru yüklenemedi", type(e).__name__, str(e)[:200])
        self.tani(np.full((64, 256, 3), 255, np.uint8))  # ısınma
        if self.tam is not None:   # [2026-10-26 Claude#HtqxxY] det modelini de ısıt: aksi halde ilk sayfa ~20-30 sn fazla sürer
            try:
                isi = np.full((320, 480, 3), 255, np.uint8)
                isi[140:180, 60:420] = 0
                list(self.tam.predict(isi))
            except Exception as e:
                log("det ısınma hata", type(e).__name__, str(e)[:120])
        self.yukleme_ms = int((time.time() - t0) * 1000)

    def tani(self, bgr):
        try:
            for s in self.rec.predict(bgr, batch_size=1):
                d = s if isinstance(s, dict) else getattr(s, "json", {}).get("res", {})
                return str(d.get("rec_text", "")), float(d.get("rec_score", 0.0))
        except Exception as e:
            log("tani hata", type(e).__name__, str(e)[:200])
        return "", 0.0

    def sayfa(self, rgb):
        """Tam sayfa det+rec: [(x0,y0,x1,y1,metin,guven)]."""
        if self.tam is None:
            raise RuntimeError("tam sayfa motoru yok")
        out = []
        for s in self.tam.predict(rgb):
            d = s if isinstance(s, dict) else getattr(s, "json", {}).get("res", {})
            kutular = d.get("rec_boxes")
            if kutular is None or len(kutular) == 0:
                kutular = [[min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q)] for q in d.get("rec_polys", d.get("dt_polys", []))]
            for k, m, sc in zip(kutular, d.get("rec_texts", []), d.get("rec_scores", [])):
                out.append((float(k[0]), float(k[1]), float(k[2]), float(k[3]), str(m), float(sc)))
        return out

    def hucre(self, gri2d):
        a = np.pad(np.asarray(gri2d, dtype=np.uint8), 24, constant_values=255)
        return self.tani(np.stack([a, a, a], -1))


_CNN = {"model": None, "grup": {}, "yol": None}   # yol: --cnn <model.json> ya da motor.json "cnn_model" (varsayılan egitim/model.json)


def cnn_model():
    if _CNN["model"] is None:
        import cikarim_numpy as cn
        yol = _CNN["yol"]
        if not yol:
            try:
                yol = json.load(open(os.path.join(HERE, "motor.json"), encoding="utf-8")).get("cnn_model")
            except Exception:
                yol = None
        if not yol:
            yol = os.path.join(HERE, "..", "egitim", "model.json")
        elif not os.path.isabs(yol):
            yol = os.path.join(HERE, "..", yol) if not os.path.exists(yol) else yol
        _CNN["model"] = cn.model_yukle(yol)
    return _CNN["model"]


def cnn_grup(kodlar):
    import coz
    anahtar = hash(tuple(kodlar))
    if anahtar not in _CNN["grup"]:
        _CNN["grup"] = {anahtar: coz.kod_dizinleri(sorted(set(kodlar)))}
    return _CNN["grup"][anahtar]


def cnn_oku(st, ad, kodlar):
    """Bizim CNN: stok için kısıtlı adaylar [(kod,puan)], adet için (deger,guven)."""
    import coz, cikarim_numpy as cn
    m = cn_model = cnn_model()
    kar = st["karakterler"]
    P = cn.ileri_toplu(m, np.stack(kar)).astype(np.float64) if len(kar) else np.zeros((0, 12))   # [2026-10-26 Claude#HtqxxY] toplu, aynı sonuç
    if ad == "adet":
        r = coz.adet_coz(P)
        return r["adet"] if r["ham"] else None, r["guven"]
    if not kodlar:
        return [], 0.0
    r = coz.stok_coz(P, cnn_grup(kodlar), [k[4] for k in st["kutular"]])
    return r["adaylar"], r["guven"]


def kucult(yol, en_buyuk=2000):
    im = Image.open(yol)
    im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > en_buyuk:
        o = en_buyuk / max(w, h)
        im = im.resize((int(round(w * o)), int(round(h * o))), Image.LANCZOS)
    return im


def temiz_gri(maske):
    return (255 - (np.asarray(maske).astype(np.uint8) * 255)).astype(np.uint8)


def en_iyi_oku(motor, hucre):
    """gri ve temiz ile oku; (secim_adi, metin, guven, {ad:(metin,guven)})."""
    bilgi = {}
    gri = hucre.get("gri")
    if gri is not None:
        bilgi["gri"] = motor.hucre(gri)
    bilgi["temiz"] = motor.hucre(temiz_gri(hucre["maske"]))
    ad = max(bilgi, key=lambda k: bilgi[k][1])
    return ad, bilgi[ad][0], bilgi[ad][1], bilgi


# ---------------------------------------------------------------- görüntü yönü (ön adım)
YON_ATLAMA_ACIK = False   # bkz. sayfa_oku; 180° sorunu çözülmeden açılmaz
YON_ESIK = {"kenar": 960, "kalite_yeter": 150.0, "guven_yeter": 0.80, "kazanc": 1.5}


def yon_kalitesi(motor, im):
    """Küçültülmüş görüntüde tam sayfa det+rec; kalite = Σ (karakter sayısı × güven) (güven >= 0.5 olanlar). Dönüş (kalite, ortalama güven, madde)."""
    kes = motor.sayfa(np.asarray(im))
    top, n, say = 0.0, 0, 0
    for k in kes:
        m, g = k[4], k[5]
        if g >= 0.5:
            top += sum(c.isalnum() for c in m) * g
            n += 1
            say += g
    return top, (say / n if n else 0.0), n


def yon_bul(motor, im, esik=None):
    """PIL RGB görüntünün 'dik' olması için saat yönünün TERSİNE kaç derece (0/90/180/270) döndürülmesi gerektiğini bulur.
    Yöntem: PaddleOCR'ın doc-orientation modeli yerelde yok; bunun yerine 4 dönüşte okuma kalitesini karşılaştırırız.
    0° yeterince iyiyse (kalite >= kalite_yeter ve ort. güven >= guven_yeter) diğerleri denenmez. Dönüş (derece, ayrıntı sözlüğü)."""
    e = dict(YON_ESIK, **(esik or {}))
    w, h = im.size
    o = e["kenar"] / float(max(w, h))
    kucuk = im.resize((max(1, int(round(w * o))), max(1, int(round(h * o)))), Image.LANCZOS) if o < 1 else im
    sonuc = {}
    q0, g0, n0 = yon_kalitesi(motor, kucuk)
    sonuc[0] = {"kalite": round(q0, 1), "ort_guven": round(g0, 3), "madde": n0}
    if q0 >= e["kalite_yeter"] and g0 >= e["guven_yeter"]:
        return 0, {"karar": "0 yeterli", "olcum": sonuc}
    for aci in (90, 270, 180):
        q, g, n = yon_kalitesi(motor, kucuk.rotate(aci, expand=True))
        sonuc[aci] = {"kalite": round(q, 1), "ort_guven": round(g, 3), "madde": n}
    en = max(sonuc, key=lambda a: sonuc[a]["kalite"])
    if en != 0 and sonuc[en]["kalite"] < e["kazanc"] * max(sonuc[0]["kalite"], 1.0):
        en = 0
    return en, {"karar": "en iyi kalite", "olcum": sonuc}


def sayfa_oku(motor, foto, kodlar, en_buyuk=2000, yon_duzelt=True):
    """Dönüş: (yanıt_dict, ölçüm_ek_listesi)."""
    import bolme
    im = kucult(foto, en_buyuk)
    yon_bilgi = None
    # [2026-10-26 07:55 Claude#HtqxxY] KAPALI: 180° ters fotoğrafta da atlıyordu (verifier); 180° denetimi de yakalamadı (t1-180 testi).
    # Düzeltilene kadar eski davranış: yön araması her zaman yapılır.
    if yon_duzelt and YON_ATLAMA_ACIK:
        # [2026-10-26 Claude#HtqxxY] hız: dik fotoğrafta tablo çizgileri 0°'de bulunuyorsa yön araması (tam sayfa Paddle, ~15-40 sn) atlanır
        tmp0 = tempfile.NamedTemporaryFile(suffix=".png", delete=False); tmp0.close()
        try:
            im.save(tmp0.name)
            _g, _sat, _sut, _son = bolme.sayfa_isle(tmp0.name)
            # yalnız asıl (sıkı) tablo yolu ve yatay satırlı tablo: gevşek yol dönük görüntüde de çizgi bulabilir
            if bolme.SON.get("yol") != "gevsek" and len(_sat) >= 4 and len(_sut) >= 3:
                # [2026-10-26 verifier bulgusu] 180° ters fotoğrafta da tablo bulunur: en çok mürekkepli stok hücresini
                # 0° ve 180° tanıyıp karşılaştır (2 hücre tanıma, ~1-2 sn); 180° açıkça iyiyse tam yön aramasına düş
                dolu = [s for s in _son if s["stok"]["maske"].sum() > 50]
                ters = False
                if dolu:
                    h = max(dolu, key=lambda s: int(s["stok"]["maske"].sum()))["stok"]
                    gr = h.get("gri") if h.get("gri") is not None else temiz_gri(h["maske"])
                    _, g0 = motor.hucre(gr)
                    _, g180 = motor.hucre(np.ascontiguousarray(np.asarray(gr)[::-1, ::-1]))
                    ters = g180 > g0 + 0.15
                if not ters:
                    yon_duzelt, yon_bilgi = False, {"karar": "0° tablo bulundu, yön araması atlandı"}
        except Exception:
            pass
        finally:
            try:
                os.unlink(tmp0.name)  # kendi ürettiğim geçici dosya
            except Exception:
                pass
    if yon_duzelt:
        try:
            aci_y, yon_bilgi = yon_bul(motor, im)
            if aci_y:
                im = im.rotate(aci_y, expand=True)
        except Exception as e:
            yon_bilgi = {"karar": "hata: " + str(e)[:80]}
    W, Hh = im.size
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        im.save(tmp.name)
        try:
            g, satirlar, sutunlar, sonuc = bolme.sayfa_isle(tmp.name)
        except Exception as e:
            return {"yontem": "sayfa", "goruntu": {"w": W, "h": Hh}, "satirlar": [], "metinler": [], "yon": yon_bilgi,
                    "uyari": ["tablo bulunamadı: " + str(e)[:120]]}, []
    finally:
        try:
            os.unlink(tmp.name)  # kendi ürettiğim geçici dosya
        except Exception:
            pass
    H_, W_ = g.shape
    pay = bolme.AYAR["hucre_ic_pay"]
    sn_s, sn_a = bolme.SON["stok_sutun"], bolme.SON["adet_sutun"]   # eski yol: 1/3; iade formu (gevşek yol): 1/4
    renkli = np.asarray(im)
    if bolme.SON["aci"]:
        renkli = bolme.dondur_gri(renkli, bolme.SON["aci"])         # tablo koordinatları eğiklik düzeltilmiş görüntüde
    uyari = []
    kutular = []
    try:
        PAY = 20
        tx0 = max(0, int(sutunlar[0]) - PAY); tx1 = min(W_, int(sutunlar[-1]) + PAY)
        ty0 = max(0, int(satirlar[0]) - PAY); ty1 = min(H_, int(satirlar[-1]) + PAY)
        kes = motor.sayfa(renkli[ty0:ty1, tx0:tx1])
        kutular = [(k[0] + tx0, k[1] + ty0, k[2] + tx0, k[3] + ty0, k[4], k[5]) for k in kes]
    except Exception as e:
        uyari.append("tam sayfa okuma başarısız: " + str(e)[:100])

    def sutundan(r, sn):
        """Satır r, sütun sn içine merkezi düşen tespitleri soldan sağa birleştir."""
        ya, yb = satirlar[r], satirlar[r + 1]
        xa, xb = sutunlar[sn], sutunlar[sn + 1]
        L = sorted((k for k in kutular if ya <= (k[1] + k[3]) / 2 < yb and xa <= (k[0] + k[2]) / 2 < xb), key=lambda k: k[0])
        if not L:
            return "", 0.0
        return " ".join(k[4] for k in L), min(k[5] for k in L)

    def kirp3(h):
        m = np.asarray(h["maske"])[3:-3, 3:-3]
        gr = h.get("gri")
        return {"maske": m, "gri": None if gr is None else np.asarray(gr)[3:-3, 3:-3]}

    liste, ek = [], []
    sira = 0
    for s in sonuc:
        if s["stok"]["maske"].sum() <= 50:
            continue
        r = s["satir"]
        if bolme.SON["yol"] == "gevsek":
            # iade formunda başlık satırı (Sıra | Barkod / Referans No | ...) çıktıya girmesin: satırdaki tam sayfa metninden anla
            ust = " ".join(k[4] for k in kutular if satirlar[r] <= (k[1] + k[3]) / 2 < satirlar[r + 1]).lower()
            if re.search(r"barkod|referans|miktar|beden|renk|ürün adı|urun adi", ust):
                uyari.append("başlık satırı atıldı")
                continue
        sira += 1
        y0, y1 = int(satirlar[r]) + pay, int(satirlar[r + 1]) - pay
        sk = [int(sutunlar[sn_s]) + pay, y0, int(sutunlar[sn_s + 1]) - pay, y1]
        ak = [int(sutunlar[sn_a]) + pay, y0, int(sutunlar[sn_a + 1]) - pay, y1]
        # stok: önce tam sayfa metni, yoksa hücre tanıma
        sm, sg = sutundan(r, sn_s)
        # [2026-10-26 Claude#HtqxxY] hız: hücre tanıma (2 Paddle çağrısı) yalnız tam sayfa metni yetersizse
        if sum(c.isdigit() for c in sm) >= 2:
            hm, hg, bilgi = "", 0.0, {}
        else:
            _, hm, hg, bilgi = en_iyi_oku(motor, s["stok"])
        if sum(c.isdigit() for c in sm) >= 2:
            kaynak, metin, guven = "sayfa", sm, sg
        elif hm.strip():
            kaynak, metin, guven = "hucre", hm, hg
        else:
            kaynak, metin, guven = "hucre", "", 0.0
        stok, d1, d2 = stok_karar(metin, guven, kodlar)
        stok["kaynak"] = kaynak
        try:
            cad, cg = cnn_oku(s["stok"], "stok", kodlar)
        except Exception as e:
            cad, cg = [], 0.0
            uyari.append("cnn hata: " + str(e)[:80])
        cilk = cad[0][0] if cad else None
        stok["cnn"] = {"secilen": cilk, "guven": round(float(cg), 3)}
        stok["uzlasma"] = bool(cilk is not None and cilk == stok["secilen"])
        if stok["durum"] == "kabul" and not stok["uzlasma"]:
            stok["durum"] = "sor"
        if cad:
            mevcut = [a["kod"] for a in stok["aday"]]
            t_ = temizle(metin)
            for k, _p in cad:
                if k not in mevcut:
                    stok["aday"].append({"kod": k, "mesafe": min(lev(x, k) for x in ([t_, "T" + t_] if t_ and not t_.startswith("T") else [t_])), "kaynak": "cnn"})
                    mevcut.append(k)
        # adet: önce tam sayfa, yoksa hücre (3 px kenar kırpılmış)
        if s["adet"]["maske"].sum() < 15:
            adet = adet_karar("", 1.0); adet["kaynak"] = "hucre"
        else:
            am, ag = sutundan(r, sn_a)
            if re.sub(r"[^0-9]", "", am):
                adet = adet_karar(am, ag); adet["kaynak"] = "sayfa"
            else:
                _, am, ag, _ = en_iyi_oku(motor, kirp3(s["adet"]))
                adet = adet_karar(am, ag); adet["kaynak"] = "hucre"
        try:
            cad_, cag = cnn_oku(s["adet"], "adet", None)
        except Exception:
            cad_, cag = None, 0.0
        adet["cnn"] = {"deger": cad_, "guven": round(float(cag), 3)}
        adet["uzlasma"] = (cad_ == adet["deger"])
        if adet["durum"] == "kabul" and not adet["uzlasma"]:
            adet["durum"] = "sor"
        if adet["durum"] == "kabul" and bolme.SON["yol"] == "gevsek":
            # iade formu (yeni yazarlar): Paddle ve CNN birlikte "7" okudu, doğrusu 1 (ornek-7) -> adet otomatik kabulü bu formda kapalı
            adet["durum"] = "sor"
            adet["not"] = "iade formu: adet otomatik kabul kapalı"
        liste.append({"sira": sira, "kaynak": kaynak, "stok": stok, "adet": adet, "hucreKutusu": sk, "adetKutusu": ak})
        ek.append({"cnn": stok["cnn"], "uzlasma": stok["uzlasma"], "adet_murekkep": int(s["adet"]["maske"].sum()), "gri": bilgi.get("gri"), "temiz": bilgi.get("temiz"),
                   "sayfa": (sm, sg), "kaynak": kaynak, "d1": d1, "d2": d2})
    # tablonun altındaki alt bilgi satırlarını (toplam vb.) at: sondan başlayarak adet hücresi boş VE stokta 3'ten az rakam olanlar
    while liste and ek[-1]["adet_murekkep"] < 15 and sum(c.isdigit() for c in liste[-1]["stok"]["ham"]) < 3:
        liste.pop(); ek.pop()
        uyari.append("tablo altı satır atıldı")
    return {"yontem": "sayfa+hucre", "goruntu": {"w": int(W_), "h": int(H_)}, "satirlar": liste, "uyari": uyari, "yon": yon_bilgi, "tablo": bolme.SON["yol"]}, ek


# ---------------------------------------------------------------- tadilat fişi (serbest alanlar): yön düzeltmeli tam sayfa okuma
def fis_oku(motor, foto, kenar=1600):
    """Tam sayfa okuma; önce yön düzeltilir. Dönüş: {"yon", "yon_bilgi", "sure_sn", "satirlar":[{"metin","guven","kutu"}]}"""
    t0 = time.time()
    im = kucult(foto, kenar)
    aci, bilgi = yon_bul(motor, im)
    if aci:
        im = im.rotate(aci, expand=True)
    kes = motor.sayfa(np.asarray(im))
    kes.sort(key=lambda k: ((k[1] + k[3]) / 2.0 // 25, k[0]))
    return {"yon": aci, "yon_bilgi": bilgi, "sure_sn": round(time.time() - t0, 1), "goruntu": list(im.size),
            "satirlar": [{"metin": k[4], "guven": round(k[5], 2), "kutu": [int(k[0]), int(k[1]), int(k[2]), int(k[3])]} for k in kes]}


# ---------------------------------------------------------------- servis
def servis():
    try:
        motor = Motor()
    except Exception as e:
        yaz({"olay": "hata", "mesaj": f"{type(e).__name__}: {e}"[:300]})
        sys.exit(2)
    yaz({"olay": "hazir", "surum": SURUM, "motor": motor.surum, "sure_ms": motor.yukleme_ms})
    kok = None
    for satir in sys.stdin:
        satir = satir.strip()
        if not satir:
            continue
        iid = None
        try:
            ist = json.loads(satir)
            iid = ist.get("id")
            islem = ist.get("islem")
            if islem == "kapat":
                break
            if islem == "kok":
                kok = os.path.realpath(ist["yol"])
                yaz({"id": iid, "tamam": True, "kok": kok})
            elif islem == "durum":
                yaz({"id": iid, "tamam": True, "motor": motor.surum, "bekleyen": 0})
            elif islem == "oku":
                t0 = time.time()
                if not kok:
                    raise ValueError("izinli kök bildirilmedi (islem:kok)")
                foto = os.path.realpath(ist["foto"])
                try:
                    ic = os.path.normcase(os.path.commonpath([foto, kok])) == os.path.normcase(kok)
                except ValueError:
                    ic = False
                if not ic:
                    raise PermissionError("foto izinli klasörün dışında")
                if not os.path.isfile(foto):
                    raise FileNotFoundError("foto yok")
                kodlar = [k for k in (ist.get("kodlar") or []) if isinstance(k, str) and KOD_RE.match(k)]
                y, _ = sayfa_oku(motor, foto, kodlar, int(ist.get("en_buyuk_kenar") or 2000), ist.get("yon_duzelt", True) is not False)
                y.update({"id": iid, "tamam": True, "sure_ms": int((time.time() - t0) * 1000)})
                yaz(y)
            else:
                raise ValueError("bilinmeyen işlem")
        except Exception as e:
            yaz({"id": iid, "tamam": False, "hata": f"{type(e).__name__}: {e}"[:300]})


# ---------------------------------------------------------------- ölçüm
def olc(foto, dogru_yol, kod_yol, json_cikti=None, det=None, rec=None):
    dogru = json.load(open(dogru_yol, encoding="utf-8"))["satirlar"]
    kod = json.load(open(kod_yol, encoding="utf-8"))
    if not isinstance(kod, list):
        kod = kod.get("kodlar") or list(kod)
    kod = [k for k in kod if KOD_RE.match(k)]
    motor = Motor(det, rec)
    P0 = print
    t0 = time.time()
    y, ek = sayfa_oku(motor, foto, kod)
    sure = time.time() - t0
    satirlar = y["satirlar"]

    def P(*a):
        print(*a, file=_STDOUT, flush=True)

    P(f"yöntem={y['yontem']} görüntü={y['goruntu']} det={motor.det} rec={motor.rec_ad} okunan satır={len(satirlar)} doğru satır={len(dogru)} yükleme={motor.yukleme_ms}ms okuma={sure:.1f}s")
    P("sıra | doğru | ham sayfa | ham gri | ham temiz | cnn | seçilen [kaynak] | d1/d2 | güven | durum | doğru mu | adet")
    kod_dogru = ac_dogru = yanlis = sor = adet_d = kodlu = 0
    sat = []
    for i, (s, e) in enumerate(zip(satirlar, ek)):
        if i >= len(dogru):
            break
        d = dogru[i]
        dk = d.get("stok") or ""
        st = s["stok"]
        ilk = st["aday"][0]["kod"] if st["aday"] else None
        if dk:
            kodlu += 1
            kod_dogru += (ilk == dk)
        if st["durum"] == "kabul":
            if dk and ilk == dk:
                ac_dogru += 1
            else:
                yanlis += 1
        else:
            sor += 1
        if s["adet"]["deger"] == d.get("adet") and s["adet"]["durum"] != "sor":
            adet_d += 1
        if not dk:
            dm = "kod yok" + (" (kabul=YANLIŞ)" if st["durum"] == "kabul" else " (sor/bos: iyi)")
        else:
            dm = "evet" if ilk == dk else "HAYIR"
        gri, tem = e["gri"], e["temiz"]
        gs = f"{gri[0]}({gri[1]:.2f})" if gri else "-"
        ts = f"{tem[0]}({tem[1]:.2f})" if tem else "-"   # hücre tanıma atlandıysa (tam sayfa metni yeterli) yok
        P(f"{s['sira']} | {dk or '-'} | {e['sayfa'][0]!r}({e['sayfa'][1]:.2f}) | {gs} | {ts} | {e['cnn']['secilen']} | {st['secilen']} [{e['kaynak']}] | {e['d1']}/{e['d2']} | {st['guven']} | {st['durum']} | {dm} | {s['adet']['ham']!r}->{s['adet']['deger']} {s['adet']['durum']}")
        sat.append({"sira": s["sira"], "dogru": dk, "sayfa": e["sayfa"], "gri": gri, "temiz": tem, "kaynak": e["kaynak"], "secilen": st["secilen"], "d1": e["d1"], "d2": e["d2"],
                    "guven": st["guven"], "durum": st["durum"], "dogru_mu": dm, "adet": s["adet"]})
    P(f"OZET: kod dogru (ilk aday) {kod_dogru}/{kodlu} | otomatik kabul dogru {ac_dogru} | YANLIS KABUL {yanlis} | sor/bos {sor} | adet dogru {adet_d}/{min(len(dogru), len(satirlar))} | sure {sure:.1f}s (satir basina {sure / max(1, len(satirlar)):.2f}s)")
    if len(satirlar) != len(dogru):
        P(f"UYARI: okunan satir {len(satirlar)} != dogru satir {len(dogru)}")
    if json_cikti:
        with open(json_cikti, "w", encoding="utf-8") as f:
            json.dump({"foto": foto, "ozet": {"kod_dogru": kod_dogru, "kodlu": kodlu, "kabul_dogru": ac_dogru, "yanlis_kabul": yanlis,
                                              "sor": sor, "adet_dogru": adet_d, "sure_s": round(sure, 2)},
                       "satirlar": sat, "yanit": y}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--servis" in a:
        servis()
    elif "--fis" in a:
        rest = a[a.index("--fis") + 1:]
        cik = None
        if "--json" in rest:
            j = rest.index("--json"); cik = rest[j + 1]; rest = rest[:j] + rest[j + 2:]
        motor = Motor()
        toplam = {}
        for f in rest:
            try:
                r = fis_oku(motor, f)
            except Exception as e:
                r = {"hata": f"{type(e).__name__}: {e}"[:300]}
                log("fis hata", f, r["hata"])
            toplam[os.path.basename(f)] = r
            _STDOUT.write("== %s yon=%s sure=%s\n" % (os.path.basename(f), r.get("yon"), r.get("sure_sn")))
            for x in r.get("satirlar", []):
                _STDOUT.write("   %.2f  %s\n" % (x["guven"], x["metin"]))
            _STDOUT.flush()
            if cik:
                with open(cik, "w", encoding="utf-8") as fo:
                    json.dump(toplam, fo, ensure_ascii=False, indent=1)
    elif "--olc" in a:
        rest = a[a.index("--olc") + 1:]
        jc = None
        if "--json" in rest:
            j = rest.index("--json")
            jc = rest[j + 1]
            rest = rest[:j] + rest[j + 2:]
        det = rec = None
        if "--cnn" in rest:
            j = rest.index("--cnn")
            _CNN["yol"] = rest[j + 1]
            rest = rest[:j] + rest[j + 2:]
        for ad in ("--det", "--rec"):
            if ad in rest:
                j = rest.index(ad)
                if ad == "--det":
                    det = rest[j + 1]
                else:
                    rec = rest[j + 1]
                rest = rest[:j] + rest[j + 2:]
        olc(rest[0], rest[1], rest[2], jc, det, rec)
    else:
        print(__doc__, file=_STDOUT)
