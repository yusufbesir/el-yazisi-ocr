// yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı
// Taban: r2-taban/preload.js + motorDurum/gucluOku.
'use strict';
// Sandbox preload: yalnız 'electron' require edilebilir. Arayüze yalnız kayıt klasörü işlemleri açılır.
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('masaustu', {
  bilgi: () => ipcRenderer.invoke('depo:bilgi'),
  oku: (ad) => ipcRenderer.invoke('depo:oku', String(ad)),
  yaz: (ad, metin) => ipcRenderer.invoke('depo:yaz', String(ad), String(metin)),
  dogrula: () => ipcRenderer.invoke('depo:dogrula'),
  tara: () => ipcRenderer.invoke('depo:tara'),
  icAl: (ad) => ipcRenderer.invoke('depo:icAl', String(ad)),
  motorDurum: () => ipcRenderer.invoke('ocr:motorDurum'),
  gucluOku: (base64, kodlar) => ipcRenderer.invoke('ocr:gucluOku', String(base64), Array.isArray(kodlar) ? kodlar.map(String) : []),
  klasoruAc: () => ipcRenderer.invoke('depo:klasoruAc'),
  pdfKaydet: (ad) => ipcRenderer.invoke('depo:pdfKaydet', String(ad))
});
