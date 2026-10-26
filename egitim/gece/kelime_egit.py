# -*- coding: utf-8 -*-
"""
kelime_egit.py - Türkçe el yazısı KELİME tanıyıcı (ayrık ve bitişik), CTC ile, gece boyu.
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

Yusuf'un isteği (26.10 03:03): Türkçe birleşik ve ayrık el yazısı kelimeler, ayrık/el yazısı harfler, Türkçe imla, biraz rakam.
Açık Türkçe el yazısı kelime verisi yok; bu yüzden kelimeler üretilir:
  ayrık   : gerçek el yazısı karakter örnekleri (T-H-E Türkçe büyük/küçük, EMNIST harf/rakam, QMNIST, HASYv2) yan yana dizilir;
            aralık bazen eksi -> harfler değer/üst üste biner (birleşiğe yakın görünüm).
  font    : 18 ayrık (blok) + 8 bitişik el yazısı fontuyla kelime çizimi (bitişik fontlarda harfler gerçekten bağlı).
Kelimeler: FrequencyWords tr_50k (MIT, OpenSubtitles sıklığı) %70, en_50k %12, rakam/kod %18.
Doğrulama (eğitime girmez, model seçimi bununla): arşivlerin TEST bölmelerinden harflerle dizilmiş kelimeler + eğitimde HİÇ
  kullanılmayan 3 font (Kalam, Neucha, Courgette). Kaynak türüne göre ayrı ölçülür (ayrik / font-blok / font-bitisik).
İmla: sözlükle düzeltme (en yakın sık kelime, düzenleme mesafesi <= 2) ayrı ölçülür.
Kaynaklar: KAYNAK-EK-2026-10-26.md. Chars74K ve USPS (lisans metni belirsiz) denetmen önerisiyle kullanılmaz.
Kullanım: python kelime_egit.py --bitis 06:45 [--tur-ornek 24000] [--isci 3]
Çıktı: gece/kelime/en-iyi.pt, gecmis.json, gunluk.txt (kesintide son.pt'den sürer).
"""
import os, sys, json, time, glob, argparse, datetime, re
import numpy as np

AD = os.path.dirname(os.path.abspath(__file__))
EG = os.path.normpath(os.path.join(AD, ".."))
KOK = os.path.normpath(os.path.join(EG, ".."))
sys.path.insert(0, EG)
OB = os.path.join(KOK, "veri", "onbellek")
KUC = "abcçdefgğhıijklmnoöprsştuüvyzqwx"
BUY = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZQWX"
ABC = "0123456789" + KUC + BUY + "-"          # CTC: 0 = boş, sınıf i -> i+1
H, W = 32, 256
SAKLI_FONT = ("Kalam", "Neucha", "Courgette")
UZUN = set("bdfhklt") | set(BUY) | set("0123456789") | set("İ")   # tam boy
ALT = set("gpyqş") | set("ç")                                          # alt uzantı (aşağı kayar)


