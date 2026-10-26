# Ölçüm: tutanak-1.jpg cihaz

Tablo: 8 veri satırı. CNN = `model.json`; çözümleme = `coz.py` (13.127 koddan biçime uyan 12690 aday).

| Satır | Doğru | CNN ham | Kısıtlı en iyi | Güven (nat) | Durum | Tesseract (temiz maske) | Tesseract (ham gri) | EasyOCR |
|---|---|---|---|---|---|---|---|---|
| 1 | T14525 | T14525 | T14525 | 1.6 | sor | ? | ? | 744525 |
| 2 | T14522 | T14522 | T14522 | 5.7 | tamam | ? | ? | T14522 |
| 3 | T20191-08 | T20191-08 | T20191-08 | 9.2 | tamam | ? | ? | 720191-08 |
| 4 | T20097-01 | T20093-01 | T20097-01 | 0.8 | sor | ? | ? | T400926-01 |
| 5 | T20236-02 | T20236102 | T20236-02 | 6.0 | tamam | ? | ? | T20236-01 |
| 6 | T20236-01 | T20236-01 | T20236-01 | 3.7 | tamam | ? | ? | 720276-04 |
| 7 | T20136-02 | T20136-02 | T20136-02 | 4.1 | tamam | ? | ? | 20430-02 |
| 8 | T20178-01 | T20178-07 | T20178-03 (X) | 0.9 | sor | ? | ? | 720138-01 |

## Özet

- Kod doğruluğu (kısıtlı, en iyi aday): **7/8**
- Ham CNN tam eşleşme: 5/8; uzunluğu doğru satırlarda karakter doğruluğu: 63/66
- Yanlış-kabul (durum=tamam ama kod yanlış): **0**; 'sor' durumuna düşen: 3
- Adet doğru: 7/8
- Tesseract tam eşleşme: temiz maske 0/8, ham gri 0/8; EasyOCR 1/8
- Süre: bölme 1.4 sn (tam sayfa, numpy), CNN+çözümleme 5.1 sn (numpy referans, JS'e göre yavaş)
