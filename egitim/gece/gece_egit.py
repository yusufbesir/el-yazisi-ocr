# -*- coding: utf-8 -*-
"""
gece_egit.py - Ayrık (blok) el yazısı karakter modeli, uzun süreli (gece boyu) eğitim.
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

Görevler:
  kod  : "0123456789T-" (stok kodu okuyucu; motor ve JS ile aynı sınıflar)
  harf : Türkçe büyük harf (küçükler büyüğüne eşlenir) + rakam: "0123456789ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
Veri: veri/onbellek (hazirla.py) EMNIST, T-H-E, Chars74K, HASYv2 + OFL el yazısı fontlarından sentetik + veri.py sentetik T/-/bayraklı 1.
Her tur yeni rastgele bozulmalarla (telefon fotoğrafı/kalem benzetimi) yeniden üretilir -> aynı örnek iki kez aynı görünmez.
Doğrulama (eğitime GİRMEZ): gerçek tutanak kırpıntıları. Seçim kümesi tutanak-1 + yeni3-rakam, son test tutanak-3.
Mimari (yalnız conv/maxpool/fc; JS ve numpy çıkarımı aynen çalışır): conv32-conv32-pool-conv64-conv64-pool-fc128-fc(K);
  eğitimde BatchNorm, dışa aktarımda conv ağırlıklarına katlanır.
Kesinti: her tur sonunda gece/<gorev>/son.pt; yeniden çalıştırınca kaldığı turdan sürer.
Kullanım: python gece_egit.py <kod|harf> --bitis 07:00 [--tur-ornek 160000] [--isci 4]
Varsayılan modellere (egitim/model.json, js/model.js) DOKUNMAZ; çıktı gece/<gorev>/en-iyi.json.
"""
import os, sys, json, time, glob, argparse, datetime
import numpy as np

AD = os.path.dirname(os.path.abspath(__file__))
EG = os.path.normpath(os.path.join(AD, ".."))
KOK = os.path.normpath(os.path.join(EG, ".."))
sys.path.insert(0, EG)
OB = os.path.join(KOK, "veri", "onbellek")

GOREV = {"kod": "0123456789T-", "harf": "0123456789ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"}
KUCUK = {"ı": "I", "i": "İ"}


def sinif_esle(gorev, c):
    S = GOREV[gorev]
    if gorev == "kod":
        if c in "0123456789-":
            return S.index(c)
        if c in "Tt":
            return 10
        return -1
    c = KUCUK.get(c, c.upper() if c not in "ıi" else c)
    return S.index(c) if c in S else -1


# ------------------------------------------------------------------ işçi tarafı (veri üretimi)
_W = {}


def isci_baslat(gorev, tohum):
    import cv2  # noqa
    import veri, bolme
    # veri.py Linux font yollarını kullanır; bu makinede Windows fontları (veri_emnist.py ile aynı)
    _w = "C:/Windows/Fonts/"
    veri.FONTLAR = [_w + f for f in ("arial.ttf", "arialbd.ttf", "ariali.ttf", "times.ttf", "timesi.ttf", "calibri.ttf",
                                     "verdana.ttf", "tahoma.ttf", "comic.ttf", "cour.ttf", "segoeui.ttf") if os.path.exists(_w + f)]
    _W["gorev"] = gorev
    kaynak = []
    # 26.10 03:15 denetmen: lisans metni belirsiz Chars74K ve USPS eğitimden çıkarıldı
    # 26.10 08:33 Yusuf'un kararıyla Chars74K geri eklendi (kişisel/eğitim kullanımı; KAYNAK-EK Ek 7). USPS dışarıda.
    for ad in ("emnist-digits-train", "emnist-harf-train", "the-train", "hasy", "qmnist", "chars74k"):
        p = os.path.join(OB, ad + "_x.npy")
        if not os.path.exists(p):
            continue
        x = np.load(p, mmap_mode="r"); y = np.load(os.path.join(OB, ad + "_y.npy"))
        k = np.array([sinif_esle(gorev, c) for c in y])
        m = np.nonzero(k >= 0)[0]
        kaynak.append((ad, x, m, k))
    _W["kaynak"] = kaynak
    # sınıf -> [(kaynak indeksi, örnek indeksleri)]
    K = len(GOREV[gorev]); hav = [[] for _ in range(K)]
    for si, (ad, x, m, k) in enumerate(kaynak):
        for c in range(K):
            ii = m[k[m] == c]
            if len(ii):
                hav[c].append((si, ii))
    _W["havuz"] = hav
    _W["font"] = font_gliflari(gorev)
    d = [(si, m[k[m] == 1]) for si, (ad, x, m, k) in enumerate(kaynak) if ad == "emnist-digits-train"]
    _W["birler"] = kaynak[d[0][0]][1][d[0][1][:5000]] if d else None


