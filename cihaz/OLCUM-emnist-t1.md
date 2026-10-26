# Ölçüm: tutanak-1.jpg emnist-t1

Tablo: 8 veri satırı. CNN = `model-emnist.json`; çözümleme = `coz.py` (13.127 koddan biçime uyan 6350 aday).

| Satır | Doğru | CNN ham | Kısıtlı en iyi | Güven (nat) | Durum | Tesseract (temiz maske) | Tesseract (ham gri) | EasyOCR |
|---|---|---|---|---|---|---|---|---|
| 1 | T14525 | TT4525 | T14525 | 6.1 | sor | ? | ? | 744525 |
| 2 | T14522 | T74522 | T14522 | 5.8 | tamam | ? | ? | T14522 |
| 3 | T20191-08 | T26791-08 | T20191-08 | 9.2 | tamam | ? | ? | 720191-08 |
| 4 | T20097-01 | T20093-01 | T20092-01 (X) | 1.9 | sor | ? | ? | T400926-01 |
| 5 | T20236-02 | T20236102 | T20236-02 | 4.6 | tamam | ? | ? | T20236-01 |
| 6 | T20236-01 | T20236-01 | T20236-01 | 2.0 | sor | ? | ? | 720276-04 |
| 7 | T20136-02 | T20T36-02 | T20136-02 | 3.6 | tamam | ? | ? | 20430-02 |
| 8 | T20178-01 | T20178-03 | T20178-03 (X) | 2.3 | tamam | ? | ? | 720138-01 |

## Özet

- Kod doğruluğu (kısıtlı, en iyi aday): **6/8**
- Ham CNN tam eşleşme: 1/8; uzunluğu doğru satırlarda karakter doğruluğu: 58/66
- Yanlış-kabul (durum=tamam ama kod yanlış): **1**; 'sor' durumuna düşen: 3
- Adet doğru: 2/8
- Tesseract tam eşleşme: temiz maske 0/8, ham gri 0/8; EasyOCR 1/8
- Süre: bölme 1.0 sn (tam sayfa, numpy), CNN+çözümleme 4.0 sn (numpy referans, JS'e göre yavaş)