def tr_ust(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def kelimeler():
    def oku(ad, desen, n):
        out = []
        for ln in open(os.path.join(KOK, "veri", "kelime", ad), encoding="utf-8"):
            p = ln.split()
            if p and re.fullmatch(desen, p[0]) and 2 <= len(p[0]) <= 12:
                out.append((p[0], int(p[1])))
            if len(out) >= n:
                break
        return out
    return oku("tr_50k.txt", r"[a-zçğıöşü]+", 40000), oku("en_50k.txt", r"[a-z]+", 15000)


# ------------------------------------------------------------------ işçi
_W = {}


def havuz_kur(adlar):
    """karakter -> [(x mmap, indeksler)]"""
    hv = {}
    for ad in adlar:
        p = os.path.join(OB, ad + "_x.npy")
        if not os.path.exists(p):
            continue
        x = np.load(p, mmap_mode="r"); y = np.load(os.path.join(OB, ad + "_y.npy"))
        for c in set(y.tolist()):
            if c in ABC:
                hv.setdefault(c, []).append((x, np.nonzero(y == c)[0]))
    return hv


def fontlar(sakli):
    from PIL import ImageFont
    out = []
    for kl, tur in (("fontlar", "blok"), ("fontlar-bitisik", "bitisik")):
        for f in sorted(glob.glob(os.path.join(KOK, "veri", kl, "*.ttf"))):
            ad = os.path.splitext(os.path.basename(f))[0]
            if (ad in SAKLI_FONT) != sakli:
                continue
            try:
                out.append((ad, tur, ImageFont.truetype(f, 40)))
            except Exception:
                pass
    return out


def isci_baslat(dogrulama=False):
    _W["kel"] = kelimeler()
    if dogrulama:
        _W["hv"] = havuz_kur(("the-test", "emnist-harf-test", "emnist-digits-test"))
    else:
        _W["hv"] = havuz_kur(("the-train", "emnist-harf-train", "emnist-digits-train", "qmnist", "hasy"))
    _W["font"] = fontlar(dogrulama)
    _W["glif"] = {}


def kelime_sec(rng):
    tr, en = _W["kel"]
    r = rng.random()
    if r < 0.18:
        k = rng.random()
        if k < 0.4:
            return str(int(rng.integers(1, 10 ** int(rng.integers(1, 6)))))
        if k < 0.7:
            return "T" + "".join(str(int(v)) for v in rng.integers(0, 10, int(rng.choice([4, 5])))) + (("-%02d" % rng.integers(1, 20)) if rng.random() < 0.3 else "")
        return "%02d.%02d" % (rng.integers(1, 29), rng.integers(1, 13)) if False else str(int(rng.integers(10, 999)))
    liste = tr if r < 0.88 else en
    # sıklığa göre ağırlık: sık kelimeler daha çok, ama kuyruk da gelsin (karekök)
    i = int(len(liste) * rng.random() ** 2.2)
    w = liste[min(i, len(liste) - 1)][0]
    c = rng.random()
    if c < 0.25:
        w = tr_ust(w) if liste is tr else w.upper()
    elif c < 0.5:
        w = (tr_ust(w[0]) if liste is tr else w[0].upper()) + w[1:]
    return w


def glif_var(font, ch):
    from PIL import Image, ImageDraw
    k = (font[0], ch)
    if k not in _W["glif"]:
        def iz(c):
            im = Image.new("L", (60, 60), 0); ImageDraw.Draw(im).text((5, 0), c, 255, font=font[2]); return np.asarray(im).tobytes()
        _W["glif"][k] = iz(ch) != iz("")
    return _W["glif"][k]


def font_ciz(w, font, rng):
    from PIL import Image, ImageDraw
    if not all(glif_var(font, c) for c in w):
        return None
    F = font[2]
    x0, y0, x1, y1 = F.getbbox(w)
    im = Image.new("L", (x1 - x0 + 20, y1 - y0 + 20), 0)
    ImageDraw.Draw(im).text((10 - x0, 10 - y0), w, 255, font=F)
    return np.asarray(im, np.float32) / 255.0


def ayrik_ciz(w, rng):
    import cv2
    hv = _W["hv"]
    parca = []
    for c in w:
        if c not in hv:
            return None
        x, ii = hv[c][int(rng.integers(len(hv[c])))]
        a = np.asarray(x[ii[int(rng.integers(len(ii)))]], np.float32) / 255.0
        cs = np.nonzero(a.max(0) > 0.2)[0]; rs = np.nonzero(a.max(1) > 0.2)[0]
        if not len(cs):
            return None
        a = a[rs.min():rs.max() + 1, cs.min():cs.max() + 1]
        boy = 40 if (c in UZUN) else 26
        boy = int(boy * rng.uniform(0.85, 1.15))
        o = boy / a.shape[0]
        a = cv2.resize(a, (max(2, int(round(a.shape[1] * o))), boy), interpolation=cv2.INTER_AREA)
        parca.append((a, 8 if c in ALT else 0))
    Hc = 64
    taban = 46
    toplam = sum(p[0].shape[1] for p in parca) + 12 * len(parca) + 20
    t = np.zeros((Hc, toplam), np.float32)
    x = 6
    bit = rng.random() < 0.4          # birleşiğe yakın: harfler sıkışık / değer
    for a, kay in parca:
        y1 = min(Hc, taban + kay + int(rng.integers(-2, 3))); y0 = max(0, y1 - a.shape[0])
        a = a[a.shape[0] - (y1 - y0):]
        t[y0:y1, x:x + a.shape[1]] = np.maximum(t[y0:y1, x:x + a.shape[1]], a)
        x += a.shape[1] + (int(rng.integers(-4, 1)) if bit else int(rng.integers(1, 7)))
    return t[:, :max(x + 6, 8)]


def boz_kelime(t, rng):
    import cv2
    h, w = t.shape
    pad = 10
    t = cv2.copyMakeBorder(t, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    h, w = t.shape
    sh = rng.uniform(-0.35, 0.35); ac = np.deg2rad(rng.uniform(-3, 3))
    M = np.array([[np.cos(ac), -np.sin(ac) + sh, 0], [np.sin(ac), np.cos(ac), 0]], np.float32)
    M[0, 2] = -sh * h / 2
    t = cv2.warpAffine(t, M, (w, h))
    ke = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)); r = rng.random()
    if r < 0.3:
        t = cv2.dilate(t, ke)
    elif r < 0.45:
        t = cv2.erode(t, ke)
    if rng.random() < 0.25:   # satır/tablo çizgisi
        y = int(rng.uniform(0.75, 0.98) * h)
        cv2.line(t, (0, y), (w, y), float(rng.uniform(0.4, 1)), int(rng.integers(1, 3)))
    rs = np.nonzero(t.max(1) > 0.15)[0]; cs = np.nonzero(t.max(0) > 0.15)[0]
    if not len(rs):
        return None
    t = t[max(0, rs.min() - 2):rs.max() + 3, max(0, cs.min() - 2):cs.max() + 3]
    o = (H - 4) / t.shape[0]
    nw = int(round(t.shape[1] * o * rng.uniform(0.85, 1.15)))
    if nw > W - 4 or nw < 4:
        if nw > W - 4:
            nw = W - 4
        else:
            return None
    t = cv2.resize(t, (nw, H - 4), interpolation=cv2.INTER_AREA)
    if rng.random() < 0.3:
        t = cv2.GaussianBlur(t, (3, 3), rng.uniform(0.3, 1.0))
    if rng.random() < 0.4:
        t = (t > rng.uniform(0.25, 0.55)).astype(np.float32)
    out = np.zeros((H, W), np.float32)
    x = int(rng.integers(0, 3))
    out[2:2 + t.shape[0], x:x + t.shape[1]] = t
    out = out * rng.uniform(0.75, 1.0) + (rng.normal(0, 0.04, out.shape) if rng.random() < 0.5 else 0)
    return np.clip(out, 0, 1)


