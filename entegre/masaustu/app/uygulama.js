// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
// Taban: masaustu/r2-taban/web/uygulama.js. Eklenen: Tesseract yerine ElYazisiOCR (tarayıcı CNN, yedek) + masaüstünde güçlü PaddleOCR motoru (BRIDGE.gucluOku). Ayrıntı: DEGISIKLIK.md
(function () {
  var VERI = window.BARKOD_VERI || {};
  var HEADER_KEY = "tutanak-baslik";
  var SAYAC_KEY = "tutanak-sayac";
  var DOSYA_ADI = "takip-kayitlari.json";
  var KLASOR_ADI = "kayitlar";
  var REHBER_KEY = "tutanak-rehber-gizle";
  var BRIDGE = window.masaustu || null;   // masaüstü sürümünün güvenli köprüsü (preload.js)
  var DOSYA_DESTEGI = !!BRIDGE || typeof window.showDirectoryPicker === "function";
  var kayitlar = [];   // tek kaynak: kayıt dosyası; bellekteki kopya
  var bekleyenKod = { no: "", kod: "" };   // henüz kaydedilmemiş tutanağın kayıt kodu
  var klasor = null;   // kayitlar klasörü (tarayıcıda FileSystemDirectoryHandle, masaüstünde true)
  var lines = [];

  var $ = function (id) { return document.getElementById(id); };
  var alanlar = ["tarih", "dizi", "sirket", "teslimEden", "teslimAlan"];

  function lsGet(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function lsSet(key, val) {
    try { localStorage.setItem(key, val); } catch (e) { /* depolama yok */ }
  }

  function saatMetni() {
    var d = new Date();
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  // Dosya adı: dizi, tarih, saat ve işlem türü. Yazdırmada PDF adı, Nebim'de xlsx adı olur.
  function dosyaAdi() {
    var parcalar = [$("dizi").value.trim() || "Tutanak", $("tarih").value.trim() || bugun(), saatMetni().replace(":", "."), $("tur").value];
    return parcalar.join(" ").replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ").trim();
  }

  // ---- Kayıtlar: masaüstünde programın yanındaki, tarayıcıda seçilen klasördeki "kayitlar" klasörü ----
  var KOPYA_KEY = "tutanak-kayitlar-kopya";
  var klasorYolu = "";           // masaüstü sürümünde kayıt klasörünün gerçek yolu
  var yedekYerKullaniliyor = false;
  var sonYazimHatasi = false;
  var sonOtoKayit = "";
  var yazSirasi = Promise.resolve();
  var acikNo = null;             // elle açılan eski tutanağın numarası
  var bekleyenKlasor = null;     // izin bekleyen eski klasör tutamacı (tarayıcı)
  var otoZamani = null;

  function kayitlariAyristir(metin) {
    var o = JSON.parse(metin);
    var liste = Array.isArray(o) ? o : o.kayitlar;
    if (!Array.isArray(liste) || !liste.every(function (k) { return k && k.no && Array.isArray(k.satirlar); })) throw new Error("biçim");
    return liste;
  }

  function kayitMetni(liste) {
    return JSON.stringify({ kayitlar: liste }, null, 2);
  }

  // Tarayıcının kendi deposunda yedek kopya: klasör bağlı olmasa da kayıt kaybolmasın
  function kopyaYaz(liste) { lsSet(KOPYA_KEY, kayitMetni(liste)); }
  function kopyaOku() {
    var m = lsGet(KOPYA_KEY);
    try { return m ? kayitlariAyristir(m) : []; } catch (e) { return []; }
  }

  function esc(t) {
    return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }

  function rozetYaz(sinif, baslik, ayrinti) {
    $("rozet").className = "rozet" + (sinif ? " " + sinif : "");
    $("rozetBaslik").textContent = baslik;
    $("rozetAyrinti").textContent = ayrinti || "";
  }

  function dosyaDurumuYaz() {
    var uyari = $("depoUyari");
    uyari.hidden = true;
    if (!DOSYA_DESTEGI) {
      uyari.hidden = false;
      uyari.textContent = "Bu tarayıcı kayıt klasörüne otomatik yazamıyor. Chrome ya da Edge kullanın. Şimdilik kayıtlar yalnızca bu tarayıcıda saklanır; işiniz bitince Kayıtlar ve yedek menüsünden Yedek al ile dosyayı kaydedin.";
      rozetYaz("kotu", "Dosyaya yazılmıyor", "Kayıtlar yalnızca bu tarayıcıda");
    } else if (!klasor) {
      uyari.hidden = false;
      uyari.textContent = bekleyenKlasor
        ? "Kayıt klasörü için izin gerekiyor. Kayıtlar ve yedek menüsünden Kayıt klasörünü yeniden bağla düğmesine basın. Bağlanana kadar kayıtlar yalnızca bu tarayıcıda saklanır."
        : "Kayıt klasörü bağlı değil. Kayıtlar ve yedek menüsünden programın bulunduğu klasörü seçin. Bağlanana kadar kayıtlar yalnızca bu tarayıcıda saklanır.";
      rozetYaz("kotu", "Klasör bağlı değil", "Kayıtlar yalnızca bu tarayıcıda");
    } else if (sonYazimHatasi) {
      uyari.hidden = false;
      uyari.textContent = "Kayıt klasörüne yazılamadı. Klasör izni ya da erişimi kontrol edin; tutanak şimdilik bu tarayıcıda saklanıyor.";
      rozetYaz("kotu", "Yazma hatası", "Klasör iznini kontrol edin");
    } else {
      if (yedekYerKullaniliyor) {
        uyari.hidden = false;
        uyari.textContent = "Program klasörüne yazılamadığı için kayıtlar şuraya yazılıyor: " + klasorYolu;
      }
      rozetYaz("iyi", "Otomatik kayıt açık", kayitlar.length + " tutanak" + (sonOtoKayit ? " · " + sonOtoKayit : ""));
    }
    $("klasorBagla").textContent = bekleyenKlasor ? "Kayıt klasörünü yeniden bağla" : "Kayıt klasörünü bağla";
    kayitSayfasiGuncelle();
  }

  // Kayıt klasörüne tek dosya yazar (en fazla bir alt klasör: yedekler/...). Yazmalar sıraya girer.
  function klasoreYaz(ad, metin) {
    var is = function () {
      if (BRIDGE) return BRIDGE.yaz(ad, metin);
      var parcalar = ad.split("/");
      var dosya = parcalar.pop();
      var p = Promise.resolve(klasor);
      parcalar.forEach(function (d) { p = p.then(function (h) { return h.getDirectoryHandle(d, { create: true }); }); });
      return p.then(function (h) { return h.getFileHandle(dosya, { create: true }); })
        .then(function (h) { return h.createWritable(); })
        .then(function (w) { return w.write(metin).then(function () { return w.close(); }); });
    };
    var sonuc = yazSirasi.then(is);
    yazSirasi = sonuc.catch(function () {});
    return sonuc;
  }

  function klasordenOku(ad) {
    if (BRIDGE) return BRIDGE.oku(ad);
    return klasor.getFileHandle(ad).then(function (h) { return h.getFile(); }).then(function (f) { return f.text(); })
      .catch(function (e) { if (e && e.name === "NotFoundError") return ""; throw e; });
  }

  function isoGun() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  // Ana kayıt dosyasını yazar. "dosya": klasöre yazıldı, "kopya": yalnız tarayıcıda, "hata": yazılamadı.
  function kayitlariSakla(yeni) {
    kayitlar = yeni;
    kopyaYaz(yeni);
    if (!klasor) { dosyaDurumuYaz(); return Promise.resolve("kopya"); }
    // Kayıt yokken dosyaya yazılmaz: yeniden kurulumdan sonra kalan yedek dosyaları boş liste ile ezilmesin
    if (!yeni.length) { dosyaDurumuYaz(); return Promise.resolve("dosya"); }
    var metin = kayitMetni(yeni);
    return klasoreYaz(DOSYA_ADI, metin).then(function () {
      sonYazimHatasi = false;
      klasoreYaz("yedekler/yedek-" + isoGun() + ".json", metin).catch(function () {});   // günde bir yedek, aynı gün üzerine yazılır
      dosyaDurumuYaz();
      return "dosya";
    }).catch(function () {
      sonYazimHatasi = true;
      dosyaDurumuYaz();
      return "hata";
    });
  }

  function ayarlariYaz() {
    if (klasor) klasoreYaz("ayarlar.json", JSON.stringify({ sayac: getSayac() }, null, 2)).catch(function () {});
  }

  function sayacYaz(n) {
    lsSet(SAYAC_KEY, String(n));
    ayarlariYaz();
  }

  function durumEtiketiGuncelle() {
    var no = $("tutanakNo").value;
    var k = kayitlar.find(function (x) { return x.no === no; });
    var e = $("durumEtiketi");
    if (k && k.durum !== "taslak") { e.textContent = "Kayıtlı"; e.className = "etiket kayitli"; }
    else { e.textContent = "Taslak"; e.className = "etiket taslak"; }
  }

  function saniyeli() {
    var d = new Date();
    return [d.getHours(), d.getMinutes(), d.getSeconds()].map(function (n) { return String(n).padStart(2, "0"); }).join(":");
  }

  // Her okutmada ve her değişiklikte tutanak kendiliğinden kaydedilir (taslak olarak; "Tutanağı kaydet" kayıtlı yapar)
  function otomatikKaydet(hemen) {
    clearTimeout(otoZamani);
    if (hemen) { otomatikYaz(); return; }
    otoZamani = setTimeout(otomatikYaz, 400);
  }

  function otomatikYaz() {
    clearTimeout(otoZamani);
    var no = $("tutanakNo").value;
    var onceki = kayitlar.find(function (k) { return k.no === no; });
    if (!lines.length && !onceki) return Promise.resolve("yok");
    var kayit = mevcutKayit(onceki && onceki.durum !== "taslak" ? "kayitli" : "taslak");
    return kayitlariSakla(kayitlariBirlestir(kayitlar.slice(), [kayit])).then(function (d) {
      if (d !== "hata") sonOtoKayit = saniyeli();
      durumEtiketiGuncelle();
      dosyaDurumuYaz();
      return d;
    });
  }

  function dosyaBaglandi() {
    takipDiziListesi();
    dosyaDurumuYaz();
    durumEtiketiGuncelle();
  }

  // Klasör bağlandıktan sonra: kayıtları ve sırayı oku, tarayıcı kopyasındaki eksikleri ekle, yarım tutanağı geri getir
  // ---- Kayıt imzası (yalnız masaüstü sürümü): yeniden kurulumda kalan dosyaları tanır ----
  var imzaBekleyen = [];   // doğrulanamayan, kullanıcı onayı bekleyen dosyalar

  function eksikKayitlar(liste) {
    return liste.filter(function (k) { return k && k.no && Array.isArray(k.satirlar) && !kayitlar.some(function (m) { return m.no === k.no; }); });
  }

  function imzaSonucuIsle(s) {
    if (!s) return;
    var eklenen = 0;
    var ob = s[0] && s[0].oturumBasi;
    var uy = $("imzaUyari");
    if (ob && ob.durum === "degismis") {
      uy.hidden = false;
      uy.textContent = "Kayıt dosyası program dışında değiştirilmiş görünüyor (" + ob.bozuk.join(", ") + "). Kayıtları Kayıtlar ve yedek menüsünden kontrol edin.";
    }
    imzaBekleyen = [];
    (s[1] || []).forEach(function (d) {
      var eksik = eksikKayitlar(d.liste || []);
      if (!eksik.length) return;
      if (d.durum === "tamam") {
        eksik.forEach(function (k) { kayitlar.push(k); });
        eklenen += eksik.length;
      } else if (d.durum !== "bos") {
        imzaBekleyen.push({ ad: d.ad, durum: d.durum, bozuk: d.bozuk || [], eksik: eksik });
      }
    });
    if (eklenen) mesaj("İmzalı dosyalardan " + eklenen + " kayıt tanındı ve eklendi.", "tamam");
    if (imzaBekleyen.length) {
      uy.hidden = false;
      uy.textContent = (uy.textContent ? uy.textContent + " " : "") + "Doğrulanamayan dosyalarda " + imzaBekleyen.length + " dosyadan alınabilecek kayıt var. Kayıtlar ve yedek menüsünden karar verin.";
    }
    imzaPaneliniYaz();
  }

  function imzaPaneliniYaz() {
    $("imzaPanel").hidden = !(BRIDGE && BRIDGE.dogrula);
    var liste = $("imzaListe");
    liste.textContent = "";
    imzaBekleyen.forEach(function (b) {
      var kutu = document.createElement("div");
      kutu.className = "grup";
      kutu.style.margin = "10px 0 0";
      var m = document.createElement("span");
      m.textContent = b.ad + ": " + (b.durum === "imzasiz" ? "imzasız (eski sürümden)" : "imzası doğrulanamadı") + ", alınabilecek kayıt: " + b.eksik.length;
      var dugme = document.createElement("button");
      dugme.type = "button";
      dugme.className = "ikinci";
      dugme.textContent = "Yine de kayıtlara al";
      dugme.addEventListener("click", function () {
        BRIDGE.icAl(b.ad).then(function (s) {
          var eksik = eksikKayitlar((s && s.liste) || []);
          eksik.forEach(function (k) { kayitlar.push(k); });
          imzaBekleyen = imzaBekleyen.filter(function (x) { return x.ad !== b.ad; });
          return kayitlariSakla(kayitlar).then(function () {
            takipDiziListesi();
            imzaPaneliniYaz();
            kayitSayfasiGuncelle();
            mesaj(eksik.length + " kayıt eklendi.", "tamam");
          });
        });
      });
      kutu.appendChild(m);
      kutu.appendChild(dugme);
      liste.appendChild(kutu);
    });
  }

  function baglanBitir() {
    var imzaSozu = (BRIDGE && BRIDGE.tara && BRIDGE.dogrula)
      ? Promise.all([BRIDGE.dogrula(), BRIDGE.tara()]).catch(function () { return null; })   // diske ilk yazmadan ÖNCE istenir
      : Promise.resolve(null);
    return klasordenOku(DOSYA_ADI).then(function (metin) {
      var liste = metin.trim() ? kayitlariAyristir(metin) : [];
      var bellek = kayitlar.length ? kayitlar : kopyaOku();
      bellek.forEach(function (k) { if (!liste.some(function (d) { return d.no === k.no; })) liste.push(k); });
      kayitlar = liste;
      return klasordenOku("ayarlar.json");
    }).then(function (a) {
      try {
        var n = JSON.parse(a || "{}").sayac;
        if (n > getSayac()) lsSet(SAYAC_KEY, String(n));
      } catch (e) { /* ayar dosyası bozuksa yok sayılır */ }
      return imzaSozu;
    }).then(function (s) {
      imzaSonucuIsle(s);
      kopyaYaz(kayitlar);
      baslangicTutanagi();
      dosyaBaglandi();
      return kayitlariSakla(kayitlar);
    });
  }

  // Açılışta: sıradaki numara yarım (taslak) bir tutanaksa onu geri getirir, kayıtlıysa ilk boş numaraya geçer
  function baslangicTutanagi() {
    if (lines.length) return;
    var k = kayitlar.find(function (x) { return x.no === tutanakNo(); });
    if (k && k.durum === "taslak" && k.satirlar.length) {
      kaydiYukle(k);
      mesaj("Yarım kalan tutanak geri yüklendi: " + k.no, "tamam");
      return;
    }
    var guvenlik = 0;
    while (kayitlar.some(function (x) { return x.no === tutanakNo(); }) && guvenlik++ < 100000) sayacYaz(getSayac() + 1);
    basliklariGuncelle();
  }

  function kaydiYukle(kayit) {
    var yaz = function (id, v) { $(id).value = v || ""; };
    yaz("tarih", kayit.tarih); yaz("dizi", kayit.dizi); yaz("sirket", kayit.sirket);
    yaz("teslimEden", kayit.teslimEden); yaz("teslimAlan", kayit.teslimAlan);
    $("tur").value = kayit.tur === "İade" ? "İade" : "Teslim";
    acikNo = null;
    acikNo = tutanakNo() === kayit.no ? null : kayit.no;
    lines = kayit.satirlar.map(function (s) {
      var u = VERI[s.barkod] || {};
      return { k: s.k, r: s.r, a: s.a, b: s.b, n: u.n || "", barkod: s.barkod, fiyat: typeof s.f === "number" ? para(s.f) : "",
        teslimNo: s.teslimNo || "", teslimTarihi: s.teslimTarihi || "", bulunamadi: kayit.tur === "İade" && !s.teslimNo };
    });
    satirlariCiz();
    basliklariGuncelle();
    durumEtiketiGuncelle();
  }

  // ---- Kayıt klasörü: masaüstü sürümünde otomatik, tarayıcıda seçilir ve hatırlanır ----
  function idbAc() {
    return new Promise(function (coz, reddet) {
      var r = indexedDB.open("tutanak-doldurucu", 1);
      r.onupgradeneeded = function () { r.result.createObjectStore("s"); };
      r.onsuccess = function () { coz(r.result); };
      r.onerror = function () { reddet(r.error); };
    });
  }
  function idbGet(anahtar) {
    return idbAc().then(function (db) {
      return new Promise(function (coz, reddet) {
        var q = db.transaction("s").objectStore("s").get(anahtar);
        q.onsuccess = function () { coz(q.result); };
        q.onerror = function () { reddet(q.error); };
      });
    });
  }
  function idbSet(anahtar, deger) {
    return idbAc().then(function (db) {
      return new Promise(function (coz, reddet) {
        var t = db.transaction("s", "readwrite");
        t.objectStore("s").put(deger, anahtar);
        t.oncomplete = coz;
        t.onerror = function () { reddet(t.error); };
      });
    });
  }

  function tarayiciKlasoruBagla(alt) {
    klasor = alt;
    bekleyenKlasor = null;
    klasorYolu = "Seçtiğiniz klasörün içindeki \"" + alt.name + "\" klasörü";
    return baglanBitir();
  }

  function klasorBagla() {
    if (BRIDGE || !DOSYA_DESTEGI) return;
    var secici = function () {
      return window.showDirectoryPicker({ mode: "readwrite" }).then(function (secilen) {
        return secilen.getDirectoryHandle(KLASOR_ADI, { create: true });
      }).then(function (alt) {
        idbSet("klasor", alt).catch(function () {});
        return tarayiciKlasoruBagla(alt);
      }).then(function () {
        mesaj("Kayıt klasörü bağlandı: " + kayitlar.length + " kayıt.", "tamam");
      });
    };
    var is = bekleyenKlasor
      ? bekleyenKlasor.requestPermission({ mode: "readwrite" }).then(function (p) {
        return p === "granted" ? tarayiciKlasoruBagla(bekleyenKlasor).then(function () { mesaj("Kayıt klasörü yeniden bağlandı.", "tamam"); }) : secici();
      })
      : secici();
    is.catch(function (e) {
      if (e && e.name === "AbortError") return;
      mesaj("Kayıt klasörü bağlanamadı. Dosya bozuksa Yedek yükle ile düzeltebilirsiniz.", "hata");
    });
  }

  // Açılışta: önceki oturumdan kalan klasör izinliyse sessizce bağlanır
  function klasoruHatirla() {
    if (BRIDGE) {
      return BRIDGE.bilgi().then(function (b) {
        klasorYolu = b.yol;
        yedekYerKullaniliyor = !!b.yedekYer;
        klasor = true;
        return baglanBitir();
      }).catch(function () {
        sonYazimHatasi = true;
        klasor = true;
        dosyaDurumuYaz();
      });
    }
    if (!DOSYA_DESTEGI || !window.indexedDB) return Promise.resolve();
    return idbGet("klasor").then(function (h) {
      if (!h) return;
      return h.queryPermission({ mode: "readwrite" }).then(function (p) {
        if (p === "granted") return tarayiciKlasoruBagla(h);
        bekleyenKlasor = h;
        dosyaDurumuYaz();
      });
    }).catch(function () { /* hatırlanan klasör yoksa yok sayılır */ });
  }

  function diziAnahtar(s) {
    return String(s || "").trim().toLocaleLowerCase("tr");
  }

  function yeniKayitKodu() {
    var d = new Date();
    var iki = function (n) { return String(n).padStart(2, "0"); };
    return "TK" + d.getFullYear() + iki(d.getMonth() + 1) + iki(d.getDate()) + iki(d.getHours()) + iki(d.getMinutes()) + iki(d.getSeconds()) +
      String(Math.floor(Math.random() * 1000)).padStart(3, "0");
  }

  // Kayıtlıysa kayıttaki kod; değilse (uret ise) bir kez üretilir ve kaydedilene kadar sabit kalır
  function kayitKodu(uret) {
    var no = $("tutanakNo").value;
    var kayit = kayitlar.find(function (k) { return k.no === no; });
    if (kayit && kayit.kayitKodu) return kayit.kayitKodu;
    if (bekleyenKod.no !== no) bekleyenKod = { no: no, kod: "" };
    if (!bekleyenKod.kod && uret) bekleyenKod.kod = yeniKayitKodu();
    return bekleyenKod.kod;
  }

  // Barkod yalnızca kayıt kodunu taşır; QR tutanak bilgilerini taşır
  function kodlariCiz() {
    var kod = kayitKodu(false);
    var barkodSvg = "", qrSvg = "";
    try {
      if (kod) barkodSvg = BarkodCiz.svg("code128", kod, { modulGenislik: 2, yukseklik: 60, sessizBolge: 10, yaziGoster: false });
      qrSvg = QrKod.svg("NO:" + $("tutanakNo").value + "|TUR:" + $("tur").value + "|TARIH:" + $("tarih").value + "|SAAT:" + ($("pSaat").textContent.trim() || saatMetni()) +
        "|DIZI:" + $("dizi").value.trim() + "|SIRKET:" + $("sirket").value.trim() + "|URUN:" + lines.length, { modulGenislik: 4, sessizBolge: 2 });
    } catch (e) {
      mesaj("Barkod/QR üretilemedi (qr-kod.js veya barkod-kod.js yüklenemedi).", "hata");
    }
    ["pBarkod", "ekranBarkod"].forEach(function (id) { $(id).innerHTML = barkodSvg; });
    ["pQr", "ekranQr"].forEach(function (id) { $(id).innerHTML = qrSvg; });
    $("pKayitKodu").textContent = kod;
    $("kayitKodu").textContent = kod || "kaydedilince veya yazdırılınca oluşur";
  }

  // Bu tutanağın kayıt hali
  function mevcutKayit(durum) {
    return {
      durum: durum,
      no: $("tutanakNo").value,
      kayitKodu: kayitKodu(true),
      tur: $("tur").value,
      tarih: $("tarih").value,
      saat: saatMetni(),
      dizi: $("dizi").value.trim(),
      sirket: $("sirket").value,
      teslimEden: $("teslimEden").value,
      teslimAlan: $("teslimAlan").value,
      satirlar: lines.map(function (l) {
        var s = { barkod: l.barkod, k: l.k, r: l.r, a: l.a, b: l.b, f: fiyatSayi(l.fiyat) };
        if ($("tur").value === "İade") { s.teslimNo = l.teslimNo; s.teslimTarihi = l.teslimTarihi; }
        return s;
      })
    };
  }

  // Aynı no varsa değiştirir, yoksa ekler
  function kayitlariBirlestir(mevcut, gelen) {
    gelen.forEach(function (g) {
      var i = mevcut.findIndex(function (m) { return m.no === g.no; });
      if (i >= 0) mevcut[i] = g; else mevcut.push(g);
    });
    return mevcut;
  }

  // Dizi için eksik ürünler: Teslim edilenler eksi İade edilenler (barkod adedine göre)
  // dizi boşsa tüm diziler hesaba katılır
  function eksikHesapla(kayitlar, dizi) {
    var anahtar = diziAnahtar(dizi);
    var diziKayitlari = kayitlar.filter(function (k) { return k.durum !== "taslak" && (!anahtar || diziAnahtar(k.dizi) === anahtar); });
    var eksik = [];
    diziKayitlari.filter(function (k) { return k.tur === "Teslim"; }).forEach(function (k) {
      k.satirlar.forEach(function (s) {
        eksik.push({ k: s.k, a: s.a, b: s.b, barkod: s.barkod, tarih: k.tarih, no: k.no });
      });
    });
    diziKayitlari.filter(function (k) { return k.tur === "İade"; }).forEach(function (k) {
      k.satirlar.forEach(function (s) {
        var i = eksik.findIndex(function (e) { return e.barkod === s.barkod; });
        if (i >= 0) eksik.splice(i, 1);
      });
    });
    return eksik;
  }

  function eksikSatirlariYaz(tbody, eksik) {
    tbody.textContent = "";
    eksik.forEach(function (e) {
      var tr = document.createElement("tr");
      [e.k, e.a, e.b, e.barkod, e.tarih, e.no].forEach(function (v) { tr.appendChild(td(v)); });
      tbody.appendChild(tr);
    });
  }

  function takipDiziListesi() {
    var sec = $("takipDizi");
    var onceki = sec.value;
    var gorulen = {};
    sec.textContent = "";
    kayitlar.forEach(function (k) {
      var a = diziAnahtar(k.dizi);
      if (!a || gorulen[a]) return;
      gorulen[a] = true;
      var o = document.createElement("option");
      o.value = k.dizi;
      o.textContent = k.dizi;
      sec.appendChild(o);
    });
    var tercih = onceki || $("dizi").value;
    Array.prototype.some.call(sec.options, function (o) {
      if (diziAnahtar(o.value) === diziAnahtar(tercih)) { sec.value = o.value; return true; }
    });
    eksikTablosuGuncelle();
  }

  function eksikTablosuGuncelle() {
    var eksik = eksikHesapla(kayitlar, $("takipDizi").value);
    $("eksikSayi").textContent = "Eksik ürün sayısı: " + eksik.length;
    eksikSatirlariYaz($("eksikTablo").tBodies[0], eksik);
  }

  function indir(dosyaAdi, icerik, tip) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([icerik], { type: tip }));
    a.download = dosyaAdi;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  function csvHucre(v) {
    v = String(v == null ? "" : v);
    return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }

  function bugun() {
    var d = new Date();
    return String(d.getDate()).padStart(2, "0") + "." + String(d.getMonth() + 1).padStart(2, "0") + "." + d.getFullYear();
  }

  function getSayac() {
    var n = parseInt(lsGet(SAYAC_KEY), 10);
    return n >= 0 ? n : 0;
  }

  function yil() {
    var m = /(\d{4})\s*$/.exec($("tarih").value);
    return m ? m[1] : String(new Date().getFullYear());
  }

  function tutanakNo() {
    if (acikNo) return acikNo;
    return yil() + "-" + String(getSayac() + 1).padStart(3, "0");
  }

  function baslikKaydet() {
    var o = {};
    alanlar.forEach(function (id) { o[id] = $(id).value; });
    lsSet(HEADER_KEY, JSON.stringify(o));
  }

  function baslikYukle() {
    var o = {};
    try { o = JSON.parse(lsGet(HEADER_KEY)) || {}; } catch (e) { o = {}; }
    alanlar.forEach(function (id) { $(id).value = o[id] || ""; });
    if (!$("tarih").value) $("tarih").value = bugun();
  }

  function mesaj(metin, tur) {
    var el = $("mesaj");
    el.textContent = metin;
    el.className = tur || "";
  }

  function basliklariGuncelle() {
    $("tutanakNo").value = tutanakNo();
    $("sayac").value = getSayac();
    $("pNo").textContent = $("tutanakNo").value;
    $("pTur").textContent = $("tur").value.toLocaleUpperCase("tr");
    $("satirTablosu").className = $("tur").value === "İade" ? "iade" : "";
    $("pTarih").textContent = $("tarih").value;
    $("pTarih2").textContent = $("tarih").value;
    document.querySelectorAll(".pTarih3").forEach(function (e) { e.textContent = $("tarih").value; });
    $("pDizi").textContent = $("dizi").value;
    $("pSirket").textContent = $("sirket").value;
    $("pEden").textContent = $("teslimEden").value;
    $("pAlan").textContent = $("teslimAlan").value;
    yazdirmaTablosu();
    kodlariCiz();
  }

  function fiyatSayi(t) {
    t = String(t).trim();
    // "1799.9" noktalı ondalık, "1.799,90" Türkçe biçim
    var n = /^\d+\.\d{1,2}$/.test(t) ? parseFloat(t) : parseFloat(t.replace(/\./g, "").replace(",", "."));
    return isNaN(n) ? null : n;
  }

  function para(n) {
    return n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  // Baskı tablosu sütunları; İade tutanağında Renk ve Beden'den sonra teslim bilgisi eklenir
  var TESLIM_SUTUNLARI = [["Sıra", "9mm"], ["Stok Kodu", "24mm"], ["Ürün Açıklaması", ""], ["Renk", "24mm"], ["Beden", "14mm"], ["Adet", "11mm"], ["Güncel Satış Fiyatı (₺)", "22mm"], ["Tutar (₺)", "22mm"]];
  var IADE_SUTUNLARI = [["Sıra", "8mm"], ["Stok Kodu", "21mm"], ["Ürün Açıklaması", ""], ["Renk", "18mm"], ["Beden", "12mm"], ["Teslim No", "17mm"], ["Teslim Tarihi", "19mm"], ["Adet", "9mm"], ["Güncel Satış Fiyatı (₺)", "19mm"], ["Tutar (₺)", "19mm"]];

  // Ürün adından kod, renk ve cinsiyet gibi tabloda zaten yazan kelimeleri çıkarır, uzunu keser
  function kisaAd(l) {
    var ad = (l.n || "").replace(new RegExp(l.k, "gi"), " ");
    if (l.a) ad = ad.replace(new RegExp(l.a, "gi"), " ");
    ad = ad.replace(/\b(erkek|slim fit|regular fit)\b/gi, " ").replace(/\s+/g, " ").trim();
    return ad.length > 40 ? ad.slice(0, 40).replace(/\s+\S*$/, "") + "…" : ad;
  }

  // Baskı tablosu: en az 8 satır, fazlası ikinci sayfaya devam eder
  function yazdirmaTablosu() {
    var iade = $("tur").value === "İade";
    $("pUrunTablo").classList.toggle("dar", iade);
    var sutunlar = iade ? IADE_SUTUNLARI : TESLIM_SUTUNLARI;
    $("pKolonlar").textContent = "";
    $("pBasliklar").textContent = "";
    sutunlar.forEach(function (c) {
      var col = document.createElement("col");
      if (c[1]) col.style.width = c[1];
      $("pKolonlar").appendChild(col);
      var th = document.createElement("th");
      th.textContent = c[0];
      $("pBasliklar").appendChild(th);
    });
    $("pToplamEtiket").colSpan = sutunlar.length - 1;

    var tbody = $("pUrunler");
    tbody.textContent = "";
    var toplam = 0, fiyatVar = false;
    for (var i = 0; i < Math.max(8, lines.length); i++) {
      var l = lines[i];
      var tr = document.createElement("tr");
      var f = l ? fiyatSayi(l.fiyat) : null;
      if (f !== null) { toplam += f; fiyatVar = true; }
      tr.appendChild(td(i + 1, "orta"));
      tr.appendChild(td(l ? l.k : ""));
      tr.appendChild(td(l ? kisaAd(l) : ""));
      tr.appendChild(td(l ? l.a : ""));
      tr.appendChild(td(l ? l.b : "", "orta"));
      if (iade) {
        tr.appendChild(td(l ? l.teslimNo : "", "orta"));
        tr.appendChild(td(l ? l.teslimTarihi : "", "orta"));
      }
      tr.appendChild(td(l ? 1 : "", "orta"));
      tr.appendChild(td(f !== null ? para(f) : "", "sag"));
      tr.appendChild(td(f !== null ? para(f) : "", "sag"));
      tbody.appendChild(tr);
    }
    $("pToplam").textContent = fiyatVar ? para(toplam) : "";
  }

  function td(metin, sinif) {
    var c = document.createElement("td");
    c.textContent = metin;
    if (sinif) c.className = sinif;
    return c;
  }

  function satirlariCiz() {
    var tbody = $("satirlar");
    tbody.textContent = "";
    lines.forEach(function (l, i) {
      var tr = document.createElement("tr");
      tr.appendChild(td(i + 1, "no"));
      [l.k, l.r, l.a, l.b, l.barkod, l.teslimNo, l.teslimTarihi].forEach(function (v, j) { tr.appendChild(td(v, j > 4 ? "iadeSutun" : "")); });
      if (l.bulunamadi) tr.className = "uyari";

      var fiyat = td(l.fiyat, "fiyat");
      fiyat.contentEditable = "true";
      fiyat.addEventListener("input", function () { l.fiyat = fiyat.textContent; yazdirmaTablosu(); otomatikKaydet(); });
      tr.appendChild(fiyat);

      var son = document.createElement("td");
      son.className = "ekran";
      var sil = document.createElement("button");
      sil.type = "button";
      sil.className = "sil";
      sil.textContent = "Sil";
      sil.addEventListener("click", function () {
        lines.splice(i, 1);
        satirlariCiz();
        otomatikKaydet();
        $("barkod").focus();
      });
      son.appendChild(sil);
      tr.appendChild(son);
      tbody.appendChild(tr);
    });
    yazdirmaTablosu();
    kodlariCiz();
    $("ozet").textContent = "Satır sayısı: " + lines.length + "  |  Toplam adet: " + lines.length;
    $("bosSatir").hidden = lines.length > 0;
    $("satirTablosu").hidden = lines.length === 0;
  }

  // İade için: bu barkodu içeren ve henüz iade edilmemiş ilk Teslim kaydı (bu tutanak hariç)
  function teslimKaydiBul(kod) {
    var no = $("tutanakNo").value;
    var diger = kayitlar.filter(function (k) { return k.no !== no; });
    var adaylar = eksikHesapla(diger, $("dizi").value).filter(function (e) { return e.barkod === kod; });
    lines.forEach(function (l) {
      var i = l.barkod === kod && l.teslimNo ? adaylar.findIndex(function (e) { return e.no === l.teslimNo; }) : -1;
      if (i >= 0) adaylar.splice(i, 1);
    });
    return adaylar[0] || null;
  }

  function barkodOkut(kod) {
    var u = VERI[kod];
    if (!u) {
      mesaj("Barkod bulunamadı: " + kod, "hata");
      return;
    }
    var satir = { k: u.k, r: u.r, a: u.a, b: u.b, n: u.n, barkod: kod, fiyat: typeof u.f === "number" ? para(u.f) : "", teslimNo: "", teslimTarihi: "" };
    var ek = "";
    if ($("tur").value === "İade") {
      var teslim = teslimKaydiBul(kod);
      satir.bulunamadi = !teslim;
      if (teslim) {
        satir.teslimNo = teslim.no;
        satir.teslimTarihi = teslim.tarih;
        ek = " / Teslim No: " + teslim.no;
      }
    }
    lines.push(satir);
    if (satir.bulunamadi) mesaj("Bu barkod teslim kaydında yok ya da zaten iade alındı", "hata");
    else mesaj("Eklendi: " + u.k + " / " + u.r + " / " + u.b + ek, "tamam");
    satirlariCiz();
    otomatikKaydet(true);
  }

  // Fotoğraftan okuma: el yazısı stok kodu OCR'ı (ElYazisiOCR). Fotoğraf tarayıcıdan dışarı çıkmaz, ağ isteği yoktur.
  // Dosyalar aynı klasördeki elyazisi/ klasöründen, ilk fotoğrafta tembel yüklenir.
  var elyaziYuklemesi = null;
  function scriptYukle(yol) {
    return new Promise(function (coz, reddet) {
      var etiket = document.createElement("script");
      etiket.src = yol;
      etiket.onload = coz;
      etiket.onerror = function () { reddet(new Error(yol + " yüklenemedi")); };
      document.head.appendChild(etiket);
    });
  }
  function elyaziYukle() {
    if (!elyaziYuklemesi) {
      elyaziYuklemesi = scriptYukle("elyazisi/model.js")
        .then(function () { return scriptYukle("elyazisi/elyazisi-ocr.js"); })
        .catch(function (e) { elyaziYuklemesi = null; throw e; });
    }
    return elyaziYuklemesi;
  }

  var barkodDizini = null;
  function barkodDizinindeAra() {
    if (barkodDizini) return barkodDizini;
    barkodDizini = {};
    Object.keys(VERI).forEach(function (kod) {
      var u = VERI[kod];
      (barkodDizini[u.k] = barkodDizini[u.k] || []).push({ barkod: kod, a: u.a, b: u.b });
    });
    return barkodDizini;
  }

  // OCR'ın geçerli kod listesi: ürün listesindeki benzersiz stok kodları (ilk kullanımda bir kez hazırlanır)
  var elyaziKodlari = null;
  function elyaziKodListesi() {
    if (!elyaziKodlari) elyaziKodlari = Object.keys(barkodDizinindeAra());
    return elyaziKodlari;
  }

  // ---- Onay paneli: "sor" satırları ve birden çok renk/bedeni olan kodlar kullanıcıya sorulur; hiçbir şey sessizce eklenmez
  var ocrDurum = { eklenen: 0, bekleyen: 0, uyari: "", motor: "" };
  var ocrPanel = null;
  function ocrStil(el, css) { el.style.cssText = css; return el; }
  function ocrEleman(etiket, metin, css) {
    var el = document.createElement(etiket);
    if (metin !== undefined && metin !== null) el.textContent = metin;
    if (css) ocrStil(el, css);
    return el;
  }
  function ocrPaneliHazirla() {
    if (!ocrPanel) {
      ocrPanel = document.createElement("div");
      ocrPanel.id = "ocrOnay";
      ocrPanel.className = "ekran";
      var hedef = $("mesaj");
      hedef.parentNode.insertBefore(ocrPanel, hedef.nextSibling);
    }
    return ocrPanel;
  }
  function ocrOzetYaz() {
    var ozet = (ocrDurum.motor ? ocrDurum.motor + ": " : "") + ocrDurum.eklenen + " ürün eklendi, " + ocrDurum.bekleyen + " satır onay bekliyor.";
    if (ocrDurum.uyari) ozet += " " + ocrDurum.uyari;
    mesaj(ozet, ocrDurum.bekleyen ? "hata" : "tamam");
    if (ocrPanel) ocrPanel.hidden = ocrDurum.bekleyen === 0;
  }
  function ocrHucreResmi(goruntu, kutu, yukseklik) {
    var c = document.createElement("canvas");
    if (!goruntu || !goruntu.canvas || !kutu || kutu.w <= 0 || kutu.h <= 0) return c;
    var o = yukseklik / kutu.h;
    c.width = Math.max(1, Math.round(kutu.w * o));
    c.height = yukseklik;
    c.getContext("2d").drawImage(goruntu.canvas, kutu.x, kutu.y, kutu.w, kutu.h, 0, 0, c.width, c.height);
    ocrStil(c, "border:1px solid #d5d8dd;background:#fff;max-width:100%");
    return c;
  }
  function ocrAdetSayi(deger) {
    var n = parseInt(deger, 10);
    return isNaN(n) || n < 1 ? 1 : Math.min(n, 999);
  }
  function ocrSatiriKapat(kutu) {
    if (kutu.parentNode) kutu.parentNode.removeChild(kutu);
    ocrDurum.bekleyen--;
    ocrOzetYaz();
  }
  function ocrBarkodlariEkle(liste, adet) {
    for (var i = 0; i < adet; i++) barkodOkut(liste.barkod);
    ocrDurum.eklenen += adet;
  }

  // Bir stok kodunu adet kadar ekler; birden çok renk/beden varsa panelde seçtirir. Dönüş: eklendiyse true, onay bekliyorsa false.
  function ocrKodEkle(kod, adet, goruntu, satir) {
    var secenekler = barkodDizinindeAra()[kod] || [];
    if (secenekler.length === 0) {
      mesaj("Kod ürün listesinde yok: " + kod, "hata");
      return true;
    }
    if (secenekler.length === 1) {
      ocrBarkodlariEkle(secenekler[0], adet);
      return true;
    }
    ocrVaryantSor(kod, adet, secenekler, goruntu, satir);
    return false;
  }

  function ocrVaryantSor(kod, adet, secenekler, goruntu, satir) {
    var panel = ocrPaneliHazirla();
    var kutu = ocrEleman("div", null, "display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap;border-top:1px solid #d5d8dd;padding:10px 0");
    if (satir) kutu.appendChild(ocrHucreResmi(goruntu, satir.hucreKutusu, 40));
    var sag = ocrEleman("div", null, "flex:1;min-width:200px");
    sag.appendChild(ocrEleman("div", kod + " için renk/beden seçin (adet: " + adet + ")", "font-weight:bold;margin-bottom:6px"));
    secenekler.forEach(function (u) {
      var d = ocrEleman("button", (u.a || "-") + " / " + (u.b || "-"), "margin:0 6px 6px 0");
      d.type = "button";
      d.className = "ikinci";
      d.addEventListener("click", function () {
        ocrBarkodlariEkle(u, adet);
        ocrSatiriKapat(kutu);
      });
      sag.appendChild(d);
    });
    var atla = ocrEleman("button", "Atla", "margin:0 6px 6px 0");
    atla.type = "button";
    atla.addEventListener("click", function () { ocrSatiriKapat(kutu); });
    sag.appendChild(atla);
    kutu.appendChild(sag);
    panel.appendChild(kutu);
    ocrDurum.bekleyen++;
  }

  // "sor" satırı (ya da adedi belirsiz satır): hücre küçük resmi, ilk 3 aday ve "Atla"
  function ocrSatirSor(satir, goruntu) {
    var panel = ocrPaneliHazirla();
    var kutu = ocrEleman("div", null, "display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap;border-top:1px solid #d5d8dd;padding:10px 0");
    var sol = ocrEleman("div", null, "min-width:120px");
    sol.appendChild(ocrEleman("div", "Satır " + satir.sira, "font-size:13px;color:#555;margin-bottom:4px"));
    sol.appendChild(ocrHucreResmi(goruntu, satir.hucreKutusu, 40));
    kutu.appendChild(sol);

    var ortaAdet = ocrEleman("div", null, "min-width:90px");
    ortaAdet.appendChild(ocrEleman("div", "Adet", "font-size:13px;color:#555;margin-bottom:4px"));
    ortaAdet.appendChild(ocrHucreResmi(goruntu, satir.adetKutusu, 28));
    var adetGiris = document.createElement("input");
    adetGiris.type = "number";
    adetGiris.min = "1";
    adetGiris.max = "999";
    // adet okuması belirsizse varsayılan 1 olur (okunan değer notta görünür); kullanıcı düzeltir
    adetGiris.value = String(satir.adet.durum === "sor" ? 1 : ocrAdetSayi(satir.adet.deger));
    ocrStil(adetGiris, "display:block;width:80px;margin-top:4px");
    adetGiris.setAttribute("aria-label", "Adet");
    ortaAdet.appendChild(adetGiris);
    if (satir.adet.durum === "sor") ortaAdet.appendChild(ocrEleman("div", "Adet belirsiz (okunan: " + (satir.adet.ham || "?") + "), kontrol edin", "font-size:12px;color:#b42318;margin-top:2px"));
    kutu.appendChild(ortaAdet);

    var sag = ocrEleman("div", null, "flex:1;min-width:220px");
    var adaylar = (satir.stok.aday || []).slice(0, 3);
    sag.appendChild(ocrEleman("div",
      adaylar.length ? "Okunan: " + (satir.stok.ham || "?") + " - doğru kodu seçin" : "Okunamadı (ham: " + (satir.stok.ham || "-") + ")",
      "font-weight:bold;margin-bottom:6px"));
    adaylar.forEach(function (a) {
      var d = ocrEleman("button", a.kod, "margin:0 6px 6px 0");
      d.type = "button";
      d.className = "ikinci";
      d.addEventListener("click", function () {
        var adet = ocrAdetSayi(adetGiris.value);
        ocrKodEkle(a.kod, adet, goruntu, satir);   // birden çok renk/beden varsa ayrı soru satırı açılır
        ocrSatiriKapat(kutu);
      });
      sag.appendChild(d);
    });
    var hicbiri = ocrEleman("button", adaylar.length ? "Hiçbiri" : "Atla", "margin:0 6px 6px 0");
    hicbiri.type = "button";
    hicbiri.addEventListener("click", function () { ocrSatiriKapat(kutu); });
    sag.appendChild(hicbiri);
    kutu.appendChild(sag);
    panel.appendChild(kutu);
    ocrDurum.bekleyen++;
  }

  function ocrSonucuIsle(goruntu, s, motorAdi) {
    ocrDurum = { eklenen: 0, bekleyen: 0, uyari: "", motor: motorAdi || "" };
    var panel = ocrPaneliHazirla();
    panel.textContent = "";
    panel.appendChild(ocrEleman("div", "Onay bekleyen satırlar", "font-weight:bold;margin-top:8px"));
    panel.hidden = false;
    if (s.uyari && s.uyari.length) ocrDurum.uyari = "Uyarı: " + s.uyari.join("; ") + ".";
    if (!s.satirlar || s.satirlar.length === 0) {
      panel.hidden = true;
      mesaj((motorAdi ? motorAdi + ": " : "") + "Fotoğraftan satır okunamadı." + (ocrDurum.uyari ? " " + ocrDurum.uyari : "") + " Ürünleri elle okutun.", "hata");
      return;
    }
    s.satirlar.forEach(function (satir) {
      if (satir.stok.durum === "bos") return;
      var adetTamam = satir.adet.durum !== "sor" && satir.adet.deger >= 1 && satir.adet.deger <= 99;
      if (satir.stok.durum === "kabul" && adetTamam && satir.stok.secilen) {
        ocrKodEkle(satir.stok.secilen, satir.adet.deger, goruntu, satir);
      } else {
        ocrSatirSor(satir, goruntu);
      }
    });
    ocrOzetYaz();
  }

  // ---- Güçlü OCR motoru (yalnız masaüstü): yerel PaddleOCR servisi, ana süreç üzerinden. Yoksa/hata verirse tarayıcı CNN'i yedektir.
  var GUCLU_AD = "Güçlü motor (PaddleOCR)";
  var YEDEK_AD = "Yedek motor (tarayıcı)";
  var motorBilgi = { var: false, hazir: false, motor: "" };
  var motorDurumEl = null;
  function motorDurumuYaz() {
    var metin = "OCR motoru: " + (motorBilgi.var ? "Güçlü (PaddleOCR)" : "Yedek (tarayıcı)");
    if (motorBilgi.var && motorBilgi.hazir && motorBilgi.motor) metin += " - " + motorBilgi.motor + " hazır";
    else if (motorBilgi.var) metin += " - ilk fotoğrafta başlatılır";
    if (!motorDurumEl) {
      var ayar = $("gor-ayarlar");
      if (!ayar) return;
      var bolum = document.createElement("section");
      bolum.className = "panel";
      var h = document.createElement("h2");
      h.textContent = "OCR motoru";
      motorDurumEl = document.createElement("p");
      motorDurumEl.id = "ocrMotorDurum";
      motorDurumEl.className = "not";
      bolum.appendChild(h);
      bolum.appendChild(motorDurumEl);
      ayar.appendChild(bolum);
    }
    motorDurumEl.textContent = metin;
  }
  function motorDurumuYenile() {
    if (!(BRIDGE && BRIDGE.motorDurum)) { motorDurumuYaz(); return Promise.resolve(motorBilgi); }
    return BRIDGE.motorDurum().then(function (d) {
      if (d && typeof d === "object") motorBilgi = { var: !!d.var, hazir: !!d.hazir, motor: String(d.motor || "") };
      motorDurumuYaz();
      return motorBilgi;
    }, function () { motorBilgi = { var: false, hazir: false, motor: "" }; motorDurumuYaz(); return motorBilgi; });
  }
  motorDurumuYenile();

  function ocrKutuOlcekle(k, sx, sy) {
    if (!k || k.length < 4) return null;
    return { x: Math.round(k[0] * sx), y: Math.round(k[1] * sy), w: Math.max(1, Math.round((k[2] - k[0]) * sx)), h: Math.max(1, Math.round((k[3] - k[1]) * sy)) };
  }
  // Servis kutuları [x0,y0,x1,y1] ve kendi görüntü boyutundadır; onay paneli {x,y,w,h} ve canvas boyutu ister.
  function gucluSonucuHazirla(y, goruntu) {
    var gw = (y.goruntu && y.goruntu.w) || goruntu.width, gh = (y.goruntu && y.goruntu.h) || goruntu.height;
    var sx = goruntu.width / gw, sy = goruntu.height / gh;
    return {
      uyari: Array.isArray(y.uyari) ? y.uyari : [],
      satirlar: (y.satirlar || []).map(function (s) {
        var kopya = {};
        Object.keys(s).forEach(function (a) { kopya[a] = s[a]; });
        kopya.hucreKutusu = ocrKutuOlcekle(s.hucreKutusu, sx, sy);
        kopya.adetKutusu = ocrKutuOlcekle(s.adetKutusu, sx, sy);
        return kopya;
      })
    };
  }
  function gucluOku(goruntu) {
    var u = goruntu.canvas.toDataURL("image/jpeg", 0.92);
    return BRIDGE.gucluOku(u.slice(u.indexOf(",") + 1), elyaziKodListesi()).then(function (y) {
      if (!y || !y.tamam) throw new Error((y && y.hata) || "motordan yanıt gelmedi");
      motorDurumuYenile();
      if (!y.satirlar || y.satirlar.length === 0) { var t = new Error("tablo bulunamadı"); t.tabloYok = true; throw t; }
      ocrSonucuIsle(goruntu, gucluSonucuHazirla(y, goruntu), GUCLU_AD);
    });
  }
  function yedekOku(goruntu, neden) {
    return new Promise(function (coz) { setTimeout(coz, 30); }).then(function () {
      var s = window.ElYazisiOCR.oku(goruntu, elyaziKodListesi());
      if (neden) s.uyari = (s.uyari || []).concat([neden]);
      ocrSonucuIsle(goruntu, s, YEDEK_AD);
    });
  }

  $("fotoGir").addEventListener("change", function () {
    var dosya = this.files && this.files[0];
    if (!dosya) return;
    mesaj("Fotoğraf okunuyor, birkaç saniye sürebilir…", "");
    var gucluVar = !!(BRIDGE && BRIDGE.gucluOku);
    elyaziYukle()
      .then(function () {
        return new Promise(function (coz, reddet) {
          window.ElYazisiOCR.dosyadanGoruntu(dosya, 2000, function (hata, goruntu) { if (hata) reddet(hata); else coz(goruntu); });
        });
      })
      .then(function (goruntu) {
        if (!gucluVar) return yedekOku(goruntu, "");
        return gucluOku(goruntu).catch(function (e) {
          motorDurumuYenile();
          if (e && e.tabloYok) return yedekOku(goruntu, "Güçlü motor tablo bulamadı, yedek motor denendi");
          return yedekOku(goruntu, "güçlü motor kullanılamadı (" + (e && e.message || e) + "), yedek motor kullanıldı");
        });
      })
      .catch(function (e) { mesaj("Fotoğraf okunamadı: " + (e && e.message || e), "hata"); })
      .then(function () { $("fotoGir").value = ""; });
  });

  $("barkod").addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    e.preventDefault();
    var kod = this.value.trim();
    this.value = "";
    if (kod) barkodOkut(kod);
    this.focus();
  });

  alanlar.forEach(function (id) {
    $(id).addEventListener("input", function () {
      baslikKaydet();
      basliklariGuncelle();
      otomatikKaydet();
    });
  });

  // ---- Gezinme: soldaki menü ----
  var GORUNUMLER = ["tutanak", "eksik", "kayitlar", "ayarlar"];
  var GOR_BASLIK = { tutanak: "Sponsorluk Ürün Teslim Tutanağı", eksik: "Eksik ürün takibi", kayitlar: "Kayıtlar ve yedek", ayarlar: "Ayarlar ve rehber" };
  var aktifGor = "tutanak";

  function goster(ad) {
    aktifGor = ad;
    GORUNUMLER.forEach(function (g) { $("gor-" + g).hidden = g !== ad; });
    Array.prototype.forEach.call(document.querySelectorAll(".gezin button"), function (b) {
      if (b.getAttribute("data-gor") === ad) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    $("gorBaslik").textContent = GOR_BASLIK[ad];
    if (ad === "eksik") takipDiziListesi();
    if (ad === "kayitlar") kayitSayfasiGuncelle();
    if (ad === "tutanak") $("barkod").focus();
  }
  Array.prototype.forEach.call(document.querySelectorAll(".gezin button"), function (b) {
    b.addEventListener("click", function () { goster(b.getAttribute("data-gor")); });
  });

  // Barkod okuyucu klavye gibi yazar: odak başka yerdeyse karakterler barkod kutusuna yönlendirilir
  document.addEventListener("keydown", function (e) {
    if (aktifGor !== "tutanak" || !$("rehber").hidden || e.ctrlKey || e.altKey || e.metaKey) return;
    if (!e.key || e.key.length !== 1) return;
    var t = e.target && e.target.tagName;
    if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA" || (e.target && e.target.isContentEditable)) return;
    $("barkod").focus();
  });

  // ---- Kayıtlar ve yedek ekranı ----
  function kayitSayfasiGuncelle() {
    $("kSayi").textContent = String(kayitlar.length);
    $("kSon").textContent = sonOtoKayit || "-";
    $("klasorYolu").textContent = klasor ? klasorYolu : "Bağlı değil";
    $("klasorAc").hidden = !(BRIDGE && BRIDGE.klasoruAc);
    var tbody = $("kayitTablosu").tBodies[0];
    tbody.textContent = "";
    $("kayitBos").hidden = kayitlar.length > 0;
    kayitlar.slice().reverse().forEach(function (k) {
      var tr = document.createElement("tr");
      [k.no, k.tur, k.dizi, k.tarih, k.satirlar.length].forEach(function (v) { tr.appendChild(td(v)); });
      var d = document.createElement("td");
      var e = document.createElement("span");
      e.className = k.durum === "taslak" ? "etiket taslak" : "etiket kayitli";
      e.textContent = k.durum === "taslak" ? "Taslak" : "Kayıtlı";
      d.appendChild(e);
      tr.appendChild(d);
      var son = document.createElement("td");
      var ac = document.createElement("button");
      ac.type = "button";
      ac.className = "ikinci";
      ac.textContent = "Aç";
      ac.addEventListener("click", function () {
        otomatikYaz().then(function () {
          kaydiYukle(k);
          goster("tutanak");
          mesaj("Tutanak açıldı: " + k.no, "tamam");
        });
      });
      son.appendChild(ac);
      tr.appendChild(son);
      tbody.appendChild(tr);
    });
  }

  // ---- Rehber: adım adım, açılışta bir kez ----
  function rehberAdimlari() {
    return [
      { b: "Tutanak Doldurucu'ya hoş geldiniz", m: [
        "Bu program sponsorluk ürün <b>teslim</b> ve <b>iade</b> tutanaklarını hazırlar.",
        "Barkodu okutursunuz, ürün bilgileri kendiliğinden gelir. Sonunda tutanağı PDF olarak kaydedersiniz."] },
      { b: "Soldaki menü", m: [
        "<b>Tutanak</b>: günlük işiniz burada.",
        "<b>Eksik takibi</b>: teslim edilip iadesi gelmeyen ürünler.",
        "<b>Kayıtlar ve yedek</b>: eski tutanaklar, yedek al ve yedek yükle.",
        "<b>Ayarlar ve rehber</b>: sıra numarası ve bu anlatım."] },
      { b: "Kayıtlar kendiliğinden saklanır", m: [
        "Her ürün okuttuğunuzda tutanak otomatik kaydedilir. Bir şey yapmanız gerekmez; program kapansa bile yarım tutanak geri gelir.",
        BRIDGE
          ? "Kayıtlar programın kurulu olduğu klasördeki <b>kayitlar</b> klasörüne yazılır:<br><code>" + esc(klasorYolu || "") + "</code>"
          : "Kayıtlar, <b>Kayıtlar ve yedek</b> menüsünden seçeceğiniz klasörün içindeki <b>kayitlar</b> klasörüne yazılır. Bir kez seçmeniz yeter."] },
      { b: "Tutanağı doldurma", m: [
        "Üstte tarihi, işlem türünü (Teslim ya da İade), diziyi, yapım şirketini ve teslim eden ile alanı yazın.",
        "Barkod kutusuna okuyucuyla okutun. Fotoğraftan okumak için <b>Fotoğraftan oku</b> düğmesini kullanın."] },
      { b: "Kaydet, yazdır, Nebim", m: [
        "<b>Tutanağı kaydet</b> tutanağı kesinleştirir; eksik takibine ancak o zaman işlenir.",
        "<b>PDF olarak kaydet</b> şirket ve karşı taraf nüshalarını hazırlar.",
        "<b>Nebim dosyası indir</b> ürünleri Nebim'e aktarmak için Excel dosyası üretir."] },
      { b: "İade ve eksik takibi", m: [
        "İade tutanağında her ürünün hangi teslim tutanağından geldiği görünür.",
        "Eksik ürünleri <b>Eksik takibi</b> menüsünden dizi dizi görebilir, Excel'e aktarabilirsiniz."] },
      { b: "Yedek", m: [
        "Otomatik kayıtlara ek olarak <b>Kayıtlar ve yedek</b> menüsünden elle <b>Yedek al</b> ve <b>Yedek yükle</b> yapabilirsiniz.",
        "Bu anlatımı istediğiniz zaman <b>Ayarlar ve rehber</b> menüsünden yeniden açabilirsiniz."] }
    ];
  }
  var rehberAdim = 0;
  var rehberListe = [];
  var rehberOncekiOdak = null;

  function rehberCiz() {
    var a = rehberListe[rehberAdim];
    $("rehberAdim").textContent = "Adım " + (rehberAdim + 1) + " / " + rehberListe.length;
    $("rehberBaslik").textContent = a.b;
    $("rehberMetin").innerHTML = a.m.map(function (p) { return "<p>" + p + "</p>"; }).join("");
    var nk = $("rehberNoktalar");
    nk.textContent = "";
    rehberListe.forEach(function (_, i) {
      var s = document.createElement("span");
      if (i === rehberAdim) s.className = "acik";
      nk.appendChild(s);
    });
    $("rehberGeri").hidden = rehberAdim === 0;
    $("rehberIleri").textContent = rehberAdim === rehberListe.length - 1 ? "Başla" : "İleri";
  }
  function rehberiAc() {
    rehberListe = rehberAdimlari();
    rehberAdim = 0;
    rehberOncekiOdak = document.activeElement;
    $("rehberGizle").checked = lsGet(REHBER_KEY) === "1";
    rehberCiz();
    $("rehber").hidden = false;
    $("rehberIleri").focus();
  }
  function rehberiKapat() {
    lsSet(REHBER_KEY, $("rehberGizle").checked ? "1" : "0");
    $("rehberAcilista").checked = !$("rehberGizle").checked;
    $("rehber").hidden = true;
    if (aktifGor === "tutanak") $("barkod").focus();
    else if (rehberOncekiOdak && rehberOncekiOdak.focus) rehberOncekiOdak.focus();
  }
  $("rehberIleri").addEventListener("click", function () {
    if (rehberAdim >= rehberListe.length - 1) { rehberiKapat(); return; }
    rehberAdim++;
    rehberCiz();
  });
  $("rehberGeri").addEventListener("click", function () { if (rehberAdim > 0) { rehberAdim--; rehberCiz(); } });
  $("rehber").addEventListener("keydown", function (e) {
    if (e.key === "Escape") { rehberiKapat(); return; }
    if (e.key !== "Tab") return;
    var odaklar = Array.prototype.filter.call($("rehber").querySelectorAll("button, input"), function (x) { return !x.hidden && !x.disabled; });
    var ilk = odaklar[0], son = odaklar[odaklar.length - 1];
    if (e.shiftKey && document.activeElement === ilk) { e.preventDefault(); son.focus(); }
    else if (!e.shiftKey && document.activeElement === son) { e.preventDefault(); ilk.focus(); }
  });
  $("rehberAc").addEventListener("click", rehberiAc);
  $("rehberAcilista").addEventListener("change", function () { lsSet(REHBER_KEY, this.checked ? "0" : "1"); });

  // ---- Tutanak işlemleri ----
  $("yeniTutanak").addEventListener("click", function () {
    if (sonYazimHatasi && lines.length && !confirm("Son değişiklikler klasöre yazılamadı. Yine de yeni tutanağa geçilsin mi?")) return;
    otomatikYaz().then(function () {
      var vardir = function () { var no = tutanakNo(); return kayitlar.find(function (k) { return k.no === no; }); };
      if (acikNo) {
        // eski bir tutanak açıktı: sıradaki numaraya dön (yarım taslak varsa onu aç)
        acikNo = null;
        var yarim = vardir();
        if (yarim && yarim.durum === "taslak") { kaydiYukle(yarim); goster("tutanak"); mesaj("Sıradaki tutanak açıldı: " + yarim.no, "tamam"); return; }
      } else {
        sayacYaz(getSayac() + 1);
      }
      lines = [];
      var guvenlik = 0;
      while (vardir() && guvenlik++ < 100000) sayacYaz(getSayac() + 1);
      satirlariCiz();
      basliklariGuncelle();
      durumEtiketiGuncelle();
      mesaj("Yeni tutanak hazır. Öncekiler Kayıtlar ve yedek menüsünde.", "");
      $("barkod").focus();
    });
  });

  $("sayacKaydet").addEventListener("click", function () {
    var n = parseInt($("sayac").value, 10);
    if (!(n >= 0)) { mesaj("Geçerli bir sayı girin.", "hata"); return; }
    sayacYaz(n);
    acikNo = null;
    basliklariGuncelle();
    durumEtiketiGuncelle();
    mesaj("Sıra ayarlandı. Sıradaki tutanak: " + $("tutanakNo").value, "tamam");
  });

  $("tur").addEventListener("change", function () { basliklariGuncelle(); otomatikKaydet(); });

  // Baskı anında: saat bilgisayar saatinden, İade ise eksik ürün eki hesaplanır
  function yazdirmaHazirla() {
    kayitKodu(true);
    basliklariGuncelle();
    $("pSaat").textContent = saatMetni();
    document.title = dosyaAdi();
    var iade = $("tur").value === "İade";
    $("pEksik").hidden = !iade;
    if (!iade) return;
    var kayit = mevcutKayit();
    var eksik = eksikHesapla(kayitlariBirlestir(kayitlar.slice(), [kayit]), kayit.dizi);
    $("pEksikNo").textContent = kayit.no;
    $("pEksikDizi").textContent = kayit.dizi;
    $("pEksikYok").hidden = eksik.length > 0;
    $("pEksikTablo").hidden = eksik.length === 0;
    eksikSatirlariYaz($("pEksikTablo").tBodies[0], eksik);
  }

  window.addEventListener("beforeprint", yazdirmaHazirla);

  // İkinci nüsha: birinci sayfanın kopyası, kimlikleri silinmiş, yalnız nüsha yazısı farklı
  function nushaHazirla() {
    document.querySelectorAll(".yazdir.nusha2").forEach(function (e) { e.remove(); });
    document.querySelector(".yazdir .pNusha").textContent = "1 / 2";
    document.querySelector(".yazdir .nNot").textContent = "Şirket nüshası (bizde kalır)";
    if (!$("ikiNusha").checked) return;
    var kopya = document.querySelector(".yazdir").cloneNode(true);
    kopya.classList.add("nusha2");
    kopya.querySelectorAll("[id]").forEach(function (e) { e.removeAttribute("id"); });
    kopya.querySelector(".pNusha").textContent = "2 / 2";
    kopya.querySelector(".nNot").textContent = "Karşı taraf nüshası (teslim alanda kalır)";
    document.querySelector(".yazdir").after(kopya);
  }
  window.addEventListener("beforeprint", nushaHazirla);

  $("yazdir").addEventListener("click", function () {
    yazdirmaHazirla();
    if (BRIDGE && BRIDGE.pdfKaydet) {
      nushaHazirla();
      mesaj("PDF hazırlanıyor…", "");
      BRIDGE.pdfKaydet(dosyaAdi()).then(function (yol) {
        mesaj(yol ? "PDF kaydedildi: " + yol : "PDF kaydı iptal edildi.", yol ? "tamam" : "");
      }).catch(function () { mesaj("PDF kaydedilemedi.", "hata"); });
      return;
    }
    window.print();
  });

  $("kaydet").addEventListener("click", function () {
    var kayit = mevcutKayit("kayitli");
    if (!kayit.dizi) { mesaj("Kaydetmek için dizi adını girin.", "hata"); return; }
    if (!kayit.satirlar.length) { mesaj("Kaydedilecek ürün satırı yok.", "hata"); return; }
    clearTimeout(otoZamani);
    kayitlariSakla(kayitlariBirlestir(kayitlar.slice(), [kayit])).then(function (d) {
      if (d === "hata") { mesaj("Kayıt klasörüne yazılamadı. Klasör izni ya da erişimi kontrol edin.", "hata"); return; }
      sonOtoKayit = saniyeli();
      takipDiziListesi();
      durumEtiketiGuncelle();
      if (klasor) klasoreYaz(kayit.no + ".json", JSON.stringify(kayit, null, 2)).catch(function () { mesaj("Tutanak dosyası klasöre yazılamadı.", "hata"); });
      mesaj(d === "dosya" ? "Kaydedildi: " + kayit.no : "Kaydedildi (yalnızca bu tarayıcıda: Yedek al ile dosyayı kaydetmeyi unutmayın)", "tamam");
    });
  });

  $("takipDizi").addEventListener("change", eksikTablosuGuncelle);

  $("eksikCsv").addEventListener("click", function () {
    var eksik = eksikHesapla(kayitlar, $("takipDizi").value);
    var satirlar = [["Stok Kodu", "Renk", "Beden", "Barkod", "Teslim Tarihi", "Teslim No"]].concat(
      eksik.map(function (e) { return [e.k, e.a, e.b, e.barkod, e.tarih, e.no]; }));
    var csv = "﻿" + satirlar.map(function (s) { return s.map(csvHucre).join(";"); }).join("\r\n") + "\r\n";
    indir("eksik-urunler.csv", csv, "text/csv;charset=utf-8");
  });

  $("nebimIndir").addEventListener("click", function () {
    if (typeof window.nebimIndir !== "function") { mesaj("Nebim dışa aktarma modülü (nebim-xlsx.js) yüklenemedi.", "hata"); return; }
    if (!lines.length) { mesaj("Nebim dosyası için ürün satırı yok.", "hata"); return; }
    window.nebimIndir(lines.map(function (l) { return { k: l.k, r: l.r, b: l.b }; }), dosyaAdi() + ".xlsx");
  });

  $("yedekIndir").addEventListener("click", function () {
    indir("takip-yedek-" + bugun().replace(/\./g, "-") + ".json", kayitMetni(kayitlar), "application/json");
  });

  $("yedekYukle").addEventListener("change", function () {
    var secilen = this.files[0];
    var girdi = this;
    if (!secilen) return;
    secilen.text().then(function (metin) {
      var gelen = kayitlariAyristir(metin);
      return kayitlariSakla(kayitlariBirlestir(kayitlar.slice(), gelen)).then(function (d) {
        if (d === "hata") { mesaj("Yedek klasöre yazılamadı. Klasör izni ya da erişimi kontrol edin.", "hata"); return; }
        takipDiziListesi();
        durumEtiketiGuncelle();
        mesaj("Yedek yüklendi: " + gelen.length + " kayıt işlendi.", "tamam");
      });
    }).catch(function () {
      mesaj("Yedek dosyası okunamadı veya biçimi geçersiz.", "hata");
    }).then(function () { girdi.value = ""; });
  });

  function saatiYaz() {
    $("saat").textContent = new Date().toLocaleTimeString("tr-TR");
  }

  $("klasorBagla").addEventListener("click", klasorBagla);
  if (!DOSYA_DESTEGI || BRIDGE) $("klasorBagla").hidden = true;
  if (BRIDGE && BRIDGE.klasoruAc) $("klasorAc").addEventListener("click", function () { BRIDGE.klasoruAc(); });
  if (BRIDGE && BRIDGE.dogrula) {
    $("imzaPanel").hidden = false;
    $("imzaDogrula").addEventListener("click", function () {
      BRIDGE.dogrula().then(function (r) {
        var s = r.simdi;
        var metin = { tamam: "Tüm kayıtlar doğrulandı (" + s.sayi + " kayıt).", imzasiz: "Kayıtlar henüz imzalanmamış; sonraki kayıtta imzalanacak.", bos: "Henüz kayıt yok.", degismis: "DEĞİŞMİŞ görünüyor: " + s.bozuk.join(", ") }[s.durum];
        $("imzaSonuc").textContent = metin || "";
      }).catch(function () { $("imzaSonuc").textContent = "Doğrulanamadı."; });
    });
  }

  // Sayfa kapanırken bekleyen kayıt varsa hemen yazılır
  window.addEventListener("beforeunload", function () { if (otoZamani) otomatikYaz(); });

  // ---- Açılış ----
  saatiYaz();
  setInterval(saatiYaz, 1000);
  kayitlar = kopyaOku();
  baslikYukle();
  basliklariGuncelle();
  satirlariCiz();
  takipDiziListesi();
  dosyaDurumuYaz();
  durumEtiketiGuncelle();
  $("rehberAcilista").checked = lsGet(REHBER_KEY) !== "1";
  $("yukleniyor").hidden = true;
  goster("tutanak");
  if (lsGet(REHBER_KEY) !== "1") rehberiAc();
  klasoruHatirla().then(function () { if (!klasor) baslangicTutanagi(); durumEtiketiGuncelle(); });
})();
