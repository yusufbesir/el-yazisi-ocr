# REA ile statik inceleme: mevcut tesseract.js paketi ve yeni ElYazisiOCR kütüphanesi
[İP:El yazısı OCR#RKxwbX] · 2026-10-25 · yazan: [Claude#RKxwbX] · Yusuf'a ait, eğitim amaçlı. Değiştirme: yalnız bu iş parçacığı.

## Özet
- REA sağlık kontrolü: `inspect_apktool_client` → Apktool 3.0.3, `D:\Programlar\apktool\apktool.cmd` (çalışıyor).
- İncelenen klasör: `cihaz/rea-inceleme/` (tesseract.min.js 65 KB, ocr-worker.js 123 KB, elyazisi-ocr.js 34 KB). Araç: `analyze_javascript_application` (format: directory), kod çalıştırılmadan AST üzerinden.
- Sonuç: 3 dosya ayrıştırıldı, 0 ayrıştırma hatası, 24 modül (tesseract.min.js webpack paketi), 37 bulgu. Yalnız **1 ağ isteği ilişkisi** (tesseract tarafı, `fetch`); ElYazisiOCR'da ağ/çocuk süreç/zamanlayıcı/depolama ilişkisi **yok**.

## Mevcut OCR (tesseract.js) hakkında bulgular
- Paket webpack çıktısı; `tesseract.min.js` içinde CDN adresleri gömülü: `cdn.jsdelivr.net/npm/tesseract.js@v…`, `tesseract.js-core@v…`, `@tesseract.js-data/…`. Program bunları `workerPath`/`langPath`/`cacheMethod:"none"` ayarlarıyla ve `self.fetch`'i sarmalayan bir blob worker ile yerelde devre dışı bırakıyor (uygulama.js ocrCalistir). Yani ağ isteği **niyetten değil kütüphaneden** geliyor; yanlış ayarla kolayca dışarı çıkabilir.
- Worker `Blob` + `URL.createObjectURL` ile üretiliyor; CSP'de `worker-src blob:` ve `script-src blob:` açık tutulmak zorunda. Yeni kütüphane bunlara gerek bırakmıyor.
- WASM çekirdeği (ocr-core.js 3,9 MB) + Türkçe dil verisi (ocr-tur.js 2,8 MB) base64 gömülü: toplam ~6,9 MB, ilk fotoğrafta yükleniyor. Eski tarayıcıda WebAssembly yoksa hiç çalışmaz.
- İşlevsel sınır (REA'dan değil, ölçümden): el yazısı stok kodlarında 0/8 doğru (egitim/OLCUM.md).

## Yeni kütüphane (js/elyazisi-ocr.js) hakkında bulgular
- Statik tarama (REA + grep): `fetch`, `XMLHttpRequest`, `WebSocket`, `eval`, `new Function`, `innerHTML`, `document.write`, `importScripts`, `localStorage` **yok**. Tek `.src` kullanımı: EXIF yön sınaması için 2×1 piksellik gömülü data-URI ve kullanıcının seçtiği dosyanın `createObjectURL` adresi (ikisi de yerel; okunduktan sonra `revokeObjectURL`).
- ES5 uyumu: `let/const`, ok fonksiyonu, `class`, şablon dizgi yok. Promise kullanmıyor (geri çağrı). Canvas 2D dışında tarayıcı özelliği gerekmiyor.
- Tek global `ElYazisiOCR`; model `window.ELYAZISI_MODEL` (model.js, 480 KB JSON ağırlık). Toplam yük ~515 KB (tesseract'ın 1/13'ü).
- Bağımsız kanıt: `node test/node-test.js --kenar 2000` → 7/8 kod, yanlış kabul 0, 182 ms (bu makinede).

## Sınırlar
- REA inceleme statiktir; çalışma zamanı davranışını kanıtlamaz (REA'nın kendi "limitations" alanı). Çalışma zamanı kanıtı Playwright tarayıcı testi ve ağ isteği sayımıyla ayrıca alınır (test/tarayici-test.js).
- REA'nın web paketi analizi (`analyze_web_bundle`) CDP (açık tarayıcı) ister; burada gerekmedi.

## Kanıt kimlikleri (REA)
- apktool: `ev_1e619f3b…609c`
- javascript application: `ev_a6603e3d…b7ac` (özet görünümü `ev_f8cb6b85…55a8`, modül sayfası `ev_13d8a1f0…c672`)