def ornek(rng, tur=None):
    for _ in range(20):
        w = kelime_sec(rng)
        r = rng.random() if tur is None else {"ayrik": 0.0, "font-blok": 0.6, "font-bitisik": 0.99}[tur]
        if r < 0.5:
            t = ayrik_ciz(w, rng); k = "ayrik"
        else:
            fs = [f for f in _W["font"] if (f[1] == "bitisik") == (r >= 0.8)] or _W["font"]
            f = fs[int(rng.integers(len(fs)))]
            t = font_ciz(w, f, rng); k = "font-" + f[1]
        if t is None:
            continue
        g = boz_kelime(t, rng)
        if g is not None and (g > 0.3).sum() >= 25 * len(w):   # neredeyse boş/silik çıkan örnekleri at (yanlış etiket olmasın)
            return g, w, k
    return None


def uret(args):
    n, tohum = args
    rng = np.random.default_rng(tohum)
    X = np.zeros((n, H, W), np.uint8); Y = []; K = []
    j = 0
    while j < n:
        o = ornek(rng)
        if o is None:
            continue
        X[j] = (o[0] * 255).astype(np.uint8); Y.append(o[1]); K.append(o[2]); j += 1
    return X, Y, K


# ------------------------------------------------------------------ model
def ag_kur():
    import torch.nn as nn

    def blok(a, b, havuz):
        k = [nn.Conv2d(a, b, 3, padding=1), nn.BatchNorm2d(b), nn.ReLU(inplace=True)]
        if havuz:
            k.append(nn.MaxPool2d(havuz))
        return k

    class Ag(nn.Module):
        def __init__(s):
            super().__init__()
            s.g = nn.Sequential(*blok(1, 32, 2), *blok(32, 64, 2), *blok(64, 96, None), *blok(96, 96, (2, 1)),
                                *blok(96, 128, (2, 1)), nn.Conv2d(128, 160, (2, 1)), nn.BatchNorm2d(160), nn.ReLU(inplace=True))
            s.s = nn.Sequential(nn.Conv1d(160, 160, 3, padding=1), nn.ReLU(inplace=True), nn.Dropout(0.2), nn.Conv1d(160, len(ABC) + 1, 1))

        def forward(s, x):              # x: N,1,32,256 -> N,T=64,C
            f = s.g(x).squeeze(2)        # N,160,64
            return s.s(f).permute(0, 2, 1)
    return Ag()


