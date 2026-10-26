# Ölçüm: tutanak-1.jpg t3

Tablo: 8 veri satırı. CNN = `model.json`; çözümleme = `coz.py` (13.127 koddan biçime uyan 6350 aday).

| Satır | Doğru | CNN ham | Kısıtlı en iyi | Güven (nat) | Durum | Tesseract (temiz maske) | Tesseract (ham gri) | EasyOCR |
|---|---|---|---|---|---|---|---|---|
| 1 | T12631 | T12221 | T12221 (X) | 0.7 | sor | ? | ? | T1-21 |
| 2 | T20062-01 | 02--01 | T12201 (X) | 2.2 | sor | ? | ? | 1062-06 |
| 3 |  | 6152546-- | T15259-02 (X) | 0.2 | sor | ? | ? | 211231 |
| 4 | T10309 | 167303 | T12303 (X) | 0.1 | sor | ? | ? | 10299 |
| 5 | T14594 | 145911 | T10911 (X) | 0.3 | sor | ? | ? | T |
| 6 | T20163-07 | 2163-07- | T20132-22 (X) | 5.0 | sor | ? | ? | 20663-214 |
| 7 | T14498 | 144578 | T14578 (X) | 2.6 | sor | ? | ? | T46128 |
| 8 | T13881 | 435381 | T14381 (X) | 6.1 | sor | ? | ? | 144 |

## Özet

- Kod doğruluğu (kısıtlı, en iyi aday): **0/8**
- Ham CNN tam eşleşme: 0/8; uzunluğu doğru satırlarda karakter doğruluğu: 10/30
- Yanlış-kabul (durum=tamam ama kod yanlış): **0**; 'sor' durumuna düşen: 8
- Adet doğru: 6/8
- Tesseract tam eşleşme: temiz maske 0/8, ham gri 0/8; EasyOCR 0/8
- Süre: bölme 0.8 sn (tam sayfa, numpy), CNN+çözümleme 3.3 sn (numpy referans, JS'e göre yavaş)
