---
description: 26.10.2026 gece OCR eğitimi sabah ölçüm raporu
sahip: Yusuf
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY]
---
# Gece OCR eğitimi — sabah raporu (26.10.2026 07:45)

## Özet
- Üç model eğitildi: stok kodu (rakam+T+tire) CNN, Türkçe harf CNN, kelime tanıyıcı (CTC; ayrık + bitişik).
- [Düzeltme 07:50, denetmen] Yanlış kabul: iki örnek fotoğrafta (tutanak-1, tutanak-3) 0; ayrı doğrulama kümelerinde, liste-dışı ve negatif testlerde yeni modelle henüz ölçülmedi.
- Motorda yanlış kabul her iki tutanakta 0 kaldı. Yeni kod modeli motor içinde biraz daha iyi (tutanak-1 adet 4→5/8, tutanak-3 otomatik kabul 0→1), ama gerçek kırpıntıda karışık; **varsayılan model değiştirilmedi** (yan dosya: egitim/gece/kod/en-iyi.json).
- Motor hızı: ~~tutanak-1 sayfa okuma 28 sn (dünkü doğrulama) → 21-31 sn; kazanç küçük~~ (pasif, 07:50, denetmen: tek tekrar, gürültülü ölçüm) → **hız kazancı ölçülemedi**: aynı fotoğrafta 21-31 sn ve 28-40 sn arası değişti, dünkü 28-29 sn ile ayırt edilemiyor; tekrarlı ve boş makinede ölçüm gerekiyor. Asıl süre hâlâ PaddleOCR tam sayfa okumasında.
- Kelime tanıyıcı ilk sürüm: gerçek bitişik İngilizce satırlarda (IAM test, hiç görülmemiş) harf hatası %29; gerçek bitişik kelimede (RIMES/Bentham doğrulama) kelime doğruluğu %45. Uygulamaya girecek düzeyde değil; temel kuruldu.

## Motor ölçümü (doğru / sor / yanlış kabul ayrı)
Sayfa okuma süresi `--olc` içindeki "sure" (model yükleme hariç).

| Foto | CNN | kod doğru (ilk aday) | otomatik kabul doğru | sor/boş | YANLIŞ KABUL | adet doğru | süre |
|---|---|---|---|---|---|---|---|
| tutanak-1 | eski | 7/8 | 5 | 3 | 0 | 4/8 | 21,3 sn |
| tutanak-1 | yeni | 7/8 | 5 | 3 | 0 | 5/8 | 30,8 sn |
| tutanak-3 | eski | 5/7 | 0 | 8 | 0 | 3/8 | 39,5 sn |
| tutanak-3 | yeni | 5/7 | 1 | 7 | 0 | 3/8 | 28,0 sn |
Dünkü değer (tur 3, eski motor): tutanak-1 7/8, kabul 5, YK 0; süre DEVAM.md'de 28 sn, motor\olc-tutanak-1.json'da 42 sn (iki kayıt tutmuyor → süre karşılaştırması yapılamaz); tutanak-3 5/7, kabul 0, YK 0, 29 sn.
Not (08:10): bu ölçümden sonra yön atlama özelliği kapatıldı (180° ters fotoğraf sorunu, DOGRULAMA-SABAH.md); yukarıdaki süreler atlama AÇIKKEN alındı.
Not: kod ve harf modellerinin ağırlıkları Chars74K'lı turlardan devam etti (kod tur 1-19, harf tur 1-29); Chars74K'sız sıfırdan eğitim sırada.
Ayrıntı: sabah/olc-*.json.

## Kod CNN, gerçek tutanak kırpıntıları (eğitime ve seçime girmedi, yalnız son ölçüm)
| Model | tutanak-1 | tutanak-3 | yeni3 |
|---|---|---|---|
| eski model.json | 61/64 | 10/19 | 26/30 |
| yeni (gece, tur 20) | 59/64 | 11/19 | 27/30 |

