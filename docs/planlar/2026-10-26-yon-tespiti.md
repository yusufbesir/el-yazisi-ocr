---
description: Hızlı fotoğraf yönü tespiti uygulama planı (PP-LCNet doc_ori)
sahip: Yusuf
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26
---
# Hızlı Yön Tespiti Uygulama Planı

> Yürütme: native (bu oturum), sonunda bağımsız Sonnet doğrulayıcı. Yusuf kuralı: plan önce yazılır, onay beklenmez.

**Goal:** Sayfa yönünü (0/90/180/270) 15-40 sn yerine <1 sn'de doğru bulmak.
**Architecture:** `motor/paddle_motor.py` içinde `yon_bul_hizli(motor, im)` PaddleOCR `DocImgOrientationClassification("PP-LCNet_x1_0_doc_ori")` ile etiket döndürür; `PIL.rotate(+etiket)` görüntüyü düzeltir (26.10 denemesi: ornek-4 270, y5-02 90 ile doğrulandı). Güven < 0,70, model yüklenemezse ya da `YON_MODELI_ACIK=False` ise eski `yon_bul` çalışır.
**Tech Stack:** Python 3.12, PaddleOCR 3.x (venv), Pillow, numpy.
**Spec:** Yusuf, 26.10: "fotoğrafın yönünü tespit etmek için işlem yap". Ölçüm sonuçları: egitim/gece/SABAH-RAPORU.md.

## Global Constraints
- Yanlış kabul sayısı hiçbir test belgesinde artmayacak (0 kalacak).
- Ağ: model yerel önbellekten (`%USERPROFILE%\.paddlex\official_models\PP-LCNet_x1_0_doc_ori`); TAARNAK gömülü paketine model klasörü eklenmeli.
- Geri alma tek ayarla: `YON_MODELI_ACIK = False`.

## Review Focus
- 180° ters fotoğraf: doğru düzeltilmeli (eski kısa yol bunu kaçırıyordu).
- Düşük güven/boş ya da çok küçük görüntü: eski yönteme düşmeli, hata vermemeli.
- Model dosyası yok (paket eksik): motor açılmalı, eski yöntem çalışmalı.
- Dikey fiş (iade/terzihane): 0° bulunmalı, gereksiz döndürme yok.
- Süre: model ilk yüklemesi Motor açılışında (ısınma), sayfa başına değil.

---

### Task 1: Hızlı yön fonksiyonu ve sayfa_oku bağlantısı
**Files:** Modify `motor/paddle_motor.py` (Motor.__init__, yeni `yon_bul_hizli`, `sayfa_oku` yön bloğu); Test `test/yon_test.py` (yeni).
**Interfaces:** Produces `yon_bul_hizli(motor, im: PIL.Image) -> (aci: int, bilgi: dict) | None`; `Motor.yon_model` (None olabilir); sabitler `YON_MODELI_ACIK = True`, `YON_MODEL_ESIK = 0.70`.
- [ ] Test yaz (`test/yon_test.py`): tutanak-1 ve 0/90/180/270 döndürülmüş kopyaları, ornek-4 (270), y5-02 (90), y5-07 (0) için `yon_bul_hizli` düzeltme açısı beklenenle aynı; `YON_MODELI_ACIK=False` iken None döner.
- [ ] Testi çalıştır, fonksiyon yokken KALSIN.
- [ ] Uygula: Motor açılışında modeli dene (hata olursa None, log); `sayfa_oku` önce `yon_bul_hizli`, None ise `yon_bul`; `yon_bilgi`ye `{"yontem":"model","etiket":..,"guven":..}`.
- [ ] Test GEÇSİN.

### Task 2: Ölçüm ve doğrulama
- [ ] `motor/paddle_motor.py --olc` 14 teyitli belge (t1, t3, y5-01..12) + t1-180: kod doğru / kabul / YANLIŞ KABUL / süre; önceki tablo (egitim/gece/sabah2, egitim/gece/sablon) ile karşılaştır. Çıktı egitim/gece/yon/.
- [ ] Sonnet doğrulayıcı: kod incelemesi + test + rapor sayıları.
- [ ] Güvenlik: guvenlik-denetcisi (yeni dosya okuma yolu yok; model yolu sabit).
- [ ] Commit (el-yazisi-ocr deposu), DEVAM-GECE ve Tutaa-OCR ortak kurallar notuna ekleme (paketleme: model klasörü).
