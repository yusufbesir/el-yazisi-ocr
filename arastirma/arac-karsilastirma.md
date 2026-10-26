# Açık kaynak el yazısı OCR araçları karşılaştırması
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Araştırma: claude-haiku-5-5 alt ajanı (6 web araması), düzenleme: Fable

Not: "(doğrulandı)" arama sonucuyla teyit edilen bilgidir; diğerleri genel bilgidir, kullanmadan önce resmi depodan teyit edin. Sayılar yaklaşıktır.

| Araç | Lisans | El yazısı | Türkçe karakter | Model boyutu | CPU | Tarayıcı (WASM/JS) | Eski tarayıcı | Çevrimdışı |
|---|---|---|---|---|---|---|---|---|
| TrOCR (microsoft, handwritten) | MIT (doğrulandı) | Var; tek satır, İngilizce IAM ile eğitilmiş | Yok, yeniden eğitim gerekir | small ~246 MB (doğrulandı) | Yavaş | Zor (ONNX gerekir) | Zayıf | Evet |
| EasyOCR | Apache 2.0 | Zayıf/kısmi | Var (tr paketi) | ~20-100 MB | Evet | Yok (PyTorch) | Yok | Evet |
| PaddleOCR PP-OCRv5 | Apache 2.0 | Var (Çince odaklı doğrulandı) | Latin modeli var, Türkçe teyit gerekir | mobil ~16 MB, server ~81 MB (doğrulandı) | Evet | PaddleJS ile zahmetli | Zayıf | Evet |
| Kraken | Apache 2.0 (doğrulandı) | Var, eğitilebilir | Eğitimle | birkaç MB | Evet | Yok | Yok | Evet |
| Tesseract 5 / tesseract.js | Apache 2.0 | Yok; resmi SSS el yazısını desteklemediğini söyler (doğrulandı) | Var (tur) | tur ~5-10 MB, WASM ~3-4 MB | Evet | tesseract.js (WASM) | İyi | Evet |
| docTR | Apache 2.0 | Zayıf hazır model | Eğitimle | Orta | Evet | Kısmi (ONNX) | Zayıf | Evet |
| Surya | GPL-3.0 kod, ağırlıklar OpenRAIL-M, ticari eşik (doğrulandı) | Zayıf/belirsiz | Teyit gerekir | ~2 GB (doğrulandı) | Yavaş | Yok | Yok | Lisans kısıtlı |
| ONNX Runtime Web / TensorFlow.js | MIT / Apache 2.0 | Model bağımlı | Model bağımlı | Model bağımlı | Tarayıcıda | Evet (WASM/WebGL) | Orta | Evet |
| Kendi küçük karakter CNN'i (MNIST + sentetik) | Kendi kodumuz | Tek karakter (rakam/harf) için iyi | Özel karakter seti | ~0.1-2 MB | Evet | Evet, saf JS ile bile | İyi | Evet |
| Kendi CRNN+CTC (sentetik veriyle) | Kendi kodumuz | Satır düzeyi | Eğitimle | ~5-15 MB | Evet | ONNX Runtime Web | Orta | Evet |

## Özet
1. Hazır el yazısı modelleri İngilizce IAM ile eğitilmiştir; Türkçe için yeniden eğitim gerekir.
2. tesseract.js (mevcut OCR) el yazısını desteklemez; stok kodu için uygun değil. Bulut testi de bunu doğruladı ("T14525" → "7A4SAS").
3. TrOCR en bilinen el yazısı modeli ama büyük, tek satır ve tarayıcıda zor. Bu oturumda huggingface.co engelli olduğu için indirilemedi.
4. PaddleOCR modelleri (bcebos) bu oturumda engelli; kurulamadı.
5. Kraken eğitim için iyi, tarayıcıda çalışmaz.
6. Surya lisansı ticari kullanımda kısıtlı; ürün için riskli.
7. Tarayıcıda en pratik yol: kendi küçük modelini eğitip tarayıcıda çalıştırmak.
8. Stok kodu karakter kümesi küçüktür (T, 0-9, "-"); bu kısıt doğruluğu ciddi artırır.
9. Ürün listesiyle eşleme (13.127 kod) bir "dil modeli" gibi kullanılır: her aday kod karakter olasılıklarıyla puanlanır, eşik altı kullanıcıya sorulur.
10. Seçilen yol: tablo hücresi bölme + karakter CNN'i (saf JS) + ürün listesiyle kısıtlı çözümleme. Ayrıntı: ../TASARIM.md

## Kaynaklar
- https://github.com/naptha/tesseract.js/blob/master/docs/faq.md
- https://huggingface.co/microsoft/trocr-small-handwritten
- https://arxiv.org/abs/2603.24373 (PP-OCRv5)
- https://kraken.re/3.0/index.html
- https://github.com/kielin/surya
- https://icms-conference.org/2026/papers/paper29/main.pdf (ONNX Runtime Web ile el yazısı rakam)
- https://github.com/fgnt/mnist (MNIST aynası, eğitim verisi)