## Ayrı doğrulama kümesi sonuçları (seçimde kullanılan; eğitime girmeyen)
- Kod: EMNIST rakam test (bozuk) 0,970; saklı fontlar 0,937.
- Harf (tur 54/64): T-H-E test 0,936 (bozuk 0,798), EMNIST harf test 0,852 (bozuk 0,793), saklı 3 font 0,834.
- ~~Kelime (en iyi tur 22 / son tur 52) ... blok %51, bitişik %47, ayrık %19; gerçek bitişik kelime %45.~~ (pasif, 08:10, verifier: kelime\gecmis.json ve en-iyi.json ile tutmuyordu; yerine aşağısı)
- Kelime (en iyi tur 23 / son tur 52; kaynak kelime\en-iyi.json, kelime\gecmis.json son kayıt): IAM doğrulama ile seçildi. Son tur doğrulama: blok font kelime %52,7, bitişik font %52,7, ayrık (gerçek harflerden dizilmiş) %21,8; gerçek bitişik kelime (RIMES+Bentham doğrulama) %47,1; IAM doğrulama harf hatası %22,3. Son ölçüm IAM test (2.914 satır, 07:40 konsol çıktısı, ayrı dosya yok; komut: `kelime_egit.olc_satir(ag, Satirlar('test'), 2915)`): harf hatası en-iyi %29,4, son %30,8; tam satır doğru en-iyi %1,5.
- İmla (sözlükle düzeltme): ayrık kelimede %18→%23 kazandırdı, fontlu kelimelerde az kaybettirdi (rakam/İngilizce kelimeleri de Türkçeye düzeltiyor) → yalnız harfli ve Türkçe beklenen alanlarda açılmalı.

## Veri ve lisans
- Kaynak, bağlantı, lisans, SHA-256: veri/KAYNAK-EK-2026-10-26.md; dizin: veri/VERI-SETLERI-DIZIN.md.
- Kullanılan: EMNIST, T-H-E, HASYv2, QMNIST, IAM-line, RIMES (NC), Bentham, 25 OFL/Apache font, FrequencyWords. Çıkarılan: Chars74K, USPS (lisans metni yok). İndirilip kullanılmayan: MathWriting (NC-SA), BanglaLekha.
- RIMES ve MathWriting ticari olmayan lisans: kelime modeli RIMES ile eğitildi → ticari üründe kullanılmamalı (Yusuf: ticari kullanım yok).
- Commons: 483 açık lisanslı el yazısı görseli (etiketsiz; sınama/etiketleme arşivi).

## Kesintiler (dürüst kayıt)
- 01:33 kod eğitimi bellek yetersizliğiyle düştü; 02:24-03:00 TAARNAK derlemesi için duraklatıldı; kelime eğitimi 3 kez yeniden başlatıldı (IAM, RIMES ekleme, öğrenme hızı). Kayıp yok, her tur kaydedildi.
- Tur 24'te öğrenme hızı tepesi sentetik doğruluğu bozdu (0,42→0,13), sonradan 0,34'e döndü; en iyi model tur 22'de kaldı.

## Önerilen sonraki adımlar
1. Kelime modeli kapasitesi küçük (CPU'da 3 saat): daha geniş model + daha uzun eğitim; Türkçe gerçek el yazısı kelime için Yusuf'un örneklerinden etiketli küçük set.
2. Hız için asıl kazanç: TAARNAK'ta motoru uygulama açılışında başlatmak (öneri iletildi) ve Paddle mobile det modeli denemesi.
3. Liste-dışı ve negatif testler (JS) yeni modelle koşulmadı; varsayılan değişirse önce bunlar.
4. Yusuf teyidi bekleyen: ornekler/yeni2/fisler.dogru.json, ornekler/yeni/tutanak-3.dogru.json (kontrol-fisler.html).
5. Yarım: yeni4, terzihane2/3 Paddle okuması (sıra TAARNAK'tan sonra).

## Düzeltme 10:25 — Yusuf teyidi
- tutanak-3 gerçek değeri: 7. satır T14408 (eski doğru dosyası T14498 diyordu), 3. satırda 'Laci Regular' (kod yok). Teyitli dosya: ornekler\yeni\tutanak-3.teyitli.json.
- Yeniden puanlama (sabah\olc-*-t3.json): kod doğru eski 6/7, yeni 6/7 (önce 5/7 sanılıyordu; motor 7. satırı doğru okumuş); otomatik kabul doğru eski 0, yeni 1; yanlış kabul ikisinde de 0.
- Fişler: ornekler\yeni2\fisler.teyitli.json (Claude okuması 65 alanın 58'i doğruydu).

