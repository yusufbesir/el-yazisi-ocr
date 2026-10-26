/* Kaynak: barkod-sifreleme/src/barkod.js (aynen kopya, Code 128 dahil; tarayıcıda window.BarkodCiz). */
/* Barkod standartları: Code 128, Code 39, Code 93 kodlayıcıları, SVG çıktısı ve uzunluk önerisi.
 * Dış kütüphane yok. Kodlayıcılar {karakterSayisi, sembolSayisi, modulSayisi, moduller} döndürür;
 * moduller: çubuk/boşluk genişlikleri (modül cinsinden), her zaman çubukla başlar. */
(function (kok, fabrika) {
  if (typeof module === 'object' && module.exports) module.exports = fabrika();
  else kok.BarkodCiz = fabrika();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* ---------- Code 128 ---------- */
  // 0..105 veri/başlangıç desenleri (çubuk,boşluk,... genişlikleri), 106 = STOP (7 eleman)
  var C128 = ('212222 222122 222221 121223 121322 131222 122213 122312 132212 221213 ' +
    '221312 231212 112232 122132 122231 113222 123122 123221 223211 221132 ' +
    '221231 213212 223112 312131 311222 321122 321221 312212 322112 322211 ' +
    '212123 212321 232121 111323 131123 131321 112313 132113 132311 211313 ' +
    '231113 231311 112133 112331 132131 113123 113321 133121 313121 211331 ' +
    '231131 213113 213311 213131 311123 311321 331121 312113 312311 332111 ' +
    '314111 221411 431111 111224 111422 121124 121421 141122 141221 112214 ' +
    '112412 122114 122411 142112 142211 241211 221114 413111 241112 134111 ' +
    '111242 121142 121241 114212 124112 124211 411212 421112 421211 212141 ' +
    '214121 412121 111143 111341 131141 114113 114311 411113 411311 113141 ' +
    '114131 311141 411131 211412 211214 211232 2331112').split(' ');
  var START_A = 103, START_B = 104, START_C = 105, STOP = 106;
  var KOD_C = 99, KOD_B = 100, KOD_A = 101;

  function haneler(s) { return s.split('').map(Number); }

  function rakamKosusu(metin, i) {
    var k = 0;
    while (i + k < metin.length && metin.charCodeAt(i + k) >= 48 && metin.charCodeAt(i + k) <= 57) k++;
    return k;
  }

  // Bir karakterin A/B alt kümesindeki değeri; yoksa -1
  function degerAB(kod, alt) {
    if (alt === 'A') {
      if (kod >= 0 && kod <= 31) return kod + 64;
      if (kod >= 32 && kod <= 95) return kod - 32;
      return -1;
    }
    return kod >= 32 && kod <= 127 ? kod - 32 : -1;
  }

  function code128Degerler(metin) {
    metin = String(metin);
    var n = metin.length;
    if (!n) throw new Error('Code 128: boş metin kodlanamaz.');
    for (var j = 0; j < n; j++) {
      if (metin.charCodeAt(j) > 127) {
        throw new Error('Code 128: "' + metin.charAt(j) + '" karakteri desteklenmiyor (yalnızca ASCII 0-127).');
      }
    }
    var SONSUZ = 1e9, bellek = {};
    // enc: m alt kümesindeyken i. karakteri (C'de ikiliyi) yazmanın toplam maliyeti
    function enc(i, m) {
      if (i >= n) return 0;
      var a = 'enc' + i + m;
      if (a in bellek) return bellek[a];
      var s = SONSUZ;
      if (m === 'C') {
        if (i + 1 < n && rakamKosusu(metin, i) >= 2) s = 1 + maliyet(i + 2, 'C');
      } else if (degerAB(metin.charCodeAt(i), m) >= 0) {
        s = 1 + maliyet(i + 1, m);
      }
      bellek[a] = s;
      return s;
    }
    function maliyet(i, m) {
      if (i >= n) return 0;
      var a = 'mal' + i + m;
      if (a in bellek) return bellek[a];
      var en = enc(i, m);
      ['C', 'B', 'A'].forEach(function (m2) {
        if (m2 !== m) en = Math.min(en, 1 + enc(i, m2));
      });
      bellek[a] = en;
      return en;
    }
    function sirala(i, m, baslangic) {
      var L = rakamKosusu(metin, i);
      var sira = ['stay', 'C', 'B', 'A'];
      if (baslangic) {
        sira = ['C', 'B', 'A'];
        if (L >= 4 && L % 2 === 1) sira = ['B', 'C', 'A'];          // tek sayıda rakam: ilk rakam B'de
        else if (!(L >= 4 || (L >= 2 && L === n))) sira = ['B', 'A', 'C'];
      } else if (m !== 'C' && L >= 4 && L % 2 === 0) {
        sira = ['C', 'stay', 'B', 'A'];                              // çift boyda 4+ rakam koşusu: C'ye geç
      }
      return sira;
    }
    function maliyetAday(i, m, aday, baslangic) {
      if (baslangic) return enc(i, aday);
      if (aday === 'stay') return enc(i, m);
      return aday === m ? SONSUZ : 1 + enc(i, aday);
    }
    var degerler = [], m = null, i = 0, ilk = true;
    while (i < n) {
      var en = SONSUZ, secim = null, sira = sirala(i, m, ilk), k;
      if (ilk) {
        for (k = 0; k < 3; k++) en = Math.min(en, maliyetAday(i, null, sira[k], true));
      } else {
        en = maliyet(i, m);
      }
      for (k = 0; k < sira.length; k++) {
        if (maliyetAday(i, m, sira[k], ilk) === en) { secim = sira[k]; break; }
      }
      if (ilk) {
        degerler.push(secim === 'C' ? START_C : secim === 'B' ? START_B : START_A);
        m = secim;
        ilk = false;
      } else if (secim !== 'stay' && secim !== m) {
        degerler.push(secim === 'C' ? KOD_C : secim === 'B' ? KOD_B : KOD_A);
        m = secim;
      }
      if (m === 'C') {
        degerler.push(Number(metin.substr(i, 2)));
        i += 2;
      } else {
        degerler.push(degerAB(metin.charCodeAt(i), m));
        i += 1;
      }
    }
    var toplam = degerler[0];
    for (var p = 1; p < degerler.length; p++) toplam += degerler[p] * p;
    degerler.push(toplam % 103);
    return degerler;
  }

  function code128(metin) {
    var d = code128Degerler(metin);
    var tum = d.concat([STOP]);
    var moduller = [];
    tum.forEach(function (v) { moduller = moduller.concat(haneler(C128[v])); });
    var modul = moduller.reduce(function (a, b) { return a + b; }, 0);
    return {
      karakterSayisi: String(metin).length, sembolSayisi: tum.length, modulSayisi: modul,
      moduller: moduller, degerler: d, sagLama: d[d.length - 1]
    };
  }

  /* ---------- Code 39 ---------- */
  var C39_SIRA = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%';
  // n=dar, w=geniş; 9 eleman: çubuk,boşluk,çubuk,...
  var C39_DESEN = ('nnnwwnwnn wnnwnnnnw nnwwnnnnw wnwwnnnnn nnnwwnnnw wnnwwnnnn nnwwwnnnn nnnwnnwnw wnnwnnwnn nnwwnnwnn ' +
    'wnnnnwnnw nnwnnwnnw wnwnnwnnn nnnnwwnnw wnnnwwnnn nnwnwwnnn nnnnnwwnw wnnnnwwnn nnwnnwwnn nnnnwwwnn ' +
    'wnnnnnnww nnwnnnnww wnwnnnnwn nnnnwnnww wnnnwnnwn nnwnwnnwn nnnnnnwww wnnnnnwwn nnwnnnwwn nnnnwnwwn ' +
    'wwnnnnnnw nwwnnnnnw wwwnnnnnn nwnnwnnnw wwnnwnnnn nwwnwnnnn nwnnnnwnw wwnnnnwnn nwwnnnwnn ' +
    'nwnwnwnnn nwnwnnnwn nwnnnwnwn nnnwnwnwn').split(' ');
  var C39_YILDIZ = 'nwnnwnwnn';

  function c39Elemanlar(d) {
    return d.split('').map(function (c) { return c === 'w' ? 3 : 1; });
  }

  function code39(metin, secenek) {
    metin = String(metin);
    var mod43 = !!(secenek && secenek.mod43);
    if (!metin.length) throw new Error('Code 39: boş metin kodlanamaz.');
    var toplam = 0, j;
    for (j = 0; j < metin.length; j++) {
      var v = C39_SIRA.indexOf(metin.charAt(j));
      if (v < 0) {
        throw new Error('Code 39: "' + metin.charAt(j) + '" karakteri desteklenmiyor (yalnızca A-Z 0-9 - . $ / + % ve boşluk; küçük harf yok).');
      }
      toplam += v;
    }
    var govde = metin;
    if (mod43) govde += C39_SIRA.charAt(toplam % 43);
    var desenler = [C39_YILDIZ];
    for (j = 0; j < govde.length; j++) desenler.push(C39_DESEN[C39_SIRA.indexOf(govde.charAt(j))]);
    desenler.push(C39_YILDIZ);
    var moduller = [];
    desenler.forEach(function (d, ix) {
      if (ix > 0) moduller.push(1); // karakterler arası dar boşluk
      moduller = moduller.concat(c39Elemanlar(d));
    });
    return {
      karakterSayisi: metin.length, sembolSayisi: desenler.length,
      modulSayisi: moduller.reduce(function (a, b) { return a + b; }, 0),
      moduller: moduller, govde: govde, sagLama: mod43 ? govde.charAt(govde.length - 1) : null
    };
  }

  /* ---------- Code 93 ---------- */
  var C93_SIRA = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%';
  var C93_BIT = ('100010100 101001000 101000100 101000010 100101000 100100100 100100010 101010000 100010010 100001010 ' +
    '110101000 110100100 110100010 110010100 110010010 110001010 101101000 101100100 101100010 100110100 ' +
    '100011010 101011000 101001100 101000110 100101100 100010110 110110100 110110010 110101100 110100110 ' +
    '110010110 110011010 101101100 101100110 100110110 100111010 ' +
    '100101110 111010100 111010010 111001010 101101110 101110110 110101110 ' +
    // 43..46: sağlama karakterlerinde kullanılan ($) (%) (/) (+) desenleri
    '100100110 111011010 111010110 100110010').split(' ');
  var C93_YILDIZ = '101011110';

  function bitlerdenModuller(bitler) {
    var m = [], onceki = null;
    for (var i = 0; i < bitler.length; i++) {
      if (bitler.charAt(i) === onceki) m[m.length - 1]++;
      else { m.push(1); onceki = bitler.charAt(i); }
    }
    return m;
  }

  function c93Sagla(degerler, tavan) {
    var t = 0, w = 1;
    for (var i = degerler.length - 1; i >= 0; i--) {
      t += degerler[i] * w;
      w = w === tavan ? 1 : w + 1;
    }
    return t % 47;
  }

  function c93Ad(d) { return d < 43 ? C93_SIRA.charAt(d) : ['($)', '(%)', '(/)', '(+)'][d - 43]; }

  function code93(metin) {
    metin = String(metin);
    if (!metin.length) throw new Error('Code 93: boş metin kodlanamaz.');
    var v = [];
    for (var j = 0; j < metin.length; j++) {
      var x = C93_SIRA.indexOf(metin.charAt(j));
      if (x < 0) {
        throw new Error('Code 93: "' + metin.charAt(j) + '" karakteri desteklenmiyor (yalnızca A-Z 0-9 - . $ / + % ve boşluk).');
      }
      v.push(x);
    }
    var c = c93Sagla(v, 20);
    var k = c93Sagla(v.concat([c]), 15);
    var tum = v.concat([c, k]);
    var bitler = C93_YILDIZ + tum.map(function (d) { return C93_BIT[d]; }).join('') + C93_YILDIZ + '1';
    var moduller = bitlerdenModuller(bitler);
    return {
      karakterSayisi: metin.length, sembolSayisi: tum.length + 2, modulSayisi: bitler.length,
      moduller: moduller, sagLama: c93Ad(c) + c93Ad(k)
    };
  }

  /* ---------- GS1: EAN-13 ve ITF-14 ---------- */
  // GS1 kontrol rakamı: sağdan sola ağırlıklar 3,1,3,1...; verilen metin kontrol rakamı HARİÇ rakamlardır.
  function gs1Sagla(rakamlar) {
    var t = 0;
    for (var i = rakamlar.length - 1, w = 3; i >= 0; i--, w = w === 3 ? 1 : 3) t += Number(rakamlar.charAt(i)) * w;
    return (10 - (t % 10)) % 10;
  }

  // Yalnız rakam; tamUzunluk (kontrol dahil) ya da tamUzunluk-1 (kontrol hesaplanır) kabul edilir.
  function gs1Govde(ad, metin, tamUzunluk) {
    metin = String(metin);
    if (!/^[0-9]+$/.test(metin)) throw new Error(ad + ': yalnızca rakam kodlanabilir.');
    if (metin.length !== tamUzunluk && metin.length !== tamUzunluk - 1) {
      throw new Error(ad + ': ' + (tamUzunluk - 1) + ' rakam (kontrol rakamı otomatik eklenir) ya da kontrol rakamıyla birlikte ' + tamUzunluk + ' rakam verilmeli.');
    }
    var veri = metin.slice(0, tamUzunluk - 1), kontrol = gs1Sagla(veri);
    if (metin.length === tamUzunluk && Number(metin.charAt(tamUzunluk - 1)) !== kontrol) {
      throw new Error(ad + ': kontrol rakamı hatalı (beklenen ' + kontrol + ').');
    }
    return veri + kontrol;
  }

  var EAN_L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011'];
  var EAN_G = ['0100111', '0110011', '0011011', '0100001', '0011101', '0111001', '0000101', '0010001', '0001001', '0010111'];
  var EAN_R = ['1110010', '1100110', '1101100', '1000010', '1011100', '1001110', '1010000', '1000100', '1001000', '1110100'];
  var EAN_PARITE = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL'];

  function ean13(metin) {
    var govde = gs1Govde('EAN-13', metin, 13);
    var parite = EAN_PARITE[Number(govde.charAt(0))];
    var bitler = '101', j;
    for (j = 1; j <= 6; j++) {
      bitler += (parite.charAt(j - 1) === 'L' ? EAN_L : EAN_G)[Number(govde.charAt(j))];
    }
    bitler += '01010';
    for (j = 7; j <= 12; j++) bitler += EAN_R[Number(govde.charAt(j))];
    bitler += '101';
    return {
      karakterSayisi: String(metin).length, sembolSayisi: 12, modulSayisi: bitler.length,
      moduller: bitlerdenModuller(bitler), govde: govde, sagLama: govde.charAt(12)
    };
  }

  // Interleaved 2 of 5: her desen 5 eleman (n=dar, w=geniş)
  var ITF_DESEN = ['nnwwn', 'wnnnw', 'nwnnw', 'wwnnn', 'nnwnw', 'wnwnn', 'nwwnn', 'nnnww', 'wnnwn', 'nwnwn'];

  function itf14(metin) {
    var govde = gs1Govde('ITF-14', metin, 14);
    var moduller = [1, 1, 1, 1]; // başlangıç: dar çubuk, boşluk, çubuk, boşluk
    for (var j = 0; j < 14; j += 2) {
      var cubuk = ITF_DESEN[Number(govde.charAt(j))], bosluk = ITF_DESEN[Number(govde.charAt(j + 1))];
      for (var e = 0; e < 5; e++) {
        moduller.push(cubuk.charAt(e) === 'w' ? 3 : 1);
        moduller.push(bosluk.charAt(e) === 'w' ? 3 : 1);
      }
    }
    moduller.push(3, 1, 1); // bitiş: geniş çubuk, dar boşluk, dar çubuk
    return {
      karakterSayisi: String(metin).length, sembolSayisi: 7 + 2, modulSayisi: moduller.reduce(function (a, b) { return a + b; }, 0),
      moduller: moduller, govde: govde, sagLama: govde.charAt(13)
    };
  }

  var KODLAYICI = { code128: code128, code39: code39, code93: code93, ean13: ean13, itf14: itf14 };

  /* 2B standartlar (QR, Data Matrix): ayrı modüller; tarayıcıda QrKod / DataMatrixKod global, Node'da require. */
  function modul2d(ad) {
    if (typeof module === 'object' && module.exports) return require(ad === 'qr' ? './qr.js' : './datamatrix.js');
    var g = typeof self !== 'undefined' ? self : {};
    var m = ad === 'qr' ? g.QrKod : g.DataMatrixKod;
    if (!m) throw new Error('2B modülü yüklenmedi: ' + ad);
    return m;
  }
  var IKI_BOYUTLU = { qr: 1, datamatrix: 1 };

  function kodla(standart, metin) {
    if (IKI_BOYUTLU[standart]) {
      var k2 = modul2d(standart).kodla(metin);
      // Çubuk alanı yok: moduller boş; matris 0/1 dizi dizisi.
      return { karakterSayisi: String(metin).length, sembolSayisi: 1, modulSayisi: k2.boyut, moduller: [], matris: k2.matris, boyut: k2.boyut };
    }
    if (!KODLAYICI[standart]) throw new Error('Bilinmeyen barkod standardı: ' + standart);
    return KODLAYICI[standart](metin);
  }

  /* ---------- Standartlar ve uygunluk ---------- */
  var standartlar = [
    {
      id: 'code128', ad: 'Code 128',
      aciklama: 'En yaygın ve en sıkı barkod türüdür. Harf, rakam ve işaretlerin hepsini taşır. Arka arkaya gelen rakamları ikişer ikişer sıkıştırdığı için rakam ağırlıklı barkodlarda en kısa çıktıyı verir. Kendi sağlama değeri vardır ve okuyucular hatalı okumayı kendiliğinden eler. Çoğu etiket için önerilen seçimdir.',
      harfRakam: true, kucukHarf: true, rakamSikistirma: true
    },
    {
      id: 'code39', ad: 'Code 39',
      aciklama: 'Eski ve çok yaygın bir türdür; neredeyse her okuyucu okur. Büyük harf, rakam ve birkaç işaret taşır, küçük harf yoktur. Her karakter geniş yer kaplar, bu yüzden barkod uzun çıkar. Basit ve sade olduğu için eski cihazlarla uyum gerekiyorsa seçilir.',
      harfRakam: true, kucukHarf: false, rakamSikistirma: false
    },
    {
      id: 'code93', ad: 'Code 93',
      aciklama: 'Code 39\'un daha sıkı hâlidir; aynı karakterleri daha dar yerde taşır ve iki sağlama karakteri ekler. Küçük harf yoktur. Yer dar olduğunda ve okuyucunuz destekliyorsa uygundur, ancak Code 128 kadar yaygın değildir.',
      harfRakam: true, kucukHarf: false, rakamSikistirma: false
    }
  ];

  // GS1 standartları (rakamlı, sabit uzunluk; sıra numarası arayüz listesini etkilemesin diye ayrı tutulur)
  var standartlarGs1 = [
    { id: 'ean13', ad: 'EAN-13', aciklama: 'Perakende ürün barkodu. 13 rakam taşır; sonuncusu kontrol rakamıdır. 12 rakam verirseniz kontrol rakamı otomatik eklenir, 13 rakam verirseniz kontrol rakamı doğrulanır. Yalnız rakam kabul eder.', harfRakam: false, kucukHarf: false, rakamSikistirma: false, sabitUzunluk: 13 },
    { id: 'itf14', ad: 'ITF-14', aciklama: 'Koli ve toplu paket barkodu (Interleaved 2 of 5). 14 rakam taşır; sonuncusu kontrol rakamıdır. 13 rakam verirseniz kontrol rakamı otomatik eklenir, 14 rakam verirseniz doğrulanır. Çerçeve çizgisi (bearer bar) eklenmez.', harfRakam: false, kucukHarf: false, rakamSikistirma: false, sabitUzunluk: 14 }
  ];

  // 2B standartlar (arayüz listesini etkilemesin diye ayrı tutulur)
  var standartlar2d = [
    { id: 'qr', ad: 'QR Code', aciklama: 'İki boyutlu kare kod (model 2, bayt modu, sürüm 1-10, hata düzeltme L/M/Q/H). Telefon kameralarıyla okunur, UTF-8 metin taşır.', harfRakam: true, kucukHarf: true, rakamSikistirma: false, ikiBoyutlu: true },
    { id: 'datamatrix', ad: 'Data Matrix', aciklama: 'İki boyutlu küçük kare kod (ECC200, ASCII kodlama, 10x10 - 32x32). Çok küçük etiketlerde kullanılır; rakamları ikişer ikişer sıkıştırır.', harfRakam: true, kucukHarf: true, rakamSikistirma: true, ikiBoyutlu: true }
  ];

  function uygunMu(standartId, metin) {
    metin = metin == null ? '' : String(metin);
    if (IKI_BOYUTLU[standartId]) {
      if (!metin.length) return { uygun: false, neden: 'Metin boş.' };
      try { modul2d(standartId).kodla(metin); return { uygun: true, neden: 'Metin bu 2B standartta kodlanabilir.' }; }
      catch (e) { return { uygun: false, neden: e.message }; }
    }
    if (!KODLAYICI[standartId]) return { uygun: false, neden: 'Bilinmeyen barkod standardı: ' + standartId };
    if (!metin.length) return { uygun: false, neden: 'Metin boş.' };
    try {
      KODLAYICI[standartId](metin);
      return { uygun: true, neden: 'Metindeki tüm karakterler bu standartta kodlanabilir.' };
    } catch (e) {
      return { uygun: false, neden: e.message };
    }
  }

  /* ---------- Uzunluk önerisi ---------- */
  var MIN_TOPLAM = 8, MAKS_TOPLAM = 30, MODUL_MM = 0.33, SESSIZ_MODUL = 10;

  function kodlanmisBilgi(standart, onek, toplamRakam) {
    var n = Number(toplamRakam);
    if (!(n >= 1) || n !== Math.floor(n)) throw new Error('Toplam rakam pozitif tam sayı olmalı.');
    var temsil = String(onek == null ? '' : onek) + new Array(n + 1).join('0');
    var k = kodla(standart, temsil);
    var mm = k.modulSayisi * MODUL_MM;
    return {
      karakter: k.karakterSayisi, sembol: k.sembolSayisi, modul: k.modulSayisi,
      modulMm: MODUL_MM, genisMm: Math.round(mm * 10) / 10, genisCm: Math.round(mm) / 10,
      sessizliGenisMm: Math.round((k.modulSayisi + 2 * SESSIZ_MODUL) * MODUL_MM * 10) / 10
    };
  }

  function uzunlukOner(secenek) {
    secenek = secenek || {};
    var onek = secenek.onek == null ? 'TO' : String(secenek.onek);
    var standart = secenek.standart || 'code128';
    var luhn = secenek.luhn !== false;
    if (!KODLAYICI[standart] && !IKI_BOYUTLU[standart]) throw new Error('Bilinmeyen barkod standardı: ' + standart);
    var enBuyuk, direnc;
    try {
      enBuyuk = BigInt(secenek.enBuyukSira);
      direnc = BigInt(secenek.tahminDirenci == null ? 100000 : secenek.tahminDirenci);
    } catch (e) {
      throw new Error('En büyük sıra ve tahmin direnci tam sayı olmalı.');
    }
    if (enBuyuk < 1n) throw new Error('En büyük sıra numarası en az 1 olmalı.');
    if (direnc < 1n) throw new Error('Tahmin direnci en az 1 olmalı.');
    var gereken = enBuyuk * direnc, luhnH = luhn ? 1 : 0;
    var adim = standart === 'code128' || standart === 'datamatrix' ? 2 : 1; // rakamları ikişer ikişer sıkıştıranlar
    var N = MIN_TOPLAM, ustSinir = false;
    while (9n * 10n ** BigInt(N - luhnH - 1) < gereken) {
      N += adim;
      if (N > MAKS_TOPLAM) { N = MAKS_TOPLAM; ustSinir = true; break; }
    }
    function secenekSatiri(t) {
      var b = kodlanmisBilgi(standart, onek, t);
      var uzay = 9n * 10n ** BigInt(t - luhnH - 1); // ilk rakam 1-9
      var d = uzay / enBuyuk;
      var direncSayi = Number(d);
      var yeter = uzay >= gereken;
      return {
        toplamRakam: t, karakter: b.karakter, sembol: b.sembol, modul: b.modul, tahminDirenci: direncSayi,
        not: (yeter ? 'İstenen dirence uygun' : 'İstenen direncin altında') +
          '; rastgele bir sayının geçerli çıkma olasılığı yaklaşık 1/' + direncSayi + '.' +
          (t === N ? ' (önerilen)' : '')
      };
    }
    var adaylar = [N - 2 * adim, N - adim, N, N + adim, N + 2 * adim].filter(function (t) {
      return t >= MIN_TOPLAM && t <= MAKS_TOPLAM;
    });
    var neden = 'En büyük sıra numarası ' + enBuyuk + ' ve istenen tahmin direnci 1/' + direnc +
      ' için en az ' + (N - luhnH) + ' rakamlık bir sayı alanı gerekir; rastgele denenen bir sayı geçerli bir sıra numarasına' +
      ' denk gelme olasılığı bu durumda ' + (ustSinir ? 'hedeften düşük olabilir (üst sınır olan ' + MAKS_TOPLAM + ' rakama ulaşıldı)' : '1/' + direnc + '\'den küçük kalır') + '.' +
      (luhn ? ' Son rakam Luhn kontrol rakamıdır, bu yüzden ' + (N - 1) + ' rakam sıra numarasından gelir.' : '') +
      (standart === 'code128' ? ' Code 128 rakamları ikişer ikişer sıkıştırdığı için toplam rakam çift seçildi.' : '') +
      (MIN_TOPLAM > 0 ? ' Alt sınır ' + MIN_TOPLAM + ' rakamdır.' : '');
    return {
      toplamRakam: N, yukRakam: N - luhnH, neden: neden, ustSinir: ustSinir,
      secenekler: adaylar.map(secenekSatiri)
    };
  }

  /* ---------- Örnek indeksleri ---------- */
  // En az 4 farklı örnek; ilk, son, orta + tohumlu sözde-rastgele ara değerler, tohumlu karışık sırada.
  // Aralık adetten küçükse aralıktaki tüm sayılar (karışık) döner; tamamlamayı çağıran yapar. Aynı girdi -> aynı çıktı.
  function ornekIndeksleri(bas, son, adet, tohum) {
    adet = Math.max(4, adet == null ? 4 : Math.floor(Number(adet)) || 4);
    bas = Number(bas); son = Number(son);
    if (!isFinite(bas) || !isFinite(son) || son < bas) return [];
    var a = tohum == null ? 1 : (Number(tohum) | 0), kap = son - bas + 1;
    function rnd() { // mulberry32
      a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    var cikti = [];
    function ekle(v) { if (cikti.indexOf(v) < 0) cikti.push(v); }
    if (kap <= adet) { for (var i = bas; i <= son; i++) cikti.push(i); }
    else {
      ekle(bas); ekle(son); ekle(bas + Math.floor((son - bas) / 2));
      while (cikti.length < adet) ekle(bas + Math.floor(rnd() * kap));
    }
    for (var j = cikti.length - 1; j > 0; j--) { // Fisher-Yates
      var r = Math.floor(rnd() * (j + 1)), t2 = cikti[j]; cikti[j] = cikti[r]; cikti[r] = t2;
    }
    var sirali = true;
    for (var q = 1; q < cikti.length; q++) if (cikti[q] < cikti[q - 1]) { sirali = false; break; }
    if (sirali && cikti.length > 1) cikti.push(cikti.shift()); // sıralı çıkmasın
    return cikti;
  }

  /* ---------- SVG ---------- */
  function kac(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function svg(standart, metin, secenek) {
    secenek = secenek || {};
    if (IKI_BOYUTLU[standart]) {
      var o2 = {};
      ['modulGenislik', 'sessizBolge', 'hataDuzeltme'].forEach(function (a) { if (secenek[a] != null) o2[a] = secenek[a]; });
      return modul2d(standart).svg(metin, o2);
    }
    var mg = secenek.modulGenislik == null ? 2 : Number(secenek.modulGenislik);
    var yuk = secenek.yukseklik == null ? 80 : Number(secenek.yukseklik);
    var sessiz = secenek.sessizBolge == null ? 10 : Number(secenek.sessizBolge);
    var yazi = secenek.yaziGoster !== false;
    if (!(mg > 0) || !(yuk > 0) || !(sessiz >= 0)) throw new Error('SVG ölçüleri pozitif sayı olmalı.');
    var k = kodla(standart, metin);
    var genis = (k.modulSayisi + 2 * sessiz) * mg;
    var yaziYuk = yazi ? 20 : 0;
    var toplamYuk = yuk + yaziYuk;
    var x = sessiz * mg, rects = [];
    k.moduller.forEach(function (w, i) {
      if (i % 2 === 0) rects.push('<rect x="' + x + '" y="0" width="' + w * mg + '" height="' + yuk + '"/>');
      x += w * mg;
    });
    var s = '<svg xmlns="http://www.w3.org/2000/svg" width="' + genis + '" height="' + toplamYuk +
      '" viewBox="0 0 ' + genis + ' ' + toplamYuk + '">' +
      '<rect x="0" y="0" width="' + genis + '" height="' + toplamYuk + '" fill="#ffffff"/>' +
      '<g fill="#000000">' + rects.join('') + '</g>';
    if (yazi) {
      s += '<text x="' + genis / 2 + '" y="' + (yuk + 15) + '" text-anchor="middle" font-family="monospace" font-size="14" fill="#000000">' +
        kac(metin) + '</text>';
    }
    return s + '</svg>';
  }

  return {
    code128: code128, code39: code39, code93: code93, ean13: ean13, itf14: itf14, gs1Sagla: gs1Sagla, kodla: kodla,
    code128Tablo: C128.slice(), svg: svg, standartlar: standartlar, standartlarGs1: standartlarGs1, standartlar2d: standartlar2d, uygunMu: uygunMu,
    uzunlukOner: uzunlukOner, kodlanmisBilgi: kodlanmisBilgi, ornekIndeksleri: ornekIndeksleri
  };
});
