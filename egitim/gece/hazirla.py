# -*- coding: utf-8 -*-
"""
hazirla.py - gece eğitimi için kaynak verileri tek seferde uint8 .npy önbelleğine çevirir (bellek dostu, mmap ile okunur).
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
Kaynaklar (veri/ altında, KAYNAK.md): EMNIST (digits, byclass), T-H-E version6, HASYv2, Chars74K EnglishHnd, OFL el yazısı fontları.
Çıktı: veri/onbellek/<ad>_x.npy (N,28,28 uint8, beyaz mürekkep siyah zemin, ham), <ad>_y.npy (karakter dizgesi indeksleri), karakterler.json
Arşivler yalnız veri olarak açılır (tarfile 'data' süzgeci); içlerinden hiçbir şey çalıştırılmaz.
"""
import os, sys, io, gzip, json, tarfile, csv, re
import numpy as np
from PIL import Image

KOK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
V = os.path.join(KOK, "veri")
OB = os.path.join(V, "onbellek")
os.makedirs(OB, exist_ok=True)

THE_ETIKET = "abcdefghijklmnopqrstuvwxyzçğışöüáéíóőúű" + "ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİŞÖÜÁÉÍÓŐÚŰ"   # 1..78 (README tablosu)
BYCLASS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def kaydet(ad, x, y):
    np.save(os.path.join(OB, ad + "_x.npy"), np.ascontiguousarray(x, np.uint8))
    np.save(os.path.join(OB, ad + "_y.npy"), np.asarray(y, dtype="<U1"))
    print(ad, x.shape, "sınıf", len(set(y)), flush=True)


def idx(bol, ad):
    p = os.path.join(V, "emnist", "gzip", "emnist-%s-%s-%%s-idx%%d-ubyte.gz" % (bol, ad))
    with gzip.open(p % ("images", 3)) as f:
        x = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1, 28, 28).transpose(0, 2, 1)
    with gzip.open(p % ("labels", 1)) as f:
        y = np.frombuffer(f.read(), np.uint8, offset=8)
    return x, y


def emnist():
    for ad in ("train", "test"):
        x, y = idx("digits", ad)
        kaydet("emnist-digits-" + ad, x, [str(int(v)) for v in y])
        x, y = idx("byclass", ad)
        m = y >= 10                      # harfler (rakamları digits'ten alıyoruz)
        kaydet("emnist-harf-" + ad, x[m], [BYCLASS[int(v)] for v in y[m]])


def the():
    xs, ys = [], []
    with open(os.path.join(V, "the-dataset", "version6.csv")) as f:
        for ln in f:
            i = ln.find(",")
            ys.append(THE_ETIKET[int(float(ln[:i])) - 1])
            xs.append(np.array(ln[i + 1:].strip().split(","), dtype=np.float32))
    a = np.stack(xs)
    if a.max() <= 1.0:
        a = a * 255
    a = a.reshape(-1, 28, 28).transpose(0, 2, 1).astype(np.uint8)
    # yazar bazlı değil, rastgele %10 test (T-H-E'de yazar kimliği yok)
    rng = np.random.default_rng(5); p = rng.permutation(len(a)); n = len(a) // 10
    ys = np.array(ys)
    kaydet("the-test", a[p[:n]], ys[p[:n]]); kaydet("the-train", a[p[n:]], ys[p[n:]])


def kare28(im, kenar=4):
    """PIL gri (koyu mürekkep açık zemin ya da tersi) -> 28x28 beyaz mürekkep; oran korunur."""
    a = np.asarray(im.convert("L"), np.float32)
    if a.mean() > 127:
        a = 255 - a
    ys, xs = np.nonzero(a > 40)
    if len(ys) == 0:
        return None
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape; s = (28 - 2 * kenar) / max(h, w)
    b = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS))
    t = np.zeros((28, 28), np.uint8); oy, ox = (28 - b.shape[0]) // 2, (28 - b.shape[1]) // 2
    t[oy:oy + b.shape[0], ox:ox + b.shape[1]] = b
    return t


def chars74k():
    xs, ys = [], []
    with tarfile.open(os.path.join(V, "chars74k", "EnglishHnd.tgz")) as tf:
        for m in tf.getmembers():
            if not (m.isfile() and m.name.lower().endswith(".png") and "/Img/" in m.name):
                continue
            s = [p for p in m.name.split("/") if p.startswith("Sample")]
            if not s:
                continue
            k = int(s[0][6:]) - 1                  # Sample001..062 -> 0-9, A-Z, a-z
            t = kare28(Image.open(io.BytesIO(tf.extractfile(m).read())))
            if t is not None:
                xs.append(t); ys.append(BYCLASS[k])
    kaydet("chars74k", np.stack(xs), ys)


