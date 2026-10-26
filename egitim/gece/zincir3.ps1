# zincir3.ps1 - Chars74K'sız SIFIRDAN yeniden eğitim (denetmen, 26.10): kod 20 tur, sonra harf 35 tur. Düşerse son.pt'den sürer.
# yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait
# Başlatmadan önce eski klasörleri yeniden adlandır (silme yok):
#   Rename-Item kod kod-chars74kli ; Rename-Item harf harf-chars74kli
# Başlatma (egitim\gece klasöründen):
#   powershell -NoProfile -ExecutionPolicy Bypass -File zincir3.ps1
$py = 'D:\Programlar\El-Yazisi-OCR\venv\Scripts\python.exe'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
function Kos($gorev, $tur) {
  for ($i = 0; $i -lt 6; $i++) {
    & $py -X utf8 gece_egit.py $gorev --bitis 23:59 --en-cok-tur $tur --isci 3 --is-parcacigi 8 1>> "$gorev-stdout.txt" 2>> "$gorev-stderr.txt"
    if ($LASTEXITCODE -eq 0) { break }
    "$gorev düştü (kod $LASTEXITCODE) $(Get-Date -Format 'HH:mm'), yeniden" | Add-Content surecler.txt
    Start-Sleep 60
  }
}
Kos 'kod' 20
Kos 'harf' 35
"zincir3 bitti $(Get-Date -Format 'HH:mm')" | Add-Content surecler.txt