SAKLI_FONT = ("Kalam", "Neucha", "Courgette")   # [26.10 denetmen] eğitimde hiç kullanılmaz; yalnız doğrulama


def font_gliflari(gorev, sakli=False):
    """OFL el yazısı fontlarından her sınıf için ham 28x28 glif listesi (notdef/boş glifler atlanır).
    sakli=False: SAKLI_FONT dışındakiler (eğitim); sakli=True: yalnız SAKLI_FONT (doğrulama)."""
    from PIL import Image, ImageDraw, ImageFont
    import hazirla
    S = GOREV[gorev]
    ciz = {c: [c] for c in S}
    if gorev == "harf":
        for c in S:
            if not c.isdigit():
                ciz[c] = [c, {"I": "ı", "İ": "i"}.get(c, c.lower())]
    else:
        ciz["T"] = ["T", "t"]
    out = {i: [] for i in range(len(S))}
    # fontlar: ayrık (blok) el yazısı; fontlar-bitisik: bitişik (el yazısı/script) harf biçimleri, tek glif olarak
    for f in sorted(glob.glob(os.path.join(KOK, "veri", "fontlar", "*.ttf")) + glob.glob(os.path.join(KOK, "veri", "fontlar-bitisik", "*.ttf"))):
        if (os.path.splitext(os.path.basename(f))[0] in SAKLI_FONT) != sakli:
            continue
        try:
            F = ImageFont.truetype(f, 44)
        except Exception:
            continue
        def iz(ch):
            im = Image.new("L", (72, 72), 0); ImageDraw.Draw(im).text((10, 6), ch, 255, font=F)
            return np.asarray(im)
        bos = iz("").tobytes()
        for i, c in enumerate(S):
            for ch in ciz[c]:
                a = iz(ch)
                if a.max() < 100 or a.tobytes() == bos:
                    continue
                t = hazirla.kare28(Image.fromarray(255 - a))
                if t is not None:
                    out[i].append(t)
    return out


def cizgi_artigi(t, rng):
    """Tablo çizgisi kalıntısı: tuvalin bir kenarına yakın kısa/ince çizgi."""
    import cv2
    n = t.shape[0]; k = int(rng.integers(1, 3)); y = int(rng.choice([rng.integers(2, 10), rng.integers(n - 10, n - 2)]))
    x0, x1 = sorted(rng.integers(0, n, 2))
    if rng.random() < 0.5:
        cv2.line(t, (int(x0), y), (int(x1), y), float(rng.uniform(0.5, 1)), k)
    else:
        cv2.line(t, (y, int(x0)), (y, int(x1)), float(rng.uniform(0.5, 1)), k)
    return t


