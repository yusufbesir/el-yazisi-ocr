# Hazır el yazısı OCR modelleri: bu bilgisayarda kurulum ve tutanak-1.jpg karşılaştırması
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] · Yusuf'a ait, eğitim amaçlı. Değiştirme: yalnız bu iş parçacığı.

## Özet
- Bulutta engelli olan indirmeler buradan yapıldı: huggingface.co (TrOCR) ve bcebos (PaddleOCR) erişilebilir.
- Kurulum: `D:\Programlar\El-Yazisi-OCR\venv` (Python 3.12, CPU). torch 2.14.1+cpu, transformers 5.20.2, easyocr 1.7.2, paddlepaddle 3.3.1, paddleocr 3.7.0, opencv-headless. Makine: AMD tümleşik GPU, 13,7 GB RAM, GPU yok.
- Aynı 8 stok kodu hücresi (egitim/bolme.py ile kesilen, iki biçim: "temiz" = ikili maske, "gri" = ham gri) her modele verildi. Puan: tam kod eşleşmesi ve karakter doğruluğu (1 − Levenshtein/uzunluk). Ardından **adil karşılaştırma**: her modelin ham çıktısı bizim yöntemdeki gibi 13.127 kodluk listeyle kısıtlandı (en yakın geçerli kod; d1≤1 ve ikinci aday daha uzaksa "kabul", yoksa "sor").

## Sonuç tablosu (8 satır)

| Model | Giriş | Ham tam | Karakter | Kısıtlı tam | Kısıtlı yanlış-kabul | Kısıtlı "sor" | Yükleme | Hücre süresi |
|---|---|---|---|---|---|---|---|---|
| **Bizim CNN + kısıtlı çözümleme (JS)** | tam sayfa | 5/8 ham | 63/66 | **7/8** | **0** | 3 | ~0,5 MB | tüm sayfa 182 ms |
| PaddleOCR PP-OCRv6 medium (en, oneDNN kapalı) | gri | 5/8 | 0,955 | 6/8 | 1 | 1 | 1,4 s (+~100 MB model) | 0,99 s |
| PaddleOCR PP-OCRv6 medium (en, oneDNN kapalı) | temiz | 5/8 | 0,939 | 5/8 | 2 | 1 | 16 s ilk | 0,87 s |
| TrOCR small printed | temiz | 3/8 | 0,909 | 6/8 | 0 | 2 | 15 s ilk (246 MB) | 0,39 s |
| TrOCR small printed | gri | 1/8 | 0,848 | 5/8 | 1 | 2 | 1,3 s | 0,38 s |
| TrOCR small handwritten | gri | 1/8 | 0,712 | 4/8 | 0 | 5 | 1,9 s | 0,45 s |
| TrOCR small handwritten | temiz | 1/8 | 0,591 | 3/8 | 1 | 5 | 24 s ilk | 0,8 s |
| TrOCR base handwritten | temiz | 2/8 | 0,758 | 2/8 | 3 | 3 | 44 s ilk (1,3 GB) | 3,75 s |
| TrOCR base handwritten | gri | 1/8 | 0,727 | 3/8 | 3 | 2 | 2,9 s | 3,1 s |
| EasyOCR (en, beyaz liste) | gri | 0/8 | 0,742 | 3/8 | 2 | 4 | 2,5 s | 0,27 s |
| EasyOCR (en, beyaz liste) | temiz | 1/8 | 0,727 | 2/8 | 2 | 4 | 2,0 s | 0,28 s |
| Tesseract 5 / tesseract.js (bulut ölçümü) | temiz ve gri | 0/8 | — | — | — | — | ~6,9 MB | — |

Ham çıktılar: `cihaz/hazir-sonuc.json`; kısıtlı yeniden puanlama: `cihaz/kisitli_eslestir.py`; hücre resimleri: `cihaz/hucreler/`.

## Yorum
1. **El yazısı modelleri (TrOCR handwritten) bu yazıda zayıf** (IAM İngilizce el yazısıyla eğitilmiş; "T14525" → "TIYSAS", "flysas"). Büyük model (1,3 GB) küçükten iyi değil ve yanlış-kabul üretiyor (3).
2. **Şaşırtıcı: basılı yazı modelleri el yazısı rakamlarda daha iyi.** TrOCR *printed* ve PaddleOCR, bu temiz blok harfli stok kodlarında handwritten modelleri geçti. Rakam ağırlıklı, bitişik olmayan yazı basılıya yakın davranıyor.
3. **Kod listesiyle kısıtlama her modeli ciddi iyileştiriyor** (ör. TrOCR printed 3/8 → 6/8). Yani asıl kazanç alan bilgisinden geliyor; tasarımdaki hipotez doğrulandı.
4. **Bizim 0,5 MB'lık CNN + kısıtlı çözümleme, 100 MB–1,3 GB'lık hazır modellerle eşit ya da daha iyi** (7/8, yanlış-kabul 0) ve tarayıcıda, ağsız, 182 ms'de çalışıyor. Hazır modeller Python/PyTorch ister; eski bilgisayarda ve tarayıcıda çalışmaz.
5. En iyi hazır aday **PaddleOCR PP-OCRv6 medium**: ham 5/8, kısıtlı 6/8, ama 1 yanlış-kabul ("T20178-6" → yanlış kod) ve sunucu tarafı Python gerekir. İleride bir "ikinci görüş" olarak masaüstü (Electron) sürümüne yerel Python servisiyle eklenebilir; tarayıcı sürümü için uygun değil.

## Kurulum notları ve sorunlar
- `paddlepaddle 3.3.1` bu CPU'da oneDNN/PIR hatası verdi: `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support pir::ArrayAttribute<DoubleAttribute>`. Çözüm: `PaddleOCR(..., enable_mkldnn=False)` (cihaz/paddle_dene.py). Model kaynağı denetimini atlamak için `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True`.
- Aynı süreçte önce paddle sonra torch yüklenirse `WinError 127 shm.dll` (DLL çakışması). Önce torch yüklenirse sorun yok; iki paketi ayrı süreçlerde kullanmak en güvenlisi.
- opencv-python-headless 5.0.0.93 ile easyocr'ın opencv-contrib 4.10 bağımlılığı aynı anda kuruldu; çalıştı ama sürüm karışıklığı var; temiz kurulumda `opencv-python-headless<5` sabitlenmeli.
- Tesseract komut satırı bu makinede yok; Tesseract sütunu bulut ölçümünden (egitim/OLCUM.md).
- Lisanslar: TrOCR MIT, PaddleOCR Apache-2.0, EasyOCR Apache-2.0, PyTorch BSD. Ücretli API ya da anahtar kullanılmadı. Modeller yalnız bu makinede, venv içinde ve HF/Paddle önbelleklerinde (`%USERPROFILE%\.cache\huggingface`, `%USERPROFILE%\.paddlex`).

## Yeniden üretme
```powershell
cd D:\Programlar\El-Yazisi-OCR
.\venv\Scripts\python.exe -X utf8 cihaz\hazir_modeller.py ornekler\tutanak-1.jpg ornekler\tutanak-1.dogru.json cihaz\hucreler cihaz\hazir-sonuc.json
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'; .\venv\Scripts\python.exe -X utf8 cihaz\paddle_dene.py
.\venv\Scripts\python.exe -X utf8 cihaz\kisitli_eslestir.py
```
