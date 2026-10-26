/*
 * node-test.js - ElYazisiOCR'ı Node'da tutanak-1.jpg üzerinde sınar.
 * Kurulum (proje klasörünü kirletmemek için başka bir yerde):
 *   mkdir /tmp/ocrjs && cd /tmp/ocrjs && npm init -y && npm i jpeg-js
 * Çalıştırma:
 *   JPEGJS=/tmp/ocrjs/node_modules/jpeg-js node test/node-test.js [--kenar 2000] [--py py.json] [--json cikis.json]
 *   (--kenar: görüntüyü bu uzun kenara alan ortalamasıyla küçültür; tarayıcı canvas'ını taklit eder)
 */
var fs = require("fs");
var path = require("path");
var jpeg = require(process.env.JPEGJS || "jpeg-js");
require(process.env.ELYAZISI_MODEL_JS ? require("path").resolve(process.env.ELYAZISI_MODEL_JS) : "../js/model.js"); // ELYAZISI_MODEL_JS: model dosyasi secimi (varsayilan js/model.js)
var OCR = require("../js/elyazisi-ocr.js");

var kok = path.join(__dirname, "..");
var arg = process.argv.slice(2);
function bayrak(ad) { var i = arg.indexOf(ad); return i >= 0 ? arg[i + 1] : null; }

function kucult(g, en) {
  var uzun = Math.max(g.width, g.height);
  if (!en || uzun <= en) return g;
  var o = en / uzun, w = Math.round(g.width * o), h = Math.round(g.height * o);
  var cikis = new Uint8ClampedArray(w * h * 4), x, y, c, i, j;
  for (y = 0; y < h; y++) {
    var ya = Math.floor(y / o), yb = Math.max(ya + 1, Math.min(g.height, Math.floor((y + 1) / o)));
    for (x = 0; x < w; x++) {
      var xa = Math.floor(x / o), xb = Math.max(xa + 1, Math.min(g.width, Math.floor((x + 1) / o)));
      for (c = 0; c < 3; c++) {
        var s = 0, n = 0;
        for (i = ya; i < yb; i++) for (j = xa; j < xb; j++) { s += g.data[(i * g.width + j) * 4 + c]; n++; }
        cikis[(y * w + x) * 4 + c] = Math.round(s / n);
      }
      cikis[(y * w + x) * 4 + 3] = 255;
    }
  }
  return { width: w, height: h, data: cikis };
}

var tampon = fs.readFileSync(path.join(kok, "ornekler/tutanak-1.jpg"));
var t0 = Date.now();
var cozuk = jpeg.decode(tampon, { useTArray: true, formatAsRGBA: true, maxMemoryUsageInMB: 2048, maxResolutionInMP: 100 });
var tCozme = Date.now() - t0;
var goruntu = kucult({ width: cozuk.width, height: cozuk.height, data: cozuk.data }, bayrak("--kenar") ? +bayrak("--kenar") : 0);
var kodlar = JSON.parse(fs.readFileSync(path.join(kok, "ornekler/stok-kodlari.json"), "utf8"));
var dogru = JSON.parse(fs.readFileSync(path.join(kok, "ornekler/tutanak-1.dogru.json"), "utf8")).satirlar;

var s = OCR.oku(goruntu, kodlar);
console.log("görüntü %dx%d (jpeg çözme %d ms) | oku: %d ms | uyarı: %s", goruntu.width, goruntu.height, tCozme, s.sure_ms, s.uyari.join("; ") || "-");

var kod = 0, yk = 0, sor = 0, adet = 0, i;
console.log("Sıra | Doğru      | Seçilen    | Güven | Durum | Adet");
for (i = 0; i < dogru.length; i++) {
  var r = s.satirlar[i];
  if (!r) { console.log("%d | %s | (satır yok)", i + 1, dogru[i].stok); continue; }
  var dk = r.stok.secilen === dogru[i].stok, kb = r.stok.durum === "kabul";
  if (dk) kod++;
  if (kb && !dk) yk++;
  if (!kb) sor++;
  if (r.adet.deger === dogru[i].adet) adet++;
  console.log("%d    | %s | %s%s | %s | %s | %s", i + 1, dogru[i].stok.padEnd(10), r.stok.secilen.padEnd(10), dk ? "  " : " X",
    r.stok.guven.toFixed(1).padStart(5), r.stok.durum.padEnd(5), r.adet.deger + " (" + r.adet.guven.toFixed(2) + ", " + r.adet.durum + ")");
}
console.log("satır sayısı: %d (beklenen %d)", s.satirlar.length, dogru.length);
console.log("SONUÇ: kod %d/%d | yanlış-kabul %d | sor %d | adet %d/%d | süre %d ms", kod, dogru.length, yk, sor, adet, dogru.length, s.sure_ms);

// Python ara çıktılarıyla kıyas (isteğe bağlı)
if (bayrak("--py")) {
  var py = JSON.parse(fs.readFileSync(bayrak("--py"), "utf8"));
  var maxFark = 0, kutuFark = 0;
  s.satirlar.forEach(function (sr, k) {
    var p = py.rows[k]; if (!p) return;
    var a = sr.karakterKutulari, b = p.kutu;
    if (a.length !== b.length) { kutuFark++; console.log("satır", k + 1, "kutu sayısı JS", a.length, "Python", b.length); return; }
    a.forEach(function (kt, j) {
      var yer = [kt.x - sr.hucreKutusu.x, kt.y - sr.hucreKutusu.y, kt.x - sr.hucreKutusu.x + kt.w, kt.y - sr.hucreKutusu.y + kt.h];
      if (yer.join() !== b[j].slice(0, 4).join()) { kutuFark++; console.log("satır", k + 1, "kutu", j, "JS", yer.join(), "Py", b[j].slice(0, 4).join()); }
    });
  });
  console.log("Python ile kutu farkı:", kutuFark, "| çizgi farkı: bkz. --json");
}
if (bayrak("--json")) fs.writeFileSync(bayrak("--json"), JSON.stringify(s));
process.exit(kod >= 7 && yk === 0 && s.satirlar.length === 8 ? 0 : 1);
