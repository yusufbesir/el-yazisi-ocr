# Ölçüm: tutanak-1.jpg emnist-t3

Tablo: 8 veri satırı. CNN = `model-emnist.json`; çözümleme = `coz.py` (13.127 koddan biçime uyan 6350 aday).

| Satır | Doğru | CNN ham | Kısıtlı en iyi | Güven (nat) | Durum | Tesseract (temiz maske) | Tesseract (ham gri) | EasyOCR |
|---|---|---|---|---|---|---|---|---|
| 1 | T12631 | T12521 | T12521 (X) | 2.5 | tamam | ? | ? | T1-21 |
| 2 | T20062-01 | 02--01 | T27001 (X) | 6.5 | sor | ? | ? | 1062-06 |
| 3 |  | 5852346-- | T15234-01 (X) | 1.3 | sor | ? | ? | 211231 |
| 4 | T10309 | 167309 | T12309 (X) | 0.7 | sor | ? | ? | 10299 |
| 5 | T14594 | 14581T | T15012 (X) | 1.7 | sor | ? | ? | T |
| 6 | T20163-07 | 0163-02- | T15200-24 (X) | 2.0 | sor | ? | ? | 20663-214 |
| 7 | T14498 | 144T78 | T14578 (X) | 5.7 | sor | ? | ? | T46128 |
| 8 | T13881 | 435381 | T14381 (X) | 1.6 | sor | ? | ? | 144 |

## Özet

- Kod doğruluğu (kısıtlı, en iyi aday): **0/8**
- Ham CNN tam eşleşme: 0/8; uzunluğu doğru satırlarda karakter doğruluğu: 11/30
- Yanlış-kabul (durum=tamam ama kod yanlış): **1**; 'sor' durumuna düşen: 7
- Adet doğru: 3/8
- Tesseract tam eşleşme: temiz maske 0/8, ham gri 0/8; EasyOCR 0/8
- Süre: bölme 0.8 sn (tam sayfa, numpy), CNN+çözümleme 3.1 sn (numpy referans, JS'e göre yavaş)
