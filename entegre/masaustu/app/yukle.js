// Betikleri sırayla ve sayfa çizildikten sonra yükler: büyük ürün listesi okunurken ekranda "yükleniyor" görünür.
(function () {
  var liste = ["barkod-veri.js", "qr-kod.js", "barkod-kod.js", "nebim-xlsx.js", "uygulama.js"];
  var i = 0;
  function sonraki() {
    if (i >= liste.length) return;
    var s = document.createElement("script");
    s.src = liste[i++];
    s.onload = sonraki;
    s.onerror = function () {
      var u = document.getElementById("yukleniyor");
      if (u) u.textContent = "Dosya yüklenemedi: " + s.src;
    };
    document.body.appendChild(s);
  }
  setTimeout(sonraki, 30);
})();