def coz_greedy(lp):
    """lp: N,T,C -> metinler"""
    a = lp.argmax(2).cpu().numpy(); out = []
    for r in a:
        s, o = [], 0
        for v in r:
            if v != o and v != 0:
                s.append(ABC[v - 1])
            o = v
        out.append("".join(s))
    return out


def lev(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[len(b)]


class Sozluk:
    """Türkçe imla düzeltme: kelime harfli ise en yakın sık kelime (mesafe <= 2; eşitlikte sık olan). Büyük/küçük biçim korunur."""
    def __init__(s, tr, n=15000):
        s.kova = {}
        for w, f in tr[:n]:
            s.kova.setdefault(len(w), []).append(w)

    def duzelt(s, m):
        if not m or not re.fullmatch(r"[A-Za-zÇĞİIÖŞÜçğıöşü]+", m):
            return m
        k = m.replace("İ", "i").replace("I", "ı").lower()
        en, em = None, 3
        for L in (len(k), len(k) - 1, len(k) + 1, len(k) - 2, len(k) + 2):
            for w in s.kova.get(L, ()):
                if abs(len(w) - len(k)) >= em:
                    continue
                d = lev(k, w)
                if d < em:
                    en, em = w, d
                    if d == 0:
                        return m
        if en is None:
            return m
        if m.isupper() and len(m) > 1:
            return tr_ust(en)
        if m[0].isupper():
            return tr_ust(en[0]) + en[1:]
        return en


class Satirlar:
    """[26.10 04:30] Gerçek bitişik el yazısı satırları (IAM-line, hazirla.iam): (32, toplam) mmap + genişlikler + etiketler."""
    def __init__(s, bol):
        p = os.path.join(OB, "iam-%s_x.npy" % bol)
        s.var = os.path.exists(p)
        if s.var:
            s.x = np.load(p, mmap_mode="r"); s.w = np.load(os.path.join(OB, "iam-%s_w.npy" % bol))
            s.bas = np.concatenate([[0], np.cumsum(s.w)[:-1]]); s.y = json.load(open(os.path.join(OB, "iam-%s_y.json" % bol), encoding="utf-8"))
            ok = [i for i, t in enumerate(s.y) if t and all(c in ABC for c in t) and len(t) <= int(s.w[i]) // 4 - 2]
            s.ii = np.array(ok)

    def topla(s, idx, rng=None):
        """idx -> (N,1,32,Wmax) float32 tensör, hedefler, genişlikler(T)"""
        import torch
        Wm = int(max(s.w[i] for i in idx)); Wm += (-Wm) % 4
        X = np.zeros((len(idx), 1, 32, Wm), np.float32)
        for k, i in enumerate(idx):
            a = np.asarray(s.x[:, s.bas[i]:s.bas[i] + s.w[i]], np.float32) / 255.0
            if rng is not None:
                a = np.clip(a * rng.uniform(0.75, 1.0) + (rng.normal(0, 0.04, a.shape) if rng.random() < 0.5 else 0), 0, 1)
            X[k, 0, :, :a.shape[1]] = a
        return torch.from_numpy(X), [s.y[i] for i in idx], [int(s.w[i]) // 4 for i in idx]


class GercekKelime:
    """[26.10 05:00] Gerçek bitişik el yazısı KELİME kırpıntıları (32x256): RIMES (rimes_hazirla.py) + Bentham (bentham_hazirla.py).
    Bentham'ın resmi bölmesi yok: sabit tohumla %5 doğrulama. Boşluk etiketten çıkarılır; ABC dışı karakterli olan atılır."""
    def __init__(s, bolum):
        xs, ys = [], []
        for ad in ("rimes-train" if bolum == "egitim" else "rimes-val", "bentham_kelime"):
            p = os.path.join(OB, ad + "_x.npy")
            if not os.path.exists(p):
                continue
            x = np.load(p, mmap_mode="r"); y = [t.replace(" ", "") for t in json.load(open(os.path.join(OB, ad + "_y.json"), encoding="utf-8"))]
            ii = np.arange(len(y))
            if ad == "bentham_kelime":
                m = np.random.default_rng(31).random(len(y)) < 0.05
                ii = ii[m] if bolum != "egitim" else ii[~m]
            ii = [i for i in ii if y[i] and all(c in ABC for c in y[i])]
            xs.append((x, ii)); ys.append(y)
        s.kay = list(zip(xs, ys)); s.n = sum(len(k[0][1]) for k in s.kay)

    def ornekle(s, n, rng):
        out_x, out_y = [], []
        for _ in range(n):
            (x, ii), y = s.kay[int(rng.integers(len(s.kay)))]
            if not len(ii):
                continue
            i = ii[int(rng.integers(len(ii)))]
            out_x.append(np.asarray(x[i])); out_y.append(y[i])
        return (np.stack(out_x) if out_x else np.zeros((0, H, W), np.uint8)), out_y

    def hepsi(s, en_cok=1500):
        out_x, out_y = [], []
        for (x, ii), y in s.kay:
            for i in ii[:en_cok]:
                out_x.append(np.asarray(x[i])); out_y.append(y[i])
        return (np.stack(out_x), out_y) if out_x else None


def olc_satir(ag, S, n=400):
    import torch
    if not S.var:
        return {}
    idx = S.ii[:n]; ag.eval(); dog = ce = top = 0
    with torch.no_grad():
        for b in range(0, len(idx), 16):
            X, Y, T = S.topla(idx[b:b + 16])
            tah = coz_greedy(ag(X))
            for t, y in zip(tah, Y):
                dog += (t == y); ce += lev(t, y); top += len(y)
    return {"satir": round(dog / len(idx), 4), "cer": round(ce / max(1, top), 4), "n": int(len(idx))}


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(os.path.join(_KL, "gunluk.txt"), "a", encoding="utf-8") as f:
        f.write(s + "\n")


def olc(ag, V, soz=None):
    import torch
    X, Y, K = V
    ag.eval(); tahmin = []
    with torch.no_grad():
        for i in range(0, len(X), 200):
            tahmin += coz_greedy(ag(torch.from_numpy(X[i:i + 200].astype(np.float32) / 255.0).unsqueeze(1)))
    out = {}
    for tur in sorted(set(K)) + ["hepsi"]:
        ii = [i for i, k in enumerate(K) if tur == "hepsi" or k == tur]
        if not ii:
            continue
        ce = sum(lev(tahmin[i], Y[i]) for i in ii) / max(1, sum(len(Y[i]) for i in ii))
        out[tur] = {"kelime": round(sum(tahmin[i] == Y[i] for i in ii) / len(ii), 4), "cer": round(ce, 4), "n": len(ii)}
        if soz is not None:
            out[tur]["kelime_imla"] = round(sum(soz.duzelt(tahmin[i]) == Y[i] for i in ii) / len(ii), 4)
    return out, tahmin


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bitis", default="06:45")
    ap.add_argument("--tur-ornek", type=int, default=24000)
    ap.add_argument("--isci", type=int, default=3)
    ap.add_argument("--is-parcacigi", type=int, default=8)
    ap.add_argument("--en-cok-tur", type=int, default=10000)
    a = ap.parse_args()
    import torch
    import torch.nn.functional as F
    from multiprocessing import Pool
    torch.set_num_threads(a.is_parcacigi)
    _KL = os.path.join(AD, "kelime"); os.makedirs(_KL, exist_ok=True)
    simdi = datetime.datetime.now(); hh, mm = map(int, a.bitis.split(":"))
    bitis = simdi.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if bitis <= simdi:
        bitis += datetime.timedelta(days=1)
    # doğrulama kümesi (sabit tohum, eğitime girmeyen kaynaklar)
    isci_baslat(dogrulama=True)
    rng = np.random.default_rng(424242)
    V = ([], [], [])
    for tur, n in (("ayrik", 600), ("font-blok", 300), ("font-bitisik", 300)):
        say = 0
        while say < n:
            o = ornek(rng, tur)
            if o is None:
                continue
            V[0].append((o[0] * 255).astype(np.uint8)); V[1].append(o[1]); V[2].append(o[2]); say += 1
    V = (np.stack(V[0]), V[1], V[2])
    soz = Sozluk(_W["kel"][0])
    _W.clear()
    ag = ag_kur()
    opt = torch.optim.AdamW(ag.parameters(), 1e-3, weight_decay=1e-4)
    tur, en_iyi, gecmis = 0, -1.0, []
    son = os.path.join(_KL, "son.pt")
    if os.path.exists(son):
        d = torch.load(son, weights_only=True)
        ag.load_state_dict(d["ag"]); opt.load_state_dict(d["opt"]); tur, en_iyi = int(d["tur"]), float(d["en_iyi"])
        gecmis = json.load(open(os.path.join(_KL, "gecmis.json"), encoding="utf-8"))
        if int(d.get("puan_surum", 1)) != 2 and os.path.exists(os.path.join(OB, "iam-validation_x.npy")):
            # seçim ölçütü değişti (gerçek bitişik satır eklendi): eski en iyi ayrı adla saklanır, puan sıfırlanır
            for u in ("pt", "json"):
                if os.path.exists(os.path.join(_KL, "en-iyi." + u)):
                    os.replace(os.path.join(_KL, "en-iyi." + u), os.path.join(_KL, "en-iyi-yalniz-sentetik." + u))
            en_iyi = -1.0
        log("kaldığı yerden sürüyor: tur", tur, "en iyi", en_iyi)
    ctc = torch.nn.CTCLoss(blank=0, zero_infinity=True)
    SAT_E, SAT_V = Satirlar("train"), Satirlar("validation")   # IAM test bölmesi eğitimde de seçimde de kullanılmaz
    GK_E = GercekKelime("egitim"); GK_V = GercekKelime("dogrulama").hepsi()
    with Pool(a.isci, initializer=isci_baslat) as pool:
        log("başladı kelime | doğrulama", {k: V[2].count(k) for k in set(V[2])}, "bitiş", bitis.strftime("%d.%m %H:%M"))
        parca = 2000
        sonraki = pool.map_async(uret, [(parca, (tur + 1) * 7919 + i) for i in range(a.tur_ornek // parca)])
        while datetime.datetime.now() < bitis and tur < a.en_cok_tur:
            t0 = time.time()
            s_ = sonraki.get()
            X = np.concatenate([s[0] for s in s_]); Y = sum((s[1] for s in s_), []); K = sum((s[2] for s in s_), []); del s_
            tur += 1
            sonraki = pool.map_async(uret, [(parca, (tur + 1) * 7919 + i) for i in range(a.tur_ornek // parca)])
            t1 = time.time()
            lr = 1e-3 * min(1.0, tur / 3) if tur <= 3 else 1e-4 + 0.5 * (1e-3 - 1e-4) * (1 + np.cos(np.pi * (((tur - 4) % 10) / 10.0)))
            if tur > 23:   # [26.10 04:45] gerçek veri eklendikten sonra yeniden başlatma tepesi düşük (tur 24'te 1e-3 sentetik doğruluğu bozdu)
                lr = 5e-5 + 0.5 * (4e-4 - 5e-5) * (1 + np.cos(np.pi * (((tur - 24) % 10) / 10.0)))
            lr = float(lr)
            for g_ in opt.param_groups:
                g_["lr"] = lr
            ag.train(); perm = np.random.permutation(len(X)); top = 0.0; B = 64
            for i in range(0, len(X), B):
                ii = perm[i:i + B]
                xb = torch.from_numpy(X[ii].astype(np.float32) / 255.0).unsqueeze(1)
                hed = [torch.tensor([ABC.index(c) + 1 for c in Y[j]]) for j in ii]
                lp = F.log_softmax(ag(xb), 2).permute(1, 0, 2)       # T,N,C
                k = ctc(lp, torch.cat(hed), torch.full((len(ii),), lp.shape[0], dtype=torch.long), torch.tensor([len(h) for h in hed]))
                opt.zero_grad(); k.backward(); torch.nn.utils.clip_grad_norm_(ag.parameters(), 5.0); opt.step()
                top += float(k.detach()) * len(ii)
            egitim_tur = {k_: K.count(k_) for k_ in set(K)}
            del X
            # [26.10 04:30] gerçek bitişik satırlar (IAM train): tur başına 2400 satır, 16'lık değişken genişlikli gruplar
            if SAT_E.var:
                rng_s = np.random.default_rng(tur)
                sec = rng_s.choice(SAT_E.ii, min(2400, len(SAT_E.ii)), replace=False)
                for b in range(0, len(sec), 16):
                    xb, Yb, Tb = SAT_E.topla(sec[b:b + 16], rng_s)
                    hed = [torch.tensor([ABC.index(c) + 1 for c in y]) for y in Yb]
                    lp = F.log_softmax(ag(xb), 2).permute(1, 0, 2)
                    k = ctc(lp, torch.cat(hed), torch.tensor(Tb, dtype=torch.long), torch.tensor([len(h) for h in hed]))
                    opt.zero_grad(); k.backward(); torch.nn.utils.clip_grad_norm_(ag.parameters(), 5.0); opt.step()
                egitim_tur["gercek-bitisik-iam(satir)"] = int(len(sec))
            # [26.10 05:00] gerçek bitişik kelimeler (RIMES + Bentham): tur başına en çok 6000
            if GK_E.n:
                rng_k = np.random.default_rng(tur + 500)
                xg, yg = GK_E.ornekle(6000, rng_k)
                for b in range(0, len(yg), 64):
                    xb = torch.from_numpy(xg[b:b + 64].astype(np.float32) / 255.0).unsqueeze(1)
                    hed = [torch.tensor([ABC.index(c) + 1 for c in t]) for t in yg[b:b + 64]]
                    lp = F.log_softmax(ag(xb), 2).permute(1, 0, 2)
                    k = ctc(lp, torch.cat(hed), torch.full((len(hed),), lp.shape[0], dtype=torch.long), torch.tensor([len(h) for h in hed]))
                    opt.zero_grad(); k.backward(); torch.nn.utils.clip_grad_norm_(ag.parameters(), 5.0); opt.step()
                egitim_tur["gercek-bitisik-kelime"] = len(yg)
                del xg
            sonu, tah = olc(ag, V, soz if tur % 4 == 0 else None)
            if GK_V is not None:
                gk, _ = olc(ag, (GK_V[0], GK_V[1], ["gercek-bitisik-kelime"] * len(GK_V[1])))
                sonu["gercek-bitisik-kelime"] = gk["gercek-bitisik-kelime"]
            sat = olc_satir(ag, SAT_V)              # IAM validation: seçimde kullanılır
            if sat:
                sonu["gercek-bitisik-iam"] = sat
            # seçim: sentetik doğrulama kelime doğruluğu + gerçek bitişik satırda (1-CER); IAM test yalnız son ölçüm
            puan = float(0.5 * sonu["hepsi"]["kelime"] + 0.5 * (1 - sat["cer"])) if sat else float(sonu["hepsi"]["kelime"])
            gecmis.append({"tur": tur, "lr": round(lr, 6), "kayip": round(top / len(perm), 4), "dogrulama": sonu, "egitim_kaynak": egitim_tur,
                           "puan": round(puan, 4), "puan_surum": 2 if sat else 1})
            if puan > en_iyi:
                en_iyi = puan
                torch.save(ag.state_dict(), os.path.join(_KL, "en-iyi.pt"))
                json.dump({"tur": tur, "dogrulama": sonu, "abc": ABC, "H": H, "W": W, "tarih": time.strftime("%Y-%m-%d %H:%M"),
                           "ornekler": [[V[1][i], tah[i], V[2][i]] for i in range(0, len(tah), 40)]},
                          open(os.path.join(_KL, "en-iyi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            torch.save({"ag": ag.state_dict(), "opt": opt.state_dict(), "tur": tur, "en_iyi": en_iyi, "puan_surum": 2 if sat else 1}, son + ".yeni")
            os.replace(son + ".yeni", son)
            json.dump(gecmis, open(os.path.join(_KL, "gecmis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            log("tur %d lr %.5f kayıp %.3f bekleme %.0fs eğitim %.0fs | %s | en iyi %.4f" % (
                tur, lr, top / len(perm), t1 - t0, time.time() - t1, json.dumps(sonu, ensure_ascii=False), en_iyi))
        sonraki.wait()
    log("bitti: tur", tur, "en iyi", en_iyi)
