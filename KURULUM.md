# El yazısı stok kodu OCR'ı: kurulum ve programa bağlama
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] · Yusuf'a ait, eğitim amaçlı. Değiştirme: yalnız bu iş parçacığı.

## Ne kuruluyor
İki dosya, başka bir şey yok:
- `elyazisi/elyazisi-ocr.js` (35 KB, saf ES5; ağ isteği, eval, innerHTML yok)
- `elyazisi/model.js` (480 KB; eğitilmiş küçük CNN'in ağırlıkları, `window.ELYAZISI_MODEL`)

Tesseract dosyaları (`ocr/` klasörü, ~6,9 MB) artık kullanılmıyor; silinmez, yerinde kalabilir.

## 1) Denemek için (programa dokunmadan)
`D:\Programlar\El-Yazisi-OCR\demo.html` dosyasına çift tıkla (file:// ile açılır, internet gerekmez). Fotoğraf seç → tablo gelir: yeşil satırlar kesin okunanlar, "sor" satırlarında 3 aday + "Hiçbiri" seçilir. "Seçilenleri listele" kod ve adetleri yazar.

## 2) Yeni tutanak programına (tutanak-programi/web) bağlama
Hazır yamalı kopya: `D:\Programlar\El-Yazisi-OCR\entegre\yeni-web\` (orijinaller `*.orijinal.*` adıyla yanında, değiştirilmedi).
1. `entegre\yeni-web\elyazisi\` klasörünü programın `web\` klasörünün içine kopyala (`web\elyazisi\elyazisi-ocr.js`, `web\elyazisi\model.js`).
2. `web\uygulama.js` dosyasını `entegre\yeni-web\uygulama.js` ile değiştir (önce eskisini `uygulama.tesseract-yedek.js` olarak yanına kopyala; silme yok).
3. `web\index.html` değişmedi (yalnız açıklama yorumu eklendi); mevcut CSP yeterli (`script-src 'self'`, `img-src data: blob:`). İstersen `blob:`/`worker-src` izinleri artık gerekmediği için daraltılabilir; bu ayrı bir karar.
4. Programı aç, "Fotoğraftan oku" ile `ornekler\tutanak-1.jpg` seç. Beklenen: kesin okunanlar renk/beden sorusuna ya da doğrudan listeye düşer; belirsizler onay panelinde hücre resmiyle sorulur. Hiçbir ürün sorulmadan eklenmez.
5. Masaüstü (Electron) sürümü aynı `web\` klasörünü paketlediği için ek iş yok; yeniden derlemede (`npm run dist:win`) otomatik girer.

## 3) Eski programa (fatura-urun-kodlari/program) bağlama
Hazır yamalı kopya: `entegre\eski-program\index.html` (+ `elyazisi\`). Programın `index.html`'ini bununla değiştir (eskisini `index.tesseract-yedek.html` diye sakla), `elyazisi\` klasörünü yanına kopyala.

## Davranış kuralları (koddaki sabitler)
- `ESIK = 2.0` nat: en iyi adayla ikincisi arasındaki fark bunun altındaysa "sor". Düşürmek daha çok otomatik kabul, daha çok yanlış kabul riski demektir; **tek fotoğrafla ayarlandı, ikinci tutanak gelmeden değiştirme**.
- `ESIK_MUTLAK = 3.0` nat: seçilen kod, CNN'in kendi okumasından bundan fazla uzaksa "sor" (kapalı liste koruması: listede olmayan kod komşu koda oturmasın). Yükseltmek daha az soru, daha çok sessiz hata riski demektir.
- `adet_esik = 0.8`: adet güveni altındaysa adet de sorulur (varsayılan 1).
- Tablo biçimi değişirse (sütun sırası) `AYAR.stok_sutun` / `AYAR.adet_sutun` güncellenir.

## Sınırlar
- Üstü çizilip düzeltilmiş kodlar güvenilir okunmaz; kullanıcıya sorulur (örnekte 4. satır).
- Çok soluk kurşun kalem ve eğik (>5°) fotoğraf zayıf kalabilir.
- Tarayıcı canvas'ı fotoğrafı Node'dan biraz farklı küçülttüğü için tarayıcıda "sor" sayısı 1-3 fazla çıkabilir; yanlış kabul artmaz.
- Fotoğrafta tablonun altındaki boş satırlar bazen fazladan "satır" sayılır; onay panelinde "Atla" ile geçilir.

## Testler
```powershell
cd D:\Programlar\El-Yazisi-OCR
$env:JPEGJS='<jpeg-js yolu>'; node test\node-test.js --kenar 2000      # kod 7/8, yanlış-kabul 0
node test\negatif-test.js ornekler\tadilat-fisi-1.jpg ornekler\tadilat-fisi-2.jpg   # yanlış kabul 0
node test\liste-disi-test.js                                           # doğru kod listede yokken sessiz kabul: 1/8 (hedef 0)
node test\tarayici-test.js                                             # headless Chrome ile demo + yeni-web
```
