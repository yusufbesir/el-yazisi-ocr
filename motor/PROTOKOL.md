# Güçlü OCR motoru (masaüstü): servis protokolü
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] · Yusuf'a ait. Değiştirme: yalnız bu iş parçacığı.

Karar (Yusuf, 25.10 19:11): güçlü motor yalnız masaüstü sürümünde. Tarayıcı CNN'i yedek olarak kalır.

## Süreç modeli
- Electron ana süreci `python motor/paddle_motor.py --servis` komutunu başlatır (yol `motor/motor.json` → `python` alanı; yoksa `D:\Programlar\El-Yazisi-OCR\venv\Scripts\python.exe`). Ağ yok; iletişim **stdin/stdout, satır başına bir JSON** (UTF-8). stderr yalnız günlük.
- Servis ilk satır olarak `{"olay":"hazir","surum":"1.0","motor":"PaddleOCR x.y","sure_ms":n}` yazar (model yükleme bitince). Yüklenemezse `{"olay":"hata","mesaj":"..."}` yazıp çıkar (kod 2).
- Ortam: `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True`; PaddleOCR `enable_mkldnn=False`, `use_textline_orientation=False`, `lang="en"` (bu cihazda zorunlu; HAZIR-MODELLER.md).

## İstek (Electron → servis)
```json
{"id":"i1","islem":"oku","foto":"C:\\...\\gecici\\x.png","kodlar":["T14525","T20236-01", "..."], "en_buyuk_kenar":2000}
```
- `foto`: Electron'un userData altındaki geçici klasöre yazdığı PNG/JPEG yolu (renderer'dan base64 gelir, main yazar). Servis dosyayı okur, **silmez**; silmeyi main yapar.
- `kodlar`: geçerli stok kodu listesi (VERI'deki benzersiz `u.k`). Boşsa kısıtsız ham okuma.
- `{"id":"i2","islem":"durum"}` → `{"id":"i2","tamam":true,"motor":"...","bekleyen":0}`
- `{"islem":"kapat"}` → servis temiz çıkar.

## Yanıt (servis → Electron)
```json
{"id":"i1","tamam":true,"sure_ms":3200,"yontem":"hucre",
 "goruntu":{"w":1424,"h":2000},
 "satirlar":[
   {"sira":1,"stok":{"ham":"T14525","secilen":"T14525","aday":[{"kod":"T14525","mesafe":0},{"kod":"T14575","mesafe":1}],"guven":0.93,"durum":"kabul"},
    "adet":{"ham":"1","deger":1,"guven":0.98,"durum":"kabul"},
    "hucreKutusu":[x0,y0,x1,y1],"adetKutusu":[x0,y0,x1,y1]}
 ],
 "uyari":[]}
```
- Koordinatlar `goruntu.w/h` boyutundaki (küçültülmüş) görüntüye göre; renderer kendi canvas'ına ölçekler.
- `yontem`: `"sayfa+hucre"` (varsayılan, tur 2+: tablo bölgesinde tam tespit+tanıma, kutular satır/sütuna eşlenir, boş kalan hücre tek tek tanınır), `"hucre"` (yalnız hücre hücre tanıma) ya da `"sayfa"` (tablo bulunamadı; `satirlar` boş döner, renderer yedek motora düşer).
- Satır başına ek alanlar (tur 2+): `kaynak:"sayfa"|"hucre"` (stok ve adet için), tur 3+: `uzlasma:true|false` ve `cnn:{secilen,guven}` (ikinci motor: bizim CNN). **Kabul kuralı tur 3+:** Paddle kabul koşulu sağlanmış VE CNN'in kısıtlı ilk adayı aynı kod olmalı; aksi `sor`.
- Durum kuralı (kisitli_eslestir.py ile aynı): `temizle(ham)` → en yakın kod `d1`, ikinci `d2`; **kabul** yalnız `d1 ≤ 1 ve d2 > d1 ve Paddle güveni ≥ 0.80`; aksi **sor**; hiç aday yoksa `bos`. Hiçbir kod sessizce eklenmez; "sor" satırlarında ilk 3 aday ve ham okuma gösterilir.
- Adet: yalnız rakam; boşsa 1 (`durum:"bos"`); 1-99 dışı → sor.
- Hata: `{"id":"i1","tamam":false,"hata":"..."}`; servis çökmez, bir sonraki isteğe devam eder.

## Güvenlik
- Servis yalnız `foto` ile verilen dosyayı okur; yol userData geçici klasörü altında olmalı (main doğrular, servis de `os.path.realpath` ile kontrol edip dışarıdaysa reddeder; izinli kök ilk istekte `{"islem":"kok","yol":...}` ile bildirilir).
- Ağ isteği yok; model dosyaları yerel önbellekten (`%USERPROFILE%\.paddlex`), yoksa `{"olay":"hata"}`.
- Electron: `ocr:gucluOku` IPC yalnız kendi `app/index.html` sayfasından (mevcut `gonderenKontrol`), base64 en çok 20 MB, PNG/JPEG imzası doğrulanır, geçici dosya iş bitince silinir (Geri Dönüşüm Kutusu kuralı geçici dosyalar için geçerli değil: program kendi ürettiği geçici dosyayı siler).
