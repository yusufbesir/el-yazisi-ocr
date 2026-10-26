---
description: Gece eğitimi (ayrık el yazısı) ve motor hızlandırma devir notu
sahip: Yusuf
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY]
tarih: 2026-10-26
degistirme: yalnız bu iş parçacığı (devralan başlık devam edebilir, etiketini ekler)
---
# DEVAM — Gece eğitimi ve motor hızlandırma

## Özet
- Yusuf'un isteği (25.10 21:33): seçim yaptırma kalsın; motor yavaş; ayrık (bitişik değil) el yazısı örnekleri araştır, eğitimi çoğalt, sabaha kadar eğit.
- Gece zinciri `zincir.ps1` (01:04 başladı): `gece_egit.py kod` 04:50'ye kadar, sonra `gece_egit.py harf` 07:30'a kadar. Süreç PID'leri `surecler.txt`.
- RAM ~1,4 GB boş: iki eğitim aynı anda bellek yetersizliğiyle düştü, bu yüzden sırayla. Eğitim sürerken PaddleOCR koşma.

## Veri (eğitim)
- `veri/onbellek/` (hazirla.py): EMNIST digits/harf, T-H-E (Türkçe harfler, %10 test ayrıldı), Chars74K EnglishHnd (3.410, 55 yazar), HASYv2 Latin alt kümesi (4.658).
- `veri/fontlar/`: 19 OFL/Apache el yazısı fontu (Google Fonts deposu); eksik glifler (notdef) atlanır.
- İndirilenler 26.10: HASYv2 (zenodo.org/records/259444, ODbL), Chars74K (info-ee.surrey.ac.uk, atıf: de Campos ve ark. 2009), fontlar (github google/fonts). SHA-256: yapılacak (KAYNAK.md'ye).
- Her tur 160k örnek yeniden bozulur (afin, elastik, kalem kalınlığı, tablo çizgisi kalıntısı, ikili maske, bulanıklık) → bolme.mnist_normalle.
- Gerçek tutanak kırpıntıları EĞİTİME GİRMEZ: seçim kümesi tutanak-1 + yeni3, son test tutanak-3.

## Model
- conv32-conv32-pool-conv64-conv64-pool-fc128-fcK, BN dışa aktarımda conv'a katlanır; JSON biçimi eskisiyle aynı (cikarim_numpy ve JS çalışır).
- Çıktılar: `kod/en-iyi.json` (+.pt), `kod/gecmis.json`, `kod/gunluk.txt`; aynısı `harf/`. Kesintide `son.pt`'den sürer (aynı komutu yeniden çalıştır).
- Taban karşılaştırma (karsilastir.py, gerçek kırpıntı): eski model.json t1 61/64, t3 10/19, yeni3 26/30; inceayar t1 64/64 (t1 ile eğitildi), t3 11/19, yeni3 23/30. Gece tur 1: t1 %95,3, t3 %47,4, yeni3 %93,3.
- Büyük model döngülü numpy'de karakter başına ~0,5 sn: `cikarim_numpy.ileri_toplu` eklendi (vektörleştirilmiş, fark < 1e-6); motor artık onu kullanır.

## Motor hızlandırma (motor/paddle_motor.py, [Claude#HtqxxY] etiketli)
- Ölçüm öncesi (hiz_profil.py, tutanak-1, eğitimle çekişmeli CPU): toplam 81 sn; Paddle tam sayfa det+rec 2 çağrı 67 sn (yön bulma 46 sn dahil), hücre rec 24 çağrı 9 sn, CNN 1,4 sn, bölme 0,5 sn.
- Yapılan: (1) 0°'de sıkı tablo bulunursa yön araması atlanır; (2) tam sayfa metni ≥2 rakam verdiyse stok hücre tanıma yapılmaz; (3) det modeli açılışta ısıtılır; (4) CNN toplu çıkarım. Sözdizimi derlendi; DAVRANIŞ ÖLÇÜLMEDİ.

## Yusuf kuralı (25.10 22:59, TAARNAK'ta uygulanıyor)
- Sayıyla başlayan el yazısı kodlara "T" eklenir; 01K, 01G, PK gibi istisnalar hariç (kural değişebilir).
- Bizde karşılığı: coz.py CEZA_T (T'siz yazım T ekleyerek eşlenir). Ancak kod deseni `^T\d{4,5}(-\d{2})?$` olduğu için 01K/PK türü kodlar motorun kısıtlı listesine hiç girmez; sabah ölçümde bu istisnaların listede olup olmadığına bak, varsa deseni Yusuf'a öner (sessizce değiştirme).

## 03:15 yeniden düzen (Yusuf: Türkçe kelime/harf öncelikli; denetmen 4 bulgu)
- Kod modeli 20 turda durdu (01:33 RAM düşmesi + 02:24 TAARNAK derlemesi duraklatması). Son: kod\son.pt, kod\en-iyi.json (tur 20, yeni seçimle).
- Yeni: `kelime_egit.py` (CTC kelime tanıyıcı: ayrık = gerçek el yazısı harflerden dizilmiş kelime, bitişik = bitişik fontlar; FrequencyWords tr/en; sözlükle imla düzeltme ayrı ölçülür). Zincir: kelime 06:35'e, sonra harf 07:30'a kadar.
- Denetmen: (1) yanlış kabul sabah motor ölçümünde ayrı (doğru/sor/yanlış kabul); (2) seçim artık arşiv TEST bölmelerinin bozuk kopyası + saklı 3 font, gerçek kırpıntılar yalnız kayıt; (3) KAYNAK-EK tablosu, Chars74K/USPS çıkarıldı; (4) eğitimde kaynak sayımı (font ayrı), doğrulamada `font-sakli` ve kelimede ayrik/font-blok/font-bitisik ayrı.
- Bilinen kusur: kod en-iyi seçimi eski düzende gerçek kırpıntıyla yapılmıştı → en-iyi-eski-secim.json olarak ayrıldı, kullanılmaz.

## 05:02 eski OCR başlığından devralınanlar
- Paddle okuması yarım: ornekler\yeni4, terzihane2, terzihane3 (cihaz\serbest_paddle.py, cihaz\terzihane2_paddle.py; ayrıntı ana DEVAM.md "21:30"). Eğitim bitince, sırayla, tek seferde bir koşu.
- Yusuf teyidi bekleyen: ornekler\yeni2\fisler.dogru.json ve ornekler\yeni\tutanak-3.dogru.json (kontrol sayfası ornekler\kontrol-fisler.html). Sabah raporunda hatırlat.

## 07:50 sıradaki ağır işler (sıra Adım Adım'dan sonra; denetmen)
1. Ayrı doğrulama kümelerinde yanlış kabul ölçümü (coz.stok_coz ile, bozuk arşiv rakamlarından dizilmiş kodlar + saklı fontlar).
2. Liste-dışı ve negatif testler yeni modelle (test\liste-disi-test.js, test\node-test.js; ELYAZISI_MODEL_JS).
3. Kod ve harf modellerini Chars74K'sız SIFIRDAN yeniden eğit (gece_egit.py; kod/ ve harf/ klasörlerini yeniden adlandırıp boş başlat).
4. Hız: aynı fotoğraf 3 tekrar, boş makinede, eski (yedek) ve yeni paddle_motor ile.
5. Paddle okumaları: yeni4, terzihane2/3.

## Sabah yapılacaklar (sırayla)
1. Zincir bitince: `python karsilastir.py ..\model.json kod\en-iyi.json` ; tutanak-3 son test.
2. `motor\paddle_motor.py --olc` tutanak-1 ve tutanak-3 (yeni model `--cnn egitim\gece\kod\en-iyi.json` ile ve eski modelle): yanlış kabul 0 şart; eski ölçümlerle (cihaz/OLCUM-*.md) karşılaştır.
3. `hiz_profil.py` ile önce/sonra süre; `motor\test_servis.py`.
4. Verifier (Sonnet) bağımsız kontrol; JS'de yeni model hızı (node).
5. Varsayılan model yalnız yanlış kabul 0 ve gerçek kırpıntıda iyileşme varsa değişir; değilse yan dosya olarak kalır.
6. Rapor Yusuf'a; kasa notu.

## 07:55 DURDURULDU (Yusuf: "işlemleri durdur") — [Claude#HtqxxY]
- Çalışan süreç yok (eğitim 07:31'de bitti; doğrulama ajanı bitmişti). Yeni iş başlatılmadı.
- Bağımsız doğrulama: egitim\gece\DOGRULAMA-SABAH.md — 3 GEÇTİ, 2 KALDI:
  - KALDI (motor): tablo bulununca yön aramasını atlama 180° ters fotoğrafta da atlıyor. Hücre 0°/180° karşılaştırması eklendi ama t1-180 testinde yakalamadı → özellik KAPATILDI (YON_ATLAMA_ACIK=False; eski davranış). Diğer motor değişiklikleri (det ısınma, tembel hücre tanıma, toplu CNN) yerinde.
  - KALDI (rapor sayıları): kelime en iyi tur 23 (rapor 22), son tur sentetik blok %53/bitişik %53/ayrık %22, gerçek bitişik kelime %47; IAM test sayıları konsol çıktısından (kaynak dosyası yok); dünkü t1 süresi olc json'da 42 sn. SABAH-RAPORU düzeltilmedi (durdurma), sıradaki iş.
- Sıradaki (Yusuf izin verince): rapor sayılarını düzelt; 07:50 listesi (yanlış kabul ölçümü, liste-dışı/negatif test, Chars74K'sız yeniden eğitim, tekrarlı hız ölçümü, Paddle okumaları); 180° denetimini düzgün çöz.

## 09:20 durum — [Claude#HtqxxY]
- Chars74K Yusuf onayıyla geri eklendi → sıfırdan yeniden eğitim İPTAL (zincir3.ps1 hazır ama gereksiz).
- Yanlış kabul (ayrı doğrulama, yk_olc.py, sabah\yk-olcum.json): eski model listede YK 21/600, liste-dışı 2/300; gece modeli YK 1/600, liste-dışı 4/300, doğru kabul 364 (eski 100).
- JS testleri: gece modeli liste-dışı 0/8 (eski 1/8), negatif geçti, tutanak-1 6/8 (eski 7/8), sor 5 (eski 3), 1,8 sn (eski 0,4). js\model-gece-kod.js (varsayılan değil).
- İnce ayar (inceayar_gece.py; sis/bozukluk/eksiklik artırma): dışarıda tutulan fotoğrafta kazanç yok/çok küçük, genel YK arttı → hiçbiri kullanıma alınmadı.
- Paddle okumaları bitti: yeni4 16 görsel (cihaz\serbest-paddle.json), terzihane2+3 29 fiş (cihaz\terzihane2-paddle.json).
- Yeni veri: nist-sd19, cvl-digit-strings, ardis (KAYNAK-EK Ek 8). Kayıt isteyen sayfalar Claude tarayıcısında açıldı (GNHK, Kaggle A-Z, CVL, Kaggle Türkçe arama).
- Ek zip kopyaları Yusuf isteğiyle Geri Dönüşüm Kutusu'na (1,24 GB).
- Açık: 180° yön denetimi (atlama kapalı); varsayılan model kararı (Yusuf); fisler/tutanak-3 doğru değer teyidi; Paddle çıktısına Türkçe imla düzeltmesi denemesi (öneri).
