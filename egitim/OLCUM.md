# Ölçüm: tutanak-1.jpg 

Tablo: 8 veri satırı. CNN = `model.json`; çözümleme = `coz.py` (13.127 koddan biçime uyan 6350 aday).

| Satır | Doğru | CNN ham | Kısıtlı en iyi | Güven (nat) | Durum | Tesseract (temiz maske) | Tesseract (ham gri) | EasyOCR |
|---|---|---|---|---|---|---|---|---|
| 1 | T14525 | T14525 | T14525 | 1.6 | sor | T | T | 744525 |
| 2 | T14522 | T14522 | T14522 | 6.1 | tamam | 74822 | 14820 | T14522 |
| 3 | T20191-08 | T20191-08 | T20191-08 | 9.2 | tamam | T209-0 | T20144-0 | 720191-08 |
| 4 | T20097-01 | T20093-01 | T20097-01 | 0.8 | sor | T0-07 | T-01 | T400926-01 |
| 5 | T20236-02 | T20236102 | T20236-02 | 6.0 | tamam | T2023-01 |  | T20236-01 |
| 6 | T20236-01 | T20236-01 | T20236-01 | 3.7 | tamam | T2076-04 |  | 720276-04 |
| 7 | T20136-02 | T20136-02 | T20136-02 | 4.1 | tamam | 720186-62 |  | 20430-02 |
| 8 | T20178-01 | T20178-07 | T20178-03 (X) | 0.9 | sor | 720175-07 | 720198-0 | 720138-01 |

## Özet

- Kod doğruluğu (kısıtlı, en iyi aday): **7/8**
- Ham CNN tam eşleşme: 5/8; uzunluğu doğru satırlarda karakter doğruluğu: 63/66
- Yanlış-kabul (durum=tamam ama kod yanlış): **0**; 'sor' durumuna düşen: 3
- Adet doğru: 7/8
- Tesseract tam eşleşme: temiz maske 0/8, ham gri 0/8; EasyOCR 1/8
- Süre: bölme 2.2 sn (tam sayfa, numpy), CNN+çözümleme 4.2 sn (numpy referans, JS'e göre yavaş)

## Notlar

- Eğitim: MNIST (60k) + 60k bozulmuş MNIST + 7k sentetik T + 7k sentetik "-" + 7k bayraklı "1" (sentetik). Gerçek tutanak kırpıntıları eğitime girmedi.
- Tur 1 (ilk model): 7/8 kod, 1 yanlış-kabul (satır 1, "5"->"2" yerine 7 okundu), adet 3/8 (bayraklı "1" 7 okunuyordu). Tur 2: bayraklı "1" sentetik verisi, daha güçlü afin bozulma, benek filtresi, olasılık sıcaklığı (TAU=1.5) eklendi; yanlış-kabul 0'a indi. TAU ve benek eşiği bu tek fotoğraf görülerek ayarlandı: tek örnek üzerinde ölçüm, genelleme kanıtı değildir.
- Satır 4 (üstü çizili): doğru aday ilk sırada ama güven düşük, "sor" durumuna düştü (beklenen davranış).
- Satır 8: doğru kod 2. sırada, "sor" durumunda; kullanıcı seçer. Sessiz hata yok.
- Tesseract/EasyOCR aynı hücrelerde el yazısını okuyamıyor (T14525 -> "744525"/"T"), tasarım hipotezi doğrulandı.
- Karakter bölme: 8/8 satırda doğru kutu sayısı (6 veya 9). Birleşik karakterler için `genis_bol` (kutu sayısı 6/9 değilse en oranlı geniş kutuyu böl) kullanıldı.
