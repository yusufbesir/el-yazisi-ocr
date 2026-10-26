# el-yazisi-ocr

Tutanak, iade formu ve terzihane fişlerindeki el yazısı stok kodlarını, adetleri ve metni okuyan OCR motoru. TAARNAK (Tutanak Doldurucu) programında kullanılır.

Sahip: Yusuf · Yazan: Claude oturumları ([Claude#RKxwbX], [Claude#WqTeinGYcW], [Claude#HtqxxY]) · Özel depo.

## Özet
- `js/`: tarayıcıda çalışan saf JS kütüphane (tablo bölme + küçük CNN + ürün listesiyle kısıtlı çözümleme). Emin olmadığı satırları kullanıcıya sorar, kod uydurmaz.
- `motor/`: masaüstü güçlü motor (PaddleOCR + CNN uzlaşması, stdin/stdout JSON servisi; `PROTOKOL.md`).
- `egitim/`: CNN eğitimi, bölme, çözümleme; `egitim/gece/` gece eğitimi (kod, Türkçe harf, kelime tanıyıcı), ölçüm ve ince ayar betikleri.
- `test/`: Node testleri (normal, liste dışı, negatif).
- `entegre/`: programa entegrasyon kopyaları.
- Belgeler: `TASARIM.md`, `KURULUM.md`, `SONUC.md`, `DEVAM.md`, `egitim/gece/DEVAM-GECE.md`, `egitim/gece/SABAH-RAPORU.md`.

## Depoya girmeyenler (.gitignore)
Eğitim veri setleri (`veri/`), örnek fotoğraflar ve teyitli doğru değerler (`ornekler/`, müşteri bilgisi içerir), model ağırlıkları (`*.json` modeller, `*.pt`, `js/model*.js`), sanal ortam, şirket ürün/fiyat listesi ve müşteri bilgisi içeren fiş ölçüm raporları. Bunlar yalnız yerel makinede durur (`D:\Programlar\El-Yazisi-OCR`).

## Veri ve lisans
Eğitimde kullanılan açık setlerin lisans, bağlantı ve SHA kaydı yerel `veri/KAYNAK-EK-2026-10-26.md` dosyasındadır. Bazı setler yalnız ticari olmayan kullanıma izin verir (RIMES, IAM, CVL); bu setlerle eğitilen modeller ticari üründe kullanılmamalıdır.
