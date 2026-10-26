// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
// Electron + güçlü OCR motoru entegrasyon testi (Playwright _electron).
// Varsayılan: sahte servis (test/sahte_motor.py). TEST_GERCEK=1 ise motor/paddle_motor.py (motor.json / varsayılan python) kullanılır.
// Çalıştırma: node test/electron.motor.test.js   (önce npm run kopyala)
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

let pw;
try { pw = require('playwright'); } catch (e) { pw = require('D:/YusufII/Projeler/agentmom/node_modules/playwright-core'); }
const { _electron } = pw;

const ROOT = path.join(__dirname, '..');
const FOTO = path.join(ROOT, '..', '..', 'ornekler', 'tutanak-1.jpg');
const GERCEK = process.env.TEST_GERCEK === '1';
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'tutanak-test-'));
const userData = path.join(tmp, 'userData');
const pidDosya = path.join(tmp, 'sahte.pid');

const sonuc = [];
function kontrol(ad, tamam, ayrinti) {
  sonuc.push(tamam);
  console.log((tamam ? 'GEÇTİ ' : 'KALDI ') + ad + (ayrinti !== undefined ? ' :: ' + ayrinti : ''));
}

async function ac(komut) {
  const env = Object.assign({}, process.env);
  env.TUTANAK_TEST = '1';   // test kancası yalnız bu bayrakla ve paketlenmemiş sürümde açılır (ocr-main.js motorKomutu)
  if (komut) env.TUTANAK_MOTOR_KOMUT = komut;
  else if (!GERCEK) {
    env.TUTANAK_MOTOR_KOMUT = 'python "' + path.join(__dirname, 'sahte_motor.py') + '" --servis';
    env.TUTANAK_SAHTE_PID = pidDosya;
  } else delete env.TUTANAK_MOTOR_KOMUT;
  const app = await _electron.launch({
    executablePath: path.join(ROOT, 'node_modules', 'electron', 'dist', 'electron.exe'),
    args: ['--user-data-dir=' + userData, ROOT], cwd: ROOT, env
  });
  const w = await app.firstWindow();
  return { app, w };
}

async function fotoOku(w, onceki) {
  await w.evaluate(() => { document.getElementById('mesaj').textContent = ''; });
  await (await w.$('#fotoGir')).setInputFiles(FOTO);
  await w.waitForFunction(() => /ürün eklendi|okunamadı/.test(document.getElementById('mesaj').textContent), null, { timeout: 240000 });
  return w.textContent('#mesaj');
}

