// liste-disi-test.js - Kapalı liste riski: her satırın DOĞRU kodu listeden çıkarılınca ne olur?
// Beklenen: kod "sor"a düşmeli ya da adaylar arasında yanlış bir kod "kabul" edilmemeli (yanlış kabul = sessiz hata).
// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
var fs = require("fs"), path = require("path");
var jpeg = require(process.env.JPEGJS || "jpeg-js");
require(process.env.ELYAZISI_MODEL_JS ? require("path").resolve(process.env.ELYAZISI_MODEL_JS) : "../js/model.js"); // ELYAZISI_MODEL_JS: model dosyasi secimi (varsayilan js/model.js)
var OCR = require("../js/elyazisi-ocr.js");
var kok = path.join(__dirname, "..");
var dogru = JSON.parse(fs.readFileSync(path.join(kok, "ornekler", "tutanak-1.dogru.json"), "utf8")).satirlar;
var kodlar = JSON.parse(fs.readFileSync(path.join(kok, "ornekler", "stok-kodlari.json"), "utf8"));
if (!Array.isArray(kodlar)) kodlar = kodlar.kodlar || Object.keys(kodlar);
var g = jpeg.decode(fs.readFileSync(path.join(kok, "ornekler", "tutanak-1.jpg")), { useTArray: true });
// node-test ile aynı küçültme (alan ortalaması, uzun kenar 2000)
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
g = kucult(g, 2000);
var tam = OCR.oku(g, kodlar);
var yk = 0, sor = 0, bos = 0;
console.log("Satır | Doğru (listeden çıkarıldı) | Seçilen | Güven | Durum | Yorum");
dogru.forEach(function (d, i) {
  var liste = kodlar.filter(function (k) { return k !== d.stok; });
  var s = OCR.oku(g, liste);
  var r = s.satirlar[i];
  if (!r) { console.log((i + 1) + " | " + d.stok + " | - | - | yok"); return; }
  var durum = r.stok.durum, yorum;
  if (durum === "kabul") { yk++; yorum = "YANLIŞ KABUL (sessiz hata)"; }
  else if (durum === "sor") { sor++; yorum = "sor (güvenli)"; }
  else { bos++; yorum = "bos"; }
  console.log((i + 1) + " | " + d.stok + " | " + r.stok.secilen + " | " + r.stok.guven.toFixed(2) + " | " + durum + " | " + yorum + " (tam listede: " + tam.satirlar[i].stok.durum + " " + tam.satirlar[i].stok.guven.toFixed(2) + ")");
});
console.log("SONUÇ: doğru kod listede yokken yanlış kabul " + yk + "/8, sor " + sor + "/8, bos " + bos + "/8");
process.exit(yk ? 1 : 0);
