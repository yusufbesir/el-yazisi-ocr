// negatif-test.js - Tablo içermeyen fotoğraflarda (tadilat fişi) kütüphane kod uydurmamalı.
// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
var fs = require("fs"), path = require("path");
var jpeg = require(process.env.JPEGJS || "jpeg-js");
require(process.env.ELYAZISI_MODEL_JS ? require("path").resolve(process.env.ELYAZISI_MODEL_JS) : "../js/model.js"); // ELYAZISI_MODEL_JS: model dosyasi secimi (varsayilan js/model.js)
var OCR = require("../js/elyazisi-ocr.js");
var kodlar = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "ornekler", "stok-kodlari.json"), "utf8"));
if (!Array.isArray(kodlar)) kodlar = kodlar.kodlar || Object.keys(kodlar);
var kotu = 0;
process.argv.slice(2).forEach(function (f) {
  var g = jpeg.decode(fs.readFileSync(f), { useTArray: true });
  var t = Date.now();
  var s = OCR.oku({ width: g.width, height: g.height, data: g.data }, kodlar);
  var kabul = s.satirlar.filter(function (r) { return r.stok.durum === "kabul"; });
  console.log(path.basename(f) + ": satir=" + s.satirlar.length + " kabul=" + kabul.length + " sor=" + (s.satirlar.length - kabul.length) + " sure=" + (Date.now() - t) + "ms uyari=" + JSON.stringify(s.uyari));
  kabul.forEach(function (r) { console.log("   SESSIZ KABUL! " + r.stok.secilen + " guven " + r.stok.guven.toFixed(2)); });
  kotu += kabul.length;
});
console.log(kotu === 0 ? "NEGATIF TEST GECTI: yanlis kabul 0" : "NEGATIF TEST KALDI: " + kotu + " yanlis kabul");
process.exit(kotu ? 1 : 0);
