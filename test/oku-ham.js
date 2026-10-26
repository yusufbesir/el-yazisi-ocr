// oku-ham.js - Doğru değer dosyası olmayan fotoğraflarda kütüphanenin okuduğunu listeler (kör okuma).
// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait; değiştirme: yalnız bu iş parçacığı
var fs = require("fs"), path = require("path");
var jpeg = require(process.env.JPEGJS || "jpeg-js");
require(process.env.ELYAZISI_MODEL_JS ? require("path").resolve(process.env.ELYAZISI_MODEL_JS) : "../js/model.js"); // ELYAZISI_MODEL_JS: model dosyasi secimi (varsayilan js/model.js)
var OCR = require("../js/elyazisi-ocr.js");
var kok = path.join(__dirname, "..");
var kodlar = JSON.parse(fs.readFileSync(path.join(kok, "ornekler", "stok-kodlari.json"), "utf8"));
if (!Array.isArray(kodlar)) kodlar = kodlar.kodlar || Object.keys(kodlar);
function kucult(g, en) {
  var uzun = Math.max(g.width, g.height); if (uzun <= en) return g;
  var o = en / uzun, w = Math.round(g.width * o), h = Math.round(g.height * o), out = new Uint8ClampedArray(w * h * 4);
  for (var y = 0; y < h; y++) { var ya = Math.floor(y / o), yb = Math.max(ya + 1, Math.min(g.height, Math.floor((y + 1) / o)));
    for (var x = 0; x < w; x++) { var xa = Math.floor(x / o), xb = Math.max(xa + 1, Math.min(g.width, Math.floor((x + 1) / o)));
      var s = [0, 0, 0], n = 0;
      for (var yy = ya; yy < yb; yy++) for (var xx = xa; xx < xb; xx++) { var i = (yy * g.width + xx) * 4; s[0] += g.data[i]; s[1] += g.data[i + 1]; s[2] += g.data[i + 2]; n++; }
      var j = (y * w + x) * 4; out[j] = s[0] / n; out[j + 1] = s[1] / n; out[j + 2] = s[2] / n; out[j + 3] = 255; } }
  return { width: w, height: h, data: out };
}
process.argv.slice(2).forEach(function (f) {
  var g = kucult(jpeg.decode(fs.readFileSync(f), { useTArray: true }), 2000);
  var t = Date.now(), s = OCR.oku(g, kodlar);
  console.log("== " + path.basename(f) + " (" + g.width + "x" + g.height + ") " + (Date.now() - t) + " ms uyari=" + JSON.stringify(s.uyari));
  s.satirlar.forEach(function (r) {
    console.log("  " + r.sira + " | " + (r.stok.secilen || "-") + " | ham " + r.stok.ham + " | guven " + r.stok.guven.toFixed(2) + " acik " + (r.stok.acik || 0).toFixed(2) + " | " + r.stok.durum + " | adet " + r.adet.deger + " (" + r.adet.durum + ") | adaylar " + r.stok.aday.map(function (a) { return a.kod; }).join(","));
  });
});