def hasy():
    izin = set(BYCLASS)
    xs, ys = [], []
    # bz2 tar'da rastgele erişim her seferinde baştan açar (çok yavaş): tek geçişte akış olarak oku
    resim, etiket_metni = {}, None
    with tarfile.open(os.path.join(V, "hasyv2", "HASYv2.tar.bz2"), "r|bz2") as tf:
        for m in tf:
            if not m.isfile():
                continue
            if m.name.endswith("hasy-data-labels.csv"):
                etiket_metni = (m.name.rsplit("hasy-data-labels.csv", 1)[0], tf.extractfile(m).read().decode("utf-8"))
            elif m.name.endswith(".png"):
                resim[m.name] = tf.extractfile(m).read()
    kok, metin = etiket_metni
    for r in csv.DictReader(io.StringIO(metin)):
        lt = r["latex"]
        c = lt if len(lt) == 1 and lt in izin else None
        b = resim.get(kok + r["path"].lstrip("./")) or resim.get(kok + r["path"])
        if c is None or b is None:
            continue
        t = kare28(Image.open(io.BytesIO(b)))
        if t is not None:
            xs.append(t); ys.append(c)
    kaydet("hasy", np.stack(xs), ys)


def usps():
    """LIBSVM biçimi: 'etiket(1-10) i:değer(-1..1)' 16x16; etiket 10 = rakam 0? -> LIBSVM usps'de etiket-1 = rakam."""
    import bz2
    xs, ys = [], []
    for ad in ("usps.bz2", "usps.t.bz2"):
        with bz2.open(os.path.join(V, "usps", ad), "rt") as f:
            for ln in f:
                p = ln.split()
                if not p:
                    continue
                a = np.full(256, -1.0, np.float32)
                for t in p[1:]:
                    i, d = t.split(":"); a[int(i) - 1] = float(d)
                im = Image.fromarray(((a.reshape(16, 16) + 1) * 127.5).clip(0, 255).astype(np.uint8))
                t = kare28(im)
                if t is not None:
                    xs.append(t); ys.append(str(int(float(p[0])) - 1))
    kaydet("usps", np.stack(xs), ys)


def qmnist():
    """QMNIST test (60k; MNIST'in kayıp 50k test rakamı dahil, farklı yazarlar). Etiket dosyası idx2-int: N x 8, ilk sütun rakam."""
    with gzip.open(os.path.join(V, "qmnist", "qmnist-test-images-idx3-ubyte.gz")) as f:
        x = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1, 28, 28)
    with gzip.open(os.path.join(V, "qmnist", "qmnist-test-labels-idx2-int.gz")) as f:
        y = np.frombuffer(f.read(), ">i4", offset=12).reshape(-1, 8)[:, 0]
    kaydet("qmnist", x, [str(int(v)) for v in y])


def iam():
    """IAM-line (Teklia, parquet): bitişik İngilizce satırlar -> yükseklik 32, mürekkep beyaz; genişlik <= 1024.
    Etiket: yalnız harf/rakam/boşluk/'-' içeren satırlar; boşluk etiketten çıkarılır (kelime tanıyıcıda boşluk sınıfı yok).
    Kayıt: iam-<bolum>_x.npy (32, toplam_genislik) + _w.npy (genişlikler) + _y.json."""
    import pyarrow.parquet as pq, cv2
    izin = re.compile("^[A-Za-z0-9 \\-.,'\"!?;:()#&*/+]+$")   # noktalama izinli ama etiketten çıkarılır (küçük işaretler; bilinen gürültü)
    for bol in ("train", "validation", "test"):
        t = pq.read_table(os.path.join(V, "iam-line", "data", bol + ".parquet")).to_pylist()
        sut, gen, ys = [], [], []
        for r in t:
            m = r["text"].strip()
            if not izin.match(m):
                continue
            a = 255 - np.asarray(Image.open(io.BytesIO(r["image"]["bytes"])).convert("L"), np.float32)
            a = np.clip((a - np.percentile(a, 50)) * 1.5, 0, 255)
            rs = np.nonzero(a.max(1) > 60)[0]; cs = np.nonzero(a.max(0) > 60)[0]
            if not len(rs):
                continue
            a = a[rs.min():rs.max() + 1, cs.min():cs.max() + 1]
            w = int(round(a.shape[1] * 28.0 / a.shape[0]))
            if w > 1020 or w < 8:
                continue
            b = np.zeros((32, w + 4), np.uint8)
            b[2:30, 2:2 + w] = cv2.resize(a, (w, 28), interpolation=cv2.INTER_AREA).astype(np.uint8)
            sut.append(b); gen.append(b.shape[1]); ys.append(re.sub(r"[^A-Za-z0-9\-]", "", m))
        np.save(os.path.join(OB, "iam-%s_x.npy" % bol), np.concatenate(sut, 1))
        np.save(os.path.join(OB, "iam-%s_w.npy" % bol), np.array(gen, np.int32))
        json.dump(ys, open(os.path.join(OB, "iam-%s_y.json" % bol), "w", encoding="utf-8"), ensure_ascii=False)
        print("iam", bol, len(ys), "/", len(t), "satır, ort. genişlik", int(np.mean(gen)), flush=True)
        del t, sut


if __name__ == "__main__":
    adim = sys.argv[1:] or ["emnist", "the", "chars74k", "hasy"]
    for a in adim:
        globals()[a]()
