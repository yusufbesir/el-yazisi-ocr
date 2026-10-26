# motor/ - güçlü OCR motoru (masaüstü)
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı

- `paddle_motor.py`: tutanak fotoğrafını hücre hücre PaddleOCR (PP-OCRv5_server_rec, yalnız tanıma) ile okur. Protokol: `PROTOKOL.md`.
- Tur 2 yöntemi `sayfa+hucre`: önce küçültülmüş TAM sayfada PaddleOCR det+rec; tespit merkezi bolme satır/sütununa eşlenir, stok/adet metni birleştirilir. Satırda stok metni (≥2 rakam) yoksa hücre tanımaya düşülür; satırda `kaynak:"sayfa"|"hucre"`. Süre ~65-70 sn/sayfa.
- Adet: ham okuma tek karakterli rakamsa güven eşiği 0.6, aksi 0.8; hücreden okurken 3 px kenar kırpılır (çizgi artığı).
- Tur 3: bizim CNN (egitim/model.json, numpy) her stok/adet hücresini de okur; `kabul` yalnız Paddle kabul VE CNN kısıtlı ilk adayı aynıysa (aksi `sor`, `uzlasma:false`, `cnn:{secilen,guven}`); adet de CNN ile uyuşmalı. Tam sayfa yerine tablo kırpıntısında (+20 px) det+rec: ~30-40 sn. Farklı yazarda CNN uyuşmaz, çoğu satır `sor` olur (güvenli ama otomatik kabul az).
- Model: motor.json `det_model`/`rec_model` (null=varsayılan v6); indirilen modellerin sha256'sı `model-kaynak.json`.
- Bilinen risk (tur 2, tur 3'te CNN uzlaşmasıyla kapandı): Paddle yanlış ama geçerli bir kodu yüksek güvenle okuyabilir (d1=0, güven .92-.99) ve kabul çıkar; kısıtlı eşleme bunu yakalayamaz.
- (Tur 1) Akış: görüntü uzun kenar 2000'e küçülür → `egitim/bolme.py` hücreleri keser → her hücre 24 px beyaz kenarla "gri" ve "temiz" (maske) olarak okunur, Paddle güveni yüksek olan seçilir → stok kodu listeyle kısıtlanır (en yakın kod; T'siz yazıma T eklenip de denenir) → durum kabul/sor/bos.
- Kabul kuralı: d1 ≤ 1, d2 > d1 ve güven ≥ 0.80. Aksi "sor"; hiçbir kod sessizce eklenmez.
- Servis: `venv\Scripts\python.exe motor\paddle_motor.py --servis` (stdin/stdout JSON satırları; stderr günlük). Önce `kok` ile izinli klasör bildirilir.
- Ölçüm: `--olc foto dogru.json stok-kodlari.json [--json cikti.json]`. Test: `motor\test_servis.py`. Python yolu: `motor.json`.
- Sınırlar: tablo çizgileri `bolme.py` ile bulunamazsa `yontem:"sayfa"` ve boş `satirlar` döner (tam sayfa okuma yok). Tablo altı satırlar (toplam vb.) sondan atılır.
- Soğuk başlangıç ~10 sn, hücre başına ~1,9 sn (CPU). Paddle ve torch aynı süreçte kullanılmaz.
- Adet hücresinde tek hane "1" güveni sık 0.8 altında kalır; bu yüzden "sor" çıkar (eşik protokoldeki gibi bırakıldı).
- Ağ: HF_HUB_OFFLINE=1 ve model kaynak denetimi kapalı; modeller `%USERPROFILE%\.paddlex` önbelleğinde.
- `_err*.txt`, `_servis_stderr.txt`: günlük çıktıları, kendi ürettiğim geçici dosyalar.

- (2026-10-25, devralan) Yön düzeltme: `yon_bul` (4 dönüşte okuma kalitesi; dik fişte 0° yeterliyse diğerleri denenmez), `sayfa_oku(..., yon_duzelt=True)` ve istekte `yon_duzelt:false`. Fiş okuma: `paddle_motor.py --fis foto... [--json cikti.json]` (yön düzeltmeli tam sayfa metin).
- İade formu: `egitim/bolme.py` yedek `gevsek` tablo yolu (`bolme.SON`); gevşek yolda motor eğiklik açısını renkli görüntüye de uygular, başlık satırını atlar, adet otomatik kabulünü kapatır. Ölçüm: `cihaz/OLCUM-fisler2.md`.
