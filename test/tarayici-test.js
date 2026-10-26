/*
 * yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
 * tarayici-test.js - demo.html ve entegre/yeni-web/index.html'i gerçek tarayıcıda (Chromium/Chrome) file:// ile açıp
 * ornekler/tutanak-1.jpg üzerinde sınar. Ölçüt: doğru kod sayısı, yanlış kabul (0 olmalı), "sor" satırlarının onay panelinde olması,
 * konsol hatası olmaması.
 * Çalıştırma:  node test/tarayici-test.js
 * Playwright bulunamazsa PLAYWRIGHT_YOLU (playwright ya da playwright-core klasörü) ortam değişkeni kullanılır; sistem Chrome'u denenir.
 */
var path = require("path");
var fs = require("fs");

function playwrightBul() {
  var adaylar = [process.env.PLAYWRIGHT_YOLU, "playwright", "playwright-core", "D:/YusufII/Projeler/agentmom/node_modules/playwright-core"];
  for (var i = 0; i < adaylar.length; i++) {
    if (!adaylar[i]) continue;
    try { return require(adaylar[i]); } catch (e) { /* sıradaki */ }
  }
  return null;
}

var kok = path.join(__dirname, "..");
var dogru = JSON.parse(fs.readFileSync(path.join(kok, "ornekler/tutanak-1.dogru.json"), "utf8")).satirlar;
var dogruKodlar = dogru.map(function (s) { return s.stok; });
var foto = path.join(kok, "ornekler/tutanak-1.jpg");

function adres(yol) { return "file:///" + path.resolve(kok, yol).replace(/\\/g, "/"); }

async function tarayiciAc(pw) {
  var secenekler = [{}, { channel: "chrome" }, { channel: "msedge" }];
  var sonHata;
  for (var i = 0; i < secenekler.length; i++) {
    try { return await pw.chromium.launch(secenekler[i]); } catch (e) { sonHata = e; }
  }
  throw sonHata;
}

function degerlendir(ad, okunanKodlar, sorKodlari) {
  // okunanKodlar: otomatik kabul edilen kodlar; sorKodlari: onay panelinde sorulan satırların aday kodları (dizi dizisi)
  var dogruSay = 0, yanlis = [];
  okunanKodlar.forEach(function (k) {
    if (dogruKodlar.indexOf(k) >= 0) dogruSay++; else yanlis.push(k);
  });
  console.log("[" + ad + "] kabul edilen: " + JSON.stringify(okunanKodlar));
  console.log("[" + ad + "] sor/onay satırları aday listeleri: " + JSON.stringify(sorKodlari));
  console.log("[" + ad + "] doğru kabul: " + dogruSay + "/" + dogruKodlar.length + " | yanlış kabul: " + yanlis.length + (yanlis.length ? " " + JSON.stringify(yanlis) : ""));
  return { dogru: dogruSay, yanlis: yanlis.length };
}

