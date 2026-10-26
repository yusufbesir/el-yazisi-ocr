---
description: Yön tespiti + şablon yolu doğrulama raporu (verifier, düzeltme yapılmadı)
yazan: [Claude#HtqxxY verifier]
---
# Doğrulama: yön tespiti ve şablon okuma (2026-10-26)
1. GEÇTİ: `test\yon_test.py` -> "YON TEST GECTI" (tutanak-1 0/90/180/270 doğru, ornek-4 270, y5-02 90, y5-07 0).
2. Kod incelemesi: GEÇTİ (notlarla)
   - Açı kuralı: yon_bul_hizli etiketi doğrudan `im.rotate(etiket, expand=True)` ile uygular; yon_bul ile aynı kural, test 90->270, 270->90 ile uyumlu.
   - Geri düşüş: model yok/yükleme hatası (yon_model=None), hata, güven<0.70, min kenar<32 -> None -> yon_bul. Doğru.
   - sablon_oku: eğiklik dönüşü (x*c+y*s, -x*s+y*c) doğru; sütun sınırı başlık merkez ortası; kabul yalnız d1==0 ve güven>=0.90, adet güven>=0.90; ek anahtarları (cnn, uzlasma, adet_murekkep, gri, temiz, sayfa, kaynak, d1, d2) olc() düzeniyle birebir.
   - Notlar: satır kümeleme son kutuya göre (zincirleme kayma olası, tol=0.6*medyan yükseklik); BITIS "onay|kase|imza" gövde satırında geçerse tabloyu erken keser; tek kutuda birleşmiş başlık satırı bulunamaz (None, eski yol).
3. GEÇTİ: olc-*.json özet toplamı: kod_dogru 100/109, kabul_dogru 83, yanlis_kabul 0 (t1-180 dahil 15 dosya).
4. Riskler: SABLON_SATIR_ESIK=4 -> gerçekten 1-3 satırlı tablolarda ek tam sayfa OCR (~birkaç sn; y5-05 gibi 2 satırlı). Yanlış başlık riski: başlık yalnız stok + >=3 alan aynı bantta ise; sonuç yalnız daha çok satır verirse alınır, kabul birebir kodla sınırlı -> düşük.