def boz(a28, rng):
    """Ham 28x28 uint8 -> gerçek tutanak kırpıntısı benzetimi -> bolme.mnist_normalle biçimi (float32 0..1)."""
    import cv2, veri, bolme
    t = np.zeros((56, 56), np.float32)
    t[14:42, 14:42] = a28.astype(np.float32) / 255.0
    t = veri.afin(t, rng, aci=14, kayma=0.35, olcek=(0.7, 1.25))
    if rng.random() < 0.3:   # elastik dalgalanma (el titremesi)
        dx = cv2.GaussianBlur(rng.uniform(-1, 1, t.shape).astype(np.float32), (0, 0), 4) * 6
        dy = cv2.GaussianBlur(rng.uniform(-1, 1, t.shape).astype(np.float32), (0, 0), 4) * 6
        gy, gx = np.mgrid[0:56, 0:56].astype(np.float32)
        t = cv2.remap(t, gx + dx, gy + dy, cv2.INTER_LINEAR)
    r = rng.random()   # kalem kalınlığı: tükenmez ince .. keçeli kalın
    ke = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    if r < 0.3:
        t = cv2.dilate(t, ke, iterations=int(rng.integers(1, 3)))
    elif r < 0.45:
        t = cv2.erode(t, ke)
    if rng.random() < 0.25:
        t = cizgi_artigi(t, rng)
    t = veri.kirp(t, rng, 0.08)
    if rng.random() < 0.5:   # gerçek yol ikili maske kullanır
        t = (t > rng.uniform(0.25, 0.6)).astype(np.float32)
    if t.max() <= 0.05:
        t[24:32, 26:30] = 1.0
    c = bolme.mnist_normalle(t)
    if rng.random() < 0.3:
        c = cv2.GaussianBlur(c, (3, 3), rng.uniform(0.3, 0.9))
    return veri.son_gurultu(c, rng)


def uret(args):
    """Bir parça örnek üret: (n, tohum) -> (X uint8 n,28,28 ; Y int64)."""
    n, tohum = args
    import veri
    rng = np.random.default_rng(tohum)
    g = _W["gorev"]; K = len(GOREV[g]); hav = _W["havuz"]; kay = _W["kaynak"]; fnt = _W["font"]
    X = np.zeros((n, 28, 28), np.uint8); Y = np.zeros(n, np.int64)
    say = {}   # [26.10 denetmen] örnek kaynağı sayımı (font ayrı etiketli)
    for j in range(n):
        c = int(rng.integers(K))
        r = rng.random()
        a = None
        if g == "kod" and c == 11:                      # tire: sentetik
            X[j] = (veri.tire_uret(rng) * 255).astype(np.uint8); Y[j] = c; say["sentetik"] = say.get("sentetik", 0) + 1; continue
        if g == "kod" and c == 1 and r < 0.2:           # bayraklı 1
            X[j] = (veri.bir_uret(rng) * 255).astype(np.uint8); Y[j] = c; say["sentetik"] = say.get("sentetik", 0) + 1; continue
        if g == "kod" and c == 10 and r < 0.15 and _W["birler"] is not None:
            X[j] = (veri.t_uret(_W["birler"], rng) * 255).astype(np.uint8); Y[j] = c; say["sentetik"] = say.get("sentetik", 0) + 1; continue
        if (r < 0.18 or not hav[c]) and fnt[c]:
            a = fnt[c][int(rng.integers(len(fnt[c])))]; kad = "font"
        elif hav[c]:
            # kaynaklar arası dengeli: önce kaynak seç, sonra örnek
            si, ii = hav[c][int(rng.integers(len(hav[c])))]
            a = np.asarray(kay[si][1][ii[int(rng.integers(len(ii)))]]); kad = kay[si][0]
        if a is None:
            a = np.zeros((28, 28), np.uint8); kad = "bos"
        say[kad] = say.get(kad, 0) + 1
        X[j] = (boz(a, rng) * 255).astype(np.uint8); Y[j] = c
    return X, Y, say


# ------------------------------------------------------------------ model
def ag_kur(K):
    import torch.nn as nn

    class Ag(nn.Module):
        def __init__(s):
            super().__init__()
            s.c = nn.ModuleList([nn.Conv2d(1, 32, 3), nn.Conv2d(32, 32, 3), nn.Conv2d(32, 64, 3), nn.Conv2d(64, 64, 3)])
            s.b = nn.ModuleList([nn.BatchNorm2d(32), nn.BatchNorm2d(32), nn.BatchNorm2d(64), nn.BatchNorm2d(64)])
            s.f1 = nn.Linear(64 * 4 * 4, 128); s.f2 = nn.Linear(128, K); s.d = nn.Dropout(0.3)

        def forward(s, x):
            import torch.nn.functional as F
            for i in range(4):
                x = F.relu(s.b[i](s.c[i](x)))
                if i in (1, 3):
                    x = F.max_pool2d(x, 2)       # 28-26-24 ->12 -10-8 -> 4
            return s.f2(s.d(F.relu(s.f1(x.flatten(1)))))
    return Ag()


