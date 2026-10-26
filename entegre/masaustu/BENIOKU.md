# Tutanak Doldurucu masaüstü: güçlü OCR motoru entegrasyon çalışma kopyası
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

## Çalıştırma
```
cd D:\Programlar\El-Yazisi-OCR\entegre\masaustu
npm i                          # electron 43 (indirme gerekirse: node node_modules/electron/install.js)
npm run kopyala                # app/ = ../yeni-web + r2-taban/web/index.html + ocr-uygulama.js (uygulama.js adıyla)
npx electron .                 # gerçek motorla (motor/paddle_motor.py + venv python)
node test/electron.motor.test.js               # sahte servisle Playwright testi
set TEST_GERCEK=1 && node test/electron.motor.test.js   # gerçek PaddleOCR servisiyle
```
- kopyala.js bu çalışma düzeninde kaynağı `../yeni-web` alır (gerçek depoda `web/`). Çalışma kopyası main.js/preload.js/package.json = ocr-main.js/ocr-preload.js/r2-taban/package.json kopyalarıdır; teslim dosyaları ocr-* adlıdır (bkz. DEGISIKLIK.md). `*.orijinal.*` dosyalara dokunulmadı.
- Test: TUTANAK_MOTOR_KOMUT ortam değişkeni servis komutunu geçersiz kılar (ör. `python test/sahte_motor.py --servis`). Test kayıtlar/ klasörünü uygulama yanında oluşturur; kullanıcı verisi geçici `--user-data-dir` altındadır.

## motor.json
`motor/motor.json`: `{"python": "C:\...\python.exe"}`. Yoksa `D:\Programlar\El-Yazisi-OCR\venv\Scripts\python.exe`. Motor klasörü: paketliyse `<exe klasörü>\motor`, değilse depodaki `motor/`. paddle_motor.py ya da python yoksa motor "yok" sayılır, program tarayıcı CNN (yedek) ile çalışır.

## Paketleme notu
motor/ klasörü ve Python (venv ya da gömülü) exe'nin yanında taşınmalıdır; build.files bunları içermez. Gömülü Python paketleme sonraki iş.
