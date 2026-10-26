// Nebim içe aktarma dosyası (.xlsx) üretici: çevrimdışı çalışır, kütüphane gerektirmez.
// Sütun düzeni Nebim "örnek" şablonunu izler (sayfa adı "Excel", 44 sütun).
// Kullanım: window.nebimIndir([{k:'T14525', r:'49', b:'M'}], 'tutanak-2026-001.xlsx')
(function () {
  'use strict';

  var BASLIKLAR = ['Barcode','ItemTypeCode','ItemCode','ColorCode','ItemDim1Code','ItemDim2Code','ItemDim3Code','Qty1','Qty2','LineDescription','PriceCurrencyCode','PriceExchangeRate','Price','PriceVI','DocCurrencyCode','LDisRate1','LDisRate2','LDisRate3','LDisRate4','LDisRate5','UnitOfMeasureCode','PaymentPlanCode','SalespersonCode','CostCenterCode','ITAtt01','ITAtt02','ITAtt03','ITAtt04','ITAtt05','ITAtt06','ITAtt07','ITAtt08','ITAtt09','ITAtt10','LineSumID','LotCode','ImportFileNumber','ExportFileNumber','ProductSerialNumber','PurchasePlanCode','BatchCode','GLTypeCode','ManufactureDate','ExpiryDate'];

  function kac(s) {
    return String(s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
  }

  function sutunAdi(i) {
    var s = '';
    i++;
    while (i > 0) { var m = (i - 1) % 26; s = String.fromCharCode(65 + m) + s; i = Math.floor((i - 1) / 26); }
    return s;
  }

  function metin(ref, v) {
    return '<c r="' + ref + '" t="inlineStr"><is><t xml:space="preserve">' + kac(v) + '</t></is></c>';
  }
  function sayi(ref, v) {
    return '<c r="' + ref + '"><v>' + v + '</v></c>';
  }

  function sayfaXml(satirlar) {
    var x = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>';
    x += '<row r="1">';
    for (var i = 0; i < BASLIKLAR.length; i++) x += metin(sutunAdi(i) + '1', BASLIKLAR[i]);
    x += '</row>';
    for (var n = 0; n < satirlar.length; n++) {
      var s = satirlar[n] || {};
      var rn = n + 2;
      var deger = {
        ItemCode: s.k, ColorCode: s.r, ItemDim1Code: s.b,
        DocCurrencyCode: 'TRY', UnitOfMeasureCode: 'AD'
      };
      var sayilar = { ItemTypeCode: 1, Qty1: 1, Qty2: 0, Price: 0, LineSumID: 0 };
      x += '<row r="' + rn + '">';
      for (var c = 0; c < BASLIKLAR.length; c++) {
        var ad = BASLIKLAR[c], ref = sutunAdi(c) + rn;
        if (Object.prototype.hasOwnProperty.call(sayilar, ad)) x += sayi(ref, sayilar[ad]);
        else if (Object.prototype.hasOwnProperty.call(deger, ad)) x += metin(ref, deger[ad] == null ? '' : deger[ad]);
        else x += metin(ref, '');
      }
      x += '</row>';
    }
    return x + '</sheetData></worksheet>';
  }

  var XMLH = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>';

  function parcalar(satirlar) {
    return [
      ['[Content_Types].xml', XMLH +
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
        '<Default Extension="xml" ContentType="application/xml"/>' +
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' +
        '</Types>'],
      ['_rels/.rels', XMLH +
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' +
        '</Relationships>'],
      ['xl/workbook.xml', XMLH +
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
        '<sheets><sheet name="Excel" sheetId="1" r:id="rId1"/></sheets></workbook>'],
      ['xl/_rels/workbook.xml.rels', XMLH +
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>' +
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' +
        '</Relationships>'],
      ['xl/styles.xml', XMLH +
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>' +
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>' +
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>' +
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>' +
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>' +
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>' +
        '</styleSheet>'],
      ['xl/worksheets/sheet1.xml', sayfaXml(satirlar)]
    ];
  }

  var CRC_TABLO = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
      var c = n;
      for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32(b) {
    var c = 0xFFFFFFFF;
    for (var i = 0; i < b.length; i++) c = CRC_TABLO[(c ^ b[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  function zipYap(dosyalar) {
    var enc = new TextEncoder();
    var yerel = [], merkez = [], offset = 0, merkezBoyut = 0;
    var d = new Date();
    var dosTime = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
    var dosDate = (((d.getFullYear() - 1980) & 0x7F) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();

    dosyalar.forEach(function (f) {
      var ad = enc.encode(f[0]);
      var veri = enc.encode(f[1]);
      var crc = crc32(veri);

      var lh = new DataView(new ArrayBuffer(30));
      lh.setUint32(0, 0x04034B50, true);
      lh.setUint16(4, 20, true);
      lh.setUint16(6, 0x0800, true);      // UTF-8 dosya adı
      lh.setUint16(8, 0, true);           // STORE
      lh.setUint16(10, dosTime, true);
      lh.setUint16(12, dosDate, true);
      lh.setUint32(14, crc, true);
      lh.setUint32(18, veri.length, true);
      lh.setUint32(22, veri.length, true);
      lh.setUint16(26, ad.length, true);
      lh.setUint16(28, 0, true);
      yerel.push(new Uint8Array(lh.buffer), ad, veri);

      var ch = new DataView(new ArrayBuffer(46));
      ch.setUint32(0, 0x02014B50, true);
      ch.setUint16(4, 20, true);
      ch.setUint16(6, 20, true);
      ch.setUint16(8, 0x0800, true);
      ch.setUint16(10, 0, true);
      ch.setUint16(12, dosTime, true);
      ch.setUint16(14, dosDate, true);
      ch.setUint32(16, crc, true);
      ch.setUint32(20, veri.length, true);
      ch.setUint32(24, veri.length, true);
      ch.setUint16(28, ad.length, true);
      ch.setUint16(30, 0, true);
      ch.setUint16(32, 0, true);
      ch.setUint16(34, 0, true);
      ch.setUint16(36, 0, true);
      ch.setUint32(38, 0, true);
      ch.setUint32(42, offset, true);
      merkez.push(new Uint8Array(ch.buffer), ad);

      merkezBoyut += 46 + ad.length;
      offset += 30 + ad.length + veri.length;
    });

    var son = new DataView(new ArrayBuffer(22));
    son.setUint32(0, 0x06054B50, true);
    son.setUint16(4, 0, true);
    son.setUint16(6, 0, true);
    son.setUint16(8, dosyalar.length, true);
    son.setUint16(10, dosyalar.length, true);
    son.setUint32(12, merkezBoyut, true);
    son.setUint32(16, offset, true);
    son.setUint16(20, 0, true);

    return yerel.concat(merkez, [new Uint8Array(son.buffer)]);
  }

  window.nebimIndir = function (satirlar, dosyaAdi) {
    if (!satirlar || !satirlar.length) return false;
    var blob = new Blob(zipYap(parcalar(satirlar)),
      { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = dosyaAdi || 'nebim.xlsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    return true;
  };
})();
