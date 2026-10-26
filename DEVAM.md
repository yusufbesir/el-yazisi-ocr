# DEVAM — El yazısı stok kodu OCR'ı
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] · Yusuf'a ait. Önceki devir notu (bulut, 15:17) aşağıda "Geçmiş" bölümünde özetlendi.

## Güncelleme 18:55: yeni örnekler geldi, sonuç değişti
- tutanak-3 (farklı yazar): bizim CNN 0/7 + 1 yanlış kabul; PaddleOCR 4/7. Kütüphane bu yazarda güvenli değil. Ayrıntı cihaz/OLCUM-yeni.md.
- Eklenenler: ESIK_MUTLAK (kapalı liste koruması), CEZA_T (T'siz kod), test/liste-disi-test.js, test/oku-ham.js, cihaz/model-kaynak-kaydi.json, cihaz/terzihane-paddle.json.
- Yusuf'un kararı bekleyen iki yol: (A) daha çok tutanak toplayıp CNN'i gerçek kırpıntılarla ince ayarla (tarayıcıda kalır, eski PC'de çalışır); (B) masaüstü sürüme yerel PaddleOCR servisi ekle (güçlü ama 250 MB, 40 s/sayfa, yalnız Electron). İkisi birlikte de olur.
- Terzihane fişi: önce "hangi alanlar okunsun" kararı; kurşun kalem için ön işleme araştırması ayrı iş.

## Güncelleme 20:05: masaüstü güçlü motor hazır (teslim bekliyor)
- Yusuf kararı (19:11): yalnız masaüstü. Yapılan: motor/paddle_motor.py (tur 3: tablo kırpıntısı + Paddle + CNN uzlaşması, yanlış kabul 0), Electron köprüsü ocr-main.js / ocr-preload.js / ocr-uygulama.js (taban kaynak-r2), test/electron.motor.test.js 18/18, güvenlik düzeltmeleri (TUTANAK_TEST kancası, python yolu doğrulama, kod süzgeci).
- Teslim biçimi (koordinatör): exe burada derlenmez; ocr-*.js + DEGISIKLIK.md Tutanak başlığına verilir, o birleştirir ve test\kanit.ps1 ile derler.
- Son verifier (tur 3) sonucu: bu dosyanın altına eklenecek.
- Sonraki: Yusuf'un el yazısı kaynak dosyası → CNN ince ayarı (uzlaşma oranı artar) → yeniden ölçüm (yalnız test fotoğraflarıyla). Gömülü Python paketleme ayrı iş. Terzihane fişi alan kararı Yusuf'ta.

## Durum: İlk teslim tamam; genelleme için ek iş gerekli; Bağımsız denetmen kontrolü bekliyor
- Kütüphane, demo, iki programa entegrasyon kopyası, testler, hazır model karşılaştırması, REA incelemesi, KURULUM.md ve SONUC.md bitti. Verifier GEÇTİ, güvenlik GEÇTİ.
- Yusuf'un kararı bekleyenler: (1) entegrasyonun gerçek programa kopyalanması (KURULUM.md adımları), (2) orijinal programdaki düşük güvenlik bulgularının düzeltilmesi (innerHTML, CSP daraltma), (3) ikinci tutanak fotoğrafı ile yeniden ölçüm.

## Sonraki adımlar (sırayla)
1. Bağımsız denetmen SONUC.md ve testleri kontrol eder.
2. Yusuf onaylarsa KURULUM.md ile programa kopyala; Electron sürümünü yeniden derle.
3. Yeni tutanak fotoğrafı gelince: `node test/node-test.js` + `tarayici-test.js`; yanlış kabul 0 değilse ESIK yükselt.
4. İsteğe bağlı iyileştirmeler (ayrı iş): tarayıcı küçültmesini kütüphane içine almak; boş satır eşiği; adet için gerçek kırpıntılarla ince ayar.

## Geçmiş (bulut devir notu özeti)
Araştırma (arastirma/arac-karsilastirma.md), tasarım (TASARIM.md), Python prototipi ve eğitim (egitim/), JS portu taslağı bulutta yapıldı; huggingface/bcebos bulutta engelliydi. Cihaz oturumu 25.10 15:14'te devraldı; bu makinede her iki kaynak erişilebilir çıktı.

## Tur 3 verifier sonucu (20:15): GEÇTİ
- tutanak-1: 7/8, otomatik kabul 5, yanlış kabul 0, 28 s. tutanak-3: 5/7, kabul 0, yanlış kabul 0, 29 s. test_servis.py ve Electron gerçek motor testi geçti (ağ 0, konsol 0, geçici dosya silindi).
- Açık risk (not edildi, değiştirilmedi): Paddle ile CNN aynı yanlış geçerli kodda buluşursa kabul çıkar; ek güvence olarak kabul için CNN `durum=="tamam"` şartı eklenebilir (bir sonraki turda, Yusuf'un örnekleriyle ölçülerek).

## Güncelleme 21:15: açık arşivlerle eğitim denemesi
- EMNIST + T-H-E indirildi (veri/, KAYNAK.md, SHA-256). Yeni model (model-emnist) tutanakta iyileşme getirmedi, tutanak-1'de 1 yanlış kabul → varsayılan model DEĞİŞMEDİ. Rapor: cihaz/OLCUM-arsiv-egitimi.md.
- Yusuf'un netleştirmesi: rakam için Türkçe şart değil; harfler için Türkçe veri (T-H-E) önemli → harf okuma aşamasında kullanılacak.
- Sonraki: Yusuf'un el yazısı dosyası → etiketleme aracı → gerçek kırpıntılarla ince ayar (EMNIST+T-H-E ön eğitim olarak kullanılabilir).

## Güncelleme 21:40: etiketleme aracı ve ince ayar altyapısı hazır
- egitim/etiketle.py: fotoğraf + dogru.json → veri/tutanak-kirpinti/<foto>/<sınıf>/*.png + etiketler.csv + gozden-gecir.html (Yusuf yanlışları hatalar.txt'ye yazar). tutanak-1: 64 karakter, tutanak-3: 19 (kutu sayısı tutmayan satırlar eşleşmedi).
- egitim/egit_inceayar.py: tabandan (model.json ya da model-emnist.json) gerçek kırpıntılarla ince ayar; model-inceayar.json (t1 ile), model-inceayar-t13.json (t1+t3, test yok).
- Deney: tutanak-1 ile ince ayar → tutanak-3 testinde değişiklik yok (0/8); liste-dışı yanlış kabul 1/8 → 0/8. Varsayılan model değişmedi. Yusuf'un örnekleri gelince: etiketle.py → gözden geçirme → egit_inceayar.py → yalnız yeni test fotoğraflarıyla ölçüm.
- Not: eski modelin MNIST kontrol doğruluğu bu betikte 0,94 çıktı (önceki 0,993); bölme yönü şüphesi, araştırılmadı; mutlak değere güvenme.

## Güncelleme 21:30 (bilgisayar kapanmadan önce) — [Claude#WqTeinGYcW] [İP:El yazısı OCR#RKxwbX devralındı]
Durum: bilgisayar kapanırken arka planda iki PaddleOCR koşusu çalışıyordu; kapanırsa SONUÇ YOK, yeniden başlat.
### Bitenler
- yeni3 (13-18) indirildi, SHA-256 ornekler\yeni3\BENIOKU.md; Paddle ölçümü cihaz\serbest-paddle.json (14.webp karakter hatası ~%1,9; el yazısı rakamlar zayıf).
- Rakam kırpıntıları veri\yeni3-rakam (22 temiz), ince ayar deneyi: kazanç yok, liste dışı yanlış kabul 1/8→2/8 → varsayılan model DEĞİŞMEDİ (cihaz\OLCUM-yeni3.md).
- Google araması Crawl4AI ile kazındı: CAPTCHA, aşılmadı. Katalog (awesome-turkish-datasets) kazındı: modern Türkçe el yazısı açık veri yok. Araçlar: web-kazima\kazi-google.py, kazi-url.py (PLAYWRIGHT_BROWSERS_PATH=D:\Programlar\web-kazima\tarayici).
- Eski iki başlık (OCR ve Fatura→Excel) bu başlığa birleşti; kasa notu güncellendi.
### Yarım kalanlar (bilgisayar açılınca sırayla)
1. ornekler\yeni4 (16 görsel) ve ornekler\terzihane2 (14 fiş) Paddle okuması: `venv\Scripts\python.exe cihaz\serbest_paddle.py ornekler\yeni4\*.*` (PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True, PYTHONIOENCODING=utf-8) → cihaz\serbest-paddle.json; fişler için cihaz\terzihane2_paddle.py → cihaz\terzihane2-paddle.json. Aynı anda ikisini değil, sırayla çalıştır.
2. Sonuçları özetle, Yusuf'a bildir (terzihane alan kararı hâlâ onda).
3. Test dosyalarını Geri Dönüşüm Kutusu'na taşı: cihaz\*.log, web-kazima\crawl4ai (boş klasör, benim oluşturduğum), scratchpad; kalıcı silme yok.
### Yusuf kararı bekleyenler
Terzihane okunacak alanlar; orijinal programdaki düşük güvenlik bulguları; Düzce veri seti e-posta taslağı (göndermeden sor).

## Güncelleme 22:25: başlık birleştirildi, devir
Bu başlık koordinatörce "El yazısı örnekleriyle OCR eğitimi" başlığıyla birleştirildi; iş orada sürecek. Son durum:
- Yeni örnekler: ornekler/yeni2/ornek-1..5 tadilat fişi (yeni yazarlar), ornek-6..8 **İade ve Değişim Tutanağı** (yeni form: Barkod | Ürün Adı | Beden/Renk | Miktar). Doğru değerler ornekler/yeni2/fisler.dogru.json (Claude okuması, teyit gerek). Ölçüm: cihaz/OLCUM-fisler.md (Paddle: fiş no/telefon/tarih iyi, isim yaklaşık, kurşun kalem ve dönük fotoğraf okunmuyor; iade formunda stok kodu 3/4 güven 1.0).
- Bizim tablo bulucu iade formunda çizgi bulamıyor (1080×1920, açık gri çizgiler; teşhis: sütun eşiği sutun_oran*tablo yüksekliği ve cizgi_kalinlik; satır dizisi şüpheli). Düzeltme yapılmadı.
- **Kod deseni** `^T\d{4,5}(-\d{2})?$` oldu (listenin yarısı T+4 rakam; JS, coz.py, motor, ocr-main.js, kisitli_eslestir). Kutu sayısı kümesi [6,9] kaldı ([5,6,8,9] yanlış kabul artırdı). Ek kural: cezalı (uzunluğu tutmayan) eşleşme otomatik kabul edilmez. Sonuç: tutanak-1 7/8 YK 0, liste-dışı 1/8, negatif 0, tutanak-3 yalnız bilinen satır-1 kabulü. Verifier KOŞULMADI (başlık kapandığı için); devralan başlık verifier koşmalı.
- Türkçe el yazısı arşivi: veri/el-yazisi-turkce/yusuf-gonderdi (22 görsel) + google-kucuk-resim (62 küçük resim, alt metinleri) + BENIOKU.md + SHA256.txt. Etiketsiz; harf modeli için transkripsiyon + onay gerekir.
- Açık: ornek-2 Paddle çökmesi tekrar denenmeli; yön düzeltme; iade formu için form şablonu; T+4 kısa kodların yanlış kabul riski (JS ESIK_MUTLAK + cezasız şartıyla kontrol altında, Python'da aynı).

## Güncelleme 23:00: yön düzeltme, iade tablo bulucu [Claude#RKxwbX devralan]
- Yapıldı: motor/paddle_motor.py `yon_bul` (ornek-4 → 270°, fiş no/saat okundu), `--fis` modu; egitim/bolme.py `tablo_bul_gevsek` + js/elyazisi-ocr.js `gevsekTablo` (iade formu ornek-6..8 satırları bulunuyor, başlık atlanıyor); ornek-2 çökmesi yeniden üretilemedi (eşzamanlı eğitim çekişmesi şüphesi). Ayrıntı ve önce/sonra: cihaz/OLCUM-fisler2.md.
- Eski testlerde değişiklik yok (tutanak-1/3 motor ve JS, liste-dışı 1/8, negatif 0). Verifier hâlâ KOŞULMADI (kod deseni T+4/5 rakam dahil).
- Açık: gevşek yol yalnız iade formu şablonuna kilitli; iade stok kabulü bu formda kapalı/çok seyrek (JS hepsi sor; motor adet kapalı); yön düzeltme JS'e eklenmedi.

## Güncelleme 22:50 — [Claude#WqTeinGYcW] [İP:El yazısı OCR#RKxwbX devralındı]
- Implementer: yön düzeltme (yon_bul, 4 dönüş), iade formu için gevşek tablo bulucu (bolme.py tablo_bul_gevsek, js gevsekTablo), ornek-2 yeniden okundu (çökme yeniden üretilemedi). Ayrıntı cihaz\OLCUM-fisler2.md.
- Bağımsız verifier: GEÇTİ (desen 5 dosyada tutarlı; yanlış kabul 0; liste-dışı 1/8; negatif 0; tarayıcı testi, motor test_servis 8/8). Electron sahte motor testi ayrıca benim tarafımdan koşuldu: 18/18 GEÇTİ (npm run kopyala sonrası; jpeg-js yolu JPEGJS ile).
- Notlar: entegre\eski-program ve entegre\yeni-web kopyaları js\ ile senkron değil (gevsekTablo yok) → KURULUM öncesi senkronla. motor\gunluk klasörü yeniden oluşturuldu. İade formunda JS gevşek yolu otomatik kabul etmez (hepsi "sor").
- TAARNAK (Tutanak başlığı) r3'ü yeni ocr-main.js/paddle_motor.py ile yeniden birleştirebilir.
- Arka planda: yeni4, terzihane2, terzihane3 (15 fiş) Paddle okuması; sonuçlar cihaz\serbest-paddle.json ve cihaz\terzihane2-paddle.json.

## Güncelleme 26.10 00:40: eğitim işi ayrı oturuma devrediliyor — [Claude#WqTeinGYcW] [İP:El yazısı OCR#RKxwbX devralındı]
Yusuf (25.10 21:35): OCR motorunu ayrık (bitişik olmayan) el yazısıyla eğitme işi ayrı bir oturumun; bu oturum eğitim BAŞLATMADI.
### Eğitim için mevcut çıktılar (hepsi bu klasörde)
- Model/kod: egitim\ (veri.py, egit.py, egit_emnist.py, egit_inceayar.py, etiketle.py, bolme.py, coz.py, olc.py); varsayılan model egitim\model.json (+ js\ içinde kopyası) — DEĞİŞTİRME kuralı: yalnız ölçüm iyileşir ve yanlış kabul 0 kalırsa.
- Veri: veri\emnist (SHA-256 kayıtlı, KAYNAK.md), veri\the-dataset (T-H-E Türkçe harfler, 78 sınıf), veri\tutanak-kirpinti (tutanak-1: 64, tutanak-3: 19 karakter; bunlar TEST), veri\yeni3-rakam (22 rakam, serbest metin), veri\el-yazisi-turkce (22 görsel + 62 küçük resim, etiketsiz).
- Ham örnekler: ornekler\ (tutanak-1/2/3, yeni2 fişler+iade, yeni3 6 sayfa, yeni4 16 görsel, terzihane2 14 fiş, terzihane3 15 fiş). Doğru değerler: tutanak-1.dogru.json, yeni\tutanak-3.dogru.json, yeni2\fisler.dogru.json (Claude okuması, Yusuf teyidi bekliyor).
- Ölçüm kayıtları: cihaz\OLCUM-*.md (varsayılan: tutanak-1 JS 7/8 YK 0; motor tutanak-1 7/8 kabul 5; tutanak-3 motor 5/7 kabul 0; liste-dışı YK 1/8; negatif 0). Önceki deneyler: EMNIST ön eğitimi ve yeni3 ince ayarı kazanç getirmedi (cihaz\OLCUM-arsiv-egitimi.md, OLCUM-yeni3.md).
- Bilinen engeller: kıvrık "1", açık "4", "g" gibi "9" (tutanak-3 yazarı) MNIST/EMNIST'te yok; gerçek kazanç tablo hücresi kırpıntıları ve çok yazarlı örnekten beklenir. Eski modelin MNIST kontrol doğruluğu 0,94 çıktı (önce 0,993), bölme yönü şüphesi açık.
- Kabul kapısı (öneri): yanlış kabul 0, isabet ≥ varsayılan, liste-dışı YK ≤ 1/8, negatif 0; ayar/test fotoğrafları ayrı tutulsun.
### Yarım kalan (eğitimle ilgisiz)
- yeni4 (16 görsel), terzihane2 (14 fiş) ve terzihane3 (15 fiş) Paddle okuması oturum yeniden başlayınca kesildi; yalnız yeni3 sonuçları var (cihaz\serbest-paddle.json). Gerekirse yeniden: `venv\Scripts\python.exe cihaz\serbest_paddle.py ornekler\yeni4\*.*` ve cihaz\terzihane2_paddle.py ile fişler (sırayla).
- Verifier GEÇTİ, TAARNAK'a r3 yeniden birleştirme bildirildi.

## 26.10 00:55: son
- Bellek isteği üzerine Paddle koşuları durduruldu; yeni4 (16 görsel), terzihane2 (14) ve terzihane3 (15 fiş) OKUNMADI. Eğitim oturumu bitince tek tek (fiş başına ayrı süreç) çalıştırılabilir. motor\paddle_motor.py şu an serbest, bu oturum o dosyada çalışmıyor.
- Test artıkları (log, boş crawl4ai klasörü) Geri Dönüşüm Kutusu'na taşındı.

## Güncelleme 26.10 01:20 — [Claude#HtqxxY] OCR eğitimi bu başlığa devredildi
Gece eğitimi ve motor hızlandırma: egitim\gece\DEVAM-GECE.md. Eğitim sürerken (07:30'a kadar) PaddleOCR koşmayın, RAM yetmiyor.


## 26.10 02:50: açık veri adayları (aramayla bulundu, indirilmedi, lisans sayfası doğrulanmadı) — [Claude#WqTeinGYcW]
Eğitim oturumu için ipuçları (Yusuf: "daha fazla ayrık ve birleşik el yazısı bul"):
- Chars74K English handwritten (tablet, 55 yazar, 62 sınıf, 3410 örnek, ~13 MB, ODbL; ayrık harf/rakam): https://mldata-static.ml.tu-berlin.de/repository/data/viewslug/chars74k-english-hnd/9.html
- Teklia/IAM-line (Hugging Face; birleşik satır; MIT etiketli ama IAM kaynağı yalnız ticari olmayan araştırma): https://huggingface.co/datasets/Teklia/IAM-line
- RKK01/SSL-HWD-Words (Hugging Face; kelime düzeyi, Apache-2.0, tarihî belgeler): https://huggingface.co/datasets/RKK01/SSL-HWD-Words
- emredeveloper/turkish-ocr (HF; sentetik Türkçe, MIT): https://huggingface.co/datasets/emredeveloper/turkish-ocr
- Zaten var: EMNIST, T-H-E. Türkçe gerçek el yazısı rakam/harf açık seti bulunamadı (Düzce Ü. seti kapalı erişim).
- Google görsel araması CAPTCHA verdi; CAPTCHA aşılmaz (Yusuf kendi tarayıcısında geçip görselleri klasöre kaydederse kullanılır).

## 26.10 03:05: Chars74K indirildi (Yusuf: "indir ve eğitim oturumuna bildir")
veri\chars74k-hnd\ (KAYNAK.md, SHA-256, ham\English\Hnd\Img 3410 PNG; ayrık el yazısı, 55 yazar, ODbL). IAM-line indirilmedi (yalnız ticari olmayan araştırma, büyük). Eğitim oturumu kullanabilir.

## 26.10 03:15: düzeltme
veri\chars74k-hnd\ kopyası KULLANILMAYACAK (eğitimde zaten veri\chars74k\ var; yinelenen, aynı SHA-256 beklenir). Bu oturum bundan sonra veri indirmez; veri işi "OCR motorunu ayrık el yazısıyla eğit" başlığında. Silme kararı Yusuf'undur.

## 26.10 03:40: IAM-line indirildi (Yusuf: "Onu da indir")
veri\iam-line\ (265,6 MB, 10.373 birleşik İngilizce el yazısı satırı, parquet; KAYNAK.md, SHA256.txt). Ticari olmayan koşul: model dağıtımı öncesi IAM şartları kontrol edilmeli. Eğitim oturumu kullanabilir.

## 26.10 03:55: IAM-line kuruldu (Yusuf: "iam da kur")
veri\iam-line\goruntu\ altında PNG + etiketler.csv (egitim\iam_ac.py ile; ~988 MB). Eğitim oturumu doğrudan kullanabilir.
