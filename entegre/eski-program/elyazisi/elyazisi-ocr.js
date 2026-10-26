/*
 * [2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: KOD_DESENI T+4/5 rakam; hucreOku hedef kutu sayilari [6,9] AYNEN: [5,6,8,9] denendi, 5 kutuda bolmeyi durdurup yanlis kabul artirdi]
 * elyazisi-ocr.js - El yazısı stok kodu ve adet okuyucu (saf ES5, bağımlılık yok).
 *
 * Python prototipinin (egitim/bolme.py, cikarim_numpy.py, coz.py) birebir JS karşılığıdır.
 * Tek global: ElYazisiOCR. Ağ isteği yok, eval/Function/innerHTML yok.
 *
 * Kullanım:
 *   var s = ElYazisiOCR.oku({width:w, height:h, data:rgba}, kodListesi, ayar);
 *   s.satirlar[i].stok.secilen / .aday / .guven / .durum  ("kabul" | "sor" | "bos")
 *
 * Model: window.ELYAZISI_MODEL (js/model.js) ya da ayar.model.
 * Çözünürlük: piksel cinsinden sabitler referans çözünürlüğe (uzun kenar 3966 px, Python'un
 * çalıştığı tutanak-1.jpg) göre yazılmıştır; görüntü daha küçükse ayar.olcekle ile orantılanır.
 */
