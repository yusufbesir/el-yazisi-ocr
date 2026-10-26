# zincir.ps1 - gece eğitim zinciri (26.10 03:15 yeniden düzen): Yusuf'un önceliği Türkçe kelime + harf, biraz rakam.
#   1) kelime (CTC kelime tanıyıcı, ayrık + bitişik) 06:35'e kadar  2) harf (Türkçe harf, yeni seçim düzeni) 07:30'a kadar
#   kod (stok kodu rakam) modeli 19 turla durduruldu; son hali kod\son.pt (seçimsiz).
# Düşerse 60 sn bekleyip son.pt'den sürer.
# yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait
$py = 'D:\Programlar\El-Yazisi-OCR\venv\Scripts\python.exe'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
function Kos($betik, $ad, $bitis, $ekarg) {
  $son = [datetime]::ParseExact($bitis, 'HH:mm', $null); if ($son -lt (Get-Date).AddMinutes(-60)) { $son = $son.AddDays(1) }
  while ((Get-Date) -lt $son.AddMinutes(-4)) {
    & $py -X utf8 $betik @ekarg --bitis $bitis --isci 3 --is-parcacigi 8 1>> "$ad-stdout.txt" 2>> "$ad-stderr.txt"
    if ($LASTEXITCODE -eq 0) { break }
    "$ad düştü (kod $LASTEXITCODE) $(Get-Date -Format 'HH:mm'), yeniden" | Add-Content surecler.txt
    Start-Sleep 60
  }
}
Kos 'kelime_egit.py' 'kelime' '06:35' @()
Kos 'gece_egit.py' 'harf' '07:30' @('harf')
"zincir bitti $(Get-Date -Format 'HH:mm')" | Add-Content surecler.txt
