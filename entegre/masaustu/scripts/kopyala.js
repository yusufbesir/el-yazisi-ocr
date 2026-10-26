'use strict';
// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
// Test düzeni: app/ = ../yeni-web (tüm arayüz dosyaları, elyazisi/ dahil) + r2-taban/web/index.html + ocr-uygulama.js (uygulama.js adıyla).
// Gerçek depoda kaynak web/ klasörüdür (BENIOKU.md, DEGISIKLIK.md).
const fs = require('fs');
const path = require('path');
const taban = path.join(__dirname, '..');
const hedef = path.join(taban, 'app');
fs.rmSync(hedef, { recursive: true, force: true });
fs.cpSync(path.join(taban, '..', 'yeni-web'), hedef, { recursive: true });
for (const f of ['index.orijinal.html', 'uygulama.orijinal.js']) fs.rmSync(path.join(hedef, f), { force: true });
fs.copyFileSync(path.join(taban, 'r2-taban', 'web', 'index.html'), path.join(hedef, 'index.html'));
fs.copyFileSync(path.join(taban, 'ocr-uygulama.js'), path.join(hedef, 'uygulama.js'));
console.log('app/ güncellendi:', fs.readdirSync(hedef).length, 'öğe');
