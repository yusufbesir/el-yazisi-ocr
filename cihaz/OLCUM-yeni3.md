---
sahip: [Claude#RKxwbX]
tarih: 2026-10-25
aciklama: Yusuf'a aittir. Eğitim/ölçüm raporu (yeni3 serbest metin rakam kırpıntılarıyla ince ayar deneyi). Değiştirme yalnız bu iş parçacığı (El yazısı OCR#RKxwbX).
---
# yeni3 rakam ince ayarı: ölçüm

## Özet
- ornekler/yeni3 (6 yazar, serbest metin) fotoğraflarından Yusuf'un okuduğu sayılar PaddleOCR satır kutusu + bolme.py karakter bölmesiyle kırpıldı: 30 aday, gözle kontrolde 8 bozuk çıkarıldı, **22 temiz rakam** kaldı.
- Yan model `egitim/model-inceayar-yeni3.json` (+ .pt) üretildi; varsayılan model ve js/ dokunulmadı.
- **Sonuç: modeli ÖNERMİYORUM.** Test fotoğraflarında isabet artmadı, otomatik kabul düştü, kapalı liste dışı testte yanlış kabul 1'den 2'ye çıktı.

## Kırpıntılar
Yöntem: cihaz/yeni3_kutular.py (PaddleOCR dt_polys) -> cihaz/yeni3_rakam.py: çokgenle sınırlı uyarlamalı eşik, satır genişliğinde cetvel silme, üst/alt kenara değen komşu satır taşması silme, bölge içinde `bolme.karakter_kutulari` (+genis_bol), kutu sayısı doğru rakam sayısına eşitse etiket, küçük parçalar atılıp `mnist_normalle`. Bölge (x aralığı) satır içinde gözle seçildi (tam otomatik değil).
- Etiketlenen 30 -> kullanılan 22. Sınıf başına (kullanılan): 0:8, 1:1, 2:4, 3:1, 4:1, 5:1, 6:3, 7:1, 8:0, 9:2.
- Alınan: 20.06.2026 (8 rakam; ilk 2 çıkarıldı: cetvel izi), 146, 10 (yalnız "0"), 2.900.000 (4 rakam), 3 hariç: 7, 2023, 95, 81 (ikisi de çıkarıldı: bozuk kenar).
- Çıkarılanlar (hatalar.txt): 15-t00-k0, 15-t02-k0/k1 (81), 16-t04-k0 (10'daki "1" parçası), 16-t05-k0/k5/k6, 18-t07-k0 (3, üst çizgi).
- Atlananlar (kutu sayısı tutmadı, eslesmedi.txt): "22:00" (3 kutu != 4, cetvel ve iki nokta), "2.9" (3 != 2), ikinci "7 yaşında" (2 != 1). 17.jpg 11/01/2026 üstten kırpık olduğu için alınmadı, 13.jpg rakam yok.
- Gözden geçirme: veri/yeni3-rakam/gozden-gecir.html (ve gözle kontrol sayfası).

## Önce / sonra (aynı betikler: test/node-test.js, test/oku-ham.js, test/liste-disi-test.js; model js/model.js vs ince ayarlı)
| Ölçüt | Varsayılan | ince ayar yeni3 |
|---|---|---|
| tutanak-1 kod doğru | 7/8 | 7/8 |
| tutanak-1 otomatik kabul | 5 | 4 |
| tutanak-1 yanlış kabul | 0 | 0 |
| tutanak-1 adet | 7/8 | 7/8 |
| tutanak-3 kod doğru | 0/7 | 0/7 |
| tutanak-3 kabul / yanlış kabul | 1 / 1 (T12221) | 0 / 0 |
| liste dışı testte (tutanak-1) yanlış kabul | 1/8 | **2/8** |
Taban model zaten bu 22 kırpıntının %95,5'ini doğru bilir (ince ayar sonrası %100, MNIST test 0,9376 -> 0,9476 / eğitim sonu yüksek).

## Sonuç ve dürüst sınırlar
- Veri çok az (22 rakam, 8 yok, 1/3/4/5/7 birer tane); eğitim doğruluğu %100 ezber niteliğinde, genelleme kanıtı değil. Tutanak-3'te karakter düzeyinde birkaç satır yaklaştı (T12661, T13309) ama kod doğruluğu 0 kaldı.
- tutanak-1 kabul sayısı düştü ve liste dışı yanlış kabul arttı: bu yüzden önerilmez. Varsayılan model korunur.
- Bu kırpıntılar tablo hücresi değil serbest metindir (ince, farklı kalem, düşük çözünürlük); tutanak karakter dağılımından farklıdır. Asıl iyileşme için tutanak türü (tablodaki) gerçek kırpıntı gerekir.
- Test fotoğraflarının kırpıntıları eğitime katılmadı. Ölçüm tek örnek sayfa; fark küçük, gürültü sınırında olabilir.
