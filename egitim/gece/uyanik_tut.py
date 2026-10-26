# -*- coding: utf-8 -*-
"""
uyanik_tut.py - Verilen eğitim süreçleri çalıştıkça Windows'un boşta uykuya geçmesini engeller (SetThreadExecutionState).
Sistem ayarını DEĞİŞTİRMEZ; süreç bitince istek kendiliğinden kalkar. Ekranı açık tutmaz.
yazan: [Claude#HtqxxY] · [İP:OCR ayrık el yazısı eğitimi#HtqxxY] · 2026-10-26 · Yusuf'a ait
Kullanım: python uyanik_tut.py PID [PID ...]
"""
import sys, time, ctypes

ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
k32 = ctypes.windll.kernel32


def yasiyor(pid):
    h = k32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    kod = ctypes.c_ulong()
    k32.GetExitCodeProcess(h, ctypes.byref(kod)); k32.CloseHandle(h)
    return kod.value == 259                     # STILL_ACTIVE


if __name__ == "__main__":
    pidler = [int(p) for p in sys.argv[1:]]
    while any(yasiyor(p) for p in pidler):
        k32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        time.sleep(60)
    k32.SetThreadExecutionState(ES_CONTINUOUS)
