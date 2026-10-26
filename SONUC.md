# El yazısı stok kodu OCR'ı: sonuç raporu
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] (cihaz oturumu, Fable koordinatör) · Yusuf'a ait, eğitim amaçlı. Değiştirme: yalnız bu iş parçacığı.

## Özet
- Tutanak Doldurucu'nun "Fotoğraftan oku" özelliği için **el yazısı stok kodlarını okuyan yeni OCR** bitti: saf JavaScript, 0,5 MB, internet gerektirmez, eski tarayıcıda çalışır.
- Ölçüm (gerçek tutanak fotoğrafı, 8 satır): **7/8 kod doğru, yanlış kabul 0**, 3 satır kullanıcıya soruluyor; tüm sayfa 182 ms (Node), ~460 ms (tarayıcı). Eski tesseract.js: 0/8.
- Hazır açık kaynak modeller (TrOCR, PaddleOCR, EasyOCR) bu bilgisayara kuruldu ve aynı hücrelerde ölçüldü: en iyisi PaddleOCR 5/8 (kısıtlı 6/8, 1 yanlış kabul); el yazısı TrOCR modelleri 1-2/8. Hiçbiri tarayıcıda çalışmaz. Ayrıntı: `cihaz/HAZIR-MODELLER.md`.
- Doğrulama: bağımsız verifier GEÇTİ (8/8 madde), güvenlik denetçisi GEÇTİ (yüksek/orta bulgu yok). REA ile statik inceleme: yeni kütüphanede ağ isteği yok (`cihaz/REA-INCELEME.md`).
- Programa bağlama hazır: `entegre/yeni-web/` (yeni arayüz) ve `entegre/eski-program/` (eski arayüz), adımlar `KURULUM.md`. Orijinal program dosyalarına dokunulmadı.

## Nasıl çalışıyor (kısaca, eğitim amaçlı)
1. Fotoğraf canvas'a alınır (EXIF yönü düzeltilir, uzun kenar 2000 px).
2. Yerel eşikleme ile mürekkep maskesi; yatay/dikey izdüşümlerle tablo satır ve sütun çizgileri bulunur.
3. "Stok Kodu" ve "Adet" hücreleri kesilir, tablo çizgileri ve filigran temizlenir, bağlı bileşenlerle karakterler bölünür.
4. Her karakter 28×28'e normalize edilip küçük bir CNN'e (MNIST + sentetik "T" ve "-") verilir: 12 sınıflı olasılık.
5. **Asıl numara:** 13.127 geçerli stok kodu bir "sözlük" gibi kullanılır; her aday kod karakter olasılıklarıyla puanlanır. En iyi ile ikinci arasındaki fark eşiğin altındaysa kod eklenmez, kullanıcıya hücre resmiyle 3 aday gösterilir.

## Ölçümler

