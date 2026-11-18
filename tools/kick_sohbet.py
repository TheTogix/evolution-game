#!/usr/bin/env python3
"""kick_sohbet.py - Kick yayin kaydinin sohbetini indirir.

Ciktiyi TwitchDownloader chat.json bicimiyle yazar, boylece
sohbet_klip.py ile dogrudan kullanilabilir.

Kullanim:
    python kick_sohbet.py https://kick.com/KANAL/videos/UUID -o chat.json

Kick, Cloudflare korumasi kullanir. 403 hatasi alirsan:
    pip install curl_cffi
komutunu calistir; arac bunu otomatik kullanir.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ADIM = 5  # sn: Kick bu kadarlik pencereler halinde mesaj dondurur
BASLIKLAR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/json",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

try:
    from curl_cffi import requests as cffi
except ImportError:
    cffi = None


def getir(url, deneme=4):
    for i in range(deneme):
        try:
            if cffi:
                r = cffi.get(url, impersonate="chrome", timeout=30)
                if r.status_code == 200:
                    return r.json()
                kod = r.status_code
            else:
                req = urllib.request.Request(url, headers=BASLIKLAR)
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            kod = e.code
        except Exception as e:  # ag hatasi: tekrar dene
            kod = str(e)
        if kod == 403 and not cffi:
            sys.exit("Kick erisimi engelledi (403). Su komutu calistirip tekrar dene:\n"
                     "    pip install curl_cffi")
        if kod == 404:
            return None
        time.sleep(2 * (i + 1))
    sys.exit(f"Istek basarisiz ({kod}): {url}")


def uuid_bul(link):
    m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", link)
    if not m:
        sys.exit("Linkte video kimligi bulunamadi. Ornek: "
                 "https://kick.com/kanal/videos/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    return m.group(0)


def zaman_oku(s):
    s = s.replace("Z", "+00:00").replace(" ", "T")
    t = datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def emote_temizle(metin):
    # "[emote:12345:KEKW]" -> "KEKW"
    return re.sub(r"\[emote:\d+:([^\]]+)\]", r"\1", metin or "").strip()


def main():
    p = argparse.ArgumentParser(description="Kick yayin sohbetini indirir.")
    p.add_argument("link", help="Kick video linki")
    p.add_argument("-o", "--cikti", default="chat.json")
    a = p.parse_args()

    uuid = uuid_bul(a.link)
    print("Video bilgisi aliniyor...")
    v = getir(f"https://kick.com/api/v1/video/{uuid}")
    if not v:
        sys.exit("Video bulunamadi.")
    ls = v.get("livestream") or {}
    kanal = ls.get("channel_id") or (ls.get("channel") or {}).get("id")
    bas_str = ls.get("start_time") or v.get("start_time") or v.get("created_at")
    sure_ms = ls.get("duration") or v.get("duration") or 0
    if not kanal or not bas_str or not sure_ms:
        sys.exit("Video bilgisi eksik geldi (kanal/baslangic/sure).")
    bas = zaman_oku(bas_str)
    sure = sure_ms / 1000
    print(f"  baslangic {bas:%Y-%m-%d %H:%M} UTC, sure {sure / 3600:.1f} saat")

    gorulen, yorumlar = set(), []
    adim_say = int(sure // ADIM) + 1
    for i in range(adim_say):
        t = bas + timedelta(seconds=i * ADIM)
        iso = t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        url = (f"https://kick.com/api/v2/channels/{kanal}/messages?"
               + urllib.parse.urlencode({"start_time": iso}))
        veri = getir(url) or {}
        for m in (veri.get("data") or {}).get("messages") or []:
            if m.get("id") in gorulen:
                continue
            gorulen.add(m.get("id"))
            ofset = (zaman_oku(m["created_at"]) - bas).total_seconds()
            if ofset < 0:
                continue
            yorumlar.append({
                "content_offset_seconds": round(ofset, 3),
                "commenter": {"display_name": (m.get("sender") or {}).get("username")},
                "message": {"body": emote_temizle(m.get("content"))},
            })
        if i % 60 == 0 or i == adim_say - 1:
            print(f"  %{100 * (i + 1) // adim_say:3d}  ({len(yorumlar)} mesaj)",
                  flush=True)
        time.sleep(0.15)

    yorumlar.sort(key=lambda y: y["content_offset_seconds"])
    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump({"comments": yorumlar}, f, ensure_ascii=False)
    print(f"Bitti: {a.cikti} ({len(yorumlar)} mesaj)")


if __name__ == "__main__":
    main()