(function (kok) {
  "use strict";

  var SINIFLAR = "0123456789T-";

  // ---------------------------------------------------------------- ayarlar
  // bolme.py AYAR ile aynı. referans_kenar: bu sabitlerin ayarlandığı uzun kenar.
  var AYAR = {
    stok_sutun: 1,
    adet_sutun: 3,
    esik_yaricap: 25,
    esik_fark: 12,
    satir_oran: 0.30,
    sutun_oran: 0.40,
    murekkep_mutlak: 130,
    murekkep_fark: 25,
    hucre_ic_pay: 7,
    referans_kenar: 3966,   // piksel sabitlerinin ölçeklendiği referans uzun kenar
    olcekle: true,          // false: sabitler olduğu gibi (Python ile birebir) kullanılır
    adet_esik: 0.8          // adet güveni (ortalama en yüksek olasılık) bunun altındaysa "sor"
  };

  // coz.py sabitleri
  var EPS = 1e-6;
  var CEZA_KUTU = 6.0;   // fazladan kutu: log ceza
  var CEZA_HARF = 6.0;   // kodun bir harfi için kutu yok: log ceza
  var CEZA_T = 1.0;      // yalnız baştaki 'T' yazılmamışsa: hafif ceza (T'siz yazan yazarlar için)
  var TIRE_IPUCU = 1.0;  // geometri "tire" dediyse '-' log-puanına eklenir
  var TAU = 1.5;         // sıcaklık
  var ESIK = 2.0;        // en iyi - ikinci farkı (nat) bunun altındaysa "sor"
  var ESIK_MUTLAK = 3.0; // kısıtsız en iyi okuma ile seçilen kod arasındaki log fark (nat) bunu aşarsa "sor" (kapalı liste koruması)
  var KOD_DESENI = /^T\d{4,5}(-\d{2})?$/;

  function simdi() {
    return (typeof performance !== "undefined" && performance.now) ? performance.now() : new Date().getTime();
  }

  // Python round(): yarımlarda çifte yuvarlar (banker's rounding)
  function yuvarla(x) {
    var f = Math.floor(x), d = x - f;
    if (d < 0.5) return f;
    if (d > 0.5) return f + 1;
    return (f % 2 === 0) ? f : f + 1;
  }

  function ayarBirlestir(ayar) {
    var o = {}, k;
    for (k in AYAR) if (AYAR.hasOwnProperty(k)) o[k] = AYAR[k];
    if (ayar) for (k in ayar) if (ayar.hasOwnProperty(k)) o[k] = ayar[k];
    return o;
  }

  // -------------------------------------------------------- görüntü -> gri
  // PIL convert("L") ile aynı: (R*19595 + G*38470 + B*7471 + 0x8000) >> 16
  function griyeCevir(goruntu) {
    var w = goruntu.width, h = goruntu.height, d = goruntu.data;
    var g = new Uint8Array(w * h);
    var n = w * h, i, j = 0;
    for (i = 0; i < n; i++, j += 4) {
      g[i] = (d[j] * 19595 + d[j + 1] * 38470 + d[j + 2] * 7471 + 32768) >> 16;
    }
    return g;
  }

  // ------------------------------------------------ yerel ortalama ve maskeler
  // bolme.py kutu_ortalama + tablo_bul koyu maskesi + murekkep_maskesi tek geçişte.
  // Pencere (2r+1)^2, kenar yineleme (edge pad). Tam sayı toplamlarla karşılaştırılır:
  //   g < toplam/kk - fark   <=>   g*kk < toplam - fark*kk
  function maskeleriUret(g, w, h, r, esikFark, murMutlak, murFark) {
    var kk = (2 * r + 1) * (2 * r + 1);
    var tmp = new Int32Array(w * h);
    var koyu = new Uint8Array(w * h);
    var mur = new Uint8Array(w * h);
    var x, y, s, b, i, a;
    // 1) yatay geçiş: her satırda (2r+1) genişlikli kayan toplam, kenar yinelemeli
    for (y = 0; y < h; y++) {
      b = y * w;
      s = r * g[b];
      for (i = 0; i <= r; i++) s += g[b + (i < w ? i : w - 1)];
      for (x = 0; x < w; x++) {
        tmp[b + x] = s;
        a = x + r + 1; if (a > w - 1) a = w - 1;
        i = x - r; if (i < 0) i = 0;
        s += g[b + a] - g[b + i];
      }
    }
    // 2) dikey geçiş: sütun toplamlarını satır satır kaydır
    var acc = new Int32Array(w);
    var ust, alt, tb;
    for (x = 0; x < w; x++) acc[x] = r * tmp[x];
    for (i = 0; i <= r; i++) {
      tb = (i < h ? i : h - 1) * w;
      for (x = 0; x < w; x++) acc[x] += tmp[tb + x];
    }
    var ekKoyu = esikFark * kk, ekMur = murFark * kk;
    for (y = 0; y < h; y++) {
      b = y * w;
      for (x = 0; x < w; x++) {
        var v = g[b + x] * kk, S = acc[x];
        if (v < S - ekKoyu) {
          koyu[b + x] = 1;
          if (g[b + x] < murMutlak && v < S - ekMur) mur[b + x] = 1;
        }
      }
      ust = y + r + 1; if (ust > h - 1) ust = h - 1;
      alt = y - r; if (alt < 0) alt = 0;
      ust *= w; alt *= w;
      for (x = 0; x < w; x++) acc[x] += tmp[ust + x] - tmp[alt + x];
    }
    return { koyu: koyu, mur: mur };
  }

  // ------------------------------------------------------------ tablo bulma
  function kumeler(profil, esik) {
    var sonuc = [], bas = -1, i, n = profil.length;
    for (i = 0; i < n; i++) {
      if (profil[i] > esik && bas < 0) bas = i;
      else if (profil[i] <= esik && bas >= 0) { sonuc.push([bas, i - 1]); bas = -1; }
    }
    if (bas >= 0) sonuc.push([bas, n - 1]);
    return sonuc;
  }

  // Aralıkları referans aralığın +-%8'i içinde kalan en uzun ardışık çizgi dizisi
  function duzenliDizi(merkezler, tol) {
    var n = merkezler.length;
    if (n < 3) return merkezler.slice();
    var ara = [], i, j, r, enIyi = [];
    for (i = 0; i < n - 1; i++) ara.push(merkezler[i + 1] - merkezler[i]);
    for (r = 0; r < ara.length; r++) {
      var ref = ara[r], blok = [];
      for (i = 0; i <= ara.length; i++) {
        if (i < ara.length && Math.abs(ara[i] - ref) <= tol * ref) { blok.push(i); continue; }
        if (blok.length && blok.length + 1 > enIyi.length) {
          enIyi = [merkezler[blok[0]]];
          for (j = 0; j < blok.length; j++) enIyi.push(merkezler[blok[j] + 1]);
        }
        blok = [];
      }
    }
    return enIyi;
  }

  function tabloBul(koyu, w, h, ay) {
    var satirProfil = new Int32Array(h), x, y, b, s;
    for (y = 0; y < h; y++) {
      b = y * w; s = 0;
      for (x = 0; x < w; x++) s += koyu[b + x];
      satirProfil[y] = s;
    }
    var k = kumeler(satirProfil, ay.satir_oran * w);
    var satirlar = [], i;
    for (i = 0; i < k.length; i++) {
      if (k[i][0] > ay.kenar_pay && k[i][1] < h - ay.kenar_pay) satirlar.push((k[i][0] + k[i][1]) / 2.0);
    }
    satirlar = duzenliDizi(satirlar, 0.08);
    if (satirlar.length < 3) throw new Error("tablo satır çizgileri bulunamadı");
    var y0 = Math.floor(satirlar[0]), y1 = Math.floor(satirlar[satirlar.length - 1]);
    var sutunProfil = new Int32Array(w);
    for (y = y0; y < y1; y++) {
      b = y * w;
      for (x = 0; x < w; x++) sutunProfil[x] += koyu[b + x];
    }
    var k2 = kumeler(sutunProfil, ay.sutun_oran * (y1 - y0));
    var sutunlar = [];
    for (i = 0; i < k2.length; i++) {
      if (k2[i][0] > ay.kenar_pay && k2[i][1] < w - ay.kenar_pay && k2[i][1] - k2[i][0] < ay.cizgi_kalinlik) {
        sutunlar.push((k2[i][0] + k2[i][1]) / 2.0);
      }
    }
    return { satirlar: satirlar, sutunlar: sutunlar };
  }

  // ------------------------------------------------------------ hücre temizliği
  // Maskeden uzun yatay (>%55 genişlik) ve dikey (>%85 yükseklik) koşuları siler.
  function cizgiTemizle(m, w, h) {
    var x, y, s;
    for (y = 0; y < h; y++) {
      x = 0;
      while (x < w) {
        if (m[y * w + x]) {
          s = x;
          while (x < w && m[y * w + x]) x++;
          if (x - s > 0.55 * w) { for (var t = s; t < x; t++) m[y * w + t] = 0; }
        } else x++;
      }
    }
    for (x = 0; x < w; x++) {
      y = 0;
      while (y < h) {
        if (m[y * w + x]) {
          s = y;
          while (y < h && m[y * w + x]) y++;
          if (y - s > 0.85 * h) { for (var u = s; u < y; u++) m[u * w + x] = 0; }
        } else y++;
      }
    }
  }

  // ------------------------------------------------------ bağlı bileşenler
  // 8 komşuluk, yığınlı taşkın doldurma (özyineleme yok). Dönüş: [x0,y0,x1,y1,alan] listesi.
  function bilesenler(m, w, h) {
    var etiket = new Uint8Array(w * h);
    var yigin = new Int32Array(w * h > 0 ? w * h : 1);
    var sonuc = [], p, sp, q, x, y, cx, cy, nx, ny, dx, dy;
    for (p = 0; p < w * h; p++) {
      if (!m[p] || etiket[p]) continue;
      var x0 = w, y0 = h, x1 = -1, y1 = -1, alan = 0;
      sp = 0; yigin[sp++] = p; etiket[p] = 1;
      while (sp > 0) {
        q = yigin[--sp];
        cy = (q / w) | 0; cx = q - cy * w;
        alan++;
        if (cx < x0) x0 = cx; if (cx > x1) x1 = cx;
        if (cy < y0) y0 = cy; if (cy > y1) y1 = cy;
        for (dy = -1; dy <= 1; dy++) {
          ny = cy + dy; if (ny < 0 || ny >= h) continue;
          for (dx = -1; dx <= 1; dx++) {
            nx = cx + dx; if (nx < 0 || nx >= w) continue;
            var qq = ny * w + nx;
            if (m[qq] && !etiket[qq]) { etiket[qq] = 1; yigin[sp++] = qq; }
          }
        }
      }
      sonuc.push([x0, y0, x1 + 1, y1 + 1, alan]);
    }
    return sonuc;
  }

  // ---------------------------------------------------------- karakter bölme
  function kutuKarsilastir(a, b) {
    return (a[0] - b[0]) || (a[1] - b[1]) || (a[2] - b[2]) || (a[3] - b[3]);
  }

  // Birbirine değen karakterleri izdüşüm minimumundan böler (bolme.py genis_bol)
  function genisBol(m, w, kutular, hedefler, oran, minGenislik) {
    kutular = kutular.map(function (k) { return k.slice(); });
    var enBuyukHedef = Math.max.apply(null, hedefler);
    var degisti = true;
    while (degisti && hedefler.indexOf(kutular.length) < 0 && kutular.length < enBuyukHedef) {
      degisti = false;
      var enIyi = -1, enR = 0.0, i;
      for (i = 0; i < kutular.length; i++) {
        var kk = kutular[i];
        var r = (kk[2] - kk[0]) / Math.max(1, kk[3] - kk[1]);
        var sinir = (i === 0) ? 1.9 : oran;
        if (r > sinir && r > enR && (kk[2] - kk[0]) >= minGenislik) { enIyi = i; enR = r; }
      }
      if (enIyi < 0) break;
      var x0 = kutular[enIyi][0], y0 = kutular[enIyi][1], x1 = kutular[enIyi][2], y1 = kutular[enIyi][3];
      var gen = x1 - x0, x, y;
      var izd = new Float64Array(gen);
      for (y = y0; y < y1; y++) for (x = 0; x < gen; x++) izd[x] += m[y * w + x0 + x];
      var a = Math.floor(0.35 * gen), b = Math.max(a + 1, Math.floor(0.65 * gen));
      // 3 sütunluk ortalama (np.convolve 'same', kenarlarda sıfır)
      var kes = a, enAz = Infinity;
      for (x = a; x < b; x++) {
        var d = ((x > 0 ? izd[x - 1] : 0) + izd[x] + (x < gen - 1 ? izd[x + 1] : 0)) / 3.0;
        if (d < enAz) { enAz = d; kes = x; }
      }
      var parcalar = [], pi;
      var aralik = [[x0, x0 + kes], [x0 + kes, x1]];
      for (pi = 0; pi < 2; pi++) {
        var xa = aralik[pi][0], xb = aralik[pi][1], ymin = -1, ymax = -1;
        for (y = y0; y < y1; y++) {
          var dolu = 0;
          for (x = xa; x < xb; x++) { if (m[y * w + x]) { dolu = 1; break; } }
          if (dolu) { if (ymin < 0) ymin = y; ymax = y; }
        }
        if (ymin < 0) continue;
        parcalar.push([xa, ymin, xb, ymax + 1]);
      }
      if (parcalar.length < 2) break;
      kutular.splice(enIyi, 1, parcalar[0], parcalar[1]);
      degisti = true;
    }
    return kutular;
  }

  // m: hücre maskesi (w x h). Dönüş: [[x0,y0,x1,y1,tireMi], ...] soldan sağa
  function karakterKutulari(m, w, h, hedefler, ay) {
    var bil = bilesenler(m, w, h), kutular = [], i;
    for (i = 0; i < bil.length; i++) {
      var k = bil[i], bw = k[2] - k[0], bh = k[3] - k[1];
      if (k[4] < 0.004 * h * h || (bh < 0.18 * h && bw < 0.18 * h)) continue;
      kutular.push(k);
    }
    if (kutular.length) {
      var alanlar = kutular.map(function (k) { return k[4]; }).sort(function (a, b) { return a - b; });
      var med = alanlar[Math.floor(alanlar.length / 2)];
      kutular = kutular.filter(function (k) {
        return k[4] >= 0.05 * med || (k[2] - k[0]) >= 1.6 * (k[3] - k[1]);
      });
    }
    kutular = kutular.map(function (k) { return [k[0], k[1], k[2], k[3]]; });
    kutular.sort(kutuKarsilastir);
    var birlesik = [];
    for (i = 0; i < kutular.length; i++) {
      var kk = kutular[i];
      if (birlesik.length) {
        var p = birlesik[birlesik.length - 1];
        var ort = Math.min(p[2], kk[2]) - Math.max(p[0], kk[0]);
        var dar = Math.min(p[2] - p[0], kk[2] - kk[0]);
        if (ort > 0.5 * dar) {
          p[0] = Math.min(p[0], kk[0]); p[1] = Math.min(p[1], kk[1]);
          p[2] = Math.max(p[2], kk[2]); p[3] = Math.max(p[3], kk[3]);
          continue;
        }
      }
      birlesik.push(kk.slice());
    }
    if (hedefler) birlesik = genisBol(m, w, birlesik, hedefler, 0.9, ay.bol_min_genislik);
    var sonuc = [];
    for (i = 0; i < birlesik.length; i++) {
      var b = birlesik[i], gw = b[2] - b[0], gh = b[3] - b[1];
      var tire = gw >= 1.6 * gh && gh < 0.30 * h;
      sonuc.push([b[0], b[1], b[2], b[3], tire]);
    }
    return sonuc;
  }

  // ------------------------------------------- MNIST biçimine normalleştirme
  // Alan ortalamalı yeniden örnekleme ağırlıkları: (nHedef x nKaynak) düz dizi
  function alanAgirliklari(nKaynak, nHedef) {
    var A = new Float64Array(nHedef * nKaynak);
    var oran = nKaynak / nHedef, i, j, toplam;
    for (i = 0; i < nHedef; i++) {
      var b = i * oran, s = (i + 1) * oran;
      var son = Math.min(Math.ceil(s), nKaynak);
      toplam = 0;
      for (j = Math.floor(b); j < son; j++) {
        var v = Math.min(s, j + 1) - Math.max(b, j);
        A[i * nKaynak + j] = v; toplam += v;
      }
      toplam = Math.max(toplam, 1e-9);
      for (j = 0; j < nKaynak; j++) A[i * nKaynak + j] /= toplam;
    }
    return A;
  }

  // m: hücre maskesi (mw genişlikli), kutu: [x0,y0,x1,y1]. Dönüş: Float32Array(784)
  function mnistNormalle(m, mw, kutu) {
    var T = 28, KUTU = 20;
    var cikis = new Float32Array(T * T);
    var x, y, ymin = 1e9, ymax = -1, xmin = 1e9, xmax = -1;
    for (y = kutu[1]; y < kutu[3]; y++) {
      for (x = kutu[0]; x < kutu[2]; x++) {
        if (m[y * mw + x]) {
          if (y < ymin) ymin = y; if (y > ymax) ymax = y;
          if (x < xmin) xmin = x; if (x > xmax) xmax = x;
        }
      }
    }
    if (ymax < 0) return cikis;
    var h = ymax - ymin + 1, w = xmax - xmin + 1;
    var olcek = KUTU / Math.max(h, w);
    var h2 = Math.max(1, yuvarla(h * olcek)), w2 = Math.max(1, yuvarla(w * olcek));
    var Ah = alanAgirliklari(h, h2), Aw = alanAgirliklari(w, w2);
    // tmp = Ah . a  (h2 x w)
    var tmp = new Float64Array(h2 * w), i, j, v;
    for (i = 0; i < h2; i++) {
      for (j = 0; j < h; j++) {
        v = Ah[i * h + j];
        if (v === 0) continue;
        var kb = (ymin + j) * mw + xmin;
        for (x = 0; x < w; x++) if (m[kb + x]) tmp[i * w + x] += v;
      }
    }
    // k = tmp . Aw^T  (h2 x w2), 28x28 tuvale ortalanarak yerleşir
    var tuval = new Float64Array(T * T);
    var oy = (T - h2) >> 1, ox = (T - w2) >> 1;
    var toplam = 0, sy = 0, sx = 0;
    for (i = 0; i < h2; i++) {
      for (j = 0; j < w2; j++) {
        var s = 0;
        for (x = 0; x < w; x++) s += tmp[i * w + x] * Aw[j * w + x];
        tuval[(oy + i) * T + ox + j] = s;
      }
    }
    for (y = 0; y < T; y++) for (x = 0; x < T; x++) {
      v = tuval[y * T + x]; toplam += v; sy += v * y; sx += v * x;
    }
    var son = tuval;
    if (toplam > 0) {
      var cy = sy / toplam, cx = sx / toplam;
      var dy = yuvarla(T / 2.0 - 0.5 - cy), dx = yuvarla(T / 2.0 - 0.5 - cx);
      son = new Float64Array(T * T);
      var ys0 = Math.max(0, -dy), ys1 = Math.min(T, T - dy);
      var xs0 = Math.max(0, -dx), xs1 = Math.min(T, T - dx);
      if (ys1 > ys0 && xs1 > xs0) {
        for (y = ys0; y < ys1; y++) for (x = xs0; x < xs1; x++) son[(y + dy) * T + x + dx] = tuval[y * T + x];
      }
    }
    for (i = 0; i < T * T; i++) cikis[i] = son[i] < 0 ? 0 : (son[i] > 1 ? 1 : son[i]);
    return cikis;
  }

  // ------------------------------------------------------------- CNN ileri geçiş
  // cikarim_numpy.py ile aynı: dolgu yok, adım 1, maxpool 2 (taban bölme), düzleştirme (k,y,x)
  function modelHazirla(model) {
    if (model._hazir) return model;
    var i;
    for (i = 0; i < model.katmanlar.length; i++) {
      var kat = model.katmanlar[i];
      if (kat.w) kat._w = new Float64Array(kat.w);
      if (kat.b) kat._b = new Float64Array(kat.b);
    }
    model._hazir = true;
    return model;
  }

  function evris(x, ch, hh, ww, kat) {
    var cin = kat.giris, cout = kat.cikis, k = kat.k;
    var ho = hh - k + 1, wo = ww - k + 1;
    var o = new Float64Array(cout * ho * wo);
    var W = kat._w, B = kat._b;
    var oc, ic, dy, dx, y, xx;
    for (oc = 0; oc < cout; oc++) {
      var ob = oc * ho * wo;
      for (y = 0; y < ho * wo; y++) o[ob + y] = B[oc];
      for (ic = 0; ic < cin; ic++) {
        var ib = ic * hh * ww;
        for (dy = 0; dy < k; dy++) {
          for (dx = 0; dx < k; dx++) {
            var wv = W[((oc * cin + ic) * k + dy) * k + dx];
            for (y = 0; y < ho; y++) {
              var so = ob + y * wo, si = ib + (y + dy) * ww + dx;
              for (xx = 0; xx < wo; xx++) o[so + xx] += wv * x[si + xx];
            }
          }
        }
      }
    }
    return { v: o, c: cout, h: ho, w: wo };
  }

  function havuz(x, ch, hh, ww, k) {
    var ho = (hh / k) | 0, wo = (ww / k) | 0;
    var o = new Float64Array(ch * ho * wo);
    var c, y, xx, dy, dx;
    for (c = 0; c < ch; c++) {
      for (y = 0; y < ho; y++) {
        for (xx = 0; xx < wo; xx++) {
          var m = -Infinity;
          for (dy = 0; dy < k; dy++) for (dx = 0; dx < k; dx++) {
            var v = x[(c * hh + y * k + dy) * ww + xx * k + dx];
            if (v > m) m = v;
          }
          o[(c * ho + y) * wo + xx] = m;
        }
      }
    }
    return { v: o, c: ch, h: ho, w: wo };
  }

  // goruntu: Float32Array/Array(784), 0..1. Dönüş: Float64Array(12) olasılık
  function ileri(model, goruntu) {
    modelHazirla(model);
    var x = new Float64Array(784), i;
    for (i = 0; i < 784; i++) x[i] = goruntu[i];
    var d = { v: x, c: 1, h: 28, w: 28 };
    var duz = null;   // düzleştirildikten sonra tek boyutlu vektör
    for (i = 0; i < model.katmanlar.length; i++) {
      var kat = model.katmanlar[i], t = kat.tip;
      if (t === "conv") d = evris(d.v, d.c, d.h, d.w, kat);
      else if (t === "maxpool") d = havuz(d.v, d.c, d.h, d.w, kat.k);
      else if (t === "duzlestir") duz = d.v;
      else if (t === "fc") {
        var g = kat.giris, c = kat.cikis, W = kat._w, B = kat._b, girdi = duz || d.v;
        var o = new Float64Array(c), a, b;
        for (a = 0; a < c; a++) {
          var s = B[a], wb = a * g;
          for (b = 0; b < g; b++) s += W[wb + b] * girdi[b];
          o[a] = s;
        }
        duz = o;
      }
      if (kat.aktivasyon === "relu") {
        var arr = duz || d.v, j;
        for (j = 0; j < arr.length; j++) if (arr[j] < 0) arr[j] = 0;
      }
    }
    // softmax
    var z = duz, mx = -Infinity, top = 0, n = z.length, p = new Float64Array(n);
    for (i = 0; i < n; i++) if (z[i] > mx) mx = z[i];
    for (i = 0; i < n; i++) { p[i] = Math.exp(z[i] - mx); top += p[i]; }
    for (i = 0; i < n; i++) p[i] /= top;
    return p;
  }

  // --------------------------------------------------------- kısıtlı çözümleme
  // kodListesi: dizgi dizisi. Dönüş: {sayi, gruplar:[{L, kodlar:[...], idx:Int8Array}]}
  function kodIndeksi(liste) {
    var goruldu = {}, temiz = [], i;
    for (i = 0; i < liste.length; i++) {
      var k = liste[i];
      if (typeof k === "string" && KOD_DESENI.test(k) && !goruldu.hasOwnProperty(k)) {
        goruldu[k] = 1; temiz.push(k);
      }
    }
    temiz.sort();
    var gruplar = [], tablo = {}, j;
    for (i = 0; i < temiz.length; i++) {
      var L = temiz[i].length;
      if (!tablo.hasOwnProperty(L)) { tablo[L] = { L: L, kodlar: [] }; gruplar.push(tablo[L]); }
      tablo[L].kodlar.push(temiz[i]);
    }
    for (i = 0; i < gruplar.length; i++) {
      var gr = gruplar[i];
      gr.idx = new Int8Array(gr.kodlar.length * gr.L);
      for (j = 0; j < gr.kodlar.length; j++) {
        for (var c = 0; c < gr.L; c++) gr.idx[j * gr.L + c] = SINIFLAR.indexOf(gr.kodlar[j].charAt(c));
      }
    }
    return { sayi: temiz.length, gruplar: gruplar };
  }

  function logMatris(P, tire) {
    var n = P.length, lp = new Float64Array(n * 12), i, c;
    for (i = 0; i < n; i++) {
      for (c = 0; c < 12; c++) lp[i * 12 + c] = Math.log(Math.max(P[i][c], EPS)) / TAU;
      if (tire && tire[i]) lp[i * 12 + 11] += TIRE_IPUCU;
    }
    return lp;
  }

  function hamOku(P) {
    var s = "", i, c;
    for (i = 0; i < P.length; i++) {
      var en = 0;
      for (c = 1; c < 12; c++) if (P[i][c] > P[i][en]) en = c;
      s += SINIFLAR.charAt(en);
    }
    return s;
  }

  // Her aday kodun puanı; en iyi 3 (eşitlikte listede önce gelen) ve toplam aday sayısı
  function stokCoz(P, indeks, tire) {
    var ham = hamOku(P), n = P.length;
    if (n === 0) return { ham: "", adaylar: [], guven: 0.0, durum: "sor" };
    var lp = logMatris(P, tire);
    // kısıtsız üst sınır: her kutuda en olası sınıfın log-puanı; seçilen kodun bundan uzaklığı "acik" (kapalı liste koruması)
    var ust = 0, ci, cc;
    for (ci = 0; ci < n; ci++) { var enb = -1e18; for (cc = 0; cc < 12; cc++) if (lp[ci * 12 + cc] > enb) enb = lp[ci * 12 + cc]; ust += enb; }
    var top = [];   // [{kod, puan, acik}] azalan, en çok 3
    var gi, j, i, a;
    for (gi = 0; gi < indeks.gruplar.length; gi++) {
      var gr = indeks.gruplar[gi], L = gr.L, idx = gr.idx;
      if (Math.abs(L - n) > 1) continue;
      for (j = 0; j < gr.kodlar.length; j++) {
        var b = j * L, puan, ceza = 0;
        if (L === n) {
          puan = 0;
          for (i = 0; i < n; i++) puan += lp[i * 12 + idx[b + i]];
        } else if (L === n + 1) {
          // kodun bir harfi için kutu yok: s. harf atlanır. s=0 ve harf 'T' ise ucuz: bazı yazarlar T'yi yazmıyor (tutanak-3)
          puan = -1e18; ceza = CEZA_HARF;
          for (var s = 0; s < L; s++) {
            var v = 0;
            for (i = 0; i < s; i++) v += lp[i * 12 + idx[b + i]];
            for (i = s; i < n; i++) v += lp[i * 12 + idx[b + i + 1]];
            var cz = (s === 0 && idx[b] === 10) ? CEZA_T : CEZA_HARF;
            if (v - cz > puan - ceza) { puan = v; ceza = cz; }
          }
          puan -= ceza;
        } else {
          // bir kutu fazla: s. kutu atlanır
          puan = -1e18;
          for (var t = 0; t < n; t++) {
            var w = 0;
            for (i = 0; i < t; i++) w += lp[i * 12 + idx[b + i]];
            for (i = t + 1; i < n; i++) w += lp[i * 12 + idx[b + i - 1]];
            if (w > puan) puan = w;
          }
          puan -= CEZA_KUTU; ceza = CEZA_KUTU;
        }
        if (top.length < 3 || puan > top[top.length - 1].puan) {
          a = top.length;
          while (a > 0 && puan > top[a - 1].puan) a--;
          top.splice(a, 0, { kod: gr.kodlar[j], puan: puan, acik: ust - (puan + ceza), ceza: ceza });
          if (top.length > 3) top.pop();
        }
      }
    }
    if (top.length === 0) return { ham: ham, adaylar: [], guven: 0.0, durum: "sor" };
    var guven = top.length > 1 ? top[0].puan - top[1].puan : 99.0;
    var acik = top[0].acik;
    // iki koşul birden: ikinci adaydan yeterince ayrılmış VE CNN'in kendi okumasına yeterince yakın (listede olmayan kod komşuya oturmasın)
    // Üçüncü koşul (2026-10-25, T+4 deseni sonrası): kutu sayısı kod uzunluğuna tam eşit değilse (cezalı eşleşme) otomatik kabul yok
    var durum = (guven >= ESIK && acik <= ESIK_MUTLAK && !(top[0].ceza > 0)) ? "kabul" : "sor";
    return { ham: ham, adaylar: top, guven: guven, acik: acik, durum: durum };
  }

  // Adet: yalnız rakamlar, boşsa 1
  function adetCoz(P, ay) {
    if (P.length === 0) return { deger: 1, ham: "", guven: 0.0, durum: "bos" };
    var s = "", toplam = 0, i, c;
    for (i = 0; i < P.length; i++) {
      var en = 0, tp = 0;
      for (c = 0; c < 10; c++) tp += P[i][c];
      for (c = 1; c < 10; c++) if (P[i][c] > P[i][en]) en = c;
      s += en;
      toplam += P[i][en] / Math.max(tp, EPS);
    }
    var guven = toplam / P.length;
    var deger = parseInt(s, 10);
    var durum = (guven >= ay.adet_esik && s.length <= 3) ? "kabul" : "sor";
    return { deger: deger, ham: s, guven: guven, durum: durum };
  }

  // ------------------------------------------------------------- ana akış
  function olcekliAyar(ay, w, h) {
    var o = {}, k;
    for (k in ay) if (ay.hasOwnProperty(k)) o[k] = ay[k];
    var s = ay.olcekle ? Math.max(w, h) / ay.referans_kenar : 1;
    o.olcek = s;
    function px(v, en) { return ay.olcekle ? Math.max(en, yuvarla(v * s)) : v; }
    o.esik_yaricap = px(ay.esik_yaricap, 3);
    o.hucre_ic_pay = px(ay.hucre_ic_pay, 1);
    o.kenar_pay = ay.olcekle ? 15 * s : 15;
    o.cizgi_kalinlik = ay.olcekle ? Math.max(4, 15 * s) : 15;
    o.bol_min_genislik = ay.olcekle ? Math.max(6, 24 * s) : 24;
    return o;
  }

  function hucreMaske(mur, w, x0, y0, x1, y1) {
    var cw = x1 - x0, ch = y1 - y0, m = new Uint8Array(Math.max(0, cw * ch)), y;
    if (cw <= 0 || ch <= 0) return { m: m, w: 0, h: 0, say: 0 };
    for (y = 0; y < ch; y++) {
      var kaynak = (y0 + y) * w + x0, hedef = y * cw, x;
      for (x = 0; x < cw; x++) m[hedef + x] = mur[kaynak + x];
    }
    cizgiTemizle(m, cw, ch);
    var say = 0, i;
    for (i = 0; i < m.length; i++) say += m[i];
    return { m: m, w: cw, h: ch, say: say };
  }

  function hucreOku(hm, x0, y0, hedefler, model, ay) {
    var kut = karakterKutulari(hm.m, hm.w, hm.h, hedefler, ay);
    var P = [], tire = [], kutular = [], i;
    for (i = 0; i < kut.length; i++) {
      var k = kut[i];
      var p = ileri(model, mnistNormalle(hm.m, hm.w, k));
      P.push(p); tire.push(k[4]);
      var en = 0, c;
      for (c = 1; c < 12; c++) if (p[c] > p[en]) en = c;
      kutular.push({ x: x0 + k[0], y: y0 + k[1], w: k[2] - k[0], h: k[3] - k[1], tire: k[4], sinif: SINIFLAR.charAt(en), p: p[en] });
    }
    return { P: P, tire: tire, kutular: kutular, hucre: { x: x0, y: y0, w: hm.w, h: hm.h } };
  }

  /**
   * goruntu: {width, height, data(RGBA)}, kodListesi: dizgi dizisi (ya da kodIndeksi sonucu),
   * ayar: AYAR üzerine yazılacak alanlar (isteğe bağlı; ayar.model ile model verilebilir).
   */
  var sonIndeks = { liste: null, sayi: -1, indeks: null };
  function oku(goruntu, kodListesi, ayar) {
    var t0 = simdi(), uyari = [];
    var sonuc = { satirlar: [], sure_ms: 0, uyari: uyari };
    var model = (ayar && ayar.model) || kok.ELYAZISI_MODEL;
    if (!model) { uyari.push("model yüklenmedi (js/model.js)"); return sonuc; }
    if (!goruntu || !goruntu.data || !goruntu.width || !goruntu.height) { uyari.push("görüntü geçersiz"); return sonuc; }
    var indeks;
    if (kodListesi && kodListesi.gruplar) indeks = kodListesi;
    else {
      var lst = kodListesi || [];
      if (sonIndeks.liste !== lst || sonIndeks.sayi !== lst.length) {
        sonIndeks = { liste: lst, sayi: lst.length, indeks: kodIndeksi(lst) };
      }
      indeks = sonIndeks.indeks;
    }
    if (!indeks.sayi) uyari.push("geçerli kod listesi boş; yalnız ham okuma yapılır");
    var w = goruntu.width, h = goruntu.height;
    var ay = olcekliAyar(ayarBirlestir(ayar), w, h);
    var g = griyeCevir(goruntu);
    var mk = maskeleriUret(g, w, h, ay.esik_yaricap, ay.esik_fark, ay.murekkep_mutlak, ay.murekkep_fark);
    g = null;
    var tablo;
    try { tablo = tabloBul(mk.koyu, w, h, ay); }
    catch (e) { uyari.push(String(e && e.message || e)); sonuc.sure_ms = Math.round(simdi() - t0); return sonuc; }
    mk.koyu = null;
    var satirlar = tablo.satirlar, sutunlar = tablo.sutunlar;
    var ensutun = Math.max(ay.stok_sutun, ay.adet_sutun) + 1;
    if (sutunlar.length <= ensutun) {
      uyari.push("tablo sütunları bulunamadı (" + sutunlar.length + " çizgi)");
      sonuc.sure_ms = Math.round(simdi() - t0); return sonuc;
    }
    var pay = ay.hucre_ic_pay, r, sira = 0;
    for (r = 0; r < satirlar.length - 1; r++) {
      var ya = Math.floor(satirlar[r]) + pay, yb = Math.floor(satirlar[r + 1]) - pay;
      var sx0 = Math.floor(sutunlar[ay.stok_sutun]) + pay, sx1 = Math.floor(sutunlar[ay.stok_sutun + 1]) - pay;
      var ax0 = Math.floor(sutunlar[ay.adet_sutun]) + pay, ax1 = Math.floor(sutunlar[ay.adet_sutun + 1]) - pay;
      var stokM = hucreMaske(mk.mur, w, sx0, ya, sx1, yb);
      if (stokM.say <= 50) continue;   // boş satır
      sira++;
      var st = hucreOku(stokM, sx0, ya, [6, 9], model, ay);
      var adM = hucreMaske(mk.mur, w, ax0, ya, ax1, yb);
      var ad = hucreOku(adM, ax0, ya, null, model, ay);
      var cz = stokCoz(st.P, indeks, st.tire);
      var stokDurum = st.P.length === 0 ? "bos" : cz.durum;
      var ac = adetCoz(ad.P, ay);
      sonuc.satirlar.push({
        sira: sira,
        tabloSatiri: r,
        stok: {
          aday: cz.adaylar,
          secilen: cz.adaylar.length ? cz.adaylar[0].kod : "",
          ham: cz.ham,
          guven: cz.guven,
          acik: cz.acik || 0,
          durum: stokDurum
        },
        adet: { deger: ac.deger, ham: ac.ham, guven: ac.guven, durum: ac.durum },
        hucreKutusu: st.hucre,
        adetKutusu: ad.hucre,
        karakterKutulari: st.kutular,
        adetKarakterKutulari: ad.kutular
      });
    }
    sonuc.sure_ms = Math.round(simdi() - t0);
    return sonuc;
  }

  // ----------------------------------------------------------- EXIF yönü
  // JPEG baytlarından (ArrayBuffer ya da Uint8Array) EXIF Orientation (1..8). Bulunamazsa 1.
  function exifYonu(tampon) {
    try {
      var b = (tampon instanceof Uint8Array) ? tampon : new Uint8Array(tampon);
      if (b.length < 4 || b[0] !== 0xFF || b[1] !== 0xD8) return 1;
      var ofs = 2;
      while (ofs + 4 < b.length) {
        if (b[ofs] !== 0xFF) return 1;
        var isaret = b[ofs + 1], uz = (b[ofs + 2] << 8) | b[ofs + 3];
        if (isaret === 0xE1 && b[ofs + 4] === 0x45 && b[ofs + 5] === 0x78 && b[ofs + 6] === 0x69 && b[ofs + 7] === 0x66) {
          var t = ofs + 10;   // TIFF başlığı
          var kucukU = (b[t] === 0x49);
          var o16 = function (p) { return kucukU ? (b[p] | (b[p + 1] << 8)) : ((b[p] << 8) | b[p + 1]); };
          var o32 = function (p) { return kucukU ? (b[p] | (b[p + 1] << 8) | (b[p + 2] << 16) | (b[p + 3] << 24)) : ((b[p] << 24) | (b[p + 1] << 16) | (b[p + 2] << 8) | b[p + 3]); };
          var ifd = t + o32(t + 4), sayi = o16(ifd), i;
          for (i = 0; i < sayi; i++) {
            var e = ifd + 2 + i * 12;
            if (o16(e) === 0x0112) { var y = o16(e + 8); return (y >= 1 && y <= 8) ? y : 1; }
          }
          return 1;
        }
        if (isaret === 0xDA) return 1;
        ofs += 2 + uz;
      }
    } catch (e) { /* bozuk EXIF: yön 1 */ }
    return 1;
  }

  // Tarayıcı EXIF yönünü <img> çiziminde kendisi uyguluyor mu? (bir kez sınanır, geri çağrı ile)
  // 2x1 piksellik, Orientation=6 etiketli JPEG: uygulanıyorsa genişlik 1, yükseklik 2 görünür.
  var EXIF_SINAMA = "/9j/4AAQSkZJRgABAQAAAQABAAD/4QAiRXhpZgAATU0AKgAAAAgAAQESAAMAAAABAAYAAAAAAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDi6KKK+ZP3E//Z";
  var exifOtomatik = null;
  function exifOtomatikMi(geriCagri) {
    if (exifOtomatik !== null) { geriCagri(exifOtomatik); return; }
    try {
      var im = new Image();
      im.onload = function () { exifOtomatik = (im.width === 1 && im.height === 2); geriCagri(exifOtomatik); };
      im.onerror = function () { exifOtomatik = false; geriCagri(false); };
      im.src = "data:image/jpeg;base64," + EXIF_SINAMA;
    } catch (e) { exifOtomatik = false; geriCagri(false); }
  }

  /**
   * Tarayıcı yardımcısı: HTMLImageElement -> ölçeklenmiş canvas -> ImageData.
   * enBuyukKenar: uzun kenar üst sınırı (varsayılan 2000; büyütme yapılmaz).
   * yon: elle okunan EXIF yönü (1..8); yalnız tarayıcı EXIF'i kendisi uygulamıyorsa kullanılır.
   * Dönüş: {width, height, data, canvas}
   */
  function goruntudenCanvas(img, enBuyukKenar, yon) {
    var sw = img.naturalWidth || img.width, sh = img.naturalHeight || img.height;
    yon = (yon >= 1 && yon <= 8) ? yon : 1;
    var cevir = yon >= 5;
    var dw = cevir ? sh : sw, dh = cevir ? sw : sh;
    var kenar = enBuyukKenar || 2000;
    var olcek = Math.min(1, kenar / Math.max(dw, dh));
    var cw = Math.max(1, Math.round(dw * olcek)), ch = Math.max(1, Math.round(dh * olcek));
    var canvas = document.createElement("canvas");
    canvas.width = cw; canvas.height = ch;
    var ctx = canvas.getContext("2d");
    // yön 1..8 için dönüşüm matrisleri (a b c d e f)
    var M = [null, [1, 0, 0, 1, 0, 0], [-1, 0, 0, 1, 1, 0], [-1, 0, 0, -1, 1, 1], [1, 0, 0, -1, 0, 1],
             [0, 1, 1, 0, 0, 0], [0, 1, -1, 0, 1, 0], [0, -1, -1, 0, 1, 1], [0, -1, 1, 0, 0, 1]][yon];
    ctx.save();
    ctx.scale(cw, ch);
    ctx.transform(M[0], M[1], M[2], M[3], M[4], M[5]);
    // birim kareye çiz; scale ile hedef boyuta
    ctx.drawImage(img, 0, 0, sw, sh, 0, 0, 1, 1);
    ctx.restore();
    var id = ctx.getImageData(0, 0, cw, ch);
    return { width: cw, height: ch, data: id.data, canvas: canvas };
  }

  /**
   * Dosyadan (File/Blob) görüntü: EXIF yönünü okur, gerekirse uygular, geriCagri(hata, goruntu) çağırır.
   * Promise kullanmaz (eski tarayıcı).
   */
  function dosyadanGoruntu(dosya, enBuyukKenar, geriCagri) {
    var okuyucu = new FileReader();
    okuyucu.onerror = function () { geriCagri(new Error("dosya okunamadı")); };
    okuyucu.onload = function () {
      var yon = exifYonu(okuyucu.result);
      exifOtomatikMi(function (oto) {
        var URLsi = window.URL || window.webkitURL;
        var adres = URLsi.createObjectURL(dosya);
        var im = new Image();
        im.onload = function () {
          try {
            var gor = goruntudenCanvas(im, enBuyukKenar, oto ? 1 : yon);
            URLsi.revokeObjectURL(adres);
            geriCagri(null, gor);
          } catch (e) { URLsi.revokeObjectURL(adres); geriCagri(e); }
        };
        im.onerror = function () { URLsi.revokeObjectURL(adres); geriCagri(new Error("görüntü açılamadı")); };
        im.src = adres;
      });
    };
    okuyucu.readAsArrayBuffer(dosya);
  }

  var ElYazisiOCR = {
    surum: "1.0",
    AYAR: AYAR,
    SINIFLAR: SINIFLAR,
    oku: oku,
    kodIndeksi: kodIndeksi,
    goruntudenCanvas: goruntudenCanvas,
    dosyadanGoruntu: dosyadanGoruntu,
    exifYonu: exifYonu,
    // iç adımlar (test ve hata ayıklama için, Python ile aynı adlar)
    _ic: {
      griyeCevir: griyeCevir, maskeleriUret: maskeleriUret, tabloBul: tabloBul, cizgiTemizle: cizgiTemizle,
      bilesenler: bilesenler, karakterKutulari: karakterKutulari, genisBol: genisBol,
      mnistNormalle: mnistNormalle, ileri: ileri, stokCoz: stokCoz, adetCoz: adetCoz,
      olcekliAyar: olcekliAyar, hucreMaske: hucreMaske
    }
  };

  kok.ElYazisiOCR = ElYazisiOCR;
  if (typeof module !== "undefined" && module.exports) module.exports = ElYazisiOCR;
})(typeof window !== "undefined" ? window : (typeof global !== "undefined" ? global : this));
