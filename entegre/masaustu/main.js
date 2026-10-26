// 2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: KOD_DESENI ^T\d{4,5}(-\d{2})?$
// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
// Taban: r2-taban/main.js (değişmeden) + güçlü OCR motoru IPC ekleri (ocr:motorDurum, ocr:gucluOku). Ayrıntı: DEGISIKLIK.md
'use strict';
// Tutanak Doldurucu masaüstü kabuğu. Arayüz app/index.html'de; burada yalnız kayıt klasörü,
// PDF ve pencere işleri var. Renderer'a yol verilmez: yalnız dar bir IPC köprüsü (preload.js) açıktır.
const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const crypto = require('crypto');
const { spawn } = require('child_process');
const readline = require('readline');

const KAYIT_KLASORU = 'kayitlar';
const AD_KURALI = /^(yedekler\/)?[A-Za-z0-9._ -]{1,100}\.json$/;
const AZAMI_BOYUT = 64 * 1024 * 1024;

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  let pencere = null;
  let kayitKlasoru = null;
  let yedekYer = false;

  app.on('second-instance', () => {
    if (pencere) {
      if (pencere.isMinimized()) pencere.restore();
      pencere.focus();
    }
  });

  function yazilabilir(klasor) {
    try {
      fs.mkdirSync(klasor, { recursive: true });
      const deneme = path.join(klasor, '.yazma-denemesi');
      fs.writeFileSync(deneme, 'x');
      fs.unlinkSync(deneme);
      return true;
    } catch (e) { return false; }
  }

  // Kurulu programın bulunduğu klasörün altındaki "kayitlar". Yazılamıyorsa kullanıcı verisi klasörü.
  function klasorBelirle() {
    if (kayitKlasoru) return kayitKlasoru;
    const taban = app.isPackaged ? path.dirname(process.execPath) : __dirname;
    const aday = path.join(taban, KAYIT_KLASORU);
    if (yazilabilir(aday)) kayitKlasoru = aday;
    else {
      kayitKlasoru = path.join(app.getPath('userData'), KAYIT_KLASORU);
      fs.mkdirSync(kayitKlasoru, { recursive: true });
      yedekYer = true;
    }
    return kayitKlasoru;
  }

  // Yalnız uygulamanın kendi yerel sayfasından gelen çağrılar kabul edilir.
  // Tam yol karşılaştırılır: yalnız bu programın kendi app/index.html dosyası kabul edilir.
  const IZINLI_SAYFA = pathToFileURL(path.join(__dirname, 'app', 'index.html')).href;
  function gonderenKontrol(event) {
    const f = event && event.senderFrame;
    const url = f && typeof f.url === 'string' ? f.url : '';
    if (!pencere || event.sender !== pencere.webContents || f !== event.sender.mainFrame) throw new Error('Yetkisiz gönderen');
    if (url.split('#')[0].split('?')[0] !== IZINLI_SAYFA) throw new Error('Yetkisiz gönderen');
  }

  function adCoz(ad) {
    if (typeof ad !== 'string' || !AD_KURALI.test(ad) || ad.includes('..')) throw new Error('Geçersiz dosya adı');
    return path.join(klasorBelirle(), ...ad.split('/'));
  }

  ipcMain.handle('depo:bilgi', (event) => {
    gonderenKontrol(event);
    return { yol: klasorBelirle(), yedekYer, surum: app.getVersion() };
  });

  // Güvenlik kopyası: ana kayıt dosyaları kullanıcı verisi klasörüne de yazılır. Program kaldırılıp
  // yeniden kurulursa kayitlar klasörü boşken buradan geri okunur.
  const KOPYALANAN = ['takip-kayitlari.json', 'ayarlar.json'];
  const kopyaYolu = (ad) => path.join(app.getPath('userData'), 'kayit-kopyasi', ad);

  ipcMain.handle('depo:oku', (event, ad) => {
    gonderenKontrol(event);
    const yol = adCoz(ad);
    try {
      const boyut = fs.statSync(yol).size;
      if (boyut > AZAMI_BOYUT) throw new Error('Dosya çok büyük');
      return fs.readFileSync(yol, 'utf8');
    } catch (e) {
      if (e && e.code === 'ENOENT') {
        if (!KOPYALANAN.includes(ad)) return '';
        try { return fs.readFileSync(kopyaYolu(ad), 'utf8'); } catch (e2) { return ''; }
      }
      throw e;
    }
  });

  // ---- Kayıt imzası ----
  // Her kayıt, bilgisayara özel gizli anahtarla (HMAC-SHA256) imzalanır; imza bir önceki kaydın imzasına bağlıdır
  // (zincir). Anahtar kayitlar klasörünün dışında, kullanıcı verisi klasöründe durur. Kayıt dosyası program dışında
  // elle değiştirilir, kayıt silinir ya da sırası bozulursa doğrulama "değişmiş" der.
  const IMZALI = (ad) => ad === 'takip-kayitlari.json' || /^yedekler\/yedek-[\w.-]+\.json$/.test(ad);
  const anahtarYolu = () => path.join(app.getPath('userData'), 'imza-anahtari.json');
  let anahtarOnbellek = null;
  function anahtarAl() {
    if (anahtarOnbellek) return anahtarOnbellek;
    try {
      anahtarOnbellek = Buffer.from(JSON.parse(fs.readFileSync(anahtarYolu(), 'utf8')).k, 'hex');
      if (anahtarOnbellek.length !== 32) throw new Error('anahtar');
      return anahtarOnbellek;
    } catch (e) {
      if (fs.existsSync(anahtarYolu())) fs.renameSync(anahtarYolu(), anahtarYolu() + '.bozuk-' + Date.now());   // silinmez, kenara alınır
      anahtarOnbellek = crypto.randomBytes(32);
      fs.mkdirSync(path.dirname(anahtarYolu()), { recursive: true });
      fs.writeFileSync(anahtarYolu(), JSON.stringify({ k: anahtarOnbellek.toString('hex'), olusturma: new Date().toISOString() }), { flag: 'wx' });
      return anahtarOnbellek;
    }
  }
  function kanon(v) {
    if (Array.isArray(v)) return '[' + v.map(kanon).join(',') + ']';
    if (v && typeof v === 'object') return '{' + Object.keys(v).sort().map((k) => JSON.stringify(k) + ':' + kanon(v[k])).join(',') + '}';
    return JSON.stringify(v === undefined ? null : v);
  }
  function hmac(govde, onceki) {
    return crypto.createHmac('sha256', anahtarAl()).update(kanon(govde) + '|' + onceki).digest('hex');
  }
  function listeAl(metin) {
    const o = JSON.parse(metin);
    return Array.isArray(o) ? { liste: o, ust: {} } : { liste: o.kayitlar, ust: o };
  }
  function imzaliMetin(metin) {
    let r;
    try { r = listeAl(metin); } catch (e) { return metin; }
    if (!Array.isArray(r.liste)) return metin;
    let onceki = '';
    const imzali = r.liste.map((k) => {
      const govde = Object.assign({}, k); delete govde.imza;
      const h = hmac(govde, onceki); onceki = h;
      return Object.assign({}, govde, { imza: h });
    });
    const ozet = { sayi: imzali.length, son: onceki };
    return JSON.stringify({ kayitlar: imzali, imzaBilgisi: { surum: 1, algoritma: 'HMAC-SHA256', sayi: ozet.sayi, son: ozet.son, imza: hmac(ozet, 'ozet') } }, null, 2);
  }
  const HEX64 = /^[0-9a-f]{64}$/;
  const imzaEsit = (a, b) => typeof a === 'string' && HEX64.test(a) && crypto.timingSafeEqual(Buffer.from(a, 'hex'), Buffer.from(b, 'hex'));
  // durum: tamam | imzasiz (eski, imzalanmamış kayıtlar) | degismis | bos
  function dogrulaMetin(metin) {
    if (!metin || !metin.trim()) return { durum: 'bos', sayi: 0, bozuk: [] };
    let r;
    try { r = listeAl(metin); } catch (e) { return { durum: 'degismis', sayi: 0, bozuk: ['dosya okunamadı'] }; }
    if (!Array.isArray(r.liste)) return { durum: 'degismis', sayi: 0, bozuk: ['dosya biçimi'] };
    const b = r.ust && r.ust.imzaBilgisi;
    if (!r.liste.length) {
      if (b && b.sayi > 0) return { durum: 'degismis', sayi: 0, bozuk: ['tüm kayıtlar silinmiş'] };
      return { durum: 'bos', sayi: 0, bozuk: [] };
    }
    if (!r.liste.some((k) => k && k.imza)) {
      if (b) return { durum: 'degismis', sayi: r.liste.length, bozuk: ['imzalar silinmiş'] };
      return { durum: 'imzasiz', sayi: r.liste.length, bozuk: [] };
    }
    const bozuk = [];
    let onceki = '';
    r.liste.forEach((k, i) => {
      const no = (k && k.no) || ('#' + (i + 1));
      if (!k || typeof k.imza !== 'string' || !HEX64.test(k.imza)) { bozuk.push(no); onceki = ''; return; }
      const govde = Object.assign({}, k); delete govde.imza;
      if (!imzaEsit(k.imza, hmac(govde, onceki))) bozuk.push(no);
      onceki = k.imza;
    });
    // Özet (kayıt sayısı + son imza) de imzalıdır: son kaydı silip özeti elle düzeltmek işe yaramaz.
    const ozetTamam = !!b && b.sayi === r.liste.length && b.son === onceki && imzaEsit(b.imza, hmac({ sayi: b.sayi, son: b.son }, 'ozet'));
    if (!ozetTamam) bozuk.push('kayıt sayısı, sıra ya da özet imzası (silinmiş kayıt olabilir)');
    return { durum: bozuk.length ? 'degismis' : 'tamam', sayi: r.liste.length, bozuk };
  }
  function gunluge(satir) {
    try {
      fs.mkdirSync(app.getPath('userData'), { recursive: true });
      fs.appendFileSync(path.join(app.getPath('userData'), 'imza-gunlugu.log'), new Date().toISOString() + ' ' + satir + '\n', 'utf8');
    } catch (e) { /* günlük yazılamazsa doğrulama yine çalışır */ }
  }
  let oturumBasiSonuc = null;   // bu oturumda ilk yazmadan ÖNCE diskteki kayıt dosyasının durumu

  function diskteDogrula() {
    let metin = '';
    try { metin = fs.readFileSync(adCoz('takip-kayitlari.json'), 'utf8'); } catch (e) { metin = ''; }
    return dogrulaMetin(metin);
  }

  ipcMain.handle('depo:dogrula', (event) => {
    gonderenKontrol(event);
    if (!oturumBasiSonuc) oturumBasiSonuc = diskteDogrula();
    const simdi = diskteDogrula();
    if (simdi.durum === 'degismis') gunluge('degismis ' + JSON.stringify(simdi.bozuk));
    return { oturumBasi: oturumBasiSonuc, simdi };
  });

  // Yeniden kurulumdan sonra kayitlar klasöründe kalan dosyaları tarar: imzası geçerli olanların kayıtları
  // doğrudan, geçersiz ya da imzasız olanlar kullanıcı onayıyla (depo:icAl) hafızaya alınır.
  function dosyaListesi() {
    const dir = klasorBelirle();
    const adlar = ['takip-kayitlari.json'];
    try {
      fs.readdirSync(path.join(dir, 'yedekler')).filter((a) => /^yedek-[\w.-]+\.json$/.test(a)).sort().forEach((a) => adlar.push('yedekler/' + a));
    } catch (e) { /* yedek klasörü yoksa yalnız ana dosya */ }
    return adlar;
  }
  function dosyaIncele(ad) {
    let metin = '';
    try { metin = fs.readFileSync(adCoz(ad), 'utf8'); } catch (e) { return null; }
    const d = dogrulaMetin(metin);
    let liste = [];
    try { const r = listeAl(metin); if (Array.isArray(r.liste)) liste = r.liste.map((k) => { const g = Object.assign({}, k); delete g.imza; return g; }); } catch (e) { liste = []; }
    return { ad, durum: d.durum, bozuk: d.bozuk, sayi: d.sayi, liste };
  }
  ipcMain.handle('depo:tara', (event) => {
    gonderenKontrol(event);
    return dosyaListesi().map(dosyaIncele).filter(Boolean);
  });
  ipcMain.handle('depo:icAl', (event, ad) => {
    gonderenKontrol(event);
    if (!dosyaListesi().includes(ad)) throw new Error('Geçersiz dosya');
    const s = dosyaIncele(ad);
    gunluge('icAl ' + ad + ' ' + (s ? s.durum : 'yok'));
    return s;
  });

  // Önce geçici dosyaya yazılır, sonra yerine taşınır: yarım yazılmış kayıt dosyası oluşmaz.
  ipcMain.handle('depo:yaz', (event, ad, metin) => {
    gonderenKontrol(event);
    if (typeof metin !== 'string' || Buffer.byteLength(metin) > AZAMI_BOYUT) throw new Error('Geçersiz içerik');
    const yol = adCoz(ad);
    // İlk yazmadan önce diskteki dosya doğrulanır: elle değiştirilmişse yeniden imzalanıp gizlenmeden kayda geçer.
    if (ad === 'takip-kayitlari.json' && !oturumBasiSonuc) {
      oturumBasiSonuc = diskteDogrula();
      if (oturumBasiSonuc.durum === 'degismis') gunluge('degismis (oturum basi) ' + JSON.stringify(oturumBasiSonuc.bozuk));
    }
    // Aynı günün yedeği daha çok kayıt içeriyorsa ezilmez, yanına ".onceki" adıyla kenara alınır (silme yok).
    if (/^yedekler\//.test(ad) && fs.existsSync(yol)) {
      try {
        const eskiSayi = listeAl(fs.readFileSync(yol, 'utf8')).liste.length;
        const yeniSayi = listeAl(metin).liste.length;
        if (eskiSayi > yeniSayi) fs.renameSync(yol, yol.replace(/\.json$/, '.onceki-' + Date.now() + '.json'));
      } catch (e) { /* okunamayan eski yedek: normal yazım sürer */ }
    }
    if (IMZALI(ad)) metin = imzaliMetin(metin);
    fs.mkdirSync(path.dirname(yol), { recursive: true });
    const gecici = yol + '.tmp';
    fs.writeFileSync(gecici, metin, 'utf8');
    fs.renameSync(gecici, yol);
    if (KOPYALANAN.includes(ad)) {
      try {
        fs.mkdirSync(path.dirname(kopyaYolu(ad)), { recursive: true });
        fs.writeFileSync(kopyaYolu(ad), metin, 'utf8');
      } catch (e) { /* kopya yazılamazsa asıl kayıt yine de geçerli */ }
    }
    return true;
  });

  ipcMain.handle('depo:klasoruAc', async (event) => {
    gonderenKontrol(event);
    await shell.openPath(klasorBelirle());
    return true;
  });

  // Yazdırma görünümünü (nüsha dahil) PDF yapar; kayit klasörü altındaki pdf klasörü önerilir.
  ipcMain.handle('depo:pdfKaydet', async (event, ad) => {
    gonderenKontrol(event);
    const temiz = String(ad || 'Tutanak').replace(/[\\/:*?"<>|]/g, '-').replace(/\s+/g, ' ').trim().slice(0, 120) || 'Tutanak';
    const klasor = path.join(klasorBelirle(), 'pdf');
    fs.mkdirSync(klasor, { recursive: true });
    const secim = await dialog.showSaveDialog(pencere, {
      title: 'Tutanağı PDF olarak kaydet',
      defaultPath: path.join(klasor, temiz + '.pdf'),
      filters: [{ name: 'PDF', extensions: ['pdf'] }]
    });
    if (secim.canceled || !secim.filePath) return '';
    const veri = await event.sender.printToPDF({ preferCSSPageSize: true, printBackground: true });
    fs.writeFileSync(secim.filePath, veri);
    return secim.filePath;
  });

  // ---- Güçlü OCR motoru: yerel Python PaddleOCR servisi (motor/PROTOKOL.md), stdin/stdout satır başına bir JSON ----
  // Servis ilk istekte (tembel) başlar; çökerse bir sonraki istekte yeniden başlatılır. Ağ yoktur.
  const MOTOR_HAZIR_ZAMAN = 120000;
  const MOTOR_OKU_ZAMAN = 180000;
  const AZAMI_FOTO = 20 * 1024 * 1024;
  const AZAMI_KOD = 15000;                       // ürün listesi ~13.100 kod
  const KOD_DESENI = /^T\d{4,5}(-\d{2})?$/;         // servise yalnız biçime uyan kodlar gider
  const VARSAYILAN_PYTHON = 'D:\\Programlar\\El-Yazisi-OCR\\venv\\Scripts\\python.exe';
  // motor.json'daki python yolu: mutlak, python(.exe) ile biten, var olan bir dosya olmalı
  function pythonYoluGecerli(p) {
    return typeof p === 'string' && path.isAbsolute(p) && /(^|[\\/])python(w|3(\.\d+)?)?(\.exe)?$/i.test(p) && fs.existsSync(p);
  }

  function motorKlasoru() {
    const adaylar = [];
    if (app.isPackaged) adaylar.push(path.join(path.dirname(process.execPath), 'motor'));
    adaylar.push(path.join(__dirname, '..', '..', 'motor'));
    return adaylar.find((a) => { try { return fs.statSync(a).isDirectory(); } catch (e) { return false; } }) || null;
  }
  function komutBol(s) {
    const o = []; const re = /"([^"]*)"|(\S+)/g; let m;
    while ((m = re.exec(s))) o.push(m[1] !== undefined ? m[1] : m[2]);
    return o;
  }
  // Dönüş: { komut, args, cwd } ya da motor yoksa null
  function motorKomutu() {
    const klasor = motorKlasoru();
    const cwd = klasor || __dirname;
    // Test kancası: yalnız paketlenmemiş (geliştirme) sürümde ve TUTANAK_TEST=1 ile. Paketli sürümde yok sayılır
    // (güvenlik incelemesi 25.10: aksi halde ortam değişkeniyle keyfi komut çalıştırılabilirdi).
    const ortam = process.env.TUTANAK_MOTOR_KOMUT;
    if (!app.isPackaged && process.env.TUTANAK_TEST === '1' && ortam && ortam.trim()) {
      const p = komutBol(ortam);
      return p.length ? { komut: p[0], args: p.slice(1), cwd } : null;
    }
    if (!klasor) return null;
    const betik = path.join(klasor, 'paddle_motor.py');
    if (!fs.existsSync(betik)) return null;
    let python = VARSAYILAN_PYTHON;
    try {
      const j = JSON.parse(fs.readFileSync(path.join(klasor, 'motor.json'), 'utf8'));
      if (j && pythonYoluGecerli(j.python)) python = j.python;
    } catch (e) { /* motor.json yoksa varsayılan */ }
    if (!pythonYoluGecerli(python)) return null;
    return { komut: python, args: [betik, '--servis'], cwd };
  }

  const motor = { proc: null, hazirSoz: null, bilgi: null, bekleyen: new Map(), sayac: 0, kapaniyor: false, gunluk: '' };
  const gecici = () => path.join(app.getPath('userData'), 'ocr-gecici');

  function motorYaz(nesne) {
    if (!motor.proc || !motor.proc.stdin.writable) throw new Error('Motor çalışmıyor');
    motor.proc.stdin.write(JSON.stringify(nesne) + '\n');
  }
  function motorBaslat() {
    if (motor.proc && motor.hazirSoz) return motor.hazirSoz;
    const k = motorKomutu();
    if (!k) return Promise.reject(new Error('Güçlü OCR motoru bulunamadı'));
    fs.mkdirSync(gecici(), { recursive: true });
    const env = Object.assign({}, process.env, { PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK: 'True', PYTHONIOENCODING: 'utf-8' });
    const proc = spawn(k.komut, k.args, { cwd: k.cwd, env, stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true });
    motor.proc = proc; motor.bilgi = null; motor.gunluk = '';
    motor.hazirSoz = new Promise((coz, reddet) => {
      let bitti = false;
      const zaman = setTimeout(() => { if (!bitti) { bitti = true; reddet(new Error('Motor 120 sn içinde hazır olmadı')); try { proc.kill(); } catch (e) { /* zaten kapalı */ } } }, MOTOR_HAZIR_ZAMAN);
      const bitir = (hata, bilgi) => { if (bitti) return; bitti = true; clearTimeout(zaman); if (hata) reddet(hata); else coz(bilgi); };
      readline.createInterface({ input: proc.stdout, crlfDelay: Infinity }).on('line', (satir) => {
        let m; try { m = JSON.parse(satir); } catch (e) { return; }
        if (!m || typeof m !== 'object') return;
        if (m.olay === 'hazir') {
          motor.bilgi = { motor: String(m.motor || ''), surum: String(m.surum || '') };
          try { motorYaz({ islem: 'kok', yol: gecici() }); } catch (e) { /* çıkış olayı yakalar */ }
          bitir(null, motor.bilgi);
        } else if (m.olay === 'hata') {
          bitir(new Error('Motor başlatılamadı: ' + String(m.mesaj || '')));
        } else if (m.id !== undefined && motor.bekleyen.has(m.id)) {
          const b = motor.bekleyen.get(m.id); motor.bekleyen.delete(m.id); clearTimeout(b.zaman); b.coz(m);
        }
      });
      proc.stderr.on('data', (d) => { motor.gunluk = (motor.gunluk + d.toString('utf8')).slice(-4000); });
      proc.stdin.on('error', () => { /* süreç kapanmış olabilir; exit olayı ele alır */ });
      proc.on('error', (e) => bitir(new Error('Motor başlatılamadı: ' + e.message)));
      proc.on('exit', (kod) => {
        if (motor.proc === proc) { motor.proc = null; motor.hazirSoz = null; motor.bilgi = null; }
        const hata = new Error('Motor kapandı (kod ' + kod + ')');
        bitir(hata);
        motor.bekleyen.forEach((b) => { clearTimeout(b.zaman); b.reddet(hata); });
        motor.bekleyen.clear();
      });
    });
    motor.hazirSoz.catch(() => { /* çağıran ele alır; yeniden denemede yeni süreç başlar */ });
    return motor.hazirSoz;
  }
  function motorIstek(nesne, zamanAsimi) {
    return new Promise((coz, reddet) => {
      const id = 'i' + (++motor.sayac);
      const zaman = setTimeout(() => { motor.bekleyen.delete(id); reddet(new Error('Motor yanıt vermedi (zaman aşımı)')); }, zamanAsimi);
      motor.bekleyen.set(id, { coz, reddet, zaman });
      try { motorYaz(Object.assign({ id }, nesne)); } catch (e) { clearTimeout(zaman); motor.bekleyen.delete(id); reddet(e); }
    });
  }

  ipcMain.handle('ocr:motorDurum', (event) => {
    gonderenKontrol(event);
    return { var: motorKomutu() !== null, motor: motor.bilgi ? motor.bilgi.motor : '', hazir: !!(motor.proc && motor.bilgi) };
  });

  ipcMain.handle('ocr:gucluOku', async (event, base64, kodlar) => {
    gonderenKontrol(event);
    if (typeof base64 !== 'string' || base64.length === 0 || base64.length > Math.ceil(AZAMI_FOTO / 3) * 4 + 4) throw new Error('Geçersiz fotoğraf');
    if (!Array.isArray(kodlar) || kodlar.length > AZAMI_KOD || !kodlar.every((x) => typeof x === 'string' && x.length <= 64)) throw new Error('Geçersiz kod listesi');
    // Servise yalnız biçime uyan kodlar gider (ek süzgeç; servis de kendi süzer)
    kodlar = kodlar.filter((x) => KOD_DESENI.test(x));
    const veri = Buffer.from(base64, 'base64');
    if (veri.length === 0 || veri.length > AZAMI_FOTO) throw new Error('Geçersiz fotoğraf boyutu');
    const png = veri.length > 4 && veri.readUInt32BE(0) === 0x89504e47;
    const jpg = veri.length > 3 && veri[0] === 0xff && veri[1] === 0xd8 && veri[2] === 0xff;
    if (!png && !jpg) throw new Error('Yalnız PNG ya da JPEG kabul edilir');
    fs.mkdirSync(gecici(), { recursive: true });
    const dosya = path.join(gecici(), crypto.randomBytes(12).toString('hex') + (png ? '.png' : '.jpg'));
    fs.writeFileSync(dosya, veri);
    try {
      await motorBaslat();
      return await motorIstek({ islem: 'oku', foto: dosya, kodlar, en_buyuk_kenar: 2000 }, MOTOR_OKU_ZAMAN);
    } finally {
      try { fs.unlinkSync(dosya); } catch (e) { /* geçici dosya zaten yok */ }
    }
  });

  // Çıkışta servise "kapat" gönderilir; 3 sn içinde kapanmazsa sonlandırılır.
  app.on('before-quit', (e) => {
    if (!motor.proc || motor.kapaniyor) return;
    e.preventDefault();
    motor.kapaniyor = true;
    const p = motor.proc;
    const bitir = () => { try { p.kill(); } catch (x) { /* kapalı */ } app.quit(); };
    p.once('exit', () => app.quit());
    try { p.stdin.write(JSON.stringify({ islem: 'kapat' }) + '\n'); } catch (x) { /* süreç gitmiş */ }
    setTimeout(bitir, 3000);
  });

  function olustur() {
    pencere = new BrowserWindow({
      width: 1280, height: 860, minWidth: 900, minHeight: 600,
      title: 'Tutanak Doldurucu',
      backgroundColor: '#f1f5f9',
      icon: path.join(__dirname, 'build', 'icon.png'),
      show: false,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
        webSecurity: true,
        spellcheck: false
      }
    });
    pencere.once('ready-to-show', () => pencere.show());
    // Program kamera, mikrofon, konum vb. izin istemez (fotoğraf dosyadan seçilir): hepsi kapalı.
    const oturum = pencere.webContents.session;
    oturum.setPermissionRequestHandler((wc, izin, geriCagri) => geriCagri(false));
    oturum.setPermissionCheckHandler(() => false);
    // Dış adrese gidiş ve yeni pencere engellenir
    pencere.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    pencere.webContents.on('will-navigate', (e) => e.preventDefault());
    pencere.loadFile(path.join(__dirname, 'app', 'index.html'));
    pencere.on('closed', () => { pencere = null; });
  }

  app.whenReady().then(() => {
    Menu.setApplicationMenu(null);
    olustur();
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) olustur(); });
  });

  app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
}
