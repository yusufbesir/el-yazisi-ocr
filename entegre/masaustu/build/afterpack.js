'use strict';
// electron-builder afterPack kancası.
// signAndEditExecutable=false olduğundan electron-builder exe kaynaklarını (rcedit) düzenlemez;
// bu kanca saf JS 'resedit' ile Tutanak Doldurucu.exe içindeki simgeyi ve sürüm adlarını yazar.
// Herhangi bir hata derlemeyi DURDURUR (sessiz geçilmez).
const fs = require('fs');
const path = require('path');

module.exports = async function afterPack(context) {
  if (context.electronPlatformName !== 'win32') return;

  const { NtExecutable, NtExecutableResource, Data, Resource } = await import('resedit');

  const exeAdi = `${context.packager.appInfo.productFilename}.exe`;
  const exeYolu = path.join(context.appOutDir, exeAdi);
  const icoYolu = path.join(context.packager.projectDir, 'build', 'icon.ico');
  if (!fs.existsSync(exeYolu)) throw new Error(`afterPack: exe bulunamadı: ${exeYolu}`);
  if (!fs.existsSync(icoYolu)) throw new Error(`afterPack: icon.ico bulunamadı: ${icoYolu}`);

  const exe = NtExecutable.from(fs.readFileSync(exeYolu));
  const res = NtExecutableResource.from(exe);

  // Simge: mevcut RT_GROUP_ICON kimliğini koru, yoksa 1 kullan.
  const ikonDosyasi = Data.IconFile.from(fs.readFileSync(icoYolu));
  if (!ikonDosyasi.icons.some((i) => i.data.width === 256)) {
    throw new Error('afterPack: icon.ico 256 piksel girişi içermiyor');
  }
  const gruplar = Resource.IconGroupEntry.fromEntries(res.entries);
  const grupId = gruplar.length ? gruplar[0].id : 1;
  const dil = gruplar.length ? gruplar[0].lang : 1033;
  // Eski gruplar (varsayılan Electron simgesi) tümüyle kaldırılsın ki eski RT_ICON kalıntısı kalmasın.
  res.entries = res.entries.filter((e) => e.type !== 14 && e.type !== 3);
  Resource.IconGroupEntry.replaceIconsForResource(
    res.entries,
    grupId,
    dil,
    ikonDosyasi.icons.map((i) => i.data)
  );

  // Sürüm bilgisi: ProductName / FileDescription = Tutanak Doldurucu; CompanyName dolu ise dokunma.
  const surumler = Resource.VersionInfo.fromEntries(res.entries);
  if (surumler.length) {
    const vi = surumler[0];
    const dilCp = vi.getAllLanguagesForStringValues()[0] || { lang: 1033, codepage: 1200 };
    const mevcut = vi.getStringValues(dilCp) || {};
    const yeni = { ProductName: 'Tutanak Doldurucu', FileDescription: 'Tutanak Doldurucu' };
    if (!mevcut.CompanyName) yeni.CompanyName = 'Tutanak Doldurucu';
    vi.setStringValues(dilCp, yeni);
    vi.outputToResourceEntries(res.entries);
  }

  res.outputResource(exe);
  const cikti = Buffer.from(exe.generate());
  fs.writeFileSync(exeYolu, cikti);
  console.log(`  • afterPack: ${exeAdi} simgesi ve sürüm bilgisi güncellendi (${ikonDosyasi.icons.length} boyut)`);
};