(async () => {
  const { app, w } = await ac();
  const hatalar = [];
  const istekler = [];
  w.on('pageerror', (e) => hatalar.push('PAGEERR ' + e.message));
  w.on('console', (m) => { if (m.type() === 'error') hatalar.push('CONSOLE ' + m.text()); });
  w.on('request', (r) => istekler.push(r.url()));

  await w.waitForSelector('#rehber:not([hidden])', { timeout: 30000 }).catch(() => {});
  if (await w.$eval('#rehber', (e) => !e.hidden).catch(() => false)) {
    await w.check('#rehberGizle');
    for (let i = 0; i < 8 && (await w.$eval('#rehber', (e) => !e.hidden)); i++) await w.click('#rehberIleri');
  }
  await w.waitForTimeout(500);

  const kopru = await w.evaluate(() => Object.keys(window.masaustu));
  kontrol('köprüde motorDurum ve gucluOku var', kopru.includes('motorDurum') && kopru.includes('gucluOku'), kopru.join(','));
  const d0 = await w.evaluate(() => window.masaustu.motorDurum());
  kontrol('motorDurum var:true, hazır değil (tembel)', d0.var === true && d0.hazir === false, JSON.stringify(d0));

  // 1. okuma
  const m1 = await fotoOku(w);
  console.log('mesaj:', m1);
  kontrol('mesajda "Güçlü" geçiyor', /Güçlü/.test(m1));
  const panel = await w.evaluate(() => {
    const p = document.getElementById('ocrOnay');
    if (!p || p.hidden) return { gorunur: false, satir: 0, sorMetni: [] };
    const satirlar = Array.prototype.slice.call(p.children).slice(1);
    return { gorunur: true, satir: satirlar.length, sorMetni: satirlar.map((s) => s.textContent.slice(0, 80)) };
  });
  console.log('onay paneli:', JSON.stringify(panel));
  kontrol('onay paneli sor satırlarını gösteriyor (>=3)', panel.gorunur && panel.satir >= 3, 'satır=' + panel.satir);
  const eklenen = parseInt((m1.match(/(\d+) ürün eklendi/) || [])[1], 10);
  // Her stok kodunun birden çok renk/beden barkodu var: kabul satırları önce renk/beden sorusuna düşer (hiçbir şey sessizce eklenmez)
  const varyant = panel.sorMetni.filter((t) => /renk\/beden seçin/.test(t)).length;
  const sor = panel.sorMetni.filter((t) => /doğru kodu seçin|Okunamadı/.test(t)).length;
  if (!GERCEK) kontrol('5 kabul satırı renk/beden sorusuna, 3 sor satırı aday seçimine düştü', varyant + eklenen === 5 && sor === 3, 'eklenen=' + eklenen + ' varyant=' + varyant + ' sor=' + sor);
  else kontrol('gerçek motor: her satır ya renk/beden sorusuna ya aday seçimine düştü, sessiz ekleme yok', eklenen === 0 && varyant + sor >= 1, 'eklenen=' + eklenen + ' varyant=' + varyant + ' sor=' + sor);
  kontrol('bekleyen sayısı mesajda (>=3)', parseInt((m1.match(/(\d+) satır onay bekliyor/) || [])[1], 10) >= 3);
  const d1 = await w.evaluate(() => window.masaustu.motorDurum());
  kontrol('okumadan sonra motor hazır', d1.hazir === true && /\S/.test(d1.motor), JSON.stringify(d1));

  // Ayarlar durumu
  await w.click('[data-gor="ayarlar"]');
  const durumMetni = await w.textContent('#ocrMotorDurum');
  kontrol('ayarlarda motor durumu "Güçlü"', /OCR motoru: Güçlü/.test(durumMetni), durumMetni);

  // geçici dosya temizliği
  const geciciKlasor = path.join(userData, 'ocr-gecici');
  const kalan = fs.existsSync(geciciKlasor) ? fs.readdirSync(geciciKlasor) : [];
  kontrol('geçici fotoğraf silindi', kalan.length === 0, JSON.stringify(kalan));

  // IPC güvenliği
  const red = (p) => p.then(() => 'KABUL', (e) => 'reddedildi: ' + String(e && e.message).slice(0, 80));
  const r1 = await w.evaluate(() => window.masaustu.gucluOku('AAAA', []).then(() => 'KABUL', (e) => 'reddedildi: ' + String(e && e.message).slice(0, 80)));
  kontrol('geçersiz imza reddedilir', /^reddedildi/.test(r1), r1);
  const r2 = await w.evaluate(() => window.masaustu.gucluOku('A'.repeat(34 * 1024 * 1024), []).then(() => 'KABUL', (e) => 'reddedildi: ' + String(e && e.message).slice(0, 80)));
  kontrol('25 MB üstü base64 reddedilir', /^reddedildi/.test(r2), r2);
  const r3 = await w.evaluate(() => window.masaustu.gucluOku('/9j/4AAQ', new Array(20001).fill('T1')).then(() => 'KABUL', (e) => 'reddedildi: ' + String(e && e.message).slice(0, 80)));
  kontrol('20.001 elemanlı kod listesi reddedilir', /^reddedildi/.test(r3), r3);

  // Servisi öldür, ikinci okumada yeniden başlasın
  if (!GERCEK) {
    const pid1 = parseInt(fs.readFileSync(pidDosya, 'utf8'), 10);
    process.kill(pid1);
    await w.waitForTimeout(1500);
    const dOlu = await w.evaluate(() => window.masaustu.motorDurum());
    kontrol('servis öldürüldü, hazır:false', dOlu.hazir === false, JSON.stringify(dOlu));
    const m2 = await fotoOku(w);
    console.log('2. mesaj:', m2);
    const pid2 = parseInt(fs.readFileSync(pidDosya, 'utf8'), 10);
    kontrol('ikinci okumada servis yeniden başladı (yeni pid)', pid2 !== pid1 && /Güçlü/.test(m2), pid1 + ' -> ' + pid2);
  }

  const harici = istekler.filter((u) => !/^(file:|data:|blob:|devtools:)/.test(u));
  kontrol('harici ağ isteği 0', harici.length === 0, JSON.stringify(harici.slice(0, 5)) + ' toplam=' + istekler.length);
  kontrol('konsol/pageerror 0', hatalar.length === 0, JSON.stringify(hatalar.slice(0, 5)));

  // Çıkışta servis kapanmalı
  let pidSon = null;
  if (!GERCEK) pidSon = parseInt(fs.readFileSync(pidDosya, 'utf8'), 10);
  await app.close();
  if (pidSon) {
    await new Promise((r) => setTimeout(r, 1500));
    let yasiyor = true;
    try { process.kill(pidSon, 0); } catch (e) { yasiyor = false; }
    kontrol('uygulama kapanınca servis de kapandı', !yasiyor);
  }


  // Motor yok: var olmayan komut -> hata yakalanır, CNN yedeği çalışır
  if (!GERCEK) {
    const { app: a2, w: w2 } = await ac('python yok_boyle_dosya.py');
    const h2 = [];
    w2.on('pageerror', (e) => h2.push(String(e)));
    w2.on('console', (m) => { if (m.type() === 'error') h2.push(m.text()); });
    await w2.waitForSelector('#rehber:not([hidden])', { timeout: 30000 }).catch(() => {});
    if (await w2.$eval('#rehber', (e) => !e.hidden).catch(() => false)) {
      await w2.check('#rehberGizle');
      for (let i = 0; i < 8 && (await w2.$eval('#rehber', (e) => !e.hidden)); i++) await w2.click('#rehberIleri');
    }
    const ym = await fotoOku(w2);
    console.log('yedek mesaj:', ym);
    kontrol('motor yok: yedek motor çalıştı, mesajda "yedek motor", konsol hatası 0', /[Yy]edek motor/.test(ym) && h2.length === 0, JSON.stringify(h2.slice(0, 3)));
    await a2.close();
  }

  const kalanlar = sonuc.filter((x) => !x).length;
  console.log(kalanlar ? 'SONUÇ: ' + kalanlar + ' KALDI' : 'SONUÇ: HEPSİ GEÇTİ (' + sonuc.length + ')');
  process.exit(kalanlar ? 1 : 0);
})().catch((e) => { console.error('FAIL', e); process.exit(1); });
