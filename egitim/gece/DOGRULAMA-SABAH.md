---
description: 26.10.2026 gece OCR çalışmasının bağımsız doğrulama raporu (verifier); yalnız okuma/ölçüm yapıldı, hiçbir kaynak dosya değiştirilmedi
sahip: Yusuf
yazan: [Claude#HtqxxY verifier]
---
# Doğrulama — sabah (26.10.2026)

## Özet
Genel sonuç: 5 maddenin 3'ü GEÇTİ (1, 3, 5 notlarla), 2'si KALDI (2: 180° dönük fotoğrafta yön araması yanlışlıkla atlanıyor; 4: SABAH-RAPORU kelime satırlarındaki sayılar kaynakla tutmuyor / kaynaksız). Paddle çalıştırılmadı, eğitim yapılmadı.

## 1. ileri_toplu — GEÇTİ
- 60 gerçek kırpıntı (veri/tutanak-kirpinti/tutanak-1, 28x28'e getirilmiş) üzerinde ileri ile ileri_toplu karşılaştırıldı: model.json en büyük olasılık farkı 9,2e-07, gece/kod/en-iyi.json 3,1e-07 (eşik 1e-5); argmax %100 aynı.
- Ağırlık sırası: cikarim_numpy.py:97, transpose(0,2,3,1,4,5)+reshape(n*h*w, c*k*k) -> (cin,dy,dx); ileri'deki W.reshape(cout,cin,k,k) ile aynı. Doğru.
- Not: test eşdeğerlik testi; ön işleme gerçek hat değil.

## 2. paddle_motor.py — KALDI
- py_compile (paddle_motor.py, cikarim_numpy.py): hatasız.
- BULGU (yüksek): paddle_motor.py:275-282 yön atlama koşulu `SON["yol"]!="gevsek" and len(satir)>=4 and len(sutun)>=3`. Tablo çizgileri 180° dönük görüntüde de aynen bulunur. Ölçüm (bolme.sayfa_isle, ornekler/tutanak-1.jpg, 2000 px): 0° -> eski yol, 11 satır/7 sütun ATLAR; 180° -> 11/7 ATLAR (yön araması yapılmaz, metin ters Paddle'a gider; eskiden yon_bul 180°'yi düzeltirdi); 90° ve 270° -> tablo bulunamadı, yön aranır (güvenli). Öneri: atlama kararına tek ucuz yön işareti ekle (ör. 0° ve 180° için hücre/başlık metin kalitesi) ya da atlamayı yalnız küçük görüntü yön_kalitesi 0° yeterliyse yap.
- Küçük: atlandığında yon bilgisi {"karar":...} ve "olcum" anahtarı yok (şu an tüketen kod bulunmadı).
- Geçici dosya: tmp0 try/finally ile os.unlink (satır 276-289), yol tempfile; sorun yok. Isınma (125-131) hata yakalıyor; sorun yok.
- Hücre tanıma atlama (361-365): bilgi={} iken olc çıktısı (satır 529-531) None'ı "-" yazıyor; ek alanları .get ile; stok_karar yalnız metin/guven kullanıyor, davranış değişmiyor. cnn_oku ileri_toplu: boş karakter listesi np.zeros((0,12)) ile korunuyor.
- test_servis.py: Paddle gerektirir, çalıştırılmadı.

## 3. Eğitim betikleri — GEÇTİ
- gece_egit.py: secim_puani (293-299) yalnız *-test-bozuk ve font-sakli kullanır; gercek (tutanak-1/3, yeni3) yalnız son_olcum olarak kayda gider (satır 391), puan hesabına girmez. Eğitim kaynakları satır 56: emnist-digits/harf-train, the-train, hasy, qmnist; Chars74K/USPS yok.
- kelime_egit.py: tutanak/yeni3 hiç yok; seçim = sentetik doğrulama (the-test, emnist-*-test) + IAM validation (465, 522-526); IAM test yüklenmiyor ("Satirlar" yalnız train/validation); kaynaklar satır 89-90.
- torch.load: kelime_egit.py:454 weights_only=True; gece_egit.py:343 weights_only=True, 346 yedek weights_only=False yalnız betiğin kendi ürettiği son.pt için (yorum var) — kabul edilebilir, ama dışarıdan gelen dosya konulursa pickle riski.
- Küçük: gece_egit.py:9 docstring hâlâ Chars74K'yı sayıyor (eski); hazirla.py varsayılan adımları chars74k içeriyor (yalnız önbellek üretir, eğitim okumaz).

## 4. SABAH-RAPORU sayıları — KALDI
Tutanlar:
- Motor tablosu: sabah/olc-*.json ozet ile birebir (7/8, 5, 3, 0, 4/8, 21,29 sn; yeni t1 5/8, 30,76; eski t3 5/7, 0 kabul, 39,48; yeni t3 1 kabul, 28,03). Dünkü değerler motor/olc-tutanak-1/3.json ile uyumlu (42,03 ve 29,16 sn ölçülmüş; raporda 28/29 sn yazıyor, tutmuyor: tutanak-1 dünkü 42 sn).
- karşılaştır çıktısı: model.json 61/64, 10/19, 26/30; kod/en-iyi.json 59/64, 11/19, 27/30 — rapordaki tablo ile aynı. Kod tur 20 ve 0,970/0,937 doğru. Harf tur 54: 0,936/0,798/0,852/0,793/0,834 doğru.
Tutmayanlar (kelime):
- En iyi tur: kelime/en-iyi.json ve gecmis.json tur 23 (puan 0,6214); rapor "tur 22" diyor.
- "Sentetik doğrulama (son tur): blok %51, bitişik %47, ayrık %19": gecmis.json tur 52 -> blok 0,527, bitişik 0,527, ayrık 0,218 (0,47 imla'lı bitişik). Tur 51: 0,48/0,453/0,182. Hiçbir tura birebir uymuyor.
- "gerçek bitişik kelime %45": tur 52 = 0,471, tur 51 = 0,480 (tur 23 kaydında yok).
- IAM test (2.914 satır; harf hatası %29,4/%30,8, tam satır %1,5): kaynak betik/log/JSON bulunamadı; doğrulanamadı. (IAM validation 400 satır: CER 0,204-0,223.)

## 5. Lisans — GEÇTİ (notlarla)
- KAYNAK-EK-2026-10-26.md + emnist/KAYNAK.md + iam-line: EMNIST (lisans+URL+SHA emnist/KAYNAK.md), T-H-E (the-dataset/SHA256.txt), HASYv2 (ODbL, bağlantı, SHA), QMNIST (SHA), fontlar (SHA, OFL/Apache), FrequencyWords (MIT, SHA), Bentham (CC BY 4.0, SHA), RIMES (CC BY-NC, SHA), IAM-line (bağlantı, SHA iam-line/SHA256.txt, kart MIT + IAM NC notu). Eksik yok.
- Chars74K ve USPS: gece_egit.py:56 ve kelime_egit.py:15; kaynak listelerinde yok. DİKKAT: Ek 6'ya göre kod modeli (tur 1-19) ve harf modeli (tur 1-29) Chars74K ile eğitilmiş ağırlıkla devam etti; en-iyi kod modeli (tur 20) bu yüzden Chars74K etkisi taşıyor. SABAH-RAPORU "Çıkarılan: Chars74K" diyor ama bu etkiyi anmıyor; rapora eklenmeli.