| Ölçüt | Python referans (bulut ve cihaz, aynı) | JS (Node, 2000 px) | JS (tarayıcı, Chrome headless) |
|---|---|---|---|
| Kod doğru (ilk aday) | 7/8 | 7/8 | 7/8 |
| Otomatik kabul edilen doğru | 5 | 5 → **3** (ESIK_MUTLAK sonrası) | 4 |
| "sor" durumuna düşen | 3 | 3 → 5 | 6 (2'si tablo altı boş satır) |
| Doğru kod listede YOKKEN yanlış kabul (kapalı liste testi) | — | 3/8 → **1/8** | — |
| Yanlış kabul | **0** | **0** | **0** |
| Adet doğru | 7/8 | 6/8 | — (belirsizse sorulur, varsayılan 1) |
| Süre | 1,5 s bölme + 4,3 s CNN (numpy) | 182 ms | ~460 ms |
| Negatif test (tablo olmayan 2 fiş) | — | 0 uydurma kod | — |

Satır 4 (üstü çizili, T20097-01): adaylarda yok ya da düşük güven → sor (beklenen). Satır 8 (T20178-01): doğru kod 2. aday → sor, kullanıcı seçer.

## Doğrulama kanıtı
- Verifier (claude-sonnet-5-5): `node --check` tüm dosyalar OK; ES5 ihlali 0; ağ API'si 0; `node test/node-test.js` → kod 7/8, yanlış-kabul 0; `node test/negatif-test.js` → yanlış kabul 0; `node test/tarayici-test.js` → çıkış 0, harici istek 0, konsol hatası 0; demo.html 10 satır (4 kabul, 6 sor). Orijinal dosyalar ve js/ değişmemiş (bayt karşılaştırması).
- Güvenlik denetçisi (claude-sonnet-5-5): gitleaks `no leaks found`; eval/Function/fetch/XHR/WebSocket yok; OCR çıktısı yalnız `textContent` ile gösteriliyor (XSS/dolaylı istem enjeksiyonu yolu yok); `createObjectURL` her yolda `revokeObjectURL` ile kapatılıyor; EXIF ayrıştırıcıda sonsuz döngü yok.
- Düşük bulgular (hepsi **orijinal programda zaten var**, bu işte değişmedi; öneri olarak Yusuf'a): rehber metni ve barkod/QR SVG'si `innerHTML` ile yazılıyor (uygulama.js 367-368, 1018); CSP'de `wasm-unsafe-eval`, `style-src 'unsafe-inline'` ve `worker-src blob:` artık gereksiz, daraltılabilir.
- Bilinen küçük kusur (düzeltilmedi, davranışı bozmaz): "Kod ürün listesinde yok" mesajı hemen ardından gelen özet mesajıyla ezilebilir.

## Denetmen bulguları üzerine eklenenler (25.10, 18:40 sonrası)
1. **Kapalı liste riski ölçüldü** (`test/liste-disi-test.js`): her satırın doğru kodu listeden çıkarılınca ne oluyor? İlk sürümde 8 satırın **3'ü bir harf farklı komşu koda sessizce oturdu** (T14575, T20235-02, T20226-01). Denetmen haklıydı: eşik tek koruma yetmiyordu.
2. **Düzeltme:** çözümleyiciye ikinci koşul eklendi (`ESIK_MUTLAK = 3.0` nat): seçilen kodun puanı, CNN'in kısıtsız en iyi okumasından 3 nat'tan fazla uzaksa "sor". JS ve Python birebir. Sonuç: liste dışı yanlış kabul 3/8 → **1/8** (kalan: satır 1'de "5" ile "7" karışması, T14575; bu el yazısında gerçekten belirsiz). Tam listede yanlış kabul 0 korundu; **bedeli** otomatik kabul Node'da 5 → 3 (tarayıcıda 4 → 4), yani kullanıcıya 2 satır daha soruluyor. Güvenlik tarafı seçildi; bu Yusuf'un isteyebileceği bir ayar (ESIK_MUTLAK yükseltilirse daha az soru, daha çok risk).
3. **Model kaynak kaydı** (`cihaz/model-kaynak-kaydi.json`): TrOCR üç modelinin HF commit kimlikleri ve her dosyanın SHA-256'sı; PaddleOCR PP-OCRv6 medium det/rec ve EasyOCR dosyalarının SHA-256'sı; bizim model.json/model.js/elyazisi-ocr.js özetleri. `torch.load` ile dış `.pt` açılmadı (TrOCR safetensors ile `from_pretrained`; EasyOCR kendi resmi indirmesini kendisi açar).
4. Genelleme: yeni fotoğraflar gelince **ayar / test ayrımı** yapılacak: fotoğrafların yarısı eşik ayarı, kalanı yalnız test (eşiklere bakılmadan). Terzihane fişleri farklı biçim; ayrı ölçülecek (tablo yoksa kütüphane zaten "tablo bulunamadı" der, negatif testteki gibi).
5. Dosya eşitleme: bu cihazdan proje kütüphanesine yükleme alt klasör koruyamıyor (dosyalar köke düşüyor). Tam klasör yapısı `D:\Programlar\El-Yazisi-OCR\` altında; denetmen için dosya adları bire bir aynı.

## Yeni örneklerle test (25.10, 18:35 sonrası) — ÖNEMLİ
Yusuf'un gönderdiği ikinci tutanak (**farklı yazar, T'siz ve bitişik rakamlar**) modeli düşürdü: 7 kodda 0 otomatik doğru, **1 yanlış kabul**, 6 soru. Aynı sayfada PaddleOCR 4/7 birebir. Sonuç: mevcut CNN yalnız doğrulandığı yazı biçiminde güvenilir; **gerçek kırpıntılarla ince ayar yapılmadan genel kullanıma hazır değil**. Ayrıntı ve öneriler: `cihaz/OLCUM-yeni.md`. Terzihane fişleri ayrı biçim; bizim kütüphane doğru biçimde reddediyor, PaddleOCR tükenmez kalemi kısmen, kurşun kalemi hiç okumuyor.

## Masaüstü güçlü motor (25.10 19:11 kararı: yalnız masaüstü)
- **Ne:** Electron programına yerel PaddleOCR servisi (`motor/paddle_motor.py`, stdin/stdout JSON, ağ yok) + Electron köprüsü (`entegre/masaustu/ocr-main.js`, `ocr-preload.js`, `ocr-uygulama.js`; taban Tutanak başlığının kaynak-r2'si). Tarayıcı CNN'i yedek: motor yoksa, hata verirse ya da tablo bulamazsa devreye girer. Protokol: `motor/PROTOKOL.md`.
- **Yöntem (tur 3):** tablo bölgesinde Paddle tespit+tanıma, kutular satır/sütuna eşlenir, boş hücre tek tek tanınır; **otomatik kabul yalnız Paddle ve bizim CNN aynı kodu söylerse**; aksi halde kullanıcıya iki motorun adayları gösterilir. Adet de iki motor uyuşmazsa sorulur.
- **Ölçüm (kod doğru / otomatik kabul doğru / yanlış kabul / sor / adet / süre):**

| | Tur 1 (hücre) | Tur 2 (tam sayfa) | **Tur 3 (kırpıntı + uzlaşma)** |
|---|---|---|---|
| tutanak-1 | 4/8, 4, 0, 4, 3/8, 15 s | 6/8, 6, **1**, 1, 6/8, 64 s | **7/8, 5, 0, 3, 4/8, 42 s** |
| tutanak-3 (yeni yazar) | 3/7, 2, 0, 6, 3/8, 16 s | 5/7, 5, **1**, 2, 3/8, 69 s | **5/7, 0, 0, 8, 3/8, 29 s** |

  Tur 2'de isabet arttı ama Paddle geçerli-ama-yanlış komşu kodu yüksek güvenle okuyunca sessiz hata çıktı; tur 3'teki uzlaşma kuralı bunu sıfırladı. Bedeli: yeni yazarda otomatik kabul 0 (CNN o yazıyı tanımadığı için her satır onaya düşüyor; doğru kod çoğunlukla ilk aday). Yusuf'un el yazısı örnekleriyle CNN ince ayarlanınca uzlaşma oranı ve otomatik kabul artacak. Mobil Paddle modelleri denendi: daha hızlı ama tespit kaçırıyor, varsayılan v6 medium kaldı (`motor.json` ile değiştirilebilir).
- **Doğrulama:** Electron Playwright testi 18/18 (sahte servis) + gerçek motorla; güvenlik incelemesi 1 Yüksek bulgu (test ortam değişkeni paketli sürümde de geçerliydi) düzeltildi, 1 Orta (per-user kurulumda motor klasörü yazılabilir) Tutanak başlığına karar olarak iletildi; verifier GEÇTİ. Tur 3 için son verifier turu ayrıca koşuldu (sonucu DEVAM.md'de).
- **Teslim:** exe burada derlenmedi (koordinatör kararı); birleşik tam dosyalar `entegre/masaustu/ocr-*.js` + `DEGISIKLIK.md`; Tutanak başlığı birleştirip derleyecek. Paketlemede `motor/` ve Python (şimdilik `D:\Programlar\El-Yazisi-OCR\venv`) exe'nin yanında olmalı; gömülü Python sonraki iş.

## Sınırlar ve dürüst notlar
- **Tek fotoğrafla ayarlandı.** Eşikler (TAU, ESIK, benek filtresi) bu tutanağa bakılarak seçildi; 7/8 genelleme kanıtı değildir. İkinci ve üçüncü tutanak fotoğrafı gelince aynı testler tekrarlanmalı; yanlış kabul 0 kalmıyorsa ESIK yükseltilmeli.
- Tarayıcıda küçültme Node'dan farklı olduğu için "sor" sayısı artıyor (4 kabul / 6 sor); yanlış kabul artmıyor. İyileştirme: küçültmeyi kütüphane içinde alan ortalamasıyla yapmak (ayrı iş).
- Tablo altındaki boş satırlar bazen fazladan satır sayılıyor (10 yerine 8); panelde "Atla" ile geçiliyor. İyileştirme: boş hücre eşiğini yükseltmek (ayrı iş).
- Adet okuması zayıf (bayraklı "1" bazen 7); belirsizse sorulur.
- Hazır model karşılaştırması da tek fotoğraf; PaddleOCR için oneDNN kapatma gerekti (cihaza özgü).

## Dosyalar (D:\Programlar\El-Yazisi-OCR ve proje kütüphanesi el-yazisi-ocr/)
- `js/elyazisi-ocr.js`, `js/model.js`: kütüphane (bulut yazdı, cihazda doğrulandı)
- `demo.html`, `ornekler/stok-kodlari.js`: deneme sayfası
- `entegre/yeni-web/uygulama.js`, `entegre/eski-program/index.html`: yamalı program kopyaları
- `test/node-test.js`, `test/negatif-test.js`, `test/tarayici-test.js`
- `cihaz/HAZIR-MODELLER.md`, `cihaz/hazir-sonuc.json`, `cihaz/hazir_modeller.py`, `cihaz/paddle_dene.py`, `cihaz/kisitli_eslestir.py`, `cihaz/REA-INCELEME.md`, `cihaz/OLCUM-cihaz.md`
- `KURULUM.md`, `SONUC.md`, `TASARIM.md`, `DEVAM.md`

## Birlikte çalışılanlar
- Fable (claude-fable-5-1): koordinasyon, REA incelemesi, hazır model kurulumu ve ölçümü, raporlar.
- claude-sonnet-5-5 implementer: demo.html, entegrasyon, tarayıcı testi. claude-sonnet-5-5 verifier ve güvenlik denetçisi: doğrulama.
- Bulut oturumu (önceki): araştırma (Haiku), tasarım, Python prototipi, CNN eğitimi, JS portu taslağı.

## Kullanılan yapay zeka araçları
REA (MCP, statik JS analizi), Playwright (headless Chrome), PyTorch CPU, HuggingFace transformers (TrOCR), PaddleOCR, EasyOCR, gitleaks, Node 24.

## Token (tahmini)
Cihaz oturumu: koordinatör ~120k giriş / ~25k çıkış; implementer ~199k; verifier ~90k; güvenlik ~31k. Toplam ≈ 460k (tahmin; alt ajan sayıları araç raporundan, koordinatör tahmini).