async function demoTest(tarayici) {
  var sayfa = await tarayici.newPage();
  var hatalar = [];
  sayfa.on("console", function (m) { if (m.type() === "error") hatalar.push(m.text()); });
  sayfa.on("pageerror", function (e) { hatalar.push(String(e)); });
  sayfa.on("request", function (r) { if (!/^(file|data|blob):/.test(r.url())) hatalar.push("ağ isteği: " + r.url()); });
  await sayfa.goto(adres("demo.html"));
  await sayfa.setInputFiles("#dosya", foto);
  await sayfa.click("#oku");
  await sayfa.waitForFunction(function () { return !document.getElementById("sonuc").hidden || /başarısız|açılamadı/.test(document.getElementById("durum").textContent); }, null, { timeout: 120000 });
  var durum = await sayfa.textContent("#durum");
  console.log("[demo] durum: " + durum);
  var veri = await sayfa.evaluate(function () {
    var r = [];
    Array.prototype.forEach.call(document.querySelectorAll("#govde tr"), function (tr) {
      var td = tr.children;
      var radyolar = Array.prototype.map.call(tr.querySelectorAll("input[type=radio]"), function (x) { return x.value; }).filter(function (v) { return v; });
      r.push({ durum: tr.className, sira: td[0].textContent, kod: td[2].textContent, adaylar: radyolar, adet: tr.querySelector("input.adet") ? tr.querySelector("input.adet").value : null });
    });
    return r;
  });
  veri.forEach(function (s) { console.log("[demo] satır " + s.sira + " | " + s.durum + " | " + (s.durum === "kabul" ? s.kod : "adaylar " + s.adaylar.join(",")) + " | adet " + s.adet); });
  var kabul = veri.filter(function (s) { return s.durum === "kabul"; }).map(function (s) { return s.kod; });
  var sor = veri.filter(function (s) { return s.durum === "sor"; }).map(function (s) { return s.adaylar; });
  var d = degerlendir("demo", kabul, sor);
  // listele düğmesi
  await sayfa.click("#listele");
  console.log("[demo] listele çıktısı: " + JSON.stringify(await sayfa.inputValue("#cikti")));
  console.log("[demo] konsol hataları: " + (hatalar.length ? JSON.stringify(hatalar) : "yok"));
  await sayfa.close();
  return { d: d, hatalar: hatalar.length };
}

