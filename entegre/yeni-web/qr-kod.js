/* Kaynak: barkod-sifreleme/src/qr.js (aynen kopya, QR Code model 2 kodlayıcı; tarayıcıda window.QrKod). */
/* QR Code (model 2) kodlayıcı: bayt modu, hata düzeltme L/M/Q/H, sürüm 1-10 otomatik, maske seçimi.
 * Dış kütüphane yok. moduller2d(metin, secenek) -> 0/1 dizi dizisi (sessiz bölge hariç).
 * secenek: hataDuzeltme ('L'|'M'|'Q'|'H', varsayılan 'M'), enAzSurum (1-10), maske (0-7, yoksa otomatik). */
(function (kok, fabrika) {
  if (typeof module === 'object' && module.exports) module.exports = fabrika();
  else kok.QrKod = fabrika();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var EN_BUYUK_SURUM = 10;
  var EC_INDEKS = { L: 0, M: 1, Q: 2, H: 3 };
  var EC_FORMAT = { L: 1, M: 0, Q: 3, H: 2 };
  // [seviye][sürüm]: blok başına hata düzeltme kod sözcüğü ve blok sayısı (sürüm 1..10; 0. eleman yer tutucu)
  var ECC_BLOK = [
    [0, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18],
    [0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26],
    [0, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24],
    [0, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28]
  ];
  var BLOK_SAYISI = [
    [0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4],
    [0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5],
    [0, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8],
    [0, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8]
  ];

  function ham(surum) {
    var r = (16 * surum + 128) * surum + 64;
    if (surum >= 2) {
      var n = Math.floor(surum / 7) + 2;
      r -= (25 * n - 10) * n - 55;
      if (surum >= 7) r -= 36;
    }
    return r;
  }
  function veriSozcuk(surum, ec) {
    return Math.floor(ham(surum) / 8) - ECC_BLOK[ec][surum] * BLOK_SAYISI[ec][surum];
  }

  function utf8(s) {
    var cikti = [];
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 0xD800 && c <= 0xDBFF && i + 1 < s.length) {
        var d = s.charCodeAt(i + 1);
        if (d >= 0xDC00 && d <= 0xDFFF) { c = 0x10000 + ((c - 0xD800) << 10) + (d - 0xDC00); i++; }
      }
      if (c < 0x80) cikti.push(c);
      else if (c < 0x800) cikti.push(0xC0 | (c >> 6), 0x80 | (c & 63));
      else if (c < 0x10000) cikti.push(0xE0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
      else cikti.push(0xF0 | (c >> 18), 0x80 | ((c >> 12) & 63), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    }
    return cikti;
  }

  /* ---------- Reed-Solomon, GF(256) 0x11D ---------- */
  var EXP = [], LOG = [];
  (function () {
    var x = 1;
    for (var i = 0; i < 255; i++) { EXP[i] = x; LOG[x] = i; x <<= 1; if (x & 256) x ^= 0x11D; }
    for (var j = 255; j < 512; j++) EXP[j] = EXP[j - 255];
  })();
  function carp(a, b) { return a && b ? EXP[LOG[a] + LOG[b]] : 0; }
  function rsBolen(n) {
    var g = [1];
    for (var i = 0; i < n; i++) {
      var y = new Array(g.length + 1).fill(0);
      for (var j = 0; j < g.length; j++) { y[j] ^= g[j]; y[j + 1] ^= carp(g[j], EXP[i]); }
      g = y;
    }
    return g.slice(1); // başdaki 1 atılır
  }
  function rsKalan(veri, g) {
    var r = new Array(g.length).fill(0);
    veri.forEach(function (b) {
      var f = b ^ r.shift();
      r.push(0);
      g.forEach(function (c, i) { r[i] ^= carp(c, f); });
    });
    return r;
  }

  /* ---------- Veri sözcükleri ---------- */
  function veriBitleri(baytlar, surum, ec) {
    var bits = [];
    function ekle(v, n) { for (var i = n - 1; i >= 0; i--) bits.push((v >>> i) & 1); }
    ekle(4, 4);
    ekle(baytlar.length, surum <= 9 ? 8 : 16);
    baytlar.forEach(function (b) { ekle(b, 8); });
    var kap = veriSozcuk(surum, ec) * 8;
    for (var t = 0; t < 4 && bits.length < kap; t++) bits.push(0);
    while (bits.length % 8) bits.push(0);
    var cw = [];
    for (var i = 0; i < bits.length; i += 8) {
      var v = 0;
      for (var j = 0; j < 8; j++) v = (v << 1) | bits[i + j];
      cw.push(v);
    }
    for (var p = 0xEC; cw.length < kap / 8; p ^= 0xEC ^ 0x11) cw.push(p);
    return cw;
  }

  function araya(veri, surum, ec) {
    var nb = BLOK_SAYISI[ec][surum], el = ECC_BLOK[ec][surum];
    var rawCw = Math.floor(ham(surum) / 8);
    var kisa = nb - rawCw % nb, kisaUz = Math.floor(rawCw / nb);
    var g = rsBolen(el), bloklar = [], k = 0;
    for (var i = 0; i < nb; i++) {
      var uz = kisaUz - el + (i < kisa ? 0 : 1);
      var d = veri.slice(k, k + uz); k += uz;
      var e = rsKalan(d, g);
      if (i < kisa) d.push(0);
      bloklar.push({ d: d, e: e, uz: uz });
    }
    var cikti = [];
    for (var c = 0; c < kisaUz - el + 1; c++) {
      for (var b = 0; b < nb; b++) if (c !== kisaUz - el || b >= kisa) cikti.push(bloklar[b].d[c]);
    }
    for (var c2 = 0; c2 < el; c2++) for (var b2 = 0; b2 < nb; b2++) cikti.push(bloklar[b2].e[c2]);
    return cikti;
  }

  /* ---------- Matris ---------- */
  function hizaKonumlari(surum) {
    if (surum === 1) return [];
    var n = Math.floor(surum / 7) + 2, boyut = surum * 4 + 17;
    var adim = Math.ceil((surum * 4 + 4) / (n * 2 - 2)) * 2;
    var r = [6];
    for (var p = boyut - 7; r.length < n; p -= adim) r.splice(1, 0, p);
    return r;
  }

  function bosMatris(surum) {
    var n = surum * 4 + 17, m = [], f = [];
    for (var i = 0; i < n; i++) { m.push(new Array(n).fill(0)); f.push(new Array(n).fill(false)); }
    function koy(x, y, v) { m[y][x] = v ? 1 : 0; f[y][x] = true; }
    var i2, x, y;
    for (i2 = 0; i2 < n; i2++) { koy(6, i2, i2 % 2 === 0); koy(i2, 6, i2 % 2 === 0); }
    function bulucu(cx, cy) {
      for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) {
        var xx = cx + dx, yy = cy + dy;
        if (xx < 0 || yy < 0 || xx >= n || yy >= n) continue;
        var d = Math.max(Math.abs(dx), Math.abs(dy));
        koy(xx, yy, d !== 2 && d !== 4);
      }
    }
    bulucu(3, 3); bulucu(n - 4, 3); bulucu(3, n - 4);
    var h = hizaKonumlari(surum);
    for (var a = 0; a < h.length; a++) for (var b = 0; b < h.length; b++) {
      if ((a === 0 && b === 0) || (a === 0 && b === h.length - 1) || (a === h.length - 1 && b === 0)) continue;
      for (var dy = -2; dy <= 2; dy++) for (var dx = -2; dx <= 2; dx++) {
        koy(h[a] + dx, h[b] + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
      }
    }
    // Biçim alanlarını ayır (değer sonra yazılır), sürüm alanı çiz
    for (i2 = 0; i2 < 9; i2++) { f[8][i2] = true; f[i2][8] = true; }
    for (i2 = 0; i2 < 8; i2++) { f[8][n - 1 - i2] = true; f[n - 1 - i2][8] = true; }
    koy(8, n - 8, true);
    if (surum >= 7) {
      var rem = surum;
      for (i2 = 0; i2 < 12; i2++) rem = (rem << 1) ^ ((rem >>> 11) * 0x1F25);
      var bitler = (surum << 12) | rem;
      for (i2 = 0; i2 < 18; i2++) {
        var bit = (bitler >>> i2) & 1, p = n - 11 + i2 % 3, q = Math.floor(i2 / 3);
        koy(p, q, bit); koy(q, p, bit);
      }
    }
    return { m: m, f: f, n: n };
  }

  function yerlestir(t, cw) {
    var n = t.n, i = 0, tam = cw.length * 8;
    for (var sag = n - 1; sag >= 1; sag -= 2) {
      if (sag === 6) sag = 5;
      for (var dikey = 0; dikey < n; dikey++) {
        for (var j = 0; j < 2; j++) {
          var x = sag - j, yukari = ((sag + 1) & 2) === 0, y = yukari ? n - 1 - dikey : dikey;
          if (!t.f[y][x] && i < tam) {
            t.m[y][x] = (cw[i >>> 3] >>> (7 - (i & 7))) & 1;
            i++;
          }
        }
      }
    }
  }

  var MASKE = [
    function (x, y) { return (x + y) % 2 === 0; },
    function (x, y) { return y % 2 === 0; },
    function (x, y) { return x % 3 === 0; },
    function (x, y) { return (x + y) % 3 === 0; },
    function (x, y) { return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; },
    function (x, y) { return x * y % 2 + x * y % 3 === 0; },
    function (x, y) { return (x * y % 2 + x * y % 3) % 2 === 0; },
    function (x, y) { return ((x + y) % 2 + x * y % 3) % 2 === 0; }
  ];

  function bicimYaz(m, n, ec, maske) {
    var veri = (EC_FORMAT[ec] << 3) | maske, rem = veri;
    for (var i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
    var bits = ((veri << 10) | rem) ^ 0x5412;
    function b(k) { return (bits >>> k) & 1; }
    var k;
    for (k = 0; k <= 5; k++) m[k][8] = b(k);
    m[7][8] = b(6); m[8][8] = b(7); m[8][7] = b(8);
    for (k = 9; k < 15; k++) m[8][14 - k] = b(k);
    for (k = 0; k < 8; k++) m[8][n - 1 - k] = b(k);
    for (k = 8; k < 15; k++) m[n - 15 + k][8] = b(k);
    m[n - 8][8] = 1;
  }

  function ceza(m, n) {
    var puan = 0, i, j, k;
    for (var yon = 0; yon < 2; yon++) {
      for (i = 0; i < n; i++) {
        var seri = 1, gec = [];
        for (j = 0; j < n; j++) {
          var v = yon ? m[j][i] : m[i][j];
          gec.push(v);
          if (j > 0) {
            var onceki = yon ? m[j - 1][i] : m[i][j - 1];
            if (v === onceki) { seri++; if (seri === 5) puan += 3; else if (seri > 5) puan++; } else seri = 1;
          }
        }
        var s = gec.join('');
        for (k = 0; k + 11 <= n; k++) {
          var w = s.substr(k, 11);
          if (w === '10111010000' || w === '00001011101') puan += 40;
        }
      }
    }
    var kapali = 0;
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
      kapali += m[i][j];
      if (i + 1 < n && j + 1 < n && m[i][j] === m[i][j + 1] && m[i][j] === m[i + 1][j] && m[i][j] === m[i + 1][j + 1]) puan += 3;
    }
    var toplam = n * n;
    puan += (Math.ceil(Math.abs(kapali * 20 - toplam * 10) / toplam) - 1) * 10;
    return puan;
  }

  function kodla(metin, secenek) {
    secenek = secenek || {};
    var ecAd = String(secenek.hataDuzeltme || 'M').toUpperCase();
    if (!(ecAd in EC_INDEKS)) throw new Error('QR: hata düzeltme L, M, Q veya H olmalı.');
    var ec = EC_INDEKS[ecAd];
    if (metin == null) metin = '';
    var baytlar = utf8(String(metin));
    var enAz = secenek.enAzSurum == null ? 1 : Number(secenek.enAzSurum);
    if (!(enAz >= 1 && enAz <= EN_BUYUK_SURUM)) throw new Error('QR: sürüm 1-' + EN_BUYUK_SURUM + ' aralığında olmalı.');
    var surum = Math.floor(enAz);
    for (; ; surum++) {
      if (surum > EN_BUYUK_SURUM) throw new Error('QR: metin çok uzun (' + baytlar.length + ' bayt); en çok sürüm ' + EN_BUYUK_SURUM + ' desteklenir.');
      var bitUz = 4 + (surum <= 9 ? 8 : 16) + 8 * baytlar.length;
      if (bitUz <= veriSozcuk(surum, ec) * 8) break;
    }
    var cw = araya(veriBitleri(baytlar, surum, ec), surum, ec);
    var t = bosMatris(surum), n = t.n;
    yerlestir(t, cw);
    var sabit = secenek.maske == null ? -1 : Number(secenek.maske);
    if (sabit !== -1 && !(sabit >= 0 && sabit <= 7 && sabit === Math.floor(sabit))) throw new Error('QR: maske 0-7 olmalı.');
    var enIyi = null, enIyiPuan = Infinity, enIyiMaske = 0;
    for (var mk = 0; mk < 8; mk++) {
      if (sabit !== -1 && mk !== sabit) continue;
      var m = t.m.map(function (s) { return s.slice(); });
      for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) if (!t.f[y][x] && MASKE[mk](x, y)) m[y][x] ^= 1;
      bicimYaz(m, n, ecAd, mk);
      var p = ceza(m, n);
      if (p < enIyiPuan) { enIyiPuan = p; enIyi = m; enIyiMaske = mk; }
    }
    return { matris: enIyi, surum: surum, boyut: n, hataDuzeltme: ecAd, maske: enIyiMaske, bayt: baytlar.length, sozcukler: cw };
  }

  function moduller2d(metin, secenek) { return kodla(metin, secenek).matris; }

  function kac(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // secenek: modulGenislik (varsayılan 4), sessizBolge (varsayılan 4 modül) + moduller2d seçenekleri
  function svg(metin, secenek) {
    secenek = secenek || {};
    var mg = secenek.modulGenislik == null ? 4 : Number(secenek.modulGenislik);
    var sessiz = secenek.sessizBolge == null ? 4 : Number(secenek.sessizBolge);
    if (!(mg > 0) || !(sessiz >= 0)) throw new Error('SVG ölçüleri pozitif sayı olmalı.');
    var m = moduller2d(metin, secenek), n = m.length, boy = (n + 2 * sessiz) * mg, d = [];
    for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) {
      if (m[y][x]) d.push('M' + (x + sessiz) * mg + ' ' + (y + sessiz) * mg + 'h' + mg + 'v' + mg + 'h-' + mg + 'z');
    }
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + boy + '" height="' + boy + '" viewBox="0 0 ' + boy + ' ' + boy +
      '" shape-rendering="crispEdges"><rect x="0" y="0" width="' + boy + '" height="' + boy + '" fill="#ffffff"/>' +
      '<path fill="#000000" d="' + d.join('') + '"/></svg>';
  }

  return { kodla: kodla, moduller2d: moduller2d, svg: svg, enBuyukSurum: EN_BUYUK_SURUM, kac: kac };
});