def disa_aktar(ag, yol, S, bilgi):
    """BN'yi conv'a katla; cikarim_numpy/JS biçiminde yaz."""
    import torch
    ag.eval()
    k = []
    with torch.no_grad():
        for i in range(4):
            c, b = ag.c[i], ag.b[i]
            o = b.weight / torch.sqrt(b.running_var + b.eps)
            w = c.weight * o.reshape(-1, 1, 1, 1); bb = (c.bias - b.running_mean) * o + b.bias
            k.append({"tip": "conv", "w": [round(float(v), 6) for v in w.flatten()], "b": [round(float(v), 6) for v in bb],
                      "giris": c.in_channels, "cikis": c.out_channels, "k": 3, "aktivasyon": "relu"})
            if i in (1, 3):
                k.append({"tip": "maxpool", "k": 2})
        k.append({"tip": "duzlestir"})
        for f, akt in ((ag.f1, "relu"), (ag.f2, "yok")):
            k.append({"tip": "fc", "w": [round(float(v), 6) for v in f.weight.flatten()], "b": [round(float(v), 6) for v in f.bias],
                      "giris": f.in_features, "cikis": f.out_features, "aktivasyon": akt})
    json.dump({"katmanlar": k, "siniflar": S, "giris": [28, 28], "not": "çıkışa softmax uygula", "egitim": bilgi},
              open(yol, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)


# ------------------------------------------------------------------ değerlendirme kümeleri
def gercek_kirpinti(gorev):
    """dict ad -> (X float32 N,1,28,28 ; Y). Gerçek tutanak kırpıntıları (yalnız kod görevi)."""
    from PIL import Image
    out = {}
    if gorev != "kod":
        return out
    S = GOREV["kod"]
    for foto in ("tutanak-1", "tutanak-3"):
        kl = os.path.join(KOK, "veri", "tutanak-kirpinti", foto)
        hy = os.path.join(kl, "hatalar.txt")
        hata = set(os.path.basename(s.strip().replace("\\", "/")) for s in open(hy, encoding="utf-8") if s.strip() and not s.startswith("#")) if os.path.exists(hy) else set()
        xs, ys = [], []
        for i, ln in enumerate(open(os.path.join(kl, "etiketler.csv"), encoding="utf-8")):
            if i == 0 or not ln.strip():
                continue
            d, s = ln.split(",")[:2]
            if os.path.basename(d) in hata:
                continue
            xs.append(np.asarray(Image.open(os.path.join(kl, d)), np.float32) / 255.0); ys.append(S.index(s if s != "tire" else "-"))
        out[foto] = (np.stack(xs), np.array(ys))
    xs, ys = [], []
    for f in glob.glob(os.path.join(KOK, "veri", "yeni3-rakam", "*", "*.png")):
        xs.append(np.asarray(Image.open(f), np.float32) / 255.0); ys.append(int(os.path.basename(os.path.dirname(f))))
    if xs:
        out["yeni3"] = (np.stack(xs), np.array(ys))
    return out


def standart_test(gorev, pool, n=6000):
    """Arşiv test bölmeleri (eğitime girmez), aynı bozulmayla ve bozulmasız."""
    import bolme
    out = {}
    rng = np.random.default_rng(77)
    for ad in ("emnist-digits-test", "emnist-harf-test", "the-test"):
        p = os.path.join(OB, ad + "_x.npy")
        if not os.path.exists(p):
            continue
        x = np.load(p, mmap_mode="r"); y = np.load(os.path.join(OB, ad + "_y.npy"))
        k = np.array([sinif_esle(gorev, c) for c in y]); m = np.nonzero(k >= 0)[0]
        if not len(m):
            continue
        m = rng.choice(m, min(n, len(m)), replace=False)
        out[ad] = (np.stack([bolme.mnist_normalle(np.asarray(x[i], np.float32) / 255.0) for i in m]), k[m])
        # [26.10 denetmen] seçim için: aynı test örneklerinin tutanak benzetimiyle bozulmuş kopyası (sabit tohum)
        out[ad + "-bozuk"] = (np.stack([boz(np.asarray(x[i]), rng) for i in m]), k[m])
    # eğitimde hiç kullanılmayan fontlardan (SAKLI_FONT) bozulmuş glifler: font kaynaklı örneklerin etkisi ayrı görünsün
    fg = font_gliflari(gorev, sakli=True)
    xs, ys = [], []
    for c, L in fg.items():
        for a in L:
            for _ in range(20):
                xs.append(boz(a, rng)); ys.append(c)
    if xs:
        out["font-sakli"] = (np.stack(xs), np.array(ys))
    return out


def secim_puani(gorev, sonu):
    """[26.10 denetmen] Model seçimi yalnız eğitime ve son ölçüme girmeyen kümelerle: arşiv test bölmelerinin bozuk kopyası
    + saklı fontlar. Gerçek tutanak kırpıntıları (tutanak-1, yeni3, tutanak-3) seçimde KULLANILMAZ, yalnız son ölçüm."""
    if gorev == "kod":
        return 0.5 * sonu.get("emnist-digits-test-bozuk", 0) + 0.2 * sonu.get("emnist-harf-test-bozuk", 0) + 0.3 * sonu.get("font-sakli", 0)
    return 0.45 * sonu.get("the-test-bozuk", 0) + 0.3 * sonu.get("emnist-harf-test-bozuk", 0) + 0.25 * sonu.get("font-sakli", 0)


def dogruluk(ag, X, Y):
    import torch
    ag.eval()
    with torch.no_grad():
        t = torch.from_numpy(X.astype(np.float32)).reshape(-1, 1, 28, 28)
        p = torch.cat([ag(t[i:i + 1000]).argmax(1) for i in range(0, len(t), 1000)]).numpy()
    return float((p == Y).mean())


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(os.path.join(_KL, "gunluk.txt"), "a", encoding="utf-8") as f:
        f.write(s + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("gorev", choices=list(GOREV))
    ap.add_argument("--bitis", default="07:00")
    ap.add_argument("--tur-ornek", type=int, default=160000)
    ap.add_argument("--isci", type=int, default=4)
    ap.add_argument("--is-parcacigi", type=int, default=8)
    ap.add_argument("--en-cok-tur", type=int, default=10000)
    a = ap.parse_args()
    import torch
    import torch.nn.functional as F
    from multiprocessing import Pool
    torch.set_num_threads(a.is_parcacigi)
    S = GOREV[a.gorev]; K = len(S)
    _KL = os.path.join(AD, a.gorev); os.makedirs(_KL, exist_ok=True)
    bugun = datetime.datetime.now()
    hh, mm = map(int, a.bitis.split(":"))
    bitis = bugun.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if bitis <= bugun:
        bitis += datetime.timedelta(days=1)
    ag = ag_kur(K)
    opt = torch.optim.AdamW(ag.parameters(), 2e-3, weight_decay=1e-4)
    tur, en_iyi, gecmis = 0, -1.0, []
    son = os.path.join(_KL, "son.pt")
    if os.path.exists(son):
        try:
            d = torch.load(son, weights_only=True)
        except Exception:
            # eski kayıtlarda geçmişte numpy sayıları var; dosya bu betiğin kendi ürettiği yerel kayıt (dış kaynak değil)
            d = torch.load(son, weights_only=False)
        ag.load_state_dict(d["ag"]); opt.load_state_dict(d["opt"]); tur, en_iyi, gecmis = d["tur"], d["en_iyi"], d["gecmis"]
        if d.get("puan_surum") != 2:
            # seçim ölçütü değişti (gerçek kırpıntılar artık seçimde yok): eski en iyi puanı karşılaştırılamaz, sıfırla
            if os.path.exists(os.path.join(_KL, "en-iyi.json")):
                os.replace(os.path.join(_KL, "en-iyi.json"), os.path.join(_KL, "en-iyi-eski-secim.json"))
                os.replace(os.path.join(_KL, "en-iyi.pt"), os.path.join(_KL, "en-iyi-eski-secim.pt"))
            en_iyi = -1.0
        log("kaldığı yerden sürüyor: tur", tur, "en iyi", en_iyi)
    gercek = gercek_kirpinti(a.gorev)
    with Pool(a.isci, initializer=isci_baslat, initargs=(a.gorev, 0)) as pool:
        std = standart_test(a.gorev, None)
        log("başladı", a.gorev, "sınıf", K, "bitiş", bitis.strftime("%d.%m %H:%M"), "gerçek:", {k: len(v[1]) for k, v in gercek.items()},
            "standart:", {k: len(v[1]) for k, v in std.items()})
        parca = 4000
        sonraki = pool.map_async(uret, [(parca, (tur + 1) * 100003 + i) for i in range(a.tur_ornek // parca)])
        while datetime.datetime.now() < bitis and tur < a.en_cok_tur:
            t0 = time.time()
            sonuc = sonraki.get()
            X = np.concatenate([s[0] for s in sonuc]); Y = np.concatenate([s[1] for s in sonuc])
            kaynak_say = {}
            for s in sonuc:
                for k_, v_ in s[2].items():
                    kaynak_say[k_] = kaynak_say.get(k_, 0) + v_
            del sonuc
            tur += 1
            sonraki = pool.map_async(uret, [(parca, (tur + 1) * 100003 + i) for i in range(a.tur_ornek // parca)])   # bir sonraki tur arka planda
            t1 = time.time()
            # öğrenme hızı: ilk 3 tur ısınma, sonra kosinüs benzeri 8 turluk döngüler (yeniden başlatmalı), taban 1e-4
            if tur <= 3:
                lr = 2e-3 * tur / 3
            else:
                f = ((tur - 4) % 8) / 8.0
                lr = 1e-4 + 0.5 * (1.5e-3 - 1e-4) * (1 + np.cos(np.pi * f))
            for g_ in opt.param_groups:
                g_["lr"] = lr
            ag.train(); perm = np.random.permutation(len(X)); top = 0.0; B = 256
            for i in range(0, len(X), B):
                ii = perm[i:i + B]
                xb = torch.from_numpy(X[ii].astype(np.float32) / 255.0).unsqueeze(1); yb = torch.from_numpy(Y[ii])
                k = F.cross_entropy(ag(xb), yb, label_smoothing=0.05)
                opt.zero_grad(); k.backward(); opt.step(); top += float(k.detach()) * len(ii)
            del X, Y
            sonu = {ad: round(dogruluk(ag, x, y), 4) for ad, (x, y) in list(std.items())}
            son_olcum = {ad: round(dogruluk(ag, x, y), 4) for ad, (x, y) in gercek.items()}   # yalnız kayıt, seçimde yok
            puan = float(secim_puani(a.gorev, sonu)); lr = float(lr)
            gecmis.append({"tur": tur, "lr": round(lr, 6), "kayip": round(top / len(perm), 4), "dogrulama": sonu, "gercek_son_olcum": son_olcum,
                           "puan": round(puan, 4), "puan_surum": 2, "egitim_kaynak": kaynak_say})
            sonu = dict(sonu, **{"[gerçek] " + k_: v_ for k_, v_ in son_olcum.items()})
            if puan > en_iyi:
                en_iyi = puan
                disa_aktar(ag, os.path.join(_KL, "en-iyi.json"), S, {"tur": tur, "olcum": sonu, "puan": puan, "tarih": time.strftime("%Y-%m-%d %H:%M")})
                torch.save(ag.state_dict(), os.path.join(_KL, "en-iyi.pt"))
            torch.save({"ag": ag.state_dict(), "opt": opt.state_dict(), "tur": tur, "en_iyi": en_iyi, "gecmis": gecmis, "puan_surum": 2}, son + ".yeni")
            os.replace(son + ".yeni", son)
            json.dump(gecmis, open(os.path.join(_KL, "gecmis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            log("tur %d lr %.5f kayıp %.4f üretim-bekleme %.0fs eğitim %.0fs | %s | puan %.4f en iyi %.4f" % (
                tur, lr, top / len(perm), t1 - t0, time.time() - t1, " ".join("%s=%.3f" % kv for kv in sonu.items()), puan, en_iyi))
        sonraki.wait()
    log("bitti: tur", tur, "en iyi puan", en_iyi)