async function yeniWebTest(tarayici, klasor) {
  var ad = klasor;
  var sayfa = await tarayici.newPage();
  var hatalar = [];
  sayfa.on("console", function (m) { if (m.type() === "error") hatalar.push(m.text()); });
  sayfa.on("pageerror", function (e) { hatalar.push(String(e)); });
  sayfa.on("request", function (r) { if (!/^(file|data|blob):/.test(r.url())) hatalar.push("ağ isteği: " + r.url()); });
  await sayfa.addInitScript(function () { try { localStorage.setItem("tutanak-rehber-gizle", "1"); } catch (e) {} });
  await sayfa.goto(adres("entegre/" + klasor + "/index.html"));
  await sayfa.waitForFunction(function () { return !!window.BARKOD_VERI && document.getElementById("fotoGir"); }, null, { timeout: 120000 });
  var t0 = Date.now();
  await sayfa.setInputFiles("#fotoGir", foto);
  await sayfa.waitForFunction(function () {
    var m = document.getElementById("mesaj").textContent;
    return /onay bekliyor|okunamadı/.test(m);
  }, null, { timeout: 180000 });
  console.log("[" + ad + "] süre (yükleme+okuma): " + (Date.now() - t0) + " ms");
  console.log("[" + ad + "] mesaj: " + (await sayfa.textContent("#mesaj")));
  var tablo = await sayfa.evaluate(function () {
    return Array.prototype.map.call(document.querySelectorAll("#satirlar tr"), function (tr) {
      return { k: tr.children[1].textContent, r: tr.children[2].textContent, a: tr.children[3].textContent, b: tr.children[4].textContent };
    });
  });
  tablo.forEach(function (s, i) { console.log("[" + ad + "] eklenen " + (i + 1) + ": " + s.k + " / " + s.a + " / " + s.b); });
  var panel = await sayfa.evaluate(function () {
    var p = document.getElementById("ocrOnay");
    if (!p) return [];
    return Array.prototype.map.call(p.children, function (c, i) {
      return i === 0 ? null : { metin: c.textContent, canvas: c.querySelectorAll("canvas").length, dugme: Array.prototype.map.call(c.querySelectorAll("button"), function (b) { return b.textContent; }) };
    }).filter(function (x) { return x; });
  });
  panel.forEach(function (p, i) { console.log("[" + ad + "] onay " + (i + 1) + ": düğmeler " + JSON.stringify(p.dugme) + " | küçük resim " + p.canvas + " | " + p.metin.slice(0, 60)); });
  // Bu üründe aynı stok kodunun birden çok renk/bedeni var; bu yüzden "kabul" satırları renk/beden sorusu olarak panelde görünür (sessiz ekleme yok).
  var kabulKodlar = [], sorAdaylar = [];
  panel.forEach(function (p) {
    var m = /^(T\d{4,6}(?:-\d{2})?) için renk\/beden/.exec(p.metin);
    if (m) kabulKodlar.push(m[1]);
    else sorAdaylar.push(p.dugme.filter(function (d) { return /^T\d/.test(d); }));
  });
  var d = degerlendir(ad, kabulKodlar, sorAdaylar);
  var ilkAdayDogru = kabulKodlar.filter(function (k) { return dogruKodlar.indexOf(k) >= 0; }).length +
    sorAdaylar.filter(function (a) { return a.length && dogruKodlar.indexOf(a[0]) >= 0; }).length;
  console.log("[" + ad + "] ilk aday/kabul doğru (node-test ölçütü): " + ilkAdayDogru + "/" + dogruKodlar.length);
  // akışı sına: ilk renk/beden sorusunda ilk seçeneğe, sonra ilk 'sor' satırında ilk adaya bas
  var once = (await sayfa.$$("#satirlar tr")).length;
  var vb = await sayfa.$("#ocrOnay button.ikinci");
  var bekle0 = await sayfa.evaluate(function () { return document.getElementById("ocrOnay").children.length - 1; });
  var vdugme = await sayfa.evaluateHandle(function () {
    var k = Array.prototype.filter.call(document.getElementById("ocrOnay").children, function (c) { return /için renk/.test(c.textContent); })[0];
    return k ? k.querySelector("button") : null;
  });
  if (vdugme.asElement()) { await vdugme.asElement().click(); await sayfa.waitForTimeout(300); }
  var sonra = (await sayfa.$$("#satirlar tr")).length;
  var bekle1 = await sayfa.evaluate(function () { return document.getElementById("ocrOnay").children.length - 1; });
  console.log("[" + ad + "] ilk renk/beden seçimi: tablo satırı " + once + " -> " + sonra + ", onay bekleyen " + bekle0 + " -> " + bekle1 + " | mesaj: " + (await sayfa.textContent("#mesaj")));
  var sdugme = await sayfa.evaluateHandle(function () {
    var k = Array.prototype.filter.call(document.getElementById("ocrOnay").children, function (c) { return /Okunan:/.test(c.textContent); })[0];
    return k ? k.querySelector("button.ikinci") : null;
  });
  if (sdugme.asElement()) {
    await sdugme.asElement().click(); await sayfa.waitForTimeout(300);
    console.log("[" + ad + "] ilk 'sor' adayı seçildi -> onay bekleyen " + (await sayfa.evaluate(function () { return document.getElementById("ocrOnay").children.length - 1; })) + " | mesaj: " + (await sayfa.textContent("#mesaj")));
  }

  console.log("[" + ad + "] konsol hataları: " + (hatalar.length ? JSON.stringify(hatalar) : "yok"));
  await sayfa.close();
  return { d: d, hatalar: hatalar.length };
}

(async function () {
  var pw = playwrightBul();
  if (!pw) { console.log("ÇALIŞTIRILAMADI: playwright bulunamadı (PLAYWRIGHT_YOLU ayarlayın)"); process.exit(2); }
  var tarayici = await tarayiciAc(pw);
  var hepsi = [];
  try {
    hepsi.push(await demoTest(tarayici));
    hepsi.push(await yeniWebTest(tarayici, "yeni-web"));
  } finally { await tarayici.close(); }
  var yanlis = 0, hata = 0;
  hepsi.forEach(function (h) { yanlis += h.d.yanlis; hata += h.hatalar; });
  console.log("ÖZET: yanlış kabul toplamı " + yanlis + ", konsol hatası toplamı " + hata);
  process.exit(yanlis || hata ? 1 : 0);
})().catch(function (e) { console.error("TEST HATASI:", e); process.exit(3); });
