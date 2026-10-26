# DEGISIKLIK: r2-taban'a göre güçlü OCR motoru eklemeleri
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

## Teslim dosyaları ve nereye konur
| Dosya (bu klasör) | Gerçek depoda yerine geçtiği dosya |
|---|---|
| ocr-main.js | main.js (r2-taban/main.js + motor ekleri) |
| ocr-preload.js | preload.js |
| ocr-uygulama.js | web/uygulama.js (kaynak); masaüstünde `scripts/kopyala.js` bunu `app/uygulama.js` olarak kopyalar; main.js `app/index.html` yükler ve yetki denetimini de bu yolla yapar. Elle kurulumda doğrudan `app/` altına koyun. Not: kurulum yolu 8.3 kısa adla açılırsa "Yetkisiz gönderen" hatası verir. |
| ocr-index.html | ÜRETİLMEDİ: web/index.html değişmedi (Ayarlar'daki motor durumu JS ile eklenir) |

Yanında kopyalanacak klasörler: `entegre/yeni-web/elyazisi/` (model.js, elyazisi-ocr.js) -> `web/elyazisi/` (tarayıcı CNN yedeği; `dosyadanGoruntu` EXIF düzeltmesi de buradan). `motor/` (paddle_motor.py, motor.json, PROTOKOL.md) -> paketli programda exe'nin yanına `motor/`; geliştirmede depo kökündeki `motor/` bulunur. `package.json` değişmedi; paketlemede motor/ klasörü ve Python exe ayrıca taşınmalı (embedded Python sonraki iş).
Not: r2 `web/` yalnız index.html ve uygulama.js içeriyor; diğer arayüz dosyaları (barkod-veri.js vb.) değişmedi.

## ocr-main.js (r2 main.js'e göre; başka satır değişmedi)
- `require('child_process').spawn` ve `readline` eklendi.
- `function olustur()` öncesine ~130 satır: motorKlasoru/motorKomutu (TUTANAK_MOTOR_KOMUT, motor.json, varsayılan venv python), tembel servis başlatma (hazir bekleme 120 sn, kok bildirimi, çökünce sonraki istekte yeniden başlatma), istek-id eşleme (180 sn), `ocr:motorDurum`, `ocr:gucluOku` (r2'nin gonderenKontrol'ü ile; 20 MB, PNG/JPEG imzası, kodlar dizi-string ≤20.000; geçici dosya finally'de silinir), `before-quit`'te "kapat" + 3 sn sonra kill.

## ocr-preload.js
- `motorDurum()`, `gucluOku(base64, kodlar)` eklendi (depo:* kanalları aynen).

## ocr-uygulama.js (r2 web/uygulama.js'e göre)
- Tesseract bölümü (ocrYukle/ocrCalistir/ocrSatirlariCoz ve eski fotoGir işleyicisi) kaldırıldı; yerine yeni-web/uygulama.js'teki ElYazisiOCR entegrasyonu (tembel elyazisi/ yükleme, onay paneli ocrSatirSor/ocrKodEkle/ocrVaryantSor/ocrOzetYaz) alındı.
- Eklendi: BRIDGE.gucluOku varsa önce güçlü motor (canvas -> JPEG 0.92 -> base64), servis kutuları [x0,y0,x1,y1] canvas boyutuna ölçeklenip {x,y,w,h} yapılır; hata/motor yoksa tarayıcı CNN'e düşer, mesaj ve uyarıda "yedek motor". Mesaj ön eki hangi motor olduğunu söyler. Ayarlar sekmesine salt-okunur "OCR motoru" bölümü (JS ile) eklendi.
- r2'nin imza/doğrula/tara kodlarına dokunulmadı.

## Güvenlik incelemesi sonrası (25.10 19:45, [Claude#RKxwbX])
- **Yüksek (düzeltildi):** `TUTANAK_MOTOR_KOMUT` test kancası artık yalnız paketlenmemiş sürümde ve `TUTANAK_TEST=1` ile çalışır; paketli exe'de yok sayılır (`ocr-main.js` motorKomutu).
- **Orta (kısmen):** `motor.json` içindeki `python` yolu mutlak, `python(.exe)` ile biten ve var olan bir dosya olmalı (`pythonYoluGecerli`). Kalan risk: kurulum kullanıcı başına (per-user) olduğundan kurulum klasörü kullanıcı tarafından yazılabilir; bu, programın geri kalanı için de geçerli olan genel bir durumdur. Kalıcı çözüm (Tutanak başlığının kararı): Program Files altına kurulum ya da motor dosyaları için özet/imza denetimi.
- **Düşük (düzeltildi):** kod listesi üst sınırı 15.000'e indirildi ve main tarafında `^T\d{5}(-\d{2})?$` süzgeci eklendi.
- Doğrulama: `node test\electron.motor.test.js` (TUTANAK_TEST=1 ile) 18/18 geçti.
