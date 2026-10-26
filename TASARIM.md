# El yazısı stok kodu OCR'ı — tasarım
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Amaç: eğitim (Yusuf). Koordinasyon: Fable; araştırma: Haiku; kod ve doğrulama: Sonnet.

## Hedef
Tutanak Doldurucu'daki (fatura-urun-kodlari/program/index.html) "Fotoğraftan oku" özelliği şu an tesseract.js kullanıyor ve el yazısını okuyamıyor
(bulut testi: "T14525" → "7A4SAS"). Yeni OCR, tutanak fotoğrafındaki **el yazısı stok kodlarını** (ör. `T20236-01`) ve **adet** rakamlarını okuyacak.

## Kısıtlar (Yusuf)
- Ücretli API yok, lisanslara uyulur (yalnız Apache/MIT/BSD ve kendi kodumuz; MNIST CC BY-SA 3.0).
- Güvenli: fotoğraf tarayıcıdan dışarı çıkmaz, ağ isteği yok, eval yok.
- Hızlı: bir sayfa 2-3 saniyede.
- Her bilgisayarda, eski tarayıcı dahil: saf ES5 JavaScript + Canvas 2D. WebAssembly, WebGL, fetch, Promise zorunlu değil (varsa kullanılabilir).
- Tutanak programına entegre edilebilir: `ocrSatirlariCoz` yerine geçen tek bir `ElYazisiOCR.oku(image, VERI)` arayüzü.

## Yaklaşım: alan bilgisiyle daraltılmış karakter tanıma
Genel el yazısı OCR'ı (TrOCR vb.) tarayıcıda ağır ve Türkçe'de zayıf. Oysa sorun dar:
karakter kümesi `T`, `0-9`, `-`; biçim `^T\d{5}(-\d{2})?$`; 13.127 geçerli kod listesi elimizde.

1. **Ön işleme** (JS, canvas): EXIF yönü, gri ton, yerel uyarlamalı eşikleme (Sauvola/ortalama-pencere), gürültü temizliği.
2. **Tablo bulma**: yatay/dikey çizgi izdüşümleri ile "Ürün Bilgileri" tablosunun satır ve sütun sınırları (6 sütun: Sıra, Stok Kodu, Ürün Açıklaması, Adet, Güncel Satış Fiyatı, Tutar). Stok Kodu = 2. sütun, Adet = 4. sütun. Eğik fotoğraflar için küçük açılı düzeltme (izdüşüm varyansını en büyükleyen açı, ±5°).
3. **Hücre temizliği**: tablo çizgileri ve açık gri filigran çıkarılır (uzun yatay/dikey yapılar morfolojik olarak silinir; koyu mürekkep kalır).
4. **Karakter bölme**: bağlı bileşenler, yatayda örtüşenler birleştirilir ("T" çubuğu, "5"in parçaları), soldan sağa sıralanır. Geometriyle `-` adayı: geniş-basık, satır ortasında.
5. **Sınıflandırma**: 28×28 girişli küçük CNN (2 conv + 2 FC, ~50-100 bin parametre), sınıflar `0-9`, `T`, `-`. Eğitim: MNIST (60k) + sentetik `T` ve `-` (MNIST "1" dikey çizgisine çubuk ekleme, font tabanlı, kalınlık/eğim/kırpma bozulmaları). Ağırlıklar JSON (~200-400 KB), çıkarım saf JS (tarayıcıda hücre başına <50 ms).
6. **Kısıtlı çözümleme (asıl numara)**: Her hücre için karakter olasılık matrisi P[i][c]. Geçerli kod listesindeki her aday `k` için puan = Π P[i][k_i] (uzunluk uyumlu; `-` ve `T` konumları biçimden). En iyi aday + güven oranı (en iyi/ikinci). Eşik altı ise ilk 3 aday kullanıcıya hücre küçük resmiyle gösterilir, kullanıcı seçer; hiçbir kod sessizce eklenmez.
7. **Adet**: 4. sütun aynı CNN ile (yalnız rakam), boşsa 1.
8. **Beden/renk**: açıklama sütunu okunmaz; stok kodu + (varsa) beden eşleşmesi mevcut `barkodOkut` akışıyla devam eder. Aynı kodun birden çok beden/rengi varsa kullanıcıya seçtirilir (mevcut davranış).

## Değerlendirme
- Gerçek örnek: `ornekler/tutanak-1.jpg`; doğru değerler `ornekler/tutanak-1.dogru.json` (8 satır).
- Ölçüt: karakter doğruluğu (CNN), kod doğruluğu (kısıtlı çözümleme sonrası), yanlış-kabul sayısı (en önemlisi: 0 olmalı).
- Karşılaştırma: Tesseract 5 (bulut, tur), EasyOCR (bulut) aynı hücrelerde.

## Dosyalar
- `egitim/` Python eğitim ve değerlendirme (bulut; PyTorch CPU).
- `js/elyazisi-ocr.js` saf ES5 kütüphane; `js/model.json` ağırlıklar; `demo.html` tek dosyalık deneme sayfası.
- `KURULUM.md` bilgisayara kopyalama ve index.html'e bağlama adımları.
- `SONUC.md` ölçümler ve sınırlar.

## Bilinen sınırlar
- Üstü çizilip düzeltilmiş kodlar (örnekte 4. satır) güvenilir okunmaz; kullanıcıya sorulur.
- Tablo biçimi değişirse sütun indeksleri `AYAR` nesnesinden güncellenir.
- Kalem rengi fark etmez (koyu mürekkep), ama çok soluk kurşun kalem zayıf kalabilir.
