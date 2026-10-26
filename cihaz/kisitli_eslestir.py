# -*- coding: utf-8 -*-
# 2026-10-25 T+4 rakam deseni [Claude#RKxwbX]: stok kodu deseni T+4/5 rakam
"""kisitli_eslestir.py - Hazır modellerin ham çıktısını stok kodu listesiyle kısıtlayarak (en yakın geçerli kod) yeniden puanlar.
yazan: [Claude#RKxwbX] · [İP:El yazısı OCR#RKxwbX] · 2026-10-25 · Yusuf'a ait, eğitim amaçlı; değiştirme: yalnız bu iş parçacığı.
Amaç: adil karşılaştırma. Bizim yöntem de kod listesini kullanıyor; hazır modellere de aynı avantaj verilince ne olur?"""
import json, re, sys
dogru = [s["stok"] for s in json.load(open("ornekler/tutanak-1.dogru.json", encoding="utf-8"))["satirlar"]]
kod = json.load(open("ornekler/stok-kodlari.json", encoding="utf-8"))
if not isinstance(kod, list): kod = kod.get("kodlar") or list(kod)
kod = [k for k in kod if re.match(r"^T\d{4,5}(-\d{2})?$", k)]
H = {"O":"0","I":"1","L":"1","S":"5","B":"8","Z":"2","G":"6","Q":"0","D":"0","U":"0","Y":"7"}
def temiz(s):
    s = s.upper().replace("—","-").replace("–","-")
    s = "".join(H.get(c,c) for c in s)
    return re.sub(r"[^T0-9-]", "", s)
def lev(a,b):
    dp=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        yeni=[i]
        for j,cb in enumerate(b,1):
            yeni.append(min(dp[j]+1, yeni[j-1]+1, dp[j-1]+(ca!=cb)))
        dp=yeni
    return dp[-1]
def en_yakin(s):
    t = temiz(s)
    if not t: return None, 99, 99
    puan = sorted((lev(t,k),k) for k in kod)
    (d1,k1),(d2,_) = puan[0], puan[1]
    return k1, d1, d2
r = json.load(open("cihaz/hazir-sonuc.json", encoding="utf-8"))
print("| Model | Ham tam | Kısıtlı tam | Kısıtlı yanlış-kabul (d1<=1 ve d2>d1) | Kısıtlı 'sor' |")
print("|---|---|---|---|---|")
out = {}
for ad, m in r["modeller"].items():
    if "cikti" not in m or m["cikti"][0].startswith("HATA"): continue
    tam=0; yk=0; sor=0; sec=[]
    for c,dg in zip(m["cikti"], dogru):
        k,d1,d2 = en_yakin(c)
        guvenli = (d1 <= 1 and d2 > d1)
        if k == dg: tam += 1
        if guvenli and k != dg: yk += 1
        if not guvenli: sor += 1
        sec.append(f"{k}{'' if k==dg else ' (X)'}{'' if guvenli else ' sor'}")
    out[ad] = sec
    print(f"| {ad} | {m['tam']}/8 | {tam}/8 | {yk} | {sor} |")
print()
for ad, sec in out.items(): print(ad, "->", " | ".join(sec))
