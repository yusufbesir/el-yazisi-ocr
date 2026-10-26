# Açık el yazısı arşivleriyle eğitim denemesi (EMNIST + T-H-E): sonuç
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] · Yusuf'a ait, eğitim amaçlı. Değiştirme: yalnız bu iş parçacığı.

## Özet
- Yusuf'un isteğiyle internetten iki açık arşiv indirildi ve kaynak/SHA-256 kaydedildi (`veri/emnist/KAYNAK.md`): **EMNIST** (NIST, 280k rakam ve harf, 500+ yazar) ve **T-H-E** (200 Türk/Macar/İngiliz katılımcı, 78 harf; Türkçe harfler dahil).
- CNN bu verilerle yeniden eğitildi (307k örnek, 8 epoch, 4 dk CPU; `egitim/model-emnist.json`, `js/model-emnist.js`). Tutanaklar yalnız test olarak kullanıldı, eşik değiştirilmedi.
- **Sonuç: genel arşiv tutanak okumasını iyileştirmedi.** Standart testlerde daha iyi (EMNIST rakam %99,4; T harfi %40 → %99), ama gerçek tutanakta geriledi: tutanak-1 7/8 → 6/8 ve **1 yanlış kabul**; tutanak-3 yine 0/8. **Varsayılan model değiştirilmedi** (eski model kaldı; yeni model yan dosya olarak duruyor).

## Karşılaştırma (eski model → EMNIST+T-H-E modeli)

| Ölçüt | Eski | Yeni |
|---|---|---|
| EMNIST rakam testi | 0,993 | 0,994 |
| EMNIST T/t testi | 0,40 | 0,99 |
| tutanak-1 kod doğru (Python) | 7/8 | 6/8 |
| tutanak-1 yanlış kabul (Python / JS) | 0 / 0 | **1 / 1** |
| tutanak-1 adet doğru (Python) | 7/8 | 2/8 |
| tutanak-3 kod doğru | 0/8 | 0/8 (1 yanlış kabul) |
| liste-dışı test yanlış kabul | 1/8 | 1/8 |
| negatif test (fişler) | 0 | 0 |
| motor uzlaşması tutanak-1 (doğru/kabul/yanlış) | 7/8 / 5 / 0 | 7/8 / 4 / 0 |
| motor uzlaşması tutanak-3 | 5/7 / 0 / 0 | 5/7 / 1 / 0 |

## Neden işe yaramadı (yorum)
1. **Alan farkı:** EMNIST örnekleri tarayıcıdan geçmiş, ince kalemli, merkezlenmiş formlardan; tutanak fotoğraflarında tükenmez kalem, telefon fotoğrafı, tablo çizgisi artıkları, farklı kalınlık ve kırpma var. Standart testte iyi olan model bu dağılımı tanımıyor (klasik "dağılım kayması").
2. **Tutanak-3'ün yazısı** (çengelli 1, açık 4, g gibi 9) EMNIST'te de seyrek; 500 ABD'li yazar bu Türk yazarın alışkanlıklarını kapsamıyor.
3. Adet okumasındaki gerileme (7/8 → 2/8) bayraklı "1"in EMNIST'teki düz "1" ile ezilmesinden kaynaklanıyor olabilir; sınanmadı.

## Çıkarım ve sonraki adım
- Genel arşivler **ön eğitim** için kullanılabilir ama asıl kazanç **gerçek tutanak kırpıntılarından** gelecek. Önerilen yol: yarı otomatik etiketleme aracı (hücre kırpıntısı → Yusuf onayı → karakter etiketleri) ile "Türkçe tutanak el yazısı arşivi" kurmak; EMNIST+T-H-E ile ön eğitilmiş modeli bu arşivle **ince ayarlamak** (son katmanlar, düşük öğrenme hızı). Her tutanak ≈ 50-60 etiketli karakter.
- T-H-E Türkçe harfler, ileride ürün açıklaması/beden sütunu ya da terzihane fişi alanları okunacaksa harf modelinin temel verisi (Yusuf'un isteği: harfler için Türkçe önemli).
- Lisans notları: EMNIST arşivinde lisans metni yok; kamu malı ifadesi NIST'in federal çalışma statüsüne dayanıyor. T-H-E'de LICENSE yok; yalnız eğitim/araştırma, atıf KAYNAK.md'de.

## Dosyalar
- `veri/emnist/` (gzip.zip + açılmış idx, KAYNAK.md, SHA256.txt), `veri/the-dataset/` (version6.csv, SHA256.txt)
- `egitim/veri_emnist.py`, `egitim/egit_emnist.py`, `egitim/model_test.py`, `egitim/model-emnist.json`, `js/model-emnist.js`
- Ölçümler: `cihaz/OLCUM-emnist-t1.md`, `OLCUM-emnist-t3.md`, `OLCUM-eski-t1.md`, `OLCUM-eski-t3.md`
- Model seçimi: testlerde `ELYAZISI_MODEL_JS` ortam değişkeni; motorda `motor.json` `cnn_model` ya da `--cnn`. Varsayılanlar eski model.
